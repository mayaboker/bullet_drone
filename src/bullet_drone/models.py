"""Immutable data exchanged across simulation component boundaries."""

from dataclasses import dataclass, field

type Vector3 = tuple[float, float, float]
type Quaternion = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class DroneState:
    episode_id: str
    step_index: int
    simulation_time_s: float
    position_m: Vector3
    orientation_xyzw: Quaternion
    linear_velocity_m_s: Vector3
    angular_velocity_rad_s: Vector3


@dataclass(frozen=True, slots=True)
class SensorReadings:
    """Sensor slots reserved for the next milestone; no models run yet."""

    imu: None = None
    barometer: None = None
    rangefinder: None = None


@dataclass(frozen=True, slots=True)
class DroneObservation:
    ground_truth: DroneState
    sensors: SensorReadings = field(default_factory=SensorReadings)
