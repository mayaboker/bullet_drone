"""Supervise a persistent physics loop and optional external processes."""
from collections.abc import Sequence
from contextlib import ExitStack
from functools import partial
import socket
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
from launcher.control import SimulationControl
from launcher.target_spawn import load_target_spawn


RATE_HZ = 240
TIMESTEP_S = 1 / RATE_HZ
MAX_SIMULATION_STEPS = 2**31 - 1
GRAVITY_M_S2 = 9.81
GRAVITY_VECTOR_M_S2 = (0.0, 0.0, -GRAVITY_M_S2)
INITIAL_POSITION_M = (0.0, 0.0, 0.015)
MAVLINK_PORT = 5762
MSP_PORT = 5761
SITL_READY_TIMEOUT_S = 10.0
SITL_READY_POLL_S = 0.05
GPS_ORIGIN_LATITUDE_DEG = 0.0
GPS_ORIGIN_LONGITUDE_DEG = 0.0
GPS_ORIGIN_ALTITUDE_M = 100.0


def _simulation_config(options):
    """Build matching physics and virtual-GPS sensor settings for the launcher."""
    gps = GpsSettings(True, GPS_ORIGIN_LATITUDE_DEG, GPS_ORIGIN_LONGITUDE_DEG,
                      GPS_ORIGIN_ALTITUDE_M) if options.sitl or options.gps else GpsSettings()
    initial_position, initial_yaw = (load_target_spawn(options.target_spawn_config)
                                     if options.target_scene and options.target_spawn_config is not None
                                     else (INITIAL_POSITION_M, 0.0))
    return SimulationConfig(SimulationSettings(TIMESTEP_S, MAX_SIMULATION_STEPS,
                                               GRAVITY_VECTOR_M_S2, gui=False),
                            DroneSettings(1.0, initial_position, initial_yaw_rad=initial_yaw),
                            control=ControlSettings('betaflight' if options.sitl else 'internal'),
                            sensors=SensorsSettings(gps=gps))


def _wait_sitl_ready(session):
    """Confirm that the fresh firmware has opened both App TCP listeners."""
    deadline = time.monotonic() + SITL_READY_TIMEOUT_S
    while time.monotonic() < deadline:
        session.check_running()
        ready = True
        for port in (MSP_PORT, MAVLINK_PORT):
            with socket.socket() as probe:
                probe.settimeout(SITL_READY_POLL_S)
                if probe.connect_ex(('127.0.0.1', port)) != 0:
                    ready = False
                    break
        if ready:
            return
        time.sleep(SITL_READY_POLL_S)
    raise TimeoutError('SITL MSP/MAVLink listeners did not become ready')


def run(options):
    with ExitStack() as resources:
        sitl = None
        backend = None

        def close_firmware():
            nonlocal sitl, backend
            old_backend, backend = backend, None
            old_sitl, sitl = sitl, None
            try:
                if old_backend is not None:
                    old_backend.close()
            finally:
                if old_sitl is not None:
                    old_sitl.__exit__(None, None, None)

        resources.callback(close_firmware)

        def open_sitl():
            nonlocal sitl
            candidate = SitlSession(options.sitl_binary, profile_path=options.sitl_profile,
                                    extra_ports=(MAVLINK_PORT,), gps_enabled=options.gps)
            candidate.__enter__()
            sitl = candidate

        if options.sitl:
            open_sitl()
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
        config = _simulation_config(options)
        config = _simulation_config(options)
        if options.physics_backend == 'isaac':
            from bullet_drone.isaac_physics import IsaacPhysics
            physics = IsaacPhysics(config, vehicle)
        else:
            physics = PyBulletPhysics(config, vehicle, target_scene=options.target_scene)
        resources.callback(physics.close)
        environment = DroneEnvironment(
            physics, imu=ImuSensor(GRAVITY_VECTOR_M_S2, config.sensors.imu, sample_period_s=TIMESTEP_S),
            barometer=BarometerSensor(config.sensors.barometer),
            gps=GpsSensor(config.sensors.gps) if config.sensors.gps.enabled else None)
        resources.callback(environment.close)
        def open_backend(observation):
            nonlocal backend
            backend = BetaflightBackend(vehicle, UdpSitlBridge(),
                                        encoder=partial(pack_fdm, gps_enabled=options.gps,
                                                        gps_coordinates_only=not options.gps))
            backend.reset(observation)

        observation = environment.reset()
        if options.sitl:
            open_backend(observation)

        contact_published = False

        def reset_simulation():
            nonlocal contact_published
            close_firmware()
            fresh = environment.reset()
            try:
                if options.sitl:
                    open_sitl()
                    open_backend(fresh)
                    _wait_sitl_ready(sitl)
                if viewer:
                    viewer.publisher.clear_contact()
                    viewer.wait_ready(fresh)
                contact_published = False
                return fresh
            except Exception:
                close_firmware()
                raise

        def on_state(state):
            if viewer:
                viewer.publisher.set_simulation_state(state)
                viewer.set_running(state.state == 'running')

        control = resources.enter_context(SimulationControl(
            options.simulation_control_endpoint, observation, on_state))
        ready = False
        next_step = time.monotonic()
        while True:
            if sitl is not None and control.state == 'running':
                sitl.check_running()
            if viewer:
                viewer.ensure_running()
                if not ready:
                    viewer.wait_ready(observation)
                    viewer.set_running(control.state == 'running')
                    ready = True
            observation = control.update(observation, reset_simulation)
            remaining = next_step - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            next_step = time.monotonic() + TIMESTEP_S
            if control.state == 'error':
                # A failed physics reset may leave the environment unready.
                # Keep the service alive so the operator can retry Reset.
                continue
            if backend and control.state == 'running':
                observation = environment.step(backend.command(observation))
            else:
                if backend:
                    backend.command(observation)
                observation = environment.hold()
            if viewer:
                viewer.consume(observation)
                if (control.state == 'running' and options.target_scene
                        and not contact_published and physics.target_contact()):
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
