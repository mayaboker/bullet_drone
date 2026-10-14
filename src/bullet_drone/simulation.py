"""One joystick request per physics step; the caller owns the execution loop."""

from bullet_drone.commands import HighLevelCommand, InvalidCommandError, JoystickInput, MotorAllocation
from bullet_drone.composition import FlightCommandProvider, validate_control_backend
from bullet_drone.config import SimulationConfig
from bullet_drone.contracts import LifecycleError, MotorDynamics, PropellerModel, StabilizationController
from bullet_drone.controllers import IdealStateFeedback, InternalControlSettings, InternalFlightController
from bullet_drone.environment import DroneEnvironment
from bullet_drone.joystick import SoftwareJoystick
from bullet_drone.mixer import MotorMixer
from bullet_drone.models import DroneObservation
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.vehicle import VehicleParameters, load_racer_parameters


class JoystickSimulation:
    """Own joystick translation, stabilization and physics, but no run loop.

    Inputs use Angle radians or Acro body rad/s and collective newtons. Outputs
    are immutable world-frame ground truth. Optional component injections are
    library contracts for models/probes, not alternative per-step command paths.
    Runtime failures require reset before another step; close is terminal.
    """

    def __init__(self, config: SimulationConfig, control_settings: InternalControlSettings,
                 vehicle: VehicleParameters | None = None, *,
                 stabilization: StabilizationController | None = None,
                 motor_dynamics: MotorDynamics | None = None,
                 propeller_model: PropellerModel | None = None) -> None:
        validate_control_backend(config.control)
        vehicle = vehicle if vehicle is not None else load_racer_parameters()
        self._timestep_s = config.simulation.timestep_s
        self._joystick = SoftwareJoystick()
        self._provider = FlightCommandProvider(
            self._joystick,
            stabilization if stabilization is not None else InternalFlightController(control_settings),
            IdealStateFeedback(), MotorMixer(vehicle), self._timestep_s,
        )
        self._environment = DroneEnvironment(PyBulletPhysics(
            config, vehicle, motor_dynamics=motor_dynamics, propeller_model=propeller_model,
        ))
        self._observation: DroneObservation | None = None
        self._last_command: HighLevelCommand | None = None
        self._closed = False

    @property
    def timestep_s(self) -> float:
        return self._timestep_s

    @property
    def last_command(self) -> HighLevelCommand | None:
        """Read-only identity-stamped command for the last completed step."""
        return self._last_command

    @property
    def allocation(self) -> MotorAllocation | None:
        """Read-only allocation for the last completed armed step."""
        return self._provider.allocation if self._last_command is not None else None

    def reset(self) -> DroneObservation:
        if self._closed:
            raise LifecycleError("Cannot reset a closed joystick simulation")
        self._observation = None
        self._last_command = None
        observation = self._environment.reset()
        self._provider.reset(observation)
        self._observation = observation
        return observation

    def step(self, command: JoystickInput) -> DroneObservation:
        if self._closed or self._observation is None:
            raise LifecycleError("Joystick simulation must be reset before stepping")
        if not isinstance(command, JoystickInput):
            raise InvalidCommandError("Simulation requires a JoystickInput")
        # Revalidate even if a frozen input has been deliberately tampered with.
        value = JoystickInput(command.mode, command.rpy, command.thrust_n, command.armed)
        feedback = self._observation
        self._last_command = None
        try:
            self._joystick.set_input(value)
            rotor_command = self._provider.command(feedback)
            observation = self._environment.step(rotor_command)
        except BaseException:
            # Translation may have consumed the step; never retry it implicitly.
            self._observation = None
            raise
        self._last_command = HighLevelCommand(
            value.mode, value.rpy, value.thrust_n, rotor_command.episode_id,
            rotor_command.step_index, value.armed,
        )
        self._observation = observation
        return observation

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._observation = None
        failure = None
        for resource in (self._provider, self._environment):
            try:
                resource.close()
            except BaseException as exc:
                if failure is None:
                    failure = exc
                else:
                    failure.add_note(f"Additional simulation cleanup failure: {exc}")
        if failure is not None:
            raise failure
