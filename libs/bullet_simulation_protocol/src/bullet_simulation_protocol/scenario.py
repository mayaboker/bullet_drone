"""Renderer collision proposal contracts."""
from typing import TypedDict

from .flight import _id, _integer, _number, _shape, _version, validate_source


COLLISION_TOPIC = b'render/drone_1/collision'
COLLISION_MAX_AGE_S = 1.0
COLLISION_RETRY_S = 0.1
TARGET_ID = 'red_truck'
TARGET_CONTACT_TOPIC = b'simulation/drone_1/target_contact'


def validate_target_contact(value):
    if not isinstance(value, dict) or set(value) != {'schema_version', 'drone_id', 'target_id', 'step_index', 'simulation_time_s'}:
        raise ValueError('invalid target contact fields')
    if value['schema_version'] != 1 or value['target_id'] != TARGET_ID or not isinstance(value['drone_id'], str) or not value['drone_id']:
        raise ValueError('invalid target contact identity')
    if type(value['step_index']) is not int or value['step_index'] < 0:
        raise ValueError('invalid target contact step')
    _number(value['simulation_time_s'])
    if value['simulation_time_s'] < 0:
        raise ValueError('invalid target contact time')
    return value


class CollisionReport(TypedDict):
    schema_version: int
    event_id: str
    controller_id: str
    issued_us: int
    source: dict
    target_id: str
    drone_position_m: list[float]


def validate_collision(value):
    _shape(value, set(CollisionReport.__annotations__))
    _version(value['schema_version'])
    _id(value['event_id'])
    _id(value['controller_id'])
    _integer(value['issued_us'])
    validate_source(value['source'])
    if value['target_id'] != TARGET_ID or value['issued_us'] < value['source']['measurement_us']:
        raise ValueError('invalid collision target/time')
    p = value['drone_position_m']
    if not isinstance(p, (list, tuple)) or len(p) != 3:
        raise ValueError('invalid collision position')
    for component in p:
        _number(component)
    return value
