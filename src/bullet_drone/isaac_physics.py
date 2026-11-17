"""Isaac Sim PhysX adapter matching PyBulletPhysics interface. Runs headless."""

import math
from uuid import uuid4

from bullet_drone.commands import InvalidCommandError, RotorCommand, _values
from bullet_drone.config import SimulationConfig
from bullet_drone.contracts import BackendError, LifecycleError, MotorDynamics, PropellerModel
from bullet_drone.actuators import IdealMotorDynamics
from bullet_drone.propellers import IdealPropellerModel
from bullet_drone.models import DroneState, ForceOutput, PropellerOutput, RotorSpeeds, SurfaceHit, Vector3
from bullet_drone.forces.chain import ForceChain
from bullet_drone.vehicle import VehicleParameters, load_racer_parameters


ROTOR_COUNT = 4
VECTOR_COMPONENTS = 3

_shared_app = None
_shared_interfaces = None


def _body_to_world(vector, quat_xyzw):
    """Rotate a body-frame vector to world frame using quaternion (x,y,z,w)."""
    x, y, z, w = quat_xyzw
    vx, vy, vz = vector
    tx = 2 * (y * vz - z * vy)
    ty = 2 * (z * vx - x * vz)
    tz = 2 * (x * vy - y * vx)
    return (vx + w * tx + y * tz - z * ty,
            vy + w * ty + z * tx - x * tz,
            vz + w * tz + x * ty - y * tx)


