"""Supervise a persistent physics loop and optional external processes."""
from collections.abc import Sequence
from contextlib import ExitStack
import os
import select
import sys
import time

import click
from loguru import logger

from bullet_drone.betaflight.backend import BetaflightBackend
from bullet_drone.betaflight.bridge import UdpSitlBridge
from bullet_drone.config import ControlSettings, DroneSettings, SimulationConfig, SimulationSettings
from bullet_drone.environment import DroneEnvironment
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.sensors import BarometerSensor, ImuSensor
from bullet_drone.vehicle import load_racer_parameters
from launcher.cli import CliParser
from launcher.sitl import SitlSession


RATE_HZ = 240
TIMESTEP_S = 1 / RATE_HZ
MAX_SIMULATION_STEPS = 2**31 - 1
GRAVITY_M_S2 = 9.81
GRAVITY_VECTOR_M_S2 = (0.0, 0.0, -GRAVITY_M_S2)
INITIAL_POSITION_M = (0.0, 0.0, 0.015)
MAVLINK_PORT = 5762


def run(options):
    with ExitStack() as resources:
        if options.sitl:
            sitl = resources.enter_context(SitlSession(options.sitl_binary, profile_path=options.sitl_profile,
                                                     extra_ports=(MAVLINK_PORT,)))
        viewer = None
        if options.render:
            backend_label = 'betaflight' if options.sitl else 'internal'
            if options.renderer_backend == 'isaac':
                from launcher.isaac_renderer import IsaacRenderer
                viewer = resources.enter_context(IsaacRenderer(
                    options.render_config, profile_name='Simulation Launcher',
                    backend=backend_label, headless=options.isaac_headless,
                    world=options.world))
            else:
                from launcher.renderer import ExternalRenderer
                viewer = resources.enter_context(ExternalRenderer(
                    options.renderer, options.render_config, profile_name='Simulation Launcher',
                    backend=backend_label,
                    window_monitor=options.render_monitor, window_half=options.render_half))
        vehicle = load_racer_parameters()
        config = SimulationConfig(SimulationSettings(TIMESTEP_S, MAX_SIMULATION_STEPS,
                                                     GRAVITY_VECTOR_M_S2, gui=False),
                                  DroneSettings(1.0, INITIAL_POSITION_M),
                                  control=ControlSettings('betaflight' if options.sitl else 'internal'))
        if options.physics_backend == 'isaac':
            from bullet_drone.isaac_physics import IsaacPhysics
            physics = IsaacPhysics(config, vehicle)
        else:
            physics = PyBulletPhysics(config, vehicle, target_scene=options.target_scene)
        resources.callback(physics.close)
        environment = DroneEnvironment(
            physics, imu=ImuSensor(GRAVITY_VECTOR_M_S2, config.sensors.imu, sample_period_s=TIMESTEP_S),
            barometer=BarometerSensor(config.sensors.barometer))
        resources.callback(environment.close)
        backend = BetaflightBackend(vehicle, UdpSitlBridge()) if options.sitl else None
        if backend is not None:
            resources.callback(backend.close)
        observation = environment.reset()
        if backend is not None:
            backend.reset(observation)
        ready = False
        contact_published = False
        next_step = time.monotonic()
        stdin_fd = sys.stdin.fileno() if sys.stdin.isatty() else -1
        if stdin_fd >= 0:
            os.set_blocking(stdin_fd, False)
            logger.info('Type "reset" + Enter to reset the scene without restarting')
        stdin_buf = ''
        while True:
            if stdin_fd >= 0 and select.select([stdin_fd], [], [], 0)[0]:
                chunk = os.read(stdin_fd, 256)
                if chunk:
                    stdin_buf += chunk.decode(errors='replace')
                while '\n' in stdin_buf:
                    line, stdin_buf = stdin_buf.split('\n', 1)
                    command = line.strip()
                    if command == 'reset':
                        logger.info('Resetting scene')
                        observation = environment.reset()
                        if backend is not None:
                            backend.reset(observation)
                        contact_published = False
                        if viewer:
                            viewer.consume(observation)
                        next_step = time.monotonic() + TIMESTEP_S
                        logger.info('Scene reset complete')
                    elif command:
                        logger.warning('Unknown command: {}', command)
            if options.sitl:
                sitl.check_running()
            if viewer:
                viewer.ensure_running()
                if not ready:
                    viewer.wait_ready(observation)
                    viewer.set_running(True)
                    ready = True
            remaining = next_step - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            next_step = time.monotonic() + TIMESTEP_S
            if backend:
                observation = environment.step(backend.command(observation))
            else:
                observation = environment.hold()
            if viewer:
                viewer.consume(observation)
                if options.target_scene and not contact_published and physics.target_contact():
                    viewer.publisher.set_contact(observation.ground_truth)
                    contact_published = True


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = CliParser().parse(argv)
    except click.ClickException as error:
        error.show()
        return error.exit_code
    except (click.Abort, KeyboardInterrupt):
        return 130
    if isinstance(options, int):
        return options
    logger.remove()
    logger.add(sys.stderr, level='INFO', colorize=sys.stderr.isatty(),
               format='<green>{time:HH:mm:ss.SSS}</green> | <level>{level:8}</level> | <level>{message}</level>',
               diagnose=False)
    try:
        run(options)
    except KeyboardInterrupt:
        logger.info('Interrupted; simulation, renderer, and SITL closed')
        return 130
    except Exception:
        logger.exception('Simulation launcher failed')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
