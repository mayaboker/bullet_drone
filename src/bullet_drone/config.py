"""Load and validate simulation configuration before acquiring resources."""

from dataclasses import dataclass, field
from math import isfinite
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
class FlightSettings:
    mode: str = "gravity"

    def __post_init__(self) -> None:
        if not isinstance(self.mode, str) or self.mode not in ("gravity", "hover"):
            raise ConfigurationError("flight.mode must be 'gravity' or 'hover'")


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    simulation: SimulationSettings
    drone: DroneSettings
    flight: FlightSettings = field(default_factory=FlightSettings)

    def __post_init__(self) -> None:
        gravity = self.simulation.gravity_m_s2
        if self.flight.mode == "hover" and (gravity[0] != 0 or gravity[1] != 0 or gravity[2] >= 0):
            raise ConfigurationError("Hover mode requires downward vertical gravity")


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
        root = _mapping(data, "configuration", {"simulation", "drone"}, {"flight"})
        simulation = _mapping(
            root["simulation"], "simulation",
            {"timestep_s", "max_steps", "gravity_m_s2"}, {"gui"},
        )
        drone = _mapping(root["drone"], "drone", {"mass_kg", "initial_position_m"})
        flight = FlightSettings(**_mapping(root["flight"], "flight", {"mode"})) if "flight" in root else FlightSettings()
        return SimulationConfig(SimulationSettings(**simulation), DroneSettings(**drone), flight)
