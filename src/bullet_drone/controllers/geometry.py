"""Right-handed quaternion math: xyzw, body X forward/Y left/Z up."""

from math import atan2, cos, sin, sqrt

from bullet_drone.commands import InvalidCommandError, _values
from bullet_drone.models import Quaternion, Vector3


def normalize(q: Quaternion) -> Quaternion:
    q = _values(q, 4, "orientation_xyzw")
    norm = sqrt(sum(v * v for v in q))
    if not 0 < norm < float("inf"):
        raise InvalidCommandError("Orientation must have finite, nonzero norm")
    return tuple(v / norm for v in q)


def conjugate(q: Quaternion) -> Quaternion:
    return (-q[0], -q[1], -q[2], q[3])


def multiply(a: Quaternion, b: Quaternion) -> Quaternion:
    x, y, z, w = a
    u, v, t, s = b
    return (w*u + x*s + y*t - z*v, w*v - x*t + y*s + z*u,
            w*t + x*v - y*u + z*s, w*s - x*u - y*v - z*t)


def from_rpy(rpy: Vector3) -> Quaternion:
    r, p, y = (v / 2 for v in rpy)
    cr, sr, cp, sp, cy, sy = cos(r), sin(r), cos(p), sin(p), cos(y), sin(y)
    return (sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy,
            cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy)


def world_to_body(vector: Vector3, orientation: Quaternion) -> Vector3:
    vector = _values(vector, 3, "angular_velocity_rad_s")
    q = normalize(orientation)
    return multiply(multiply(conjugate(q), (*vector, 0.0)), q)[:3]


def attitude_error(current: Quaternion, target: Quaternion) -> Vector3:
    """Shortest rotation vector in current body coordinates, radians."""
    q = normalize(multiply(conjugate(normalize(current)), normalize(target)))
    # Canonical sign also makes the exact 180-degree ambiguity deterministic.
    if q[3] < 0 or (q[3] == 0 and next((v for v in q[:3] if v != 0), 0) < 0):
        q = tuple(-v for v in q)
    length = sqrt(sum(v*v for v in q[:3]))
    if length < 1e-12:
        return tuple(2*v for v in q[:3])
    factor = 2 * atan2(length, q[3]) / length
    return tuple(v * factor for v in q[:3])


def yaw_from_quaternion(orientation: Quaternion) -> float:
    """World ZYX heading in radians from a body-to-world quaternion."""
    x, y, z, w = normalize(orientation)
    return atan2(2 * (w*z + x*y), 1 - 2 * (y*y + z*z))
