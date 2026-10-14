"""Small backend-independent lifecycle contracts."""

from typing import Protocol

from bullet_drone.commands import HighLevelCommand, RcInput, RotorCommand, WrenchCommand
from bullet_drone.models import ControlFeedback, DroneObservation, DroneState, PropellerOutput, RotorSpeeds


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
    """Runner-owned episode reset and resource cleanup, plus next-step command."""

    def reset(self, observation: DroneObservation) -> None: ...
    def close(self) -> None: ...
    def command(self, observation: DroneObservation) -> RotorCommand: ...


class HighLevelController(Protocol):
    def reset(self, observation: DroneObservation) -> None: ...
    def command(self, observation: DroneObservation, dt_s: float) -> HighLevelCommand: ...
    def close(self) -> None: ...


class FeedbackSource(Protocol):
    def read(self, observation: DroneObservation) -> ControlFeedback: ...


class StabilizationController(Protocol):
    def reset(self) -> None: ...
    def update(self, command: HighLevelCommand, feedback: ControlFeedback, dt_s: float) -> WrenchCommand: ...


class MotorDynamics(Protocol):
    """Four prop0–prop3 actual rad/s; reset stops motors, update uses positive dt."""

    def reset(self) -> RotorSpeeds: ...
    def update(self, targets_rad_s: RotorSpeeds, dt_s: float) -> RotorSpeeds: ...


class PropellerModel(Protocol):
    """Actual rad/s to body-frame forces and reaction torque; no integration."""

    def calculate(self, speeds_rad_s: RotorSpeeds) -> PropellerOutput: ...


class RcInterface(HighLevelController, Protocol):
    """18-channel RC input, translated to episode-scoped commands."""

    def set_input(self, value: RcInput) -> None: ...


class ObservationConsumer(Protocol):
    """Read-only completed observations; runner owns lifecycle."""
    def reset(self, observation: DroneObservation) -> None: ...
    def consume(self, observation: DroneObservation) -> None: ...
    def close(self) -> None: ...
