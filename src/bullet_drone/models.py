"""Immutable data exchanged across simulation component boundaries."""

from dataclasses import dataclass, field

type Vector3 = tuple[float, float, float]
type Quaternion = tuple[float, float, float, float]
type RotorSpeeds = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class DroneState:
    episode_id: str
    step_index: int
    simulation_time_s: float
    position_m: Vector3
    orientation_xyzw: Quaternion
    linear_velocity_m_s: Vector3
    angular_velocity_rad_s: Vector3
    rotor_speeds_rad_s: RotorSpeeds = (0.0, 0.0, 0.0, 0.0)


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


@dataclass(frozen=True, slots=True)
class ControlFeedback:
    """Ideal body-to-world orientation and body-axis angular rates (rad/s)."""

    orientation_xyzw: Quaternion
    body_rates_rad_s: Vector3


@dataclass(frozen=True, slots=True)
class PropellerOutput:
    """Body-frame rotor forces (N), and aggregate body reaction torque (N*m)."""

    forces_n: tuple[Vector3, Vector3, Vector3, Vector3]
    reaction_torque_nm: Vector3
