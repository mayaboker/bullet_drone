import csv
from dataclasses import FrozenInstanceError, replace
from math import cos, dist, hypot
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest
from bullet_drone.commands import InvalidCommandError
from bullet_drone.config import ConfigurationError
from bullet_drone.contracts import LifecycleError
from bullet_drone.controllers import AltitudeController, PidSettings, PositionController
from bullet_drone.controllers.geometry import attitude_error, from_rpy
from bullet_drone.rc import RcCodec, SoftwareRc
from bullet_drone.models import DroneObservation, DroneState
from bullet_drone.vehicle import load_racer_parameters
from examples.position_control.demo import ControlChainTimeoutError, run_control_chain
from examples.position_control.mission import ControlChainMission
from examples.position_control.verification import ControlChainVerificationError, verify_chain


@pytest.fixture(scope='module')
def flight(tmp_path_factory):
    path=tmp_path_factory.mktemp('chain')/'trace.csv'
    return run_control_chain(gui=False,trace_path=path), path


def test_complete_chain_and_xyz_yaw_arrivals(flight):
    result,_=flight
    assert [a.target.name for a in result.arrivals]==['takeoff','x_leg','y_leg','climb_and_return_x','return_home','align_home']
    assert result.verification.completed_steps==len(result.samples)==result.observation.ground_truth.step_index
    assert result.verification.settled_waypoints==6 and result.verification.max_arrival_error_m<=.12
    for arrival in result.arrivals:
        assert dist(arrival.target.position_m,arrival.position_m)<=.12
        assert hypot(*attitude_error(arrival.orientation_xyzw,from_rpy((0,0,arrival.target.yaw_rad))))<=.05
    assert result.arrivals[3].position_m[2]>3.88
    final=result.observation.ground_truth
    assert hypot(*final.position_m[:2])<.01 and final.position_m[2]<.02
    assert final.rotor_speeds_rad_s==(0,0,0,0)


def test_each_observed_link_and_episode_identity(flight):
    result,_=flight
    for sample in result.samples:
        assert sample.command.step_index==sample.state.step_index==sample.feedback_state.step_index+1
        assert sample.state.episode_id==sample.command.episode_id==sample.feedback_state.episode_id
        assert sample.state.rotor_speeds_rad_s==sample.motor_actual_rad_s==sample.motor_targets_rad_s
        if sample.command.armed:
            assert RcCodec(4*load_racer_parameters().max_thrust_per_rotor_n).decode(
                sample.position_output.rc_input,sample.command.episode_id,sample.command.step_index)==sample.command
            assert sample.stabilization_feedback is not None
            assert sample.stabilization_wrench==sample.allocation.requested
            assert sample.motor_targets_rad_s==sample.allocation.speeds_rad_s
            assert sum(f[2] for f in sample.propellers.forces_n)==pytest.approx(sample.allocation.achieved.thrust_n)
        else:
            assert sample.position_output is None and sample.allocation is None
            assert sample.stabilization_wrench is None and sample.motor_targets_rad_s==(0,0,0,0)
    with pytest.raises(FrozenInstanceError): result.samples[0].command=Mock()


def test_velocity_targets_and_axes_exercised(flight):
    result,_=flight
    for axis in range(3):
        assert max(abs(s.allocation.requested.torque_nm[axis]) for s in result.samples if s.allocation)>1e-6
    for axis in range(2):
        assert max(s.state.linear_velocity_m_s[axis] for s in result.samples)>.1
        assert min(s.state.linear_velocity_m_s[axis] for s in result.samples)<-.1
    for s in result.samples:
        if s.position_output:
            assert hypot(*s.position_output.velocity_target_m_s[:2])<=1+1e-12
    leg=next(s for s in result.samples if s.target.name=='x_leg')
    assert leg.position_output.velocity_target_m_s[0]>0
    assert leg.command.rpy[1]>0 and leg.command.thrust_n>0
    vertical=leg.command.thrust_n*cos(leg.command.rpy[0])*cos(leg.command.rpy[1])
    assert vertical==pytest.approx(9.81+leg.position_output.acceleration_m_s2[2],abs=.025)


