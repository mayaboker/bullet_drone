from types import SimpleNamespace

from external_render import monitor


MONITORS = ('Monitors: 2\n'
            ' 0: +*DP-2 1920/598x1080/336+0+0  DP-2\n'
            ' 1: +DP-1-0 1080/521x1920/293+1920+0  DP-1-0\n')


def test_named_monitor_places_window_inside_geometry(monkeypatch):
    monkeypatch.setattr(monitor.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout=MONITORS))
    assert monitor.godot_window_args('DP-1-0') == [
        '--windowed', '--position', '1940,20', '--resolution', '1000x900']


def test_missing_monitor_uses_primary(monkeypatch):
    monkeypatch.setattr(monitor.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout=MONITORS))
    assert monitor.godot_window_args('missing') == [
        '--windowed', '--position', '20,20', '--resolution', '1000x900']


def test_top_half_uses_upper_region(monkeypatch):
    monkeypatch.setattr(monitor.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout=MONITORS))
    assert monitor.godot_window_args('DP-1-0', 'top') == [
        '--windowed', '--position', '1940,20', '--resolution', '1000x900']


def test_bottom_half_uses_lower_region(monkeypatch):
    monkeypatch.setattr(monitor.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout=MONITORS))
    assert monitor.godot_window_args('DP-1-0', 'bottom') == [
        '--windowed', '--position', '1940,980', '--resolution', '1000x900']
