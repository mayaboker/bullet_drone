from math import acos, cos, hypot, pi, radians
import subprocess
import sys
from unittest.mock import Mock

import pytest
from bullet_drone.commands import InvalidCommandError
from bullet_drone.config import ConfigurationError
from bullet_drone.contracts import LifecycleError
from bullet_drone.controllers import AltitudeController, PidSettings, PositionController
from bullet_drone.controllers.geometry import conjugate, from_rpy, multiply
from bullet_drone.joystick import SoftwareJoystick
from bullet_drone.models import DroneObservation, DroneState
from examples.position.demo import PositionDemoTimeoutError, run_position_demo
from examples.position.mission import GATE_X_M, PositionMission, PositionPhase


def controller(tilt=15):
    return PositionController(AltitudeController(1,9.81,30,PidSettings(1.5,0,0,1,0),PidSettings(4,1,0,3,1)),
                              PidSettings(.8,0,0,1,0),PidSettings(2,0,0,1.5,0),radians(tilt))


def observation(step=0,t=0,pos=(0,0,.015),vel=(0,0,0),episode='episode'):
    return DroneObservation(DroneState(episode,step,t,pos,(0,0,0,1),vel,(0,0,0)))


@pytest.mark.parametrize('target,yaw,axis', [((1,0,3),0,0),((0,1,3),0,1),((1,0,3),pi/2,0),((0,1,3),pi/2,1)])
def test_world_force_directions_and_yaw_independence(target,yaw,axis):
    value=controller().input(target,(0,0,3),(0,0,0),.01,yaw_rad=yaw)
    q=from_rpy(value.rpy)
    force=multiply(multiply(q,(0,0,value.thrust_n,0)),conjugate(q))[:3]
    assert force[axis]>0 and abs(force[1-axis])<1e-8
    assert force[2]==pytest.approx(9.81)
    assert value.armed and value.mode=='angle'


def test_tilt_collective_bounds_and_pid_reset():
    c=controller(5)
    value=c.input((100,100,3),(0,0,3),(-100,-100,0),.01)
    assert acos(cos(value.rpy[0])*cos(value.rpy[1]))<=radians(5)+1e-12
    assert 9.81<value.thrust_n<=30
    c.input((0,0,3.1),(0,0,3),(0,0,0),.01)
    assert c.altitude.velocity.integral>0
    c.reset()
    assert c.altitude.velocity.integral==0
    level=c.input((0,0,3),(0,0,3),(0,0,0),.01)
    assert level.rpy==(0,0,0) and level.thrust_n==pytest.approx(9.81)


@pytest.mark.parametrize('kwargs', [dict(target_position_m=(float('nan'),0,3)),dict(velocity_m_s=(0,float('inf'),0)),dict(dt_s=0),dict(yaw_rad=float('nan')),dict(descent_speed_limit_m_s=-1)])
def test_invalid_controller_inputs_do_not_advance_pid(kwargs):
    c=controller()
    args=dict(target_position_m=(0,0,3),position_m=(0,0,3),velocity_m_s=(0,0,0),dt_s=.01)
    args.update(kwargs)
    with pytest.raises(InvalidCommandError): c.input(**args)
    assert all(pid._previous_measurement is None for pid in (*c.position,*c.velocity,c.altitude.position,c.altitude.velocity))


def test_mission_joystick_lifecycle_replay_and_reset():
    joystick=Mock(wraps=SoftwareJoystick());m=PositionMission(controller(),joystick)
    with pytest.raises(LifecycleError):m.command(observation(),.01)
    m.reset(observation(pos=(1.5,.25,.015)))
    value=m.command(observation(t=.5,pos=(1.5,.25,.015)),.01)
    assert value.armed and m.phase==PositionPhase.TAKEOFF
    joystick.set_input.assert_called_once();joystick.command.assert_called_once()
    with pytest.raises(InvalidCommandError):m.command(observation(t=.5,pos=(1.5,.25,.015)),.01)
    m.reset(observation(pos=(3,.5,.015),episode='new'))
    assert m.home==(3,.5,.015) and len(m.transitions)==1
    assert m.waypoints[-1]==(3,.5,3)
    with pytest.raises(InvalidCommandError):m.command(observation(),.01)
    m.close();m.close();joystick.close.assert_called_once()
    with pytest.raises(LifecycleError):m.reset(observation())


def test_arrival_dwell_requires_position_and_velocity_and_own_pad():
    m=PositionMission(controller(),SoftwareJoystick());m.reset(observation())
    def step(t,pos=(0,0,3),vel=(0,0,0)):
        return m.command(observation(m._next_step-1,t,pos,vel),.1)
    step(.5,pos=(0,0,.015));step(1);step(1.3,vel=(.2,0,0));step(1.6);step(2.1)
    assert m.phase==PositionPhase.OUTBOUND and m.index==1
    # Returning airborne to a different pad cannot trigger landing.
    m.phase=PositionPhase.RETURN;m.index=len(m.waypoints)-1;m._dwell_since=None
    step(3,pos=(1.5,.25,3));step(4,pos=(1.5,.25,3))
    assert m.phase==PositionPhase.RETURN
    step(5);step(5.5);assert m.phase==PositionPhase.LAND
    step(6,pos=(1.5,.25,.015));step(7,pos=(1.5,.25,.015))
    assert m.phase==PositionPhase.LAND
    step(8,pos=(0,0,.015));value=step(8.5,pos=(0,0,.015))
    assert not value.armed and value.thrust_n==0 and m.phase==PositionPhase.DISARMED
    step(9.5,pos=(0,0,.015));assert m.completed


