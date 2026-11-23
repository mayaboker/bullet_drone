from types import SimpleNamespace
from unittest.mock import Mock
import json
import socket
import time
import zmq

from bullet_simulation_protocol.state import SimulationState
from bullet_simulation_protocol.requests import CommandPayload, CommandRequest
from bullet_simulation_protocol.transport import ZmqIo
from launcher.control import SimulationControl
from launcher.publisher import RenderPublisher


def observation(episode='first'):
    return SimpleNamespace(ground_truth=SimpleNamespace(drone_id='drone_1', episode_id=episode))


def test_command_lifecycle_and_authoritative_state():
    published = []
    control = SimulationControl('tcp://127.0.0.1:5560', observation(), published.append,
                                clock=lambda: 10.)
    control.io = Mock(error=None)
    current = observation()
    reset = Mock(return_value=observation('second'))

    def command(action, *, drone_id='drone_1', age=0.):
        nonlocal current
        control.io.poll_request.return_value = dict(token='request', received_at=10. - age,
            payload=dict(topic='command', drone_id=drone_id, payload=dict(action=action)))
        current = control.update(current, reset)
        return control.io.reply.call_args.args[1].to_dict()

    control._publish_state()
    assert published[-1].state == 'running'
    assert command('reset')['reason'] == 'reset_requires_stopped'
    assert command('stop') == {'success': True}
    assert published[-1].state == 'stopped_reset_required'
    assert command('start')['reason'] == 'reset_required'
    assert command('reset') == {'success': True}
    assert published[-1].state == 'stopped_ready'
    assert published[-1].episode_id == 'second'
    assert command('start') == {'success': True}
    assert published[-1].state == 'running'
    assert [item.revision for item in published] == [0, 1, 2, 3, 4]
    assert command('stop', drone_id='other')['reason'] == 'unknown_drone'
    assert command('stop', age=2.)['reason'] == 'request_expired_in_queue'
    assert reset.call_count == 1


def test_failed_reset_reports_error_and_allows_retry():
    states = []
    control = SimulationControl('tcp://127.0.0.1:5560', observation(), states.append,
                                clock=lambda: 10.)
    control.io = Mock(error=None)

    def command(action, reset):
        control.io.poll_request.return_value = dict(token='request', received_at=10.,
            payload=dict(topic='command', drone_id='drone_1', payload=dict(action=action)))
        control.update(observation(), reset)
        return control.io.reply.call_args.args[1].to_dict()

    assert command('stop', Mock()) == {'success': True}
    assert command('reset', Mock(side_effect=OSError('SITL failed'))) == {
        'success': False, 'reason': 'SITL failed'}
    assert states[-1].state == 'error'
    assert command('reset', Mock(return_value=observation('retry'))) == {'success': True}
    assert states[-1].state == 'stopped_ready'


def test_state_schema_rejects_bad_values():
    state = SimulationState(1, 'drone_1', 'a' * 32, 'episode', 'running', 0)
    assert SimulationState.from_dict(state.to_dict()) == state
    for change in (dict(state='unknown'), dict(revision=-1), dict(drone_id='other')):
        try:
            SimulationState.from_dict({**state.to_dict(), **change})
        except ValueError:
            pass
        else:
            raise AssertionError(f'accepted invalid state: {change}')


def test_command_request_round_trip_over_zmq():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        endpoint = f'tcp://127.0.0.1:{probe.getsockname()[1]}'
    control = SimulationControl(endpoint, observation(), lambda state: None)
    with control, ZmqIo(request_endpoint=endpoint) as client:
        future = client.request(CommandRequest('drone_1', CommandPayload('stop')), timeout_s=2.)
        deadline = time.monotonic() + 2.
        while not future.done() and time.monotonic() < deadline:
            control.update(observation(), lambda: observation('new'))
            time.sleep(.005)
        assert future.result(timeout=.1) == {'success': True}
        assert control.state == 'stopped_reset_required'


def test_render_publisher_replays_current_state_to_new_subscriber(tmp_path):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        endpoint = f'tcp://127.0.0.1:{probe.getsockname()[1]}'
    (tmp_path / 'transport.json').write_text(json.dumps({
        'telemetry_endpoint': endpoint,
        'image_endpoint': 'tcp://127.0.0.1:5556',
        'control_endpoint': 'tcp://127.0.0.1:5557',
    }))
    (tmp_path / 'render.json').write_text(json.dumps({
        'transport_config': 'transport.json', 'fps': 30,
        'camera': {'width_px': 640, 'height_px': 480, 'fov_x_deg': 90},
    }))
    output = RenderPublisher(tmp_path / 'render.json')
    output.start()
    try:
        state = SimulationState(1, 'drone_1', 'a' * 32, 'episode', 'stopped_ready', 3)
        output.set_simulation_state(state)
        with zmq.Context() as context, context.socket(zmq.SUB) as subscriber:
            subscriber.setsockopt(zmq.SUBSCRIBE, b'simulation/drone_1/state')
            subscriber.connect(endpoint)
            deadline = time.monotonic() + 2.
            received = None
            while time.monotonic() < deadline:
                if subscriber.poll(100):
                    received = subscriber.recv_multipart()
                    break
            assert received is not None
            assert received[0] == b'simulation/drone_1/state'
            assert SimulationState.from_dict(json.loads(received[1])) == state
    finally:
        output.close()
