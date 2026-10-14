from dataclasses import replace
from unittest.mock import Mock

import pytest

from bullet_drone.commands import InvalidCommandError
from bullet_drone.config import ConfigurationError
from bullet_drone.contracts import LifecycleError
from bullet_drone.controllers import AltitudeController, PidSettings
from examples.hover.hover_demo import HoverDemoTimeoutError, run_hover_demo
from examples.hover.hover_mission import HoverMissionController, HoverMissionSettings, MissionPhase
from bullet_drone.rc import SoftwareRc
from bullet_drone.models import DroneObservation, DroneState


def observation(step=0, t=0, height=0.015, speed=0, episode='episode'):
    return DroneObservation(DroneState(episode, step, t, (0, 0, height), (0, 0, 0, 1),
                                      (0, 0, speed), (0, 0, 0)))


def mission(rc=None):
    altitude = AltitudeController(1, 9.81, 30, PidSettings(1.5, 0, 0, 1, 0), PidSettings(4, 1, 0, 3, 1))
    return HoverMissionController(altitude, rc if rc is not None else SoftwareRc())


def test_mission_dwell_interruptions_timing_and_disarm():
    m = mission()
    m.reset(observation())
    def step(t, height=3, speed=0):
        return m.command(observation(m._next_step - 1, t, height, speed), 0.1)
    assert not step(0, 0.015).armed
    assert step(0.5, 0.015).armed and m.phase == MissionPhase.TAKEOFF
    step(1)
    step(1.5, speed=0.2)  # reset altitude/speed dwell
    step(2)
    step(2.5)
    assert m.phase == MissionPhase.TAKEOFF
    step(3)
    assert m.phase == MissionPhase.HOVER
    step(22.9)
    assert m.phase == MissionPhase.HOVER
    step(23)
    assert m.phase == MissionPhase.LAND
    step(24, 0.015)
    step(24.4, 0.015, -0.1)  # reset touchdown dwell
    step(25, 0.015)
    assert step(25.4, 0.015).armed
    command = step(25.5, 0.015)
    assert m.phase == MissionPhase.DISARMED and not command.armed and command.thrust_n == 0
    assert not m.completed
    step(26.4, 0.015)
    assert not m.completed
    step(26.5, 0.015)
    assert m.completed
    assert [x.phase for x in m.transitions] == list(MissionPhase)
    assert m.transitions[3].simulation_time_s - m.transitions[2].simulation_time_s == 20
    m.close()
    m.close()
    with pytest.raises(LifecycleError):
        m.reset(observation())


def test_mission_uses_rc_interface_and_reset_clears_episode():
    rc = Mock(wraps=SoftwareRc())
    m = mission(rc)
    with pytest.raises(LifecycleError):
        m.command(observation(), 0.1)
    m.reset(observation())
    obs = observation(0, 0.5)
    command = m.command(obs, 0.1)
    rc.set_input.assert_called_once()
    rc.command.assert_called_once_with(obs, 0.1)
    assert command.armed and command.thrust_n > 9.81
    assert m.phase == MissionPhase.TAKEOFF
    m.reset(observation(0, 0, episode='new'))
    assert m.phase == MissionPhase.SETTLE and len(m.transitions) == 1
    with pytest.raises(InvalidCommandError):
        m.command(observation(), 0.1)
    assert not m.command(observation(0, 0, episode='new'), 0.1).armed


@pytest.mark.parametrize('kwargs', [dict(hover_duration_s=0), dict(target_altitude_m=True), dict(touchdown_duration_s=float('inf'))])
def test_invalid_mission_settings(kwargs):
    with pytest.raises(ConfigurationError):
        HoverMissionSettings(**kwargs)


def test_timeout_closes_physics_and_rc(monkeypatch):
    from examples.hover import hover_demo
    physics_type = hover_demo.PyBulletPhysics
    rc_type = hover_demo.SoftwareRc
    physics, rcs = [], []
    def make_physics(*args, **kwargs):
        value = physics_type(*args, **kwargs)
        physics.append(value)
        return value
    def make_rc(*args, **kwargs):
        value = rc_type(*args, **kwargs)
        rcs.append(value)
        return value
    monkeypatch.setattr(hover_demo, 'PyBulletPhysics', make_physics)
    monkeypatch.setattr(hover_demo, 'SoftwareRc', make_rc)
    with pytest.raises(HoverDemoTimeoutError, match='settle'):
        run_hover_demo(gui=False, max_duration_s=0.1)
    assert physics[0]._client is None and rcs[0]._closed


def test_complete_headless_mission_tracks_altitude_and_stops_motors(monkeypatch):
    from examples.hover import hover_demo
    physics_type = hover_demo.PyBulletPhysics
    samples, physics = [], []
    class RecordingPhysics(physics_type):
        def step(self, command=None):
            value = super().step(command)
            samples.append(value)
            return value
    def make_physics(*args, **kwargs):
        value = RecordingPhysics(*args, **kwargs)
        physics.append(value)
        return value
    monkeypatch.setattr(hover_demo, 'PyBulletPhysics', make_physics)
    result = run_hover_demo(gui=False)
    transitions = {event.phase: event.simulation_time_s for event in result.transitions}
    assert list(transitions) == list(MissionPhase)
    assert transitions[MissionPhase.HOVER] > transitions[MissionPhase.TAKEOFF]
    assert transitions[MissionPhase.LAND] - transitions[MissionPhase.HOVER] >= 20
    hovering = [s for s in samples if transitions[MissionPhase.HOVER] <= s.simulation_time_s < transitions[MissionPhase.LAND]]
    assert hovering and max(abs(s.position_m[2] - 3) for s in hovering) < 0.05
    assert max(abs(s.linear_velocity_m_s[2]) for s in hovering) < 0.1
    off = [s for s in samples if s.simulation_time_s > transitions[MissionPhase.DISARMED]]
    assert off and all(s.rotor_speeds_rad_s == (0, 0, 0, 0) for s in off)
    final = result.observation.ground_truth
    assert final.position_m[2] <= 0.02 and abs(final.linear_velocity_m_s[2]) <= 0.05
    assert final.simulation_time_s - transitions[MissionPhase.DISARMED] >= 1
    assert final.simulation_time_s < 45
    assert physics[0]._client is None


@pytest.mark.parametrize('failure', [RuntimeError('altitude failed'), KeyboardInterrupt()])
def test_controller_failure_closes_world_and_rc(monkeypatch, failure):
    from examples.hover import hover_demo
    physics_type = hover_demo.PyBulletPhysics
    rc_type = hover_demo.SoftwareRc
    physics, rcs = [], []
    def make_physics(*args, **kwargs):
        value = physics_type(*args, **kwargs)
        physics.append(value)
        return value
    def make_rc(*args, **kwargs):
        value = rc_type(*args, **kwargs)
        rcs.append(value)
        return value
    monkeypatch.setattr(hover_demo, 'PyBulletPhysics', make_physics)
    monkeypatch.setattr(hover_demo, 'SoftwareRc', make_rc)
    monkeypatch.setattr(hover_demo.AltitudeController, 'thrust', Mock(side_effect=failure))
    with pytest.raises(type(failure)):
        run_hover_demo(gui=False)
    assert physics[0]._client is None and rcs[0]._closed
