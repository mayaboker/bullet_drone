"""Physics topic names and payload schemas owned by Bullet Drone."""

GROUND_TRUTH_TOPIC = "physics/ground_truth"
SENSORS_TOPIC = "physics/sensors"


def numeric_vector(size: int, description: str) -> dict:
    return {"type": "array", "items": {"type": "number"}, "minItems": size,
            "maxItems": size, "description": description}


GROUND_TRUTH_SCHEMA = {
    "type": "object",
    "properties": {
        "position_m": numeric_vector(3, "World XYZ position in metres, Z up"),
        "orientation_xyzw": numeric_vector(4, "Body-to-world quaternion in XYZW order"),
        "linear_velocity_m_s": numeric_vector(3, "World XYZ velocity in m/s"),
        "angular_velocity_rad_s": numeric_vector(3, "World angular velocity in rad/s"),
        "rotor_speeds_rad_s": numeric_vector(4, "Actual prop0 to prop3 speeds in rad/s"),
    },
    "required": ["position_m", "orientation_xyzw", "linear_velocity_m_s",
                 "angular_velocity_rad_s", "rotor_speeds_rad_s"],
    "additionalProperties": False,
}

SENSORS_SCHEMA = {
    "type": "object",
    "properties": {name: {"type": ["object", "null"],
                           "description": "Null means unavailable; measurements retain source time/identity"}
                   for name in ("imu", "barometer", "rangefinder")},
    "required": ["imu", "barometer", "rangefinder"],
    "additionalProperties": False,
}
