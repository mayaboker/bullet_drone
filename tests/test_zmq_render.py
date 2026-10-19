from dataclasses import replace
import json
from types import SimpleNamespace

import pytest
from jsonschema import validate

from bullet_drone.config import ConfigurationError
from bullet_drone.models import DroneState
from tools.zmq_render.publisher import RenderPublisher


def publisher(tmp_path):
    path = tmp_path / 'render.json'
    path.write_text(json.dumps({'transport_config': 'transport.json', 'fps': 30,
        'camera': {'width_px': 640, 'height_px': 480, 'fov_x_deg': 90}}))
    return RenderPublisher(path)


def test_simulation_scheduling_bounded_queue_and_episode_reset(tmp_path):
    output = publisher(tmp_path)
    output.thread = SimpleNamespace()
    state = DroneState('one', 0, 0, (0, 0, 3), (0, 0, 0, 1), (0, 0, 0), (0, 0, 0))
    for step in range(241):
        output.consume(SimpleNamespace(ground_truth=replace(state, step_index=step, simulation_time_s=step/240)))
    assert output.sequence == 31
    assert output.dropped == 30
    assert output.queue.qsize() == 1
    sequence, latest, source = output.queue.get_nowait()
    assert source is None
    assert sequence == 30 and latest.step_index == 240
    output.consume(SimpleNamespace(ground_truth=replace(state, episode_id='two')))
    assert output.queue.get_nowait()[1].episode_id == 'two'


def test_invalid_render_settings_and_inactive_publisher(tmp_path):
    output = publisher(tmp_path)
    with pytest.raises(RuntimeError):
        output.consume(None)
    path = tmp_path/'render.json'
    value = json.loads(path.read_text())
    value['fps'] = 0
    path.write_text(json.dumps(value))
    with pytest.raises(ConfigurationError):
        RenderPublisher(path)


def test_worker_startup_failure_and_cleanup(tmp_path):
    output = publisher(tmp_path)
    with pytest.raises(RuntimeError, match='publisher failed'):
        output.start()
    assert not output.thread.is_alive()
    output.close()


def test_render_cli_paces_and_closes_on_failure(tmp_path, monkeypatch):
    from unittest.mock import Mock
    from examples.position_square import main, demo
    output = Mock()
    path = tmp_path/'render.json'
    path.write_text('{}')
    monkeypatch.setattr('tools.zmq_render.publisher.RenderPublisher', Mock(return_value=output))
    control = Mock()
    monkeypatch.setattr('tools.zmq_render.control.SimulationControl', Mock(return_value=control))
    run = Mock(side_effect=RuntimeError('test failure'))
    monkeypatch.setattr(demo, 'run_demo', run)
    assert main.main(['--headless', '--render-config', str(path)]) == 1
    output.start.assert_called_once()
    output.close.assert_called_once()
    control.close.assert_called_once()
    assert run.call_args.kwargs['pace'] is True
    observation = object()
    run.call_args.kwargs['on_observation'](observation)
    output.consume.assert_called_once_with(observation)


def test_real_tcp_periodic_config_pose_and_binding_cleanup(tmp_path):
    zmq = pytest.importorskip('zmq')
    from uuid import uuid4
    path = tmp_path/'render.json'
    output = publisher(tmp_path)
    profile = tcp_profile()
    (tmp_path/'transport.json').write_text(json.dumps(profile))
    with zmq.Context() as context, context.socket(zmq.SUB) as subscriber:
        subscriber.setsockopt(zmq.LINGER, 0)
        subscriber.setsockopt(zmq.SUBSCRIBE, b'render/drone_1/')
        subscriber.connect(profile['telemetry_endpoint'])
        output.start()
        try:
            assert subscriber.poll(4000)
            topic, payload = subscriber.recv_multipart()
            assert topic == b'render/drone_1/config'
            from bullet_msgs import schema_bytes
            validate(json.loads(payload), json.loads(schema_bytes('config.json')))
            assert json.loads(payload)['camera']['width_px'] == 640
            state = DroneState('drone_1', 0, 0, (0, 0, 3), (0, 0, 0, 1), (1.25, -2.5, 0.75), (0, 0, 0))
            output.consume(SimpleNamespace(ground_truth=state))
            assert subscriber.poll(2000)
            topic, payload = subscriber.recv_multipart()
            packet = json.loads(payload)
            validate(packet, json.loads(schema_bytes('pose.json')))
            assert topic == b'render/drone_1/pose'
            assert packet['sequence'] == 0 and packet['position_m'] == [0, 0, 3]
            assert packet['schema_version'] == 2
            assert packet['linear_velocity_m_s'] == [1.25, -2.5, 0.75]
            output.set_state(dict(schema_version=1, physics_id='physics', controller_id=None,
                episode_id=state.episode_id, state='stopped', reason='stopped', simulation_time_s=0))
            import time
            deadline = time.monotonic() + 3
            while True:
                assert time.monotonic() < deadline, 'held pose did not arrive'
                assert subscriber.poll(1000)
                held_topic, held_payload = subscriber.recv_multipart()
                if held_topic == b'render/drone_1/pose':
                    held = json.loads(held_payload)
                    validate(held, json.loads(schema_bytes('pose.json')))
                    assert held['linear_velocity_m_s'] == [1.25, -2.5, 0.75]
                    assert held['simulation_time_s'] == packet['simulation_time_s']
                    break
            collision = RenderPublisher(path)
            with pytest.raises(RuntimeError, match='Address already in use'):
                collision.start()
            collision.close()
        finally:
            output.close()
        assert not output.thread.is_alive()
        restarted = RenderPublisher(path)
        restarted.start()
        restarted.close()
        assert not restarted.thread.is_alive()


def tcp_profile():
    import socket
    with socket.socket() as telemetry, socket.socket() as images, socket.socket() as control:
        telemetry.bind(('127.0.0.1', 0))
        images.bind(('127.0.0.1', 0))
        control.bind(('127.0.0.1', 0))
        return {'telemetry_endpoint': f'tcp://127.0.0.1:{telemetry.getsockname()[1]}',
                'image_endpoint': f'tcp://127.0.0.1:{images.getsockname()[1]}',
                'control_endpoint': f'tcp://127.0.0.1:{control.getsockname()[1]}'}
