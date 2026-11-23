from launcher.cli import CliParser, Options
from launcher import main as launcher
from bullet_drone.config import ConfigurationError
import click
import pytest


def test_launcher_defaults_to_sitl_and_render():
    assert CliParser().parse([]) == Options()


def test_target_spawn_config_rotates_at_original_position(tmp_path):
    path = tmp_path / 'target.yaml'
    path.write_text('initial_position_m: [0, 0, 0.015]\ninitial_yaw_deg: 90\n')
    options = CliParser().parse(['--target-scene', '--target-spawn-config', str(path)])
    config = launcher._simulation_config(options)
    assert config.drone.initial_position_m == launcher.INITIAL_POSITION_M
    assert config.drone.initial_yaw_rad == pytest.approx(1.5707963267948966)


def test_isaac_backends_keep_target_spawn_and_control_options(tmp_path):
    path = tmp_path / 'target.yaml'
    path.write_text('initial_position_m: [0, 0, 0.015]\ninitial_yaw_deg: 90\n')
    options = CliParser().parse([
        '--renderer-backend', 'isaac', '--physics-backend', 'isaac',
        '--target-scene', '--target-spawn-config', str(path), '--isaac-headless',
    ])
    assert options.renderer_backend == options.physics_backend == 'isaac'
    assert options.isaac_headless
    assert launcher._simulation_config(options).drone.initial_yaw_rad == pytest.approx(1.5707963267948966)
    assert options.simulation_control_endpoint == Options().simulation_control_endpoint


def test_target_spawn_config_rejects_bad_yaw_and_non_target_scene(tmp_path):
    path = tmp_path / 'target.yaml'
    path.write_text('initial_position_m: [0, 0, 0.015]\ninitial_yaw_deg: nan\n')
    with pytest.raises(ConfigurationError, match='initial_yaw_deg'):
        launcher._simulation_config(Options(target_scene=True, target_spawn_config=path))
    with pytest.raises(click.UsageError, match='--target-scene'):
        CliParser().parse(['--target-spawn-config', str(path)])


def test_launcher_can_disable_either_process():
    assert CliParser().parse(['--no-sitl']).sitl is False
    assert CliParser().parse(['--no-render']).render is False
    options = CliParser().parse(['--no-sitl', '--no-render'])
    assert not options.sitl and not options.render


def test_launcher_accepts_render_monitor():
    assert CliParser().parse(['--render-monitor', 'DP-1-0']).render_monitor == 'DP-1-0'
    assert CliParser().parse(['--render-monitor', 'DP-1-0', '--render-half', 'top']).render_half == 'top'


def test_launcher_uses_mavlink_profile_and_reserves_uart2(monkeypatch):
    captured = {}

    class Session:
        def __init__(self, binary, **kwargs):
            captured.update(kwargs)

        def __enter__(self):
            raise RuntimeError('Stop after SITL setup')

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(launcher, 'SitlSession', Session)
    with pytest.raises(RuntimeError, match='Stop after SITL setup'):
        launcher.run(Options(render=False))
    assert captured['profile_path'] == Options().sitl_profile
    assert captured['extra_ports'] == (5762,)
    assert captured['gps_enabled'] is False


def test_launcher_gps_selects_matching_profile_and_sensor():
    from launcher.cli import DEFAULT_SITL_GPS_PROFILE

    options = CliParser().parse(['--gps', '--no-render'])
    assert options.gps is True
    assert options.sitl_profile == DEFAULT_SITL_GPS_PROFILE
    config = launcher._simulation_config(options)
    assert config.sensors.gps.enabled is True
    assert config.sensors.gps.origin_altitude_m == launcher.GPS_ORIGIN_ALTITUDE_M


def test_launcher_no_gps_keeps_coordinates_for_fdm():
    options = CliParser().parse(['--no-gps', '--no-render'])
    assert options.gps is False
    assert launcher._simulation_config(options).sensors.gps.enabled is True


