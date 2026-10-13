from unittest.mock import Mock

import pytest

from bullet_drone.main import main
from bullet_drone.models import DroneObservation, DroneState
from bullet_drone.runner import SimulationRunner


def observation(step):
    return DroneObservation(DroneState("episode", step, step * 0.01, (0, 0, 1), (0, 0, 0, 1), (0, 0, 0), (0, 0, 0)))


@pytest.mark.parametrize("operation", ["reset", "step"])
@pytest.mark.parametrize("failure", [RuntimeError("backend failure"), KeyboardInterrupt()])
def test_runner_closes_on_failure_or_interrupt(operation, failure):
    env = Mock()
    env.reset.return_value = observation(0)
    env.step.return_value = observation(1)
    getattr(env, operation).side_effect = failure
    with pytest.raises(type(failure)):
        SimulationRunner().run(env, 5)
    env.close.assert_called_once()


def test_cleanup_failure_does_not_hide_original_error():
    env = Mock()
    env.reset.side_effect = ValueError("original failure")
    env.close.side_effect = RuntimeError("cleanup failure")
    with pytest.raises(ValueError, match="original failure"):
        SimulationRunner().run(env, 5)


@pytest.mark.parametrize("failure", [RuntimeError("command provider failure"), KeyboardInterrupt()])
def test_command_provider_failure_closes_environment(failure):
    env = Mock()
    env.reset.return_value = observation(0)
    provider = Mock()
    provider.command.side_effect = failure
    with pytest.raises(type(failure)):
        SimulationRunner().run(env, 5, command_provider=provider)
    env.step.assert_not_called()
    env.close.assert_called_once()


def test_pacing_uses_simulation_time_without_skipping_steps(monkeypatch):
    env = Mock()
    env.reset.return_value = observation(0)
    env.step.side_effect = [observation(1), observation(2), observation(3)]
    monotonic = Mock(side_effect=[10, 10.004, 10.025, 10.026])
    sleep = Mock()
    monkeypatch.setattr("bullet_drone.runner.time.monotonic", monotonic)
    monkeypatch.setattr("bullet_drone.runner.time.sleep", sleep)
    result = SimulationRunner().run(env, 3, pace_wall_time=True)
    assert result.ground_truth.step_index == 3
    assert env.step.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == pytest.approx([0.006, 0.004])
    env.close.assert_called_once()


def test_headless_has_no_sleep(monkeypatch):
    env = Mock()
    env.reset.return_value = observation(0)
    env.step.return_value = observation(1)
    sleep = Mock()
    monkeypatch.setattr("bullet_drone.runner.time.sleep", sleep)
    SimulationRunner().run(env, 1)
    sleep.assert_not_called()


def test_invalid_configuration_does_not_construct_backend(tmp_path, monkeypatch):
    path = tmp_path / "invalid.yaml"
    path.write_text("simulation: {}\ndrone: {}")
    backend = Mock()
    monkeypatch.setattr("bullet_drone.main.PyBulletPhysics", backend)
    assert main(["--config", str(path)]) == 2
    backend.assert_not_called()


@pytest.mark.parametrize("failure,status", [(RuntimeError("failed"), 1), (KeyboardInterrupt(), 130)])
def test_main_exit_status_and_cleanup(failure, status, monkeypatch):
    env = Mock()
    env.reset.side_effect = failure
    monkeypatch.setattr("bullet_drone.main.DroneEnvironment", Mock(return_value=env))
    assert main(["--config", "configs/headless.yaml"]) == status
    env.close.assert_called_once()
