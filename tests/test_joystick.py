from dataclasses import replace
from unittest.mock import Mock

import pytest

from bullet_drone.commands import HighLevelCommand, InvalidCommandError, JoystickInput
from bullet_drone.composition import FlightCommandProvider
from bullet_drone.contracts import LifecycleError
from bullet_drone.joystick import SoftwareJoystick
from bullet_drone.models import DroneObservation, DroneState


def observation(step=0, episode='episode'):
    return DroneObservation(DroneState(episode, step, step * 0.1, (0, 0, 0),
                                      (0, 0, 0, 1), (0, 0, 0), (0, 0, 0)))


@pytest.mark.parametrize('mode', ['angle', 'acro'])
def test_joystick_translation_reset_and_lifecycle(mode):
    joystick = SoftwareJoystick()
    with pytest.raises(LifecycleError):
        joystick.set_input(JoystickInput())
    joystick.reset(observation())
    default = joystick.command(observation(), 0.1)
    assert not default.armed and default.thrust_n == 0
    joystick.set_input(JoystickInput(mode, (0.1, -0.2, 0.3), 12, True))
    command = joystick.command(observation(1), 0.1)
    assert command == HighLevelCommand(mode, (0.1, -0.2, 0.3), 12, 'episode', 2)
    with pytest.raises(InvalidCommandError):
        joystick.command(observation(1), 0.1)
    joystick.reset(observation(0, 'new'))
    assert not joystick.command(observation(0, 'new'), 0.1).armed
    joystick.close()
    joystick.close()
    with pytest.raises(LifecycleError):
        joystick.reset(observation())
    with pytest.raises(LifecycleError):
        joystick.command(observation(1), 0.1)


@pytest.mark.parametrize('kwargs', [dict(armed=1), dict(armed=None), dict(mode='bad'),
                                    dict(rpy=(0, 0)), dict(rpy=(0, float('nan'), 0)), dict(thrust_n=-1)])
def test_joystick_rejects_invalid_input(kwargs):
    with pytest.raises(InvalidCommandError):
        JoystickInput(**kwargs)


@pytest.mark.parametrize('kwargs', [dict(episode='wrong'), dict(step=1)])
def test_joystick_rejects_identity_and_invalid_dt_without_consuming_step(kwargs):
    joystick = SoftwareJoystick()
    joystick.reset(observation())
    with pytest.raises(InvalidCommandError):
        joystick.command(observation(**kwargs), 0.1)
    with pytest.raises(InvalidCommandError):
        joystick.command(observation(), 0)
    with pytest.raises(InvalidCommandError):
        joystick.set_input(None)
    assert joystick.command(observation(), 0.1).step_index == 1


def test_disarm_gates_nonzero_demands_and_rearm_resets_stabilization():
    joystick = SoftwareJoystick()
    stabilization, feedback, mixer = Mock(), Mock(), Mock()
    mixer.mix.return_value.speeds_rad_s = (10, 20, 30, 40)
    provider = FlightCommandProvider(joystick, stabilization, feedback, mixer, 0.1)
    provider.reset(observation())
    joystick.set_input(JoystickInput('angle', (1, 2, 3), 30, False))
    assert provider.command(observation()).speeds_rad_s == (0, 0, 0, 0)
    stabilization.update.assert_not_called()
    feedback.read.assert_not_called()
    mixer.mix.assert_not_called()
    assert provider.allocation is None
    resets = stabilization.reset.call_count
    joystick.set_input(JoystickInput('angle', (0, 0, 0), 10, True))
    assert provider.command(observation(1)).speeds_rad_s == (10, 20, 30, 40)
    assert stabilization.reset.call_count == resets + 1
    joystick.set_input(JoystickInput('angle', (1, 2, 3), 30, False))
    assert provider.command(observation(2)).speeds_rad_s == (0, 0, 0, 0)
    assert stabilization.reset.call_count == resets + 2
    assert stabilization.update.call_count == 1
    joystick.set_input(JoystickInput('angle', (0, 0, 0), 10, True))
    provider.command(observation(3))
    assert stabilization.reset.call_count == resets + 3
    provider.close()


def test_disarmed_command_is_validated_before_motor_gate():
    source, stabilization = Mock(), Mock()
    source.command.return_value = HighLevelCommand('angle', (0, 0, 0), 10, 'wrong', 1, False)
    provider = FlightCommandProvider(source, stabilization, Mock(), Mock(), 0.1)
    provider.reset(observation())
    resets = stabilization.reset.call_count
    with pytest.raises(InvalidCommandError):
        provider.command(observation())
    assert stabilization.reset.call_count == resets
    source.command.return_value = replace(source.command.return_value, episode_id='episode')
    assert provider.command(observation()).speeds_rad_s == (0, 0, 0, 0)
