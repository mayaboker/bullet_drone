"""World XYZ position control to Angle joystick input (SI, Z up)."""
from math import asin, atan2, cos, hypot, sin, tan

from bullet_drone.commands import InvalidCommandError, JoystickInput, _finite, _values
from bullet_drone.config import ConfigurationError, _number
from bullet_drone.controllers.altitude import AltitudeController
from bullet_drone.controllers.pid import PID, PidSettings
from bullet_drone.models import Vector3


class PositionController:
    """XY PID cascade and vertical force to body +Z collective and ZYX angles.

    Position PID outputs m/s, velocity PID m/s². Tilt bounds the horizontal
    force vector relative to vertical force; thrust magnitude includes tilt
    compensation. Feedback is ground-truth position/velocity, not an estimator.
    """
    def __init__(self, altitude: AltitudeController, position_pid: PidSettings,
                 velocity_pid: PidSettings, max_tilt_rad: float) -> None:
        self.altitude = altitude
        self.max_tilt_rad = _number(max_tilt_rad, 'position.max_tilt_rad', positive=True)
        if self.max_tilt_rad >= 1.0471975512:
            raise ConfigurationError('position.max_tilt_rad must be less than 60 degrees')
        self.position = tuple(PID(position_pid) for _ in range(2))
        self.velocity = tuple(PID(velocity_pid) for _ in range(2))

    def reset(self) -> None:
        self.altitude.reset()
        for pid in (*self.position, *self.velocity):
            pid.reset()

    def input(self, target_position_m: Vector3, position_m: Vector3,
              velocity_m_s: Vector3, dt_s: float, *, yaw_rad: float = 0.0,
              descent_speed_limit_m_s: float | None = None) -> JoystickInput:
        target = _values(target_position_m, 3, 'target_position_m')
        position = _values(position_m, 3, 'position_m')
        velocity = _values(velocity_m_s, 3, 'velocity_m_s')
        dt = _finite(dt_s, 'dt_s')
        yaw = _finite(yaw_rad, 'yaw_rad')
        if dt <= 0:
            raise InvalidCommandError('dt_s must be positive')
        if descent_speed_limit_m_s is not None:
            if _finite(descent_speed_limit_m_s, 'descent_speed_limit_m_s') <= 0:
                raise InvalidCommandError('descent_speed_limit_m_s must be positive')
        speeds = [pid.update(target[i], position[i], dt) for i, pid in enumerate(self.position)]
        # Bound horizontal vector magnitude, rather than allowing faster diagonals.
        speed_limit = min(pid.settings.output_limit for pid in self.position)
        factor = min(1.0, speed_limit / max(hypot(*speeds), 1e-12))
        accelerations = [pid.update(speeds[i] * factor, velocity[i], dt) for i, pid in enumerate(self.velocity)]
        fz = self.altitude.thrust(target[2], position[2], velocity[2], dt, descent_speed_limit_m_s)
        fx, fy = (a * self.altitude.mass_kg for a in accelerations)
        horizontal = hypot(fx, fy)
        factor = min(1.0, fz * tan(self.max_tilt_rad) / max(horizontal, 1e-12))
        fx, fy = fx * factor, fy * factor
        thrust = hypot(fx, fy, fz)
        roll = asin(max(-1.0, min(1.0, (fx * sin(yaw) - fy * cos(yaw)) / max(thrust, 1e-12))))
        pitch = atan2(fx * cos(yaw) + fy * sin(yaw), fz)
        return JoystickInput('angle', (roll, pitch, yaw), min(thrust, self.altitude.max_thrust_n), True)
