from examples.simulation_launcher.cli import CliParser, Options
from examples.simulation_launcher import main as launcher
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
    assert captured['profile_path'] == launcher.MAVLINK_PROFILE
    assert captured['extra_ports'] == (5762,)
    assert captured['connect_msp'] is False
