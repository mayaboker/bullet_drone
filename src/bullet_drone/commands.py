"""Requested actuator output and immutable, episode-scoped motor commands."""

from dataclasses import dataclass
from math import isfinite

from bullet_drone.models import RotorSpeeds, Vector3


class InvalidCommandError(ValueError):
    """A command is invalid; rejecting it must not advance physics."""


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidCommandError(f"{name} must be a finite number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise InvalidCommandError(f"{name} must be finite") from exc
    if not isfinite(result):
        raise InvalidCommandError(f"{name} must be finite")
    return result


def _values(value: object, count: int, name: str) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != count:
        raise InvalidCommandError(f"{name} must contain exactly {count} numbers")
    return tuple(_finite(item, name) for item in value)


@dataclass(frozen=True, slots=True)
class WrenchCommand:
    """Requested collective thrust (+body Z), and torque in body axes."""

    thrust_n: float
    torque_nm: Vector3 = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        thrust = _finite(self.thrust_n, "thrust_n")
        if thrust < 0:
            raise InvalidCommandError("thrust_n cannot be negative")
        object.__setattr__(self, "thrust_n", thrust)
        object.__setattr__(self, "torque_nm", _values(self.torque_nm, 3, "torque_nm"))


@dataclass(frozen=True, slots=True)
class RotorCommand:
    """Speeds in rad/s, ordered prop0 to prop3, for one next physics step."""

    speeds_rad_s: RotorSpeeds
    episode_id: str
    step_index: int

    def __post_init__(self) -> None:
        speeds = _values(self.speeds_rad_s, 4, "speeds_rad_s")
        if any(speed < 0 for speed in speeds):
            raise InvalidCommandError("Rotor speeds cannot be negative")
        if not isinstance(self.episode_id, str) or not self.episode_id:
            raise InvalidCommandError("episode_id must be a nonempty string")
        if type(self.step_index) is not int or self.step_index <= 0:
            raise InvalidCommandError("step_index must be a positive integer")
        object.__setattr__(self, "speeds_rad_s", speeds)

    def validate_for(self, episode_id: str, next_step: int, max_speed_rad_s: float | None = None) -> None:
        if self.episode_id != episode_id or self.step_index != next_step:
            raise InvalidCommandError("Rotor command is stale or belongs to another episode/step")
        if max_speed_rad_s is not None and any(speed > max_speed_rad_s for speed in self.speeds_rad_s):
            raise InvalidCommandError(f"Rotor speed exceeds the {max_speed_rad_s:.3f} rad/s motor limit")


@dataclass(frozen=True, slots=True)
class MotorAllocation:
    requested: WrenchCommand
    achieved: WrenchCommand
    speeds_rad_s: RotorSpeeds
    rotor_thrusts_n: tuple[float, float, float, float]
    saturated: bool
    torque_scale: float
