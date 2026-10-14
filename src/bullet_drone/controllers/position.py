"""World XYZ position control to Angle RC input (PWM-style channels, Z up)."""
from dataclasses import dataclass
from math import asin, atan2, cos, hypot, sin, tan

from bullet_drone.commands import InvalidCommandError, RcInput, _finite, _values
from bullet_drone.config import ConfigurationError, _number
from bullet_drone.controllers.altitude import AltitudeController
from bullet_drone.controllers.pid import PID, PidSettings
from bullet_drone.models import Vector3
from bullet_drone.rc import RcCodec, heading_rate


@dataclass(frozen=True, slots=True)
class PositionControlOutput:
    """Last completed PID calculation, world-frame SI values before tilt clipping."""
    velocity_target_m_s: Vector3
    acceleration_m_s2: Vector3
    rc_input: RcInput


class PositionController:
    """XY PID cascade and vertical force to body +Z collective and ZYX angles.

    Position PID outputs m/s, velocity PID m/s². Tilt bounds the horizontal
    force vector relative to vertical force; thrust magnitude includes tilt
    compensation. Feedback is ground-truth position/velocity, not an estimator.
    """
    def __init__(self, altitude: AltitudeController, position_pid: PidSettings,
                 velocity_pid: PidSettings, max_tilt_rad: float, rc_codec: RcCodec | None = None) -> None:
        self.rc_codec = rc_codec if rc_codec is not None else RcCodec(altitude.max_thrust_n)
        self.altitude = altitude
        self.max_tilt_rad = _number(max_tilt_rad, 'position.max_tilt_rad', positive=True)
        if self.max_tilt_rad >= 1.0471975512:
            raise ConfigurationError('position.max_tilt_rad must be less than 60 degrees')
        self.position = tuple(PID(position_pid) for _ in range(2))
        self.velocity = tuple(PID(velocity_pid) for _ in range(2))
        self.last_output: PositionControlOutput | None = None

    def reset(self) -> None:
        self.last_output = None
        self.altitude.reset()
        for pid in (*self.position, *self.velocity):
            pid.reset()

    def input(self, target_position_m: Vector3, position_m: Vector3,
              velocity_m_s: Vector3, dt_s: float, *, yaw_rad: float = 0.0, measured_yaw_rad: float = 0.0,
              descent_speed_limit_m_s: float | None = None) -> RcInput:
        target = _values(target_position_m, 3, 'target_position_m')
        position = _values(position_m, 3, 'position_m')
        velocity = _values(velocity_m_s, 3, 'velocity_m_s')
        dt = _finite(dt_s, 'dt_s')
        target_yaw = _finite(yaw_rad, 'yaw_rad')
        yaw = _finite(measured_yaw_rad, 'measured_yaw_rad')
        if dt <= 0:
            raise InvalidCommandError('dt_s must be positive')
        if descent_speed_limit_m_s is not None:
            if _finite(descent_speed_limit_m_s, 'descent_speed_limit_m_s') <= 0:
                raise InvalidCommandError('descent_speed_limit_m_s must be positive')
        speeds = [pid.update(target[i], position[i], dt) for i, pid in enumerate(self.position)]
        # Bound horizontal vector magnitude, rather than allowing faster diagonals.
        speed_limit = min(pid.settings.output_limit for pid in self.position)
        factor = min(1.0, speed_limit / max(hypot(*speeds), 1e-12))
        desired_speeds = tuple(v * factor for v in speeds)
        accelerations = [pid.update(desired_speeds[i], velocity[i], dt) for i, pid in enumerate(self.velocity)]
        fz = self.altitude.thrust(target[2], position[2], velocity[2], dt, descent_speed_limit_m_s)
        fx, fy = (a * self.altitude.mass_kg for a in accelerations)
        horizontal = hypot(fx, fy)
        factor = min(1.0, fz * tan(self.max_tilt_rad) / max(horizontal, 1e-12))
        fx, fy = fx * factor, fy * factor
        thrust = hypot(fx, fy, fz)
        roll = asin(max(-1.0, min(1.0, (fx * sin(yaw) - fy * cos(yaw)) / max(thrust, 1e-12))))
        pitch = atan2(fx * cos(yaw) + fy * sin(yaw), fz)
        value = self.rc_codec.encode('angle', (roll, pitch, heading_rate(target_yaw, yaw, self.rc_codec.max_rates_rad_s[2])),
                                     min(thrust, self.altitude.max_thrust_n), True)
        vertical = self.altitude.last_output
        self.last_output = (PositionControlOutput((*desired_speeds, vertical.velocity_target_m_s),
                                                  (*accelerations, vertical.acceleration_m_s2), value)
                            if vertical is not None else None)
        return value
