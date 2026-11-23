"""Authoritative launcher lifecycle state sent over ZeroMQ."""
from dataclasses import dataclass

from .wind import DictionaryMessage


STATE_TOPIC = b'simulation/drone_1/state'
DEFAULT_CONTROL_ENDPOINT = 'tcp://127.0.0.1:5561'
DEFAULT_STATE_ENDPOINT = 'tcp://127.0.0.1:5555'
STATES = frozenset(('running', 'stopped_reset_required', 'resetting', 'stopped_ready', 'error'))


@dataclass(frozen=True)
class SimulationState(DictionaryMessage):
    schema_version: int
    drone_id: str
    session_id: str
    episode_id: str
    state: str
    revision: int

    def __post_init__(self):
        if (type(self.schema_version) is not int or self.schema_version != 1
                or self.drone_id != 'drone_1' or not isinstance(self.session_id, str)
                or len(self.session_id) != 32 or any(c not in '0123456789abcdef' for c in self.session_id)
                or not isinstance(self.episode_id, str) or not self.episode_id
                or self.state not in STATES or type(self.revision) is not int or self.revision < 0):
            raise ValueError('invalid simulation state')

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) != set(cls.__dataclass_fields__):
            raise ValueError('invalid simulation state fields')
        return cls(**value)