def test_csv_contains_every_completed_step_and_no_stale_disarmed_pid(flight):
    result,path=flight
    with path.open(newline='') as stream: rows=list(csv.DictReader(stream))
    assert len(rows)==len(result.samples)
    assert [int(row['step_index']) for row in rows]==list(range(1,len(rows)+1))
    assert all(int(row['feedback_step_index'])==int(row['step_index'])-1 for row in rows)
    assert rows[-1]['rc_channel_18']==''
    assert any(row['rc_channel_5']=='2000' and row['rc_channel_6']=='2000' for row in rows)
    assert rows[-1]['armed']=='False' and rows[-1]['velocity_target_m_s_x']==''
    assert rows[-1]['motor_actual_0_rad_s']=='0.0'
    assert any(float(row['reaction_torque_nm_z'])!=0 for row in rows)


@pytest.mark.parametrize('change', ['motor','rc','identity','propellers'])
def test_chain_verifier_detects_broken_links(flight,change):
    result,_=flight
    index=next(i for i,s in enumerate(result.samples) if s.command.armed)
    sample=result.samples[index]
    if change=='motor':sample=replace(sample,motor_targets_rad_s=(0,0,0,0))
    if change=='rc':sample=replace(sample,command=replace(sample.command,rpy=(.2,0,0)))
    if change=='identity':sample=replace(sample,command=replace(sample.command,step_index=sample.command.step_index+1))
    if change=='propellers':sample=replace(sample,propellers=replace(sample.propellers,forces_n=((0,0,0),)*4))
    samples=(*result.samples[:index],sample,*result.samples[index+1:])
    with pytest.raises(ControlChainVerificationError):verify_chain(result.observation,result.arrivals,samples,load_racer_parameters())


def test_controller_last_outputs_are_immutable_and_reset_without_changing_commands():
    altitude=AltitudeController(1,9.81,30,PidSettings(1.5,0,0,1,0),PidSettings(4,1,0,3,1))
    position=PositionController(altitude,PidSettings(.8,0,0,1,0),PidSettings(2,0,0,1.5,0),.2)
    assert position.last_output is None and altitude.last_output is None
    value=position.input((1,0,3),(0,0,3),(0,0,0),.01)
    output=position.last_output
    assert output.velocity_target_m_s==(.8,0,0)
    assert output.acceleration_m_s2==(1.5,0,0) and output.rc_input==value
    with pytest.raises(FrozenInstanceError):output.velocity_target_m_s=(0,0,0)
    with pytest.raises(InvalidCommandError):position.input((0,0,3),(0,0,3),(0,0,0),0)
    assert position.last_output is output
    position.reset();assert position.last_output is None and altitude.last_output is None
    assert position.input((1,0,3),(0,0,3),(0,0,0),.01)==value


def test_mission_replay_episode_and_heading_dwell():
    altitude=AltitudeController(1,9.81,30,PidSettings(1.5,0,0,1,0),PidSettings(4,1,0,3,1))
    rc=Mock(wraps=SoftwareRc())
    mission=ControlChainMission(PositionController(altitude,PidSettings(.8,0,0,1,0),PidSettings(2,0,0,1.5,0),.2),rc)
    def obs(step=0,t=0,pos=(0,0,.015),yaw=0,episode='episode'):
        return DroneObservation(DroneState(episode,step,t,pos,from_rpy((0,0,yaw)),(0,0,0),(0,0,0)))
    with pytest.raises(LifecycleError):mission.command(obs(),.01)
    mission.reset(obs());mission.command(obs(t=.5),.01)
    with pytest.raises(InvalidCommandError):mission.command(obs(t=.5),.01)
    mission.command(obs(1,1,(0,0,3)),.01)
    mission.command(obs(2,1.4,(0,0,3),.2),.01) # wrong heading resets dwell
    mission.command(obs(3,1.5,(0,0,3)),.01)
    assert not mission.arrivals
    mission.command(obs(4,2,(0,0,3)),.01)
    assert len(mission.arrivals)==1 and mission.index==1
    assert rc.set_input.call_count==5
    mission.reset(obs(pos=(2,1,.015),episode='new'))
    assert not mission.arrivals and mission.last_command is None and mission.home==(2,1,.015)
    mission.close();mission.close();rc.close.assert_called_once()


