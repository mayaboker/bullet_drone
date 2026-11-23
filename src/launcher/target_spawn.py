"""Read target-scene drone spawn position and yaw."""
from math import isfinite, radians
from pathlib import Path

import yaml

from bullet_drone.config import ConfigurationError


def load_target_spawn(path: Path) -> tuple[object, float]:
    try:
        values = yaml.safe_load(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ConfigurationError(f'Cannot read target spawn config {path}: {error}') from error
    if not isinstance(values, dict) or set(values) != {'initial_position_m', 'initial_yaw_deg'}:
        raise ConfigurationError('Target spawn config requires initial_position_m and initial_yaw_deg only')
    yaw = values['initial_yaw_deg']
    if type(yaw) not in (int, float) or not isfinite(yaw):
        raise ConfigurationError('initial_yaw_deg must be a finite number')
    return values['initial_position_m'], radians(float(yaw))
