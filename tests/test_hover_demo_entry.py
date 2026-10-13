import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from bullet_drone.config import ConfigurationError
from examples.hover.demo_cli import HoverDemoCliParser, HoverDemoOptions
from examples.hover.hover_demo import HoverDemoTimeoutError
from bullet_drone.models import DroneObservation, DroneState


EXAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'hover' / 'main.py'


def load_example():
    spec = importlib.util.spec_from_file_location('hover_demo_example', EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_parser_only_returns_options():
    assert HoverDemoCliParser().parse([]) == HoverDemoOptions(False)
    assert HoverDemoCliParser().parse(['--headless']) == HoverDemoOptions(True)


@pytest.mark.parametrize('args,status', [(['--help'], 0), (['--unknown'], 2)])
def test_example_help_and_usage_do_not_start_physics(args, status):
    result = subprocess.run([sys.executable, str(EXAMPLE), *args], capture_output=True, text=True, timeout=10)
    assert result.returncode == status
    assert 'pybullet build time' not in result.stderr
    assert 'Hover mission:' not in result.stderr


def test_example_import_has_no_startup_or_logging_side_effects():
    code = (
        "from loguru import logger; import runpy, sys; "
        "logger.add = logger.remove = lambda *a, **kw: (_ for _ in ()).throw(AssertionError('logging configured')); "
        "runpy.run_path(sys.argv[1]); assert 'pybullet' not in sys.modules"
    )
    result = subprocess.run([sys.executable, '-c', code, str(EXAMPLE)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ''


@pytest.mark.parametrize('args,gui', [([], True), (['--headless'], False)])
def test_example_selects_gui_and_reports_success(args, gui):
    module = load_example()
    state = DroneState('episode', 8000, 33.3, (0, 0, 0.0135), (0, 0, 0, 1), (0, 0, 0), (0, 0, 0))
    module.run_hover_demo = Mock(return_value=SimpleNamespace(observation=DroneObservation(state)))
    assert module.main(args) == 0
    module.run_hover_demo.assert_called_once_with(gui=gui)


@pytest.mark.parametrize('failure,status', [(HoverDemoTimeoutError('timeout'), 1),
                                             (KeyboardInterrupt(), 130), (ConfigurationError('config'), 2)])
def test_example_returns_failure_and_interrupt_status(failure, status):
    module = load_example()
    module.run_hover_demo = Mock(side_effect=failure)
    assert module.main(['--headless']) == status


def test_example_module_help_and_import_are_safe():
    module = 'examples.hover.main'
    result = subprocess.run([sys.executable, '-m', module, '--help'], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert 'pybullet build time' not in result.stderr
    assert 'Hover mission:' not in result.stderr


def test_direct_example_help_works_outside_repository(tmp_path):
    result = subprocess.run([sys.executable, str(EXAMPLE), '--help'], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert 'pybullet build time' not in result.stderr
