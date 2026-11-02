from copy import deepcopy
import json
import time

import zmq
from bullet_msgs.scenario import COLLISION_TOPIC
from tools.zmq_render.scenario import ScenarioTermination


def report(stamp, **changes):
    value = dict(schema_version=1, event_id='hit', controller_id='godot', issued_us=1_100_000,
                 source=dict(stamp), target_id='red_truck', drone_position_m=[50., 0., 5.])
    value.update(changes)
    return value


def test_source_history_owner_freshness_first_end_and_reset():
    scenario = ScenarioTermination(clock=lambda: 1.1)
    source = dict(physics_id='physics', episode_id='episode', stream_id='stream', step_index=2,
                  simulation_time_s=.1, measurement_us=1_000_000)
    scenario.observe(source)
    final = dict(source, step_index=3, simulation_time_s=.12, measurement_us=1_050_000)
    scenario.observe(final)
    args = dict(controller_id='godot', running=True, controller_live=True)
    for changes in (dict(controller_id='foreign'), dict(source=dict(source, episode_id='foreign')),
                    dict(source=dict(source, measurement_us=1_001_000)), dict(issued_us=2_000_000)):
        assert not scenario.accept(report(source, **changes), **args)
    assert not scenario.accept(report(source), **dict(args, running=False))
    assert not scenario.accept(report(source), **dict(args, controller_live=False))
    assert scenario.accept(report(source), **args)
    assert scenario.result['final_source'] == final
    saved = deepcopy(scenario.result)
    assert not scenario.accept(report(source, event_id='duplicate'), **args)
    assert scenario.result == saved
    scenario.reset()
    assert scenario.result is None and not scenario.history
    assert not scenario.accept(report(source), **args)


def test_real_tcp_exact_collision_topic_and_control_order(tmp_path):
    from tools.zmq_render.control import SimulationControl
    class Publisher:
        def set_state(self, state):
            self.state = state
    with zmq.Context() as context, context.socket(zmq.PUB) as pub:
        pub.setsockopt(zmq.LINGER, 0)
        port = pub.bind_to_random_port('tcp://127.0.0.1')
        path = tmp_path / 'transport.json'
        path.write_text(json.dumps(dict(telemetry_endpoint='tcp://127.0.0.1:1', image_endpoint='tcp://127.0.0.1:2', control_endpoint=f'tcp://127.0.0.1:{port}')))
        scenario = ScenarioTermination(clock=lambda: 1.1)
        control = SimulationControl(path, Publisher(), clock=lambda: 1.1, scenario=scenario)
        try:
            control.controller_id, control.last_heartbeat, control.state = 'godot', 1.1, 'running'
            source = dict(physics_id=control.physics_id, episode_id='episode', stream_id='stream', step_index=2,
                          simulation_time_s=.1, measurement_us=1_000_000)
            scenario.observe(source)
            time.sleep(.1)
            pub.send_multipart([COLLISION_TOPIC + b'/extra', json.dumps(report(source)).encode()])
            pub.send_multipart([COLLISION_TOPIC, b'{'])
            time.sleep(.02)
            assert control.poll() is None
            pub.send_multipart([COLLISION_TOPIC, json.dumps(report(source)).encode()])
            deadline = time.monotonic() + 1
            action = None
            while action is None and time.monotonic() < deadline:
                action = control.poll()
                time.sleep(.001)
            assert action == 'collision'
            assert scenario.result['reason'] == 'target_hit'
        finally:
            control.close()


def test_manual_mission_and_liftoff_gates_and_delayed_reports():
    scenario=ScenarioTermination(clock=lambda:1.1,mission_gated=True)
    source=dict(physics_id='physics',episode_id='episode',stream_id='stream',step_index=2,
        simulation_time_s=.1,measurement_us=1_000_000)
    args=dict(controller_id='godot',running=True,controller_live=True)
    packet=dict(schema_version=2,active=True,mission_started=False,channels=[1500]*18)
    scenario.command(packet,3)
    scenario.observe(source)
    assert not scenario.accept(report(source),**args)
    assert not scenario.terrain_collision(step=2,clearance_m=0.,contact=True)
    scenario.command(dict(packet,mission_started=True),3)
    scenario.observe(source)
    assert not scenario.history
    assert not scenario.terrain_collision(step=3,clearance_m=0.,contact=True)
    final=dict(source,step_index=3,measurement_us=1_050_000)
    scenario.observe(final)
    assert not scenario.accept(report(source),**args)
    assert scenario.accept(report(final),**args)  # target hit works before liftoff
    assert not scenario.terrain_collision(step=4,clearance_m=.19,contact=False)
    assert not scenario.terrain_collision(step=5,clearance_m=.2,contact=False)
    assert scenario.terrain_enabled
    assert scenario.terrain_collision(step=6,clearance_m=0.,contact=True)
    scenario.stop_mission()
    assert not scenario.terrain_enabled and scenario.mission_start_step is None
    assert scenario.result is not None  # terminal publication survives gate cleanup
    scenario.reset()
    assert scenario.result is None


def test_legacy_armed_command_and_invalid_clearance_do_not_bypass_liftoff():
    scenario=ScenarioTermination(mission_gated=True)
    packet=dict(schema_version=1,active=True,channels=[1500]*18)
    scenario.command(dict(packet,active=False),2)
    assert scenario.mission_start_step is None
    scenario.command(packet,3)
    assert scenario.mission_start_step==3
    for clearance,contact in ((float('inf'),False),(float('nan'),False),(.5,True)):
        assert not scenario.terrain_collision(step=3,clearance_m=clearance,contact=contact)
    scenario.command(packet,8)
    assert scenario.mission_start_step==3  # boundary does not move on heartbeat
    scenario.stop_mission()
    scenario.command(dict(schema_version=2,active=True,mission_started=False),10)
    assert scenario.mission_start_step is None
