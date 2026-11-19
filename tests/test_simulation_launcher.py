from launcher.cli import CliParser, Options
from launcher import main as launcher
import click
import pytest


def test_launcher_defaults_to_sitl_and_render():
    assert CliParser().parse([]) == Options()


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
