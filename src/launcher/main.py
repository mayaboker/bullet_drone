"""Supervise a persistent PyBullet loop and optional external processes."""
from collections.abc import Sequence
from contextlib import ExitStack
from functools import partial
import sys
import time

import click
from loguru import logger

from bullet_drone.betaflight.backend import BetaflightBackend
from bullet_drone.betaflight.bridge import UdpSitlBridge
from bullet_drone.betaflight.fdm import pack_fdm
from bullet_drone.config import (ControlSettings, DroneSettings, GpsSettings, SensorsSettings,
                                 SimulationConfig, SimulationSettings)
from bullet_drone.environment import DroneEnvironment
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.sensors import BarometerSensor, GpsSensor, ImuSensor
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
GPS_ORIGIN_LATITUDE_DEG = 0.0
GPS_ORIGIN_LONGITUDE_DEG = 0.0
GPS_ORIGIN_ALTITUDE_M = 100.0


def _simulation_config(options):
    """Build matching physics and virtual-GPS sensor settings for the launcher."""
    gps = GpsSettings(True, GPS_ORIGIN_LATITUDE_DEG, GPS_ORIGIN_LONGITUDE_DEG,
                      GPS_ORIGIN_ALTITUDE_M) if options.sitl or options.gps else GpsSettings()
    return SimulationConfig(SimulationSettings(TIMESTEP_S, MAX_SIMULATION_STEPS,
                                               GRAVITY_VECTOR_M_S2, gui=False),
                            DroneSettings(1.0, INITIAL_POSITION_M),
                            control=ControlSettings('betaflight' if options.sitl else 'internal'),
                            sensors=SensorsSettings(gps=gps))


def run(options):
    with ExitStack() as resources:
        if options.sitl:
            sitl = resources.enter_context(SitlSession(options.sitl_binary, profile_path=options.sitl_profile,
                                                     extra_ports=(MAVLINK_PORT,), gps_enabled=options.gps))
        viewer = None
        if options.render:
            from launcher.renderer import ExternalRenderer
            viewer = resources.enter_context(ExternalRenderer(
                options.renderer, options.render_config, profile_name='Simulation Launcher',
                backend='betaflight' if options.sitl else 'internal',
                window_monitor=options.render_monitor, window_half=options.render_half))
        vehicle = load_racer_parameters()
        config = _simulation_config(options)
        physics = PyBulletPhysics(config, vehicle, target_scene=options.target_scene)
        resources.callback(physics.close)
        environment = DroneEnvironment(
            physics, imu=ImuSensor(GRAVITY_VECTOR_M_S2, config.sensors.imu, sample_period_s=TIMESTEP_S),
            barometer=BarometerSensor(config.sensors.barometer),
            gps=GpsSensor(config.sensors.gps) if config.sensors.gps.enabled else None)
        resources.callback(environment.close)
        backend = (BetaflightBackend(vehicle, UdpSitlBridge(),
                                    encoder=partial(pack_fdm, gps_enabled=options.gps,
                                                    gps_coordinates_only=not options.gps))
                   if options.sitl else None)
        if backend is not None:
            resources.callback(backend.close)
        observation = environment.reset()
        if backend is not None:
            backend.reset(observation)
        ready = False
        contact_published = False
        next_step = time.monotonic()
        while True:
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