class IsaacPhysics:
    def __init__(self, config: SimulationConfig, vehicle: VehicleParameters | None = None, *,
                 motor_dynamics: MotorDynamics | None = None, propeller_model: PropellerModel | None = None) -> None:
        self._config = config
        self._vehicle = vehicle if vehicle is not None else load_racer_parameters()
        self._motors = motor_dynamics if motor_dynamics is not None else IdealMotorDynamics(self._vehicle.max_speed_rad_s)
        self._propellers = propeller_model if propeller_model is not None else IdealPropellerModel(self._vehicle)
        self._forces = ForceChain(config.forces, config.wind, self._vehicle)
        self._rotor_speeds = (0.0, 0.0, 0.0, 0.0)
        self._app = None
        self._stage = None
        self._drone_path = '/Drone'
        self._closed = False
        self._failed = False
        self._episode_id = ""
        self._step_index = 0
        self._sim_iface = None
        self._scene_query = None
        self._stage_id = None
        self._body_path_int = None

    def _ensure_app(self):
        """Lazy-init SimulationApp once per process, shared across instances."""
        global _shared_app, _shared_interfaces
        if _shared_app is not None:
            self._app = _shared_app
            self._physx_iface, self._sim_iface, self._scene_query, self._timeline = _shared_interfaces
            return
        from isaacsim import SimulationApp
        self._app = SimulationApp({'headless': True, 'renderer': 'disabled'})
        import carb.settings
        import omni.physx
        import omni.timeline
        settings = carb.settings.get_settings()
        settings.set("/physics/updateToUsd", True)
        settings.set("/physics/updateVelocitiesToUsd", True)
        self._physx_iface = omni.physx.get_physx_interface()
        self._sim_iface = omni.physx.get_physx_simulation_interface()
        self._scene_query = omni.physx.get_physx_scene_query_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        _shared_app = self._app
        _shared_interfaces = (self._physx_iface, self._sim_iface, self._scene_query, self._timeline)

    def _build_stage(self):
        """Create a fresh stage with physics scene, ground and drone."""
        import omni.usd
        from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema, UsdUtils
        from pxr import PhysicsSchemaTools

        ctx = omni.usd.get_context()
        ctx.new_stage()
        self._app.update()
        stage = ctx.get_stage()
        self._stage = stage

        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)

        gx, gy, gz = self._config.simulation.gravity_m_s2
        scene = UsdPhysics.Scene.Define(stage, '/PhysicsScene')
        mag = math.sqrt(gx * gx + gy * gy + gz * gz)
        if mag > 0:
            scene.CreateGravityDirectionAttr(Gf.Vec3f(gx / mag, gy / mag, gz / mag))
            scene.CreateGravityMagnitudeAttr(mag)
        else:
            scene.CreateGravityMagnitudeAttr(0.0)

        physx_scene = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
        hz = round(1.0 / self._config.simulation.timestep_s)
        physx_scene.CreateTimeStepsPerSecondAttr(hz)
        physx_scene.CreateEnableGPUDynamicsAttr(False)

        ground = UsdGeom.Cube.Define(stage, '/Ground')
        ground.CreateSizeAttr(1.0)
        ground.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.5))
        ground.AddScaleOp().Set(Gf.Vec3d(1000, 1000, 1))
        UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

        drone = UsdGeom.Xform.Define(stage, self._drone_path)
        pos = self._config.drone.initial_position_m
        self._translate_op = drone.AddTranslateOp()
        self._translate_op.Set(Gf.Vec3d(*pos))
        self._orient_op = drone.AddOrientOp()
        self._orient_op.Set(Gf.Quatf(1, 0, 0, 0))

        col = UsdGeom.Sphere.Define(stage, self._drone_path + '/Collision')
        col.CreateRadiusAttr(0.06)
        col.CreatePurposeAttr('guide')
        UsdPhysics.CollisionAPI.Apply(col.GetPrim())

        UsdPhysics.RigidBodyAPI.Apply(drone.GetPrim())
        mass_api = UsdPhysics.MassAPI.Apply(drone.GetPrim())
        mass_api.CreateMassAttr(self._config.drone.mass_kg)
        nominal_mass = 0.830
        scale = self._config.drone.mass_kg / nominal_mass
        inertia = 0.003113 * scale
        mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(inertia, inertia, inertia))

        physx_rb = PhysxSchema.PhysxRigidBodyAPI.Apply(drone.GetPrim())
        physx_rb.CreateLinearDampingAttr(0.0)
        physx_rb.CreateAngularDampingAttr(0.0)
        physx_rb.CreateSleepThresholdAttr(0.0)
        physx_rb.CreateStabilizationThresholdAttr(0.0)
        physx_rb.CreateDisableGravityAttr(False)

        self._stage_id = UsdUtils.StageCache.Get().Insert(stage).ToLongInt()
        self._body_path_int = PhysicsSchemaTools.sdfPathToInt(drone.GetPrim().GetPath())

    def reset(self) -> DroneState:
        if self._closed:
            raise LifecycleError("Cannot reset a closed physics backend")
        try:
            self._ensure_app()
            from pxr import Gf
            if self._stage is None:
                self._timeline.stop()
                self._app.update()
                self._build_stage()
                self._physx_iface.force_load_physics_from_usd()
                self._app.update()
                self._timeline.play()
                self._app.update()
                self._timeline.stop()
                self._app.update()
            prim = self._stage.GetPrimAtPath(self._drone_path)
            prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*self._config.drone.initial_position_m))
            prim.GetAttribute('xformOp:orient').Set(Gf.Quatf(1, 0, 0, 0))
            self._physx_iface.force_load_physics_from_usd()
            self._app.update()

            self._episode_id = str(uuid4())
            self._step_index = 0
            self._rotor_speeds = self._validated_speeds(self._motors.reset(), 1)
            if any(self._rotor_speeds):
                raise BackendError("Motor reset must return stopped rotors")
            self._forces.reset()
            self._failed = False
            return self._state()
        except BaseException as exc:
            self._failed = True
            if isinstance(exc, (KeyboardInterrupt, SystemExit, BackendError)):
                raise
            if isinstance(exc, Exception):
                raise BackendError(f"Could not initialize Isaac PhysX world: {exc}") from exc
            raise

    @property
    def wind(self):
        return self._forces.wind

    def set_wind(self, settings):
        if self._closed or self._stage is None or self._failed:
            raise LifecycleError('Physics must be initialized before updating wind')
        self._forces.set_wind(settings, self._step_index * self._config.simulation.timestep_s)

    def step(self, command: RotorCommand | None = None) -> DroneState:
        if self._closed or self._stage is None or self._failed:
            raise LifecycleError("Physics must be reset before stepping and cannot be closed or failed")
        if command is not None:
            if not isinstance(command, RotorCommand):
                raise InvalidCommandError("Physics requires a RotorCommand or None")
            command.validate_for(self._episode_id, self._step_index + 1, self._vehicle.max_speed_rad_s)
        speeds = command.speeds_rad_s if command is not None else (0.0, 0.0, 0.0, 0.0)
        try:
            actual = self._motors.update(speeds, self._config.simulation.timestep_s)
            self._rotor_speeds = self._validated_speeds(actual, self._step_index + 1)
            output = self._propellers.calculate(self._rotor_speeds)
            self._validate_propeller_output(output)
            state = self._state()
            forces = self._forces.calculate(state, self._rotor_speeds, output, self)
            self._validate_force_output(forces)
            self._apply_forces(forces, state)
            dt = self._config.simulation.timestep_s
            self._sim_iface.simulate(dt, self._step_index * dt)
            self._sim_iface.fetch_results()
            self._step_index += 1
            return self._state()
        except BaseException as exc:
            self._failed = True
            if not isinstance(exc, Exception):
                raise
            if isinstance(exc, BackendError):
                raise
            raise BackendError(f"Isaac PhysX step failed: {exc}") from exc

    def _validated_speeds(self, speeds: RotorSpeeds, next_step: int) -> RotorSpeeds:
        command = RotorCommand(speeds, self._episode_id, next_step)
        command.validate_for(self._episode_id, next_step, self._vehicle.max_speed_rad_s)
        return command.speeds_rad_s

    @staticmethod
    def _validate_propeller_output(output: PropellerOutput) -> None:
        if not isinstance(output, PropellerOutput) or len(output.forces_n) != 4:
            raise BackendError("Propeller model must return four forces and reaction torque")
        for force in output.forces_n:
            _values(force, 3, "propeller force")
        _values(output.reaction_torque_nm, 3, "reaction torque")

    @staticmethod
    def _validate_force_output(output: ForceOutput) -> None:
        if not isinstance(output, ForceOutput) or len(output.rotor_forces_n) != ROTOR_COUNT:
            raise BackendError("Force chain must return four rotor forces, body force and body torque")
        for force in (*output.rotor_forces_n, output.body_force_n, output.body_torque_nm):
            _values(force, VECTOR_COMPONENTS, "force chain output")

    def _apply_forces(self, output: ForceOutput, state: DroneState):
        """Apply rotor forces, body force and body torque via PhysX simulation interface."""
        import carb
        orientation = state.orientation_xyzw

        total_force = [0.0, 0.0, 0.0]
        total_torque = [0.0, 0.0, 0.0]

        for body_force, rotor_pos in zip(output.rotor_forces_n, self._vehicle.rotor_positions_m):
            world_force = _body_to_world(body_force, orientation)
            world_pos = _body_to_world(rotor_pos, orientation)
            for i in range(3):
                total_force[i] += world_force[i]
            total_torque[0] += world_pos[1] * world_force[2] - world_pos[2] * world_force[1]
            total_torque[1] += world_pos[2] * world_force[0] - world_pos[0] * world_force[2]
            total_torque[2] += world_pos[0] * world_force[1] - world_pos[1] * world_force[0]

        world_body_force = _body_to_world(output.body_force_n, orientation)
        for i in range(3):
            total_force[i] += world_body_force[i]

        world_body_torque = _body_to_world(output.body_torque_nm, orientation)
        for i in range(3):
            total_torque[i] += world_body_torque[i]

        pos = state.position_m
        self._sim_iface.apply_force_at_pos(
            self._stage_id, self._body_path_int,
            carb.Float3(*total_force),
            carb.Float3(*pos),
        )
        self._sim_iface.apply_torque(
            self._stage_id, self._body_path_int,
            carb.Float3(*total_torque),
        )

    def _state(self) -> DroneState:
        prim = self._stage.GetPrimAtPath(self._drone_path)

        pos = prim.GetAttribute('xformOp:translate').Get()
        orient = prim.GetAttribute('xformOp:orient').Get()
        if orient is None:
            orientation = (0.0, 0.0, 0.0, 1.0)
        else:
            orientation = (float(orient.GetImaginary()[0]),
                           float(orient.GetImaginary()[1]),
                           float(orient.GetImaginary()[2]),
                           float(orient.GetReal()))

        lin_vel_attr = prim.GetAttribute('physics:velocity')
        ang_vel_attr = prim.GetAttribute('physics:angularVelocity')
        if lin_vel_attr and lin_vel_attr.Get() is not None:
            lv = lin_vel_attr.Get()
            linear_velocity = (float(lv[0]), float(lv[1]), float(lv[2]))
        else:
            linear_velocity = (0.0, 0.0, 0.0)
        if ang_vel_attr and ang_vel_attr.Get() is not None:
            av = ang_vel_attr.Get()
            # PhysX angular velocity is in degrees/s; convert to rad/s
            angular_velocity = (math.radians(float(av[0])),
                                math.radians(float(av[1])),
                                math.radians(float(av[2])))
        else:
            angular_velocity = (0.0, 0.0, 0.0)

        return DroneState(
            episode_id=self._episode_id, step_index=self._step_index,
            simulation_time_s=self._step_index * self._config.simulation.timestep_s,
            position_m=(float(pos[0]), float(pos[1]), float(pos[2])),
            orientation_xyzw=orientation,
            linear_velocity_m_s=linear_velocity,
            angular_velocity_rad_s=angular_velocity,
            rotor_speeds_rad_s=self._rotor_speeds,
            drone_id=self._config.drone.drone_id,
        )

    _COLLISION_RADIUS = 0.06
    _RAY_OFFSET = _COLLISION_RADIUS + 0.01

    def surface_below(self, origin_world_m: Vector3, range_m: float) -> SurfaceHit | None:
        """Downward ray from origin, offset below drone collision sphere."""
        if self._stage is None:
            raise BackendError("Physics must be initialized before raycasting")
        import carb
        ox, oy, oz = float(origin_world_m[0]), float(origin_world_m[1]), float(origin_world_m[2])
        origin = carb.Float3(ox, oy, oz - self._RAY_OFFSET)
        direction = carb.Float3(0.0, 0.0, -1.0)
        hit = self._scene_query.raycast_closest(origin, direction, float(range_m))
        if not hit or not hit.get('hit'):
            return None
        if self._drone_path in hit.get('rigidBody', ''):
            return None
        distance = hit['distance'] + self._RAY_OFFSET
        if distance > range_m:
            return None
        normal = hit.get('normal', (0.0, 0.0, 1.0))
        return SurfaceHit(distance, (float(normal[0]), float(normal[1]), float(normal[2])))

    def close(self) -> None:
        self._closed = True
        if self._stage is not None:
            try:
                self._timeline.stop()
            except Exception:
                pass
        self._stage = None
