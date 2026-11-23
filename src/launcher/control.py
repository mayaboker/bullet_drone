"""Apply simulation commands at launcher loop boundaries."""
import time
from uuid import uuid4

from bullet_simulation_protocol.requests import CommandRequest, OperationReply
from bullet_simulation_protocol.state import SimulationState
from bullet_simulation_protocol.transport import ZmqIo


MAX_QUEUE_AGE_S = 1.0
MAX_REASON_LENGTH = 256


class SimulationControl:
    def __init__(self, endpoint, observation, on_state, *, clock=time.monotonic):
        self.io = ZmqIo(reply_endpoint=endpoint)
        self.clock = clock
        self.on_state = on_state
        self.session_id = uuid4().hex
        self.episode_id = observation.ground_truth.episode_id
        self.drone_id = observation.ground_truth.drone_id
        self.state = 'running'
        self.revision = 0

    def __enter__(self):
        self.io.start()
        self._publish_state()
        return self

    def __exit__(self, *args):
        self.io.close()

    def _publish_state(self):
        self.on_state(SimulationState(1, self.drone_id, self.session_id,
                                      self.episode_id, self.state, self.revision))

    def _transition(self, state, observation=None):
        if observation is not None:
            self.episode_id = observation.ground_truth.episode_id
        self.state = state
        self.revision += 1
        self._publish_state()

    def update(self, observation, reset_simulation):
        if self.io.error:
            raise RuntimeError(self.io.error)
        message = self.io.poll_request()
        if message is None:
            return observation
        try:
            if not 0 <= self.clock() - message['received_at'] <= MAX_QUEUE_AGE_S:
                raise ValueError('request_expired_in_queue')
            request = CommandRequest.from_dict(message['payload'])
            if request.drone_id != self.drone_id:
                raise ValueError('unknown_drone')
            action = request.payload.action
            if action == 'stop':
                if self.state != 'running':
                    raise ValueError('simulation_not_running')
                self._transition('stopped_reset_required')
            elif action == 'start':
                if self.state != 'stopped_ready':
                    raise ValueError('reset_required' if self.state == 'stopped_reset_required'
                                     else 'simulation_not_ready')
                self._transition('running')
            else:
                if self.state == 'running':
                    raise ValueError('reset_requires_stopped')
                self._transition('resetting')
                try:
                    observation = reset_simulation()
                except Exception:
                    self._transition('error')
                    raise
                self._transition('stopped_ready', observation)
            reply = OperationReply(True)
        except Exception as error:
            reply = OperationReply(False, str(error)[:MAX_REASON_LENGTH] or 'request_failed')
        self.io.reply(message['token'], reply)
        return observation
