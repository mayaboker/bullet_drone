"""Simulation lifecycle and observations, independent of a physics library."""

from bullet_drone.commands import InvalidCommandError, RotorCommand
from bullet_drone.contracts import LifecycleError, PhysicsBackend
from bullet_drone.models import DroneObservation


class DroneEnvironment:
    def __init__(self, physics: PhysicsBackend) -> None:
        self._physics = physics
        self._ready = False
        self._closed = False
        self._state = None

    def reset(self) -> DroneObservation:
        if self._closed:
            raise LifecycleError("Cannot reset a closed environment")
        self._ready = False
        state = self._physics.reset()
        self._state = state
        self._ready = True
        return DroneObservation(ground_truth=state)

    def step(self, action: RotorCommand | None = None) -> DroneObservation:
        if self._closed or not self._ready:
            raise LifecycleError("Environment must be reset before stepping and cannot be closed or failed")
        if action is not None:
            if not isinstance(action, RotorCommand):
                raise InvalidCommandError("Action must be a RotorCommand or None")
            action.validate_for(self._state.episode_id, self._state.step_index + 1)
        try:
            state = self._physics.step() if action is None else self._physics.step(action)
            self._state = state
            return DroneObservation(ground_truth=state)
        except InvalidCommandError:
            # Backend limit checks run before any force application or stepping.
            raise
        except BaseException:
            self._ready = False
            raise

    def close(self) -> None:
        self._ready = False
        self._closed = True
        self._physics.close()