def test_launcher_passes_gps_flag_to_sitl_session(monkeypatch):
    captured = {}

    class Session:
        def __init__(self, binary, **kwargs):
            captured.update(kwargs)

        def __enter__(self):
            raise RuntimeError('Stop after SITL setup')

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(launcher, 'SitlSession', Session)
    options = CliParser().parse(['--gps', '--no-render'])
    with pytest.raises(RuntimeError, match='Stop after SITL setup'):
        launcher.run(options)
    assert captured['gps_enabled'] is True
    assert captured['profile_path'] == options.sitl_profile


def test_launcher_requires_external_paths_when_checkout_assets_are_unavailable(monkeypatch):
    import launcher.cli as cli
    monkeypatch.setattr(cli, 'DEFAULT_SITL_BINARY', None)
    monkeypatch.setattr(cli, 'DEFAULT_SITL_PROFILE', None)
    monkeypatch.setattr(cli, 'DEFAULT_RENDERER', None)
    monkeypatch.setattr(cli, 'DEFAULT_RENDER_CONFIG', None)
    with pytest.raises(click.UsageError, match='--sitl-binary and --sitl-profile'):
        CliParser().parse([])
    with pytest.raises(click.UsageError, match='--renderer and --render-config'):
        CliParser().parse(['--no-sitl'])
    assert CliParser().parse(['--no-sitl', '--no-render']).sitl is False


def test_launcher_accepts_explicit_external_assets(tmp_path, monkeypatch):
    import launcher.cli as cli
    for name in ('DEFAULT_SITL_BINARY', 'DEFAULT_SITL_PROFILE',
                 'DEFAULT_RENDERER', 'DEFAULT_RENDER_CONFIG'):
        monkeypatch.setattr(cli, name, None)
    paths = [tmp_path / name for name in ('sitl', 'profile', 'renderer', 'render.json')]
    for path in paths:
        path.touch()
    options = CliParser().parse([
        '--sitl-binary', str(paths[0]), '--sitl-profile', str(paths[1]),
        '--renderer', str(paths[2]), '--render-config', str(paths[3])])
    assert (options.sitl_binary, options.sitl_profile, options.renderer,
            options.render_config) == tuple(paths)


def test_launcher_reset_restarts_owned_sitl_and_backend(monkeypatch):
    from types import SimpleNamespace

    events = []
    observation = SimpleNamespace(ground_truth=SimpleNamespace(
        drone_id='drone_1', episode_id='new'))

    class Session:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            events.append('sitl_start')
            return self

        def __exit__(self, *args):
            events.append('sitl_close')

        def check_running(self):
            pass

    class Physics:
        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

    class Environment:
        def __init__(self, *args, **kwargs):
            pass

        def reset(self):
            events.append('physics_reset')
            return observation

        def hold(self):
            return observation

        def close(self):
            pass

    class Backend:
        def __init__(self, *args, **kwargs):
            pass

        def reset(self, current):
            events.append('backend_reset')

        def command(self, current):
            return None

        def close(self):
            events.append('backend_close')

    class Control:
        def __init__(self, endpoint, current, on_state):
            self.state = 'running'
            self.calls = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def update(self, current, reset):
            self.calls += 1
            if self.calls == 1:
                self.state = 'stopped_reset_required'
                current = reset()
                self.state = 'stopped_ready'
                return current
            raise StopIteration

    monkeypatch.setattr(launcher, 'SitlSession', Session)
    monkeypatch.setattr(launcher, 'PyBulletPhysics', Physics)
    monkeypatch.setattr(launcher, 'DroneEnvironment', Environment)
    monkeypatch.setattr(launcher, 'BetaflightBackend', Backend)
    monkeypatch.setattr(launcher, 'SimulationControl', Control)
    monkeypatch.setattr(launcher, '_wait_sitl_ready', lambda session: None)
    monkeypatch.setattr(launcher, 'load_racer_parameters', lambda: object())
    with pytest.raises(StopIteration):
        launcher.run(Options(render=False))
    assert events == ['sitl_start', 'physics_reset', 'backend_reset',
                      'backend_close', 'sitl_close', 'physics_reset',
                      'sitl_start', 'backend_reset', 'backend_close', 'sitl_close']
