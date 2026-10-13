from dataclasses import replace
import json
import socket
from unittest.mock import Mock
import pytest
from bullet_drone.config import ConfigurationError
from bullet_drone.models import DroneState, DroneObservation
from bullet_drone.rendering.config import CameraSettings, RenderSettings, RenderSources, UdpSettings, UnsupportedRenderSourceError, load_render_settings
from bullet_drone.rendering.models import RenderSnapshot, SnapshotBuilder
from bullet_drone.rendering.consumer import RenderConsumer
from bullet_drone.rendering.udp import UdpRenderer, encode_packet
from bullet_drone.rendering.composition import compose_rendering
from bullet_drone.runner import SimulationRunner


def observation(step=0, time=0):
    return DroneObservation(DroneState('episode', step, time, (1,2,3), (0,0,0,2), (0,0,0), (0,0,0)))


@pytest.mark.parametrize('field', ['position','altitude','attitude'])
def test_sensor_source_fails_before_resource_creation(field, monkeypatch, tmp_path):
    path=tmp_path/'render.yaml'
    path.write_text(f'sources:\n  {field}: sensor\n')
    socket_constructor=Mock(side_effect=AssertionError('must not allocate socket'))
    monkeypatch.setattr(socket, 'socket', socket_constructor)
    with pytest.raises(UnsupportedRenderSourceError):
        compose_rendering('godot',path)
    socket_constructor.assert_not_called()


@pytest.mark.parametrize('factory', [lambda: CameraSettings(width_px=True), lambda: CameraSettings(fov_y_deg=180),
    lambda: CameraSettings(mount_position_body_m=[0,0,float('nan')]), lambda: RenderSettings(drone_id=''),
    lambda: RenderSettings(rate_hz=0), lambda: UdpSettings(port=65536), lambda: RenderSources(position='unknown')])
def test_invalid_settings(factory):
    with pytest.raises(ConfigurationError): factory()


def test_snapshot_normalizes_without_changing_ground_truth():
    obs=observation()
    snapshot=SnapshotBuilder(RenderSettings()).build(obs)
    assert snapshot.orientation_xyzw==(0,0,0,1)
    assert obs.ground_truth.orientation_xyzw==(0,0,0,2)
    assert snapshot.altitude_m==snapshot.position_m[2]==3
    with pytest.raises(ValueError): replace(snapshot, orientation_xyzw=(0,0,0,0))
    with pytest.raises(ValueError): replace(snapshot, simulation_time_s=-1)
    with pytest.raises(ValueError): replace(snapshot, step_index=True)


def test_schedule_latest_initial_final():
    renderer=Mock()
    consumer=RenderConsumer(SnapshotBuilder(RenderSettings()), renderer, 60)
    consumer.reset(observation())
    for step in range(1,10): consumer.consume(observation(step,step/240))
    assert [call.args[0].step_index for call in renderer.render.call_args_list]==[4,8]
    consumer.close(); consumer.close()
    assert [call.args[0].step_index for call in renderer.render.call_args_list]==[4,8,9]
    renderer.close.assert_called_once()


def test_udp_loopback_codec_and_lifecycle():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1',0)); receiver.settimeout(1)
        settings=RenderSettings(udp=UdpSettings(port=receiver.getsockname()[1]))
        renderer=UdpRenderer(settings)
        snapshot=SnapshotBuilder(settings).build(observation())
        renderer.reset(snapshot); renderer.render(snapshot)
        first=json.loads(receiver.recv(65535)); second=json.loads(receiver.recv(65535))
        assert first['version']==1 and first['sequence']==0 and second['sequence']==1
        assert first['stream_id']==second['stream_id']
        assert first['camera']['width_px']==640 and first['camera']['fov_y_deg']==75
        assert first['snapshot']['sources']['attitude']=='ground_truth'
        renderer.close(); renderer.close()
        assert renderer._socket.fileno()==-1


def test_absent_viewer_and_send_failure_do_not_stop(monkeypatch):
    fake=Mock(); fake.sendto.side_effect=BlockingIOError('full')
    monkeypatch.setattr(socket,'socket',Mock(return_value=fake))
    settings=RenderSettings(); renderer=UdpRenderer(settings)
    renderer.reset(SnapshotBuilder(settings).build(observation()))
    renderer.close(); fake.close.assert_called_once()


@pytest.mark.parametrize('failure', ['reset','step','consume','interrupt','close',None])
def test_runner_closes_every_consumer_and_preserves_failure(failure):
    env=Mock(); env.reset.return_value=observation(); env.step.return_value=observation(1,1/240)
    one,two=Mock(),Mock()
    error=KeyboardInterrupt() if failure=='interrupt' else RuntimeError('original')
    if failure=='reset': one.reset.side_effect=error
    if failure=='step': env.step.side_effect=error
    if failure in ('consume','interrupt'): one.consume.side_effect=error
    if failure=='close': one.close.side_effect=error
    if failure:
        with pytest.raises(type(error)) as raised: SimulationRunner().run(env,1,consumers=(one,two))
        assert raised.value is error
    else: SimulationRunner().run(env,1,consumers=(one,two))
    one.close.assert_called_once(); two.close.assert_called_once(); env.close.assert_called_once()


def test_modes_preserve_defaults_and_reject_conflicts():
    assert compose_rendering(gui=True)==(True,True,())
    assert compose_rendering('none',gui=True)==(False,False,())
    gui,pace,consumers=compose_rendering('godot',gui=True)
    assert not gui and pace and len(consumers)==1
    consumers[0].close()
    with pytest.raises(ConfigurationError): compose_rendering('godot',headless=True)
    with pytest.raises(ConfigurationError): compose_rendering('none','unused.yaml')


def test_profile_roundtrip():
    from pathlib import Path
    assert load_render_settings(Path('configs/render-godot.yaml'))==RenderSettings()


def test_large_schedule_gap_sends_only_latest():
    renderer=Mock(); consumer=RenderConsumer(SnapshotBuilder(RenderSettings()),renderer,60)
    consumer.reset(observation()); consumer.consume(observation(240,1))
    renderer.render.assert_called_once()
    assert renderer.render.call_args.args[0].step_index==240
    consumer.close()


def test_core_cli_sensor_rejection_before_physics(tmp_path, monkeypatch):
    from bullet_drone import main
    path=tmp_path/'render.yaml'; path.write_text('sources:\n  altitude: sensor\n')
    backend=Mock(); monkeypatch.setattr(main,'PyBulletPhysics',backend)
    assert main.main(['--config','configs/headless.yaml','--renderer','godot','--render-config',str(path)])==2
    backend.assert_not_called()


def test_hover_cli_rejects_conflicting_renderer_before_physics(monkeypatch):
    from examples.hover import hover_demo, main
    backend=Mock(); monkeypatch.setattr(hover_demo,'PyBulletPhysics',backend)
    assert main.main(['--headless','--renderer','godot'])==2
    backend.assert_not_called()


def test_extreme_finite_quaternion_normalization():
    snapshot=SnapshotBuilder(RenderSettings()).build(observation())
    large=replace(snapshot,orientation_xyzw=(1e308,1e308,0,0))
    assert sum(v*v for v in large.orientation_xyzw)==pytest.approx(1)


def test_codec_rejects_invalid_publisher_identity():
    settings=RenderSettings(); snapshot=SnapshotBuilder(settings).build(observation())
    with pytest.raises(ValueError): encode_packet(snapshot, settings, 'stream', True)
    with pytest.raises(ValueError): encode_packet(replace(snapshot,drone_id='other'), settings, 'stream', 0)
