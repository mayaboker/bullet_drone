"""Godot lifecycle with app-owned expiring RC, ideal attitude and noisy barometer."""
import sys
import time
from pathlib import Path

import click
from loguru import logger
from bullet_msgs import load_transport
from bullet_drone.config import DroneSettings, SimulationConfig, SimulationSettings
from bullet_drone.simulation import RcSimulation
from bullet_drone.commands import RcInput
from bullet_drone.vehicle import load_racer_parameters
from examples.position_square.demo import FLIGHT_CONTROL_SETTINGS
from tools.zmq_render import DEFAULT_RENDER_CONFIG
from tools.zmq_render.control import SimulationControl
from tools.zmq_render.scenario import ScenarioTermination
from tools.zmq_render.flight import FlightLease, FlightReceiver
from tools.zmq_render.publisher import RenderPublisher


PHYSICS_HZ = 240
FEEDBACK_HZ = 120
COMMAND_HZ = 100
MAX_EPISODE_STEPS = 10**9
NANOSECONDS_PER_MICROSECOND = 1000
FIRST_COMMAND_TIMEOUT_S = 0.5
GRAVITY_M_S2 = 9.81
MASS_KG = 1.0
INITIAL_POSITION_M = (0.0, 0.0, 0.015)


class CliParser:
    def parse(self, argv=None):
        @click.command()
        @click.option('--render-config', default=DEFAULT_RENDER_CONFIG, type=click.Path(exists=True, path_type=Path))
        def command(render_config):
            return render_config
        return command.main(args=argv, prog_name='external-rc', standalone_mode=False)


def run(path, *, simulation_factory=RcSimulation):
    renderer = RenderPublisher(path)
    control = receiver = simulation = None
    try:
        renderer.start()
        transport = load_transport(renderer.transport_path)
        scenario = ScenarioTermination()
        control = SimulationControl(renderer.transport_path, renderer, scenario=scenario)
        lease = FlightLease(control.physics_id)
        receiver = FlightReceiver(transport['flight_command_endpoint'], lease)
        vehicle = load_racer_parameters()
        config = SimulationConfig(SimulationSettings(1 / PHYSICS_HZ, MAX_EPISODE_STEPS, (0., 0., -GRAVITY_M_S2), gui=False),
                                  DroneSettings(MASS_KG, INITIAL_POSITION_M))
        simulation = simulation_factory(config, FLIGHT_CONTROL_SETTINGS, vehicle)
        platform = dict(schema_version=1, physics_id=control.physics_id, stream_id=renderer.stream,
                        mass_kg=MASS_KG, gravity_m_s2=GRAVITY_M_S2,
                        max_thrust_n=len(vehicle.rotor_positions_m) * vehicle.max_thrust_per_rotor_n,
                        rc_angle_scale_rad=config.rc.max_angle_rad,
                        rc_yaw_rate_scale_rad_s=FLIGHT_CONTROL_SETTINGS.max_rates_rad_s[2],
                        aetr_channels=list(config.rc.aetr_channels),
                        arm_channel=config.rc.arm_channel, mode_channel=config.rc.mode_channel,
                        camera=renderer.config['camera'], attitude_model='ideal',
                        physics_hz=PHYSICS_HZ, feedback_hz=FEEDBACK_HZ, command_hz=COMMAND_HZ)
        observation = simulation.reset()
        applied_sequence = 0
        armed, mode = False, 'angle'
        def publish(*, captured=False):
            nonlocal source
            state = observation.ground_truth
            if captured:
                source = dict(physics_id=control.physics_id, episode_id=state.episode_id, stream_id=renderer.stream,
                              step_index=state.step_index, simulation_time_s=state.simulation_time_s,
                              measurement_us=time.monotonic_ns() // NANOSECONDS_PER_MICROSECOND)
                scenario.observe(source)
            reading = observation.sensors.barometer
            feedback = dict(schema_version=1, source=source, barometer_altitude_m=None if reading is None else reading.altitude_m,
                            orientation_xyzw=list(state.orientation_xyzw), armed=armed, mode=mode,
                            last_applied_sequence=applied_sequence, owner_id=lease.owner,
                            state=control.state, reason=control.reason)
            renderer.set_flight(platform, feedback)
            if captured:
                renderer.consume(observation, source=source)
        source = None
        control.transition('stopped', 'waiting_app', observation)
        publish(captured=True)
        start_time = first_deadline = time.monotonic()
        while True:
            receiver.poll(observation.ground_truth.episode_id)
            action = control.poll()
            if action == 'reset' or (action == 'start' and control.state != 'running'):
                can_start = action == 'start' and lease.ready()
                if action == 'start' and not can_start:
                    if scenario.result is None:
                        control.transition('stopped', 'app_not_ready', observation)
                    else:
                        control.publish(observation, force=True)
                else:
                    owner_packet = lease.candidate
                    lease.end()
                    scenario.reset()
                    observation = simulation.reset()
                    applied_sequence, armed, mode = 0, False, 'angle'
                    if can_start:
                        lease.candidate = owner_packet
                        lease.begin(observation.ground_truth.episode_id)
                    control.transition('running' if can_start else 'stopped', 'started' if can_start else 'reset', observation)
                    start_time = time.monotonic()
                    first_deadline = start_time + FIRST_COMMAND_TIMEOUT_S
                    publish(captured=True)
            elif action == 'collision':
                lease.end()
                control.transition('stopped', 'target_hit', observation)
                publish()
            elif action in ('stop', 'controller_timeout', 'controller_changed') and control.state == 'running':
                control.transition('stopped', action, observation)
                lease.end()
            control.publish(observation)
            if control.state != 'running':
                publish()
                continue
            receiver.poll(observation.ground_truth.episode_id)
            channels = lease.command()
            if channels is None:
                if lease.latest is None and time.monotonic() < first_deadline:
                    publish()
                    time.sleep(1 / PHYSICS_HZ)
                    start_time = time.monotonic()
                    continue
                control.transition('stopped', lease.reason, observation)
                lease.end()
                publish()
                continue
            observation = simulation.step(RcInput(tuple(channels)))
            applied_sequence = lease.sequence
            armed, mode = simulation.last_command.armed, simulation.last_command.mode
            publish(captured=True)
            remaining = start_time + observation.ground_truth.simulation_time_s - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
    finally:
        if simulation is not None:
            simulation.close()
        if receiver is not None:
            receiver.close()
        if control is not None:
            control.close()
        renderer.close()


def main(argv=None):
    logger.remove()
    logger.add(sys.stderr, level='INFO', diagnose=False)
    try:
        path = CliParser().parse(argv)
        if isinstance(path, int):
            return path
        run(path)
    except KeyboardInterrupt:
        return 130
    except Exception:
        logger.exception('External RC example failed')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