@pytest.mark.parametrize('home', [(0,0,.015),(1.5,.25,.015),(3,.5,.015)])
def test_complete_flights_cross_gates_both_directions_and_land_on_home(home,monkeypatch):
    from examples.position import demo
    samples=[];resources=[]
    class RecordingPhysics(demo.PyBulletPhysics):
        def reset(self):
            value=super().reset();samples.append(value);return value
        def step(self,command=None):
            value=super().step(command);samples.append(value);return value
    def create(*args,**kwargs):
        physics=RecordingPhysics(*args,**kwargs);resources.append(physics);return physics
    monkeypatch.setattr(demo,'PyBulletPhysics',create)
    result=run_position_demo(gui=False,initial_position_m=home)
    for gate in GATE_X_M:
        crossings=[]
        for a,b in zip(samples,samples[1:]):
            if (a.position_m[0]-gate)*(b.position_m[0]-gate)<0:
                crossings.append(b)
        assert len(crossings)==2
        assert crossings[0].linear_velocity_m_s[0]>0 and crossings[1].linear_velocity_m_s[0]<0
        assert all(abs(s.position_m[2]-3)<.1 and abs(s.position_m[1]-home[1])<.1 for s in crossings)
        assert all(abs(s.position_m[1])<1.5 and .2<s.position_m[2]<4.8 for s in crossings)
    state=result.observation.ground_truth
    assert hypot(state.position_m[0]-home[0],state.position_m[1]-home[1])<.03
    assert state.position_m[2]<.02 and state.rotor_speeds_rad_s==(0,0,0,0)
    assert state.simulation_time_s<180 and result.transitions[-1].phase==PositionPhase.COMPLETE
    assert resources[0]._client is None


@pytest.mark.parametrize('failure', [None,RuntimeError('control failed'),KeyboardInterrupt()])
def test_timeout_and_failure_cleanup(failure,monkeypatch):
    from examples.position import demo
    physics_type=demo.PyBulletPhysics;joystick_type=demo.SoftwareJoystick
    physics=[];joysticks=[]
    def create_physics(*args,**kwargs):
        value=physics_type(*args,**kwargs);physics.append(value);return value
    def create_joystick():
        value=joystick_type();joysticks.append(value);return value
    monkeypatch.setattr(demo,'PyBulletPhysics',create_physics);monkeypatch.setattr(demo,'SoftwareJoystick',create_joystick)
    if failure:
        monkeypatch.setattr(demo.PositionController,'input',Mock(side_effect=failure))
        with pytest.raises(type(failure)):run_position_demo(gui=False,max_duration_s=2)
    else:
        with pytest.raises(PositionDemoTimeoutError):run_position_demo(gui=False,max_duration_s=.1)
    assert physics[0]._client is None and joysticks[0]._closed


@pytest.mark.parametrize('position',[(7,0,.015),(0,2,.015),(0,0,3),(0,0,float('nan'))])
def test_unsuitable_start_rejected_before_resources(position,monkeypatch):
    from examples.position import demo
    factory=Mock();monkeypatch.setattr(demo,'PyBulletPhysics',factory)
    with pytest.raises(ConfigurationError):run_position_demo(gui=False,initial_position_m=position)
    factory.assert_not_called()


def test_cli_help_usage_import_and_tasks():
    import json
    from pathlib import Path
    from examples.position.cli import PositionDemoCliParser
    for args,status in [(['--help'],0),(['--unknown'],2)]:
        result=subprocess.run([sys.executable,'examples/position/main.py',*args],capture_output=True,text=True,timeout=10)
        assert result.returncode==status and 'pybullet build time' not in result.stderr
    code="from loguru import logger; import runpy,sys; logger.add=logger.remove=lambda *a,**k:(_ for _ in ()).throw(AssertionError());runpy.run_path('examples/position/main.py');assert 'pybullet' not in sys.modules"
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    tasks={task['label']:task for task in json.loads(Path('.vscode/tasks.json').read_text())['tasks']}
    assert tasks['Run Godot and 3 position drones']['dependsOrder']=='parallel'
    for index,home in enumerate([(0,0,.015),(1.5,.25,.015),(3,.5,.015)],1):
        options=PositionDemoCliParser().parse(tasks[f'Run position drone {index} with Godot']['args'][3:])
        assert options.initial_position_m==home and options.renderer=='godot'
