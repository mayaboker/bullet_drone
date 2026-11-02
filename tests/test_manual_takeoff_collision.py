"""Real headless physics: manual Arm on terrain, Start, liftoff, later crash."""
from dataclasses import replace
from pathlib import Path
import pytest
from bullet_app.mission import Mission
from bullet_app.flight_control import FlightSession
from bullet_drone.config import YamlConfigLoader
from bullet_drone.simulation import RcSimulation
from bullet_drone.commands import RcInput
from bullet_drone.controllers import InternalControlSettings, PidSettings
from los_tracking import NavigatorConfig
from tools.zmq_render.scenario import ScenarioTermination

ROOT=Path(__file__).resolve().parents[3]


@pytest.mark.parametrize('model',['racer','heavy_quad'])
def test_manual_arm_ground_contact_then_takeoff(model):
    physics_name='internal.yaml' if model=='racer' else 'internal_heavy_quad.yaml'
    mission_name='bullet_profile.yaml' if model=='racer' else 'bullet_profile_heavy_quad.yaml'
    config=YamlConfigLoader().load(ROOT/'config'/physics_name)
    config=replace(config,simulation=replace(config.simulation,gui=False,max_steps=10000))
    nav=NavigatorConfig.from_yaml(ROOT/'config'/mission_name)
    mission=Mission(nav,app_id='app',flight_session=FlightSession('manual'))
    mission.configure(dict(schema_version=1,physics_id='physics',stream_id='stream',
        mass_kg=nav.vehicle.mass_kg,gravity_m_s2=nav.vehicle.gravity_m_s2,max_thrust_n=nav.vehicle.max_thrust_n,
        rc_angle_scale_rad=.7853981633974483,rc_yaw_rate_scale_rad_s=2.,
        aetr_channels=[1,2,3,4],arm_channel=5,mode_channel=6,
        camera=dict(width_px=640,height_px=480,fov_x_deg=90.),attitude_model='ideal',
        physics_hz=240,feedback_hz=120,command_hz=100))
    controller=InternalControlSettings((4.,4.,4.),(2.,2.,2.),
        tuple(PidSettings(kp=kp,ki=0.,kd=0.,output_limit=.1,integral_limit=0.) for kp in config.control.rate_kp))
    sim=RcSimulation(config,controller)
    gate=ScenarioTermination(mission_gated=True)
    try:
        obs=sim.reset()
        command=None
        arm_step=360
        start_step=840
        contact_while_armed=False
        for step in range(2400):
            now=1000.+step/240
            source=dict(physics_id='physics',episode_id=obs.ground_truth.episode_id,stream_id='stream',
                step_index=step,simulation_time_s=step/240,measurement_us=int(now*1e6))
            mission.observe(dict(schema_version=1,source=source,
                barometer_altitude_m=obs.sensors.barometer.altitude_m,
                orientation_xyzw=list(obs.ground_truth.orientation_xyzw),armed=False if sim.last_command is None else sim.last_command.armed,
                mode='angle',last_applied_sequence=0 if command is None else command['sequence'],
                owner_id='app',state='running',reason='started'))
            if step==arm_step:
                mission.manual_command('height',2.,now)
                assert mission.prearm_ready(now), (mission.phase,mission.reason)
                mission.manual_command('arm',None,now)
            if step==start_step:
                assert contact_while_armed and mission.phase=='ARMED_IDLE'
                mission.manual_command('start',None,now)
            command=mission.tick(now_s=now)
            gate.command(command,step+1)
            obs=sim.step(RcInput(tuple(command['channels'])))
            contact=sim.terrain_contact()
            crash=gate.terrain_collision(step=step+1,clearance_m=sim.terrain_clearance_m(),contact=contact)
            assert not crash,(step,mission.phase,mission.reason)
            if arm_step<step<start_step:
                contact_while_armed |= contact
                assert command['channels'][2]==1000 and not command['mission_started']
            if gate.terrain_enabled:
                assert step>=start_step and sim.terrain_clearance_m()>=.2
                break
        assert gate.terrain_enabled,(mission.phase,mission.reason,sim.terrain_clearance_m())
        # A subsequent actual return to terrain must end the episode.
        disarmed=(1500,1500,1000,1500,1000,2000)+(1000,)*12
        crashed=False
        for offset in range(1000):
            obs=sim.step(RcInput(disarmed))
            crashed=gate.terrain_collision(step=step+2+offset,
                clearance_m=sim.terrain_clearance_m(),contact=sim.terrain_contact())
            if crashed:break
        assert crashed
        gate.stop_mission()
        assert not gate.terrain_enabled and gate.mission_start_step is None
    finally:
        sim.close()