@pytest.mark.parametrize('failure', ['timeout','control','interrupt','csv'])
def test_failures_close_rc_physics_and_trace(tmp_path,monkeypatch,failure):
    from examples.position_control import demo
    physics_type=demo.PyBulletPhysics;rc_type=demo.SoftwareRc;recorder_type=demo.ChainRecorder
    physics=[];rcs=[];recorders=[]
    def make_physics(*args,**kwargs):
        value=physics_type(*args,**kwargs);physics.append(value);return value
    def make_rc(*args, **kwargs):
        value=rc_type(*args, **kwargs);rcs.append(value);return value
    def make_recorder(*args,**kwargs):
        value=recorder_type(*args,**kwargs);recorders.append(value);return value
    monkeypatch.setattr(demo,'PyBulletPhysics',make_physics);monkeypatch.setattr(demo,'SoftwareRc',make_rc);monkeypatch.setattr(demo,'ChainRecorder',make_recorder)
    path=tmp_path/'trace.csv'
    duration=.1 if failure=='timeout' else 2
    error=ControlChainTimeoutError
    if failure in ('control','interrupt'):
        error=KeyboardInterrupt if failure=='interrupt' else RuntimeError
        monkeypatch.setattr(demo.PositionController,'input',Mock(side_effect=error('injected')))
    if failure=='csv':path=tmp_path/'missing'/'trace.csv';error=FileNotFoundError
    with pytest.raises(error):run_control_chain(gui=False,max_duration_s=duration,trace_path=path)
    assert physics[0]._client is None and rcs[0]._closed and recorders[0]._closed
    assert recorders[0]._file is None or recorders[0]._file.closed


def test_invalid_initial_position_fails_before_resources(monkeypatch):
    from examples.position_control import demo
    factory=Mock();monkeypatch.setattr(demo,'PyBulletPhysics',factory)
    with pytest.raises(ConfigurationError):run_control_chain(gui=False,initial_position_m=(0,0,1))
    factory.assert_not_called()


def test_cli_and_import_are_safe_and_options_forwarded(tmp_path,monkeypatch):
    from examples.position_control.cli import ControlChainCliParser
    options=ControlChainCliParser().parse(['--headless','--trace',str(tmp_path/'trace.csv')])
    assert options.headless and options.trace_path==tmp_path/'trace.csv'
    for args,status in [(['--help'],0),(['--unknown'],2)]:
        process=subprocess.run([sys.executable,'examples/position_control/main.py',*args],capture_output=True,text=True,timeout=10)
        assert process.returncode==status and 'pybullet build time' not in process.stderr
    code="from loguru import logger;import runpy,sys;logger.add=logger.remove=lambda *a,**k:(_ for _ in ()).throw(AssertionError());runpy.run_path('examples/position_control/main.py');assert 'pybullet' not in sys.modules"
    process=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=10)
    assert process.returncode==0,process.stderr
    from examples.position_control import main
    completed=Mock();completed.observation=DroneObservation(DroneState('e',1,1,(0,0,.015),(0,0,0,1),(0,0,0),(0,0,0)))
    completed.arrivals=();completed.samples=()
    runner=Mock(return_value=completed);monkeypatch.setattr(main,'run_control_chain',runner)
    assert main.main(['--headless','--trace',str(tmp_path/'trace.csv')])==0
    runner.assert_called_once_with(gui=False,trace_path=tmp_path/'trace.csv')
