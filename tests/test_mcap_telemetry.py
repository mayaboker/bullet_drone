import json
import subprocess
import sys

import pytest

pytest.importorskip('mcap_bug')
from mcap.reader import make_reader
from mcap_bug import McapRecorder

from bullet_drone.config import ConfigurationError
from bullet_drone.models import DroneObservation, DroneState
from bullet_drone.telemetry.mcap import McapObservationRecorder
from bullet_drone.telemetry.topics import GROUND_TRUTH_TOPIC, SENSORS_TOPIC


def observation(step=0, episode='episode'):
    return DroneObservation(DroneState(episode, step, step/240, (1, 2, 3),
                                      (0, 0, 0, 1), (0, 0, 0), (0, 0, 0)))


def test_default_topics_initial_observation_and_extras_share_frame(tmp_path):
    recorder = McapRecorder(tmp_path/'physics.mcap')
    consumer = McapObservationRecorder(recorder)
    topic = recorder.register_topic('application/custom', {'type': 'number'}, source_feedback=True)
    consumer.start()
    try:
        initial = observation()
        consumer.reset(initial)
        consumer.record_observation(observation(1), (topic.sample(2.5, source_step_index=0, source_timestamp_ns=0),))
        consumer.reset(observation(episode='second'))
    finally:
        consumer.close()
    assert consumer.statistics.complete
    with recorder.path.open('rb') as stream:
        messages = [(c.topic, m, json.loads(m.data)) for _, c, m in make_reader(stream).iter_messages()]
    assert len(messages) == 7
    sensors = [p for t, _, p in messages if t == SENSORS_TOPIC]
    assert all(p['data'] == {'imu': None, 'barometer': None, 'rangefinder': None} for p in sensors)
    assert next(p for t, _, p in messages if t == GROUND_TRUTH_TOPIC)['data']['position_m'] == [1, 2, 3]
    assert {m.log_time for _, m, p in messages if p['episode_id'] == 'episode' and p['step_index'] == 1} == {4166667}
    assert initial.ground_truth.step_index == 0


def test_optional_imports_do_not_load_service_for_normal_physics():
    code = "import sys;import bullet_drone.main;import bullet_drone.simulation;assert 'mcap_bug' not in sys.modules;assert 'mcap' not in sys.modules"
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_start_error_is_configuration_error(tmp_path):
    path = tmp_path/'existing.mcap'
    path.write_bytes(b'preserve')
    consumer = McapObservationRecorder(McapRecorder(path))
    with pytest.raises(ConfigurationError): consumer.start()
    consumer.close()
    assert path.read_bytes() == b'preserve'


def test_missing_optional_dependency_has_actionable_message(monkeypatch):
    import builtins
    from bullet_drone.telemetry.mcap import create_mcap_recorder
    original = builtins.__import__
    def importing(name, *args, **kwargs):
        if name == 'mcap_bug': raise ImportError('not installed')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', importing)
    with pytest.raises(ConfigurationError, match='uv sync --extra telemetry'):
        create_mcap_recorder('unused.mcap')
