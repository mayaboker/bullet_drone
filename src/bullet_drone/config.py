"""Load and validate simulation configuration before acquiring resources."""

from dataclasses import dataclass, field
from math import isfinite, pi
from pathlib import Path

import yaml

from bullet_drone.models import Vector3


class ConfigurationError(ValueError):
    """The configuration cannot describe a valid simulation."""


def _number(value: object, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{name} must be a finite number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ConfigurationError(f"{name} must be a finite number") from exc
    if not isfinite(result) or (positive and result <= 0):
        qualifier = "positive and finite" if positive else "finite"
        raise ConfigurationError(f"{name} must be {qualifier}")
    return result


def _vector(value: object, name: str) -> Vector3:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ConfigurationError(f"{name} must contain exactly three numbers")
    return tuple(_number(item, f"{name}[{i}]") for i, item in enumerate(value))


@dataclass(frozen=True, slots=True)
class SimulationSettings:
    timestep_s: float
    max_steps: int
    gravity_m_s2: Vector3
    gui: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestep_s", _number(self.timestep_s, "simulation.timestep_s", positive=True))
        if type(self.max_steps) is not int or self.max_steps <= 0:
            raise ConfigurationError("simulation.max_steps must be a positive integer")
        object.__setattr__(self, "gravity_m_s2", _vector(self.gravity_m_s2, "simulation.gravity_m_s2"))
        if type(self.gui) is not bool:
            raise ConfigurationError("simulation.gui must be a boolean")


@dataclass(frozen=True, slots=True)
class DroneSettings:
    mass_kg: float
    initial_position_m: Vector3

    def __post_init__(self) -> None:
        object.__setattr__(self, "mass_kg", _number(self.mass_kg, "drone.mass_kg", positive=True))
        object.__setattr__(self, "initial_position_m", _vector(self.initial_position_m, "drone.initial_position_m"))


@dataclass(frozen=True, slots=True)
class ControlSettings:
    backend: str = "internal"

    def __post_init__(self) -> None:
        if not isinstance(self.backend, str) or self.backend not in ("internal", "betaflight"):
            raise ConfigurationError("control.backend must be 'internal' or 'betaflight'")


@dataclass(frozen=True, slots=True)
class RcSettings:
    """One-based AETR channel assignments, AUX switches and roll/pitch angle scale."""

    aetr_channels: tuple[int, int, int, int] = (1, 2, 3, 4)
    arm_channel: int = 5
    mode_channel: int = 6
    arm_threshold: int = 1500
    angle_threshold: int = 1500
    max_angle_rad: float = pi / 4

    def __post_init__(self) -> None:
        channels = self.aetr_channels
        if not isinstance(channels, (tuple, list)) or len(channels) != 4:
            raise ConfigurationError("rc.aetr_channels requires four channel numbers")
        assignments = (*channels, self.arm_channel, self.mode_channel)
        if (any(type(v) is not int for v in assignments)
                or set(channels) != {1, 2, 3, 4}
                or not 5 <= self.arm_channel <= 18 or not 5 <= self.mode_channel <= 18
                or len(set(assignments)) != 6):
            raise ConfigurationError("AETR must permute CH1..4; distinct arm/mode AUX channels must be in CH5..18")
        object.__setattr__(self, 'aetr_channels', tuple(channels))
        for name in ('arm_threshold', 'angle_threshold'):
            value = getattr(self, name)
            if type(value) is not int or not 1000 < value <= 2000:
                raise ConfigurationError(f"rc.{name} must be an integer in 1001..2000")
        angle = _number(self.max_angle_rad, 'rc.max_angle_rad', positive=True)
        if angle >= pi / 2:
            raise ConfigurationError('rc.max_angle_rad must be less than pi/2')
        object.__setattr__(self, 'max_angle_rad', angle)


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    simulation: SimulationSettings
    drone: DroneSettings
    control: ControlSettings = field(default_factory=ControlSettings)
    rc: RcSettings = field(default_factory=RcSettings)

    def __post_init__(self) -> None:
        if not isinstance(self.rc, RcSettings):
            raise ConfigurationError('rc must be RcSettings')


def _mapping(value: object, name: str, required: set[str], optional: set[str] | None = None) -> dict:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{name} must be a mapping")
    unknown = value.keys() - required - (optional or set())
    missing = required - value.keys()
    if unknown:
        raise ConfigurationError(f"{name} has unknown keys: {', '.join(sorted(map(str, unknown)))}")
    if missing:
        raise ConfigurationError(f"{name} is missing: {', '.join(sorted(missing))}")
    return value


class YamlConfigLoader:
    def load(self, path: str | Path) -> SimulationConfig:
        try:
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise ConfigurationError(f"Cannot read YAML configuration {path}: {exc}") from exc
        root = _mapping(data, "configuration", {"simulation", "drone"}, {"control", "rc"})
        simulation = _mapping(
            root["simulation"], "simulation",
            {"timestep_s", "max_steps", "gravity_m_s2"}, {"gui"},
        )
        drone = _mapping(root["drone"], "drone", {"mass_kg", "initial_position_m"})
        control = ControlSettings(**_mapping(root["control"], "control", set(), {"backend"})) if "control" in root else ControlSettings()
        rc = RcSettings(**_mapping(root['rc'], 'rc', set(), set(RcSettings.__dataclass_fields__))) if 'rc' in root else RcSettings()
        return SimulationConfig(SimulationSettings(**simulation), DroneSettings(**drone), control, rc)
