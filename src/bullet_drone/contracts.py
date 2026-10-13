"""Small backend-independent lifecycle contracts."""

from typing import Protocol

from bullet_drone.commands import RotorCommand
from bullet_drone.models import DroneObservation, DroneState


class LifecycleError(RuntimeError):
    """An operation was requested before reset or after close/failure."""


class BackendError(RuntimeError):
    """A physics operation failed; the current episode cannot continue."""


class PhysicsBackend(Protocol):
    def reset(self) -> DroneState: ...
    def step(self, command: RotorCommand | None = None) -> DroneState: ...
    def close(self) -> None: ...


class SimulationEnvironment(Protocol):
    def reset(self) -> DroneObservation: ...
    def step(self, action: RotorCommand | None = None) -> DroneObservation: ...
    def close(self) -> None: ...


class CommandProvider(Protocol):
    def command(self, observation: DroneObservation) -> RotorCommand: ...
