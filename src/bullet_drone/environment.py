"""Simulation lifecycle and observations, independent of a physics library."""

from bullet_drone.contracts import LifecycleError, PhysicsBackend
from bullet_drone.models import DroneObservation


class DroneEnvironment:
    def __init__(self, physics: PhysicsBackend) -> None:
        self._physics = physics
        self._ready = False
        self._closed = False

    def reset(self) -> DroneObservation:
        if self._closed:
            raise LifecycleError("Cannot reset a closed environment")
        self._ready = False
        state = self._physics.reset()
        self._ready = True
        return DroneObservation(ground_truth=state)

    def step(self, action: None = None) -> DroneObservation:
        if self._closed or not self._ready:
            raise LifecycleError("Environment must be reset before stepping and cannot be closed or failed")
        if action is not None:
            raise ValueError("Only action=None is supported in the gravity-only milestone")
        try:
            return DroneObservation(ground_truth=self._physics.step())
        except BaseException:
            self._ready = False
            raise

    def close(self) -> None:
        self._ready = False
        self._closed = True
        self._physics.close()
