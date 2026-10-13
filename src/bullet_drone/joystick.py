"""Software joystick translation; no device IO, stabilization, or physics."""

from bullet_drone.commands import HighLevelCommand, InvalidCommandError, JoystickInput, _finite
from bullet_drone.contracts import LifecycleError
from bullet_drone.models import DroneObservation


class SoftwareJoystick:
    def __init__(self) -> None:
        self._input = JoystickInput()
        self._episode_id: str | None = None
        self._next_step = 0
        self._closed = False

    def reset(self, observation: DroneObservation) -> None:
        if self._closed:
            raise LifecycleError("Cannot reset a closed joystick")
        self._input = JoystickInput()
        self._episode_id = observation.ground_truth.episode_id
        self._next_step = observation.ground_truth.step_index + 1

    def set_input(self, value: JoystickInput) -> None:
        self._require_ready()
        if not isinstance(value, JoystickInput):
            raise InvalidCommandError("Joystick requires a JoystickInput")
        self._input = value

    def command(self, observation: DroneObservation, dt_s: float) -> HighLevelCommand:
        self._require_ready()
        if _finite(dt_s, "dt_s") <= 0:
            raise InvalidCommandError("dt_s must be positive")
        state = observation.ground_truth
        if state.episode_id != self._episode_id or state.step_index + 1 != self._next_step:
            raise InvalidCommandError("Joystick observation is stale or belongs to another episode/step")
        value = self._input
        command = HighLevelCommand(value.mode, value.rpy, value.thrust_n,
                                   state.episode_id, self._next_step, value.armed)
        self._next_step += 1
        return command

    def _require_ready(self) -> None:
        if self._closed or self._episode_id is None:
            raise LifecycleError("Joystick must be reset before use")

    def close(self) -> None:
        self._closed = True
        self._episode_id = None
        self._input = JoystickInput()
