"""Current-episode collision acceptance; no physics or geometry mutation."""
from collections import deque
from copy import deepcopy
import time
from math import isfinite
from loguru import logger

from bullet_msgs.scenario import COLLISION_MAX_AGE_S, validate_collision, validate_end


HISTORY_CAPACITY = 241
MICROSECONDS_PER_SECOND = 1_000_000
LIFTOFF_CLEARANCE_M = .20
ARM_INDEX = 4
ARM_THRESHOLD = 1500


class ScenarioTermination:
    def __init__(self, *, clock=time.monotonic, mission_gated=False):
        self.clock = clock
        self.mission_gated = mission_gated
        self.mission_start_step = None
        self.terrain_enabled = False
        self.history = deque(maxlen=HISTORY_CAPACITY)
        self.result = None

    def reset(self):
        self.stop_mission()
        self.result = None

    def stop_mission(self):
        self.mission_start_step = None
        self.terrain_enabled = False
        self.history.clear()

    def command(self, packet, next_step):
        """Caller supplies only an accepted, currently valid owner command."""
        if not isinstance(packet, dict) or not packet['active']:
            return
        started = (packet['mission_started'] if packet['schema_version'] == 2 else
                   packet['channels'][ARM_INDEX] >= ARM_THRESHOLD)
        if started and self.mission_start_step is None:
            self.history.clear()
            self.mission_start_step = next_step
            logger.info('Collision target gate enabled at mission step {}', next_step)

    def terrain_collision(self, *, step, clearance_m, contact):
        if self.mission_start_step is None or step < self.mission_start_step:
            return False
        if not self.terrain_enabled and isfinite(clearance_m) and clearance_m >= LIFTOFF_CLEARANCE_M and not contact:
            self.terrain_enabled = True
            logger.info('Terrain collision gate enabled after liftoff: clearance={} m step={}', clearance_m, step)
        return self.terrain_enabled and contact

    def observe(self, source):
        if self.mission_gated and (self.mission_start_step is None or source['step_index'] < self.mission_start_step):
            return
        self.history.append(dict(source))
        cutoff = source['measurement_us'] - COLLISION_MAX_AGE_S * MICROSECONDS_PER_SECOND
        while len(self.history) > 1 and self.history[0]['measurement_us'] < cutoff:
            self.history.popleft()

    def accept(self, report, *, controller_id, running, controller_live):
        validate_collision(report)
        if self.result is not None or not running or not controller_live or report['controller_id'] != controller_id:
            return False
        now = self.clock()
        if any(not 0 <= now - report[k] / MICROSECONDS_PER_SECOND <= COLLISION_MAX_AGE_S
               for k in ('issued_us',)):
            return False
        source = report['source']
        if not 0 <= now - source['measurement_us'] / MICROSECONDS_PER_SECOND <= COLLISION_MAX_AGE_S:
            return False
        if source not in self.history:
            return False
        result = dict(schema_version=1, event_id=report['event_id'], collision=deepcopy(report),
                      final_source=dict(self.history[-1]), outcome='success', reason='target_hit',
                      ended_us=int(now * MICROSECONDS_PER_SECOND))
        validate_end(result)
        self.result = result
        return True
