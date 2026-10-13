"""PyBullet adapter owning one world and no application configuration IO."""

import importlib
from importlib.resources import as_file, files
import os
import sys
from uuid import uuid4

from bullet_drone.config import SimulationConfig
from bullet_drone.contracts import BackendError, LifecycleError
from bullet_drone.models import DroneState


class PyBulletPhysics:
    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self._p = None
        self._client: int | None = None
        self._body: int | None = None
        self._closed = False
        self._failed = False
        self._episode_id = ""
        self._step_index = 0

    def reset(self) -> DroneState:
        if self._closed:
            raise LifecycleError("Cannot reset a closed physics backend")
        try:
            if self._p is None:
                self._p = importlib.import_module("pybullet")
            p = self._p
            settings = self._config.simulation
            if self._client is None:
                # PyBullet can terminate the process when X11 is absent.
                if settings.gui and sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
                    raise BackendError("GUI mode requires an X11 DISPLAY; use gui: false for headless execution")
                client = p.connect(p.GUI if settings.gui else p.DIRECT)
                if client < 0:
                    raise BackendError("Could not connect to PyBullet")
                self._client = client
            self._require_connection()
            client = self._client
            p.resetSimulation(physicsClientId=client)
            p.setRealTimeSimulation(0, physicsClientId=client)
            p.setTimeStep(settings.timestep_s, physicsClientId=client)
            p.setGravity(*settings.gravity_m_s2, physicsClientId=client)
            p.setPhysicsEngineParameter(numSolverIterations=50, physicsClientId=client)
            # Explicitly disable default damping for analytical free-fall checks.
            ground_collision = p.createCollisionShape(p.GEOM_PLANE, physicsClientId=client)
            ground_visual = p.createVisualShape(
                p.GEOM_BOX, halfExtents=[5, 5, 0.01],
                visualFramePosition=[0, 0, -0.01],
                rgbaColor=[0.65, 0.68, 0.7, 1], physicsClientId=client,
            )
            p.createMultiBody(
                baseMass=0, baseCollisionShapeIndex=ground_collision,
                baseVisualShapeIndex=ground_visual,
                basePosition=[0, 0, 0],
                baseInertialFramePosition=[0, 0, 0], physicsClientId=client,
            )
            # Load bundled meshes relative to the URDF, including in an installed wheel.
            with as_file(files("bullet_drone").joinpath("assets/racer")) as assets:
                self._body = p.loadURDF(
                    str(assets / "racer.urdf"),
                    basePosition=self._config.drone.initial_position_m,
                    baseOrientation=[0, 0, 0, 1],
                    flags=p.URDF_USE_INERTIA_FROM_FILE, physicsClientId=client,
                )
            nominal_mass, _, nominal_inertia, *_ = p.getDynamicsInfo(
                self._body, -1, physicsClientId=client,
            )
            mass_scale = self._config.drone.mass_kg / nominal_mass
            p.changeDynamics(
                self._body, -1, mass=self._config.drone.mass_kg,
                localInertiaDiagonal=[component * mass_scale for component in nominal_inertia],
                linearDamping=0, angularDamping=0,
                restitution=0, physicsClientId=client,
            )
            if settings.gui:
                p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0, physicsClientId=client)
                p.resetDebugVisualizerCamera(
                    cameraDistance=2.5, cameraYaw=45, cameraPitch=-25,
                    cameraTargetPosition=self._config.drone.initial_position_m,
                    physicsClientId=client,
                )
            self._episode_id = str(uuid4())
            self._step_index = 0
            self._failed = False
            return self._state()
        except BaseException as exc:
            self._failed = True
            try:
                self._disconnect()
            except Exception as cleanup_error:
                exc.add_note(f"Physics initialization cleanup failed: {cleanup_error}")
            if isinstance(exc, (KeyboardInterrupt, SystemExit, BackendError)):
                raise
            if isinstance(exc, Exception):
                raise BackendError(f"Could not initialize PyBullet world: {exc}") from exc
            raise

    def step(self) -> DroneState:
        if self._closed or self._body is None or self._failed:
            raise LifecycleError("Physics must be reset before stepping and cannot be closed or failed")
        try:
            self._require_connection()
            self._p.stepSimulation(physicsClientId=self._client)
            self._step_index += 1
            return self._state()
        except BaseException as exc:
            self._failed = True
            if not isinstance(exc, Exception):
                raise
            if isinstance(exc, BackendError):
                raise
            raise BackendError(f"PyBullet step failed: {exc}") from exc

    def _require_connection(self) -> None:
        if self._client is None or not self._p.isConnected(self._client):
            raise BackendError("PyBullet connection was lost (the GUI may have been closed)")

    def _state(self) -> DroneState:
        position, orientation = self._p.getBasePositionAndOrientation(self._body, physicsClientId=self._client)
        linear, angular = self._p.getBaseVelocity(self._body, physicsClientId=self._client)
        return DroneState(
            episode_id=self._episode_id, step_index=self._step_index,
            simulation_time_s=self._step_index * self._config.simulation.timestep_s,
            position_m=tuple(position), orientation_xyzw=tuple(orientation),
            linear_velocity_m_s=tuple(linear), angular_velocity_rad_s=tuple(angular),
        )

    def _disconnect(self) -> None:
        if self._client is not None:
            client = self._client
            try:
                if self._p.isConnected(client):
                    self._p.disconnect(physicsClientId=client)
            finally:
                self._client = None
                self._body = None

    def close(self) -> None:
        self._closed = True
        self._disconnect()
