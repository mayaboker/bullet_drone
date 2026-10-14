"""Compose the position gate mission without changing the simulation entry point."""
from dataclasses import dataclass
from math import ceil, radians
from pathlib import Path

from bullet_drone.composition import create_flight_command_provider
from bullet_drone.config import ConfigurationError, DroneSettings, SimulationConfig, SimulationSettings, _number
from bullet_drone.controllers import AltitudeController, InternalControlSettings, PidSettings
from bullet_drone.controllers.position import PositionController
from bullet_drone.environment import DroneEnvironment
from bullet_drone.rc import RcCodec, SoftwareRc
from bullet_drone.models import DroneObservation, Vector3
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.rendering.composition import compose_rendering
from bullet_drone.runner import SimulationRunner
from bullet_drone.vehicle import load_racer_parameters
from examples.position.mission import PositionMission, PositionTransition


class PositionDemoTimeoutError(RuntimeError):
    """Course did not finish within its simulation-time budget."""


@dataclass(frozen=True, slots=True)
class PositionDemoResult:
    observation: DroneObservation
    transitions: tuple[PositionTransition, ...]


def run_position_demo(*, gui: bool = True, max_duration_s: float = 180.,
                      renderer: str | None = None, render_config: Path | None = None,
                      headless: bool = False, initial_position_m: Vector3 = (0.,0.,.015)) -> PositionDemoResult:
    duration = _number(max_duration_s, 'position_demo.max_duration_s', positive=True)
    drone = DroneSettings(1., initial_position_m)
    x, y, z = drone.initial_position_m
    if x >= 6 or abs(y) > 1.3 or not 0 <= z <= .03:
        raise ConfigurationError('Gate mission starts require X < 6 m, |Y| <= 1.3 m and ground-level Z in 0..0.03 m')
    gui, pace, consumers = compose_rendering(renderer, render_config, gui=gui, headless=headless)
    dt = 1 / 240
    config = SimulationConfig(SimulationSettings(dt, ceil(duration/dt), (0.,0.,-9.81), gui), drone)
    vehicle = load_racer_parameters()
    altitude = AltitudeController(1., 9.81, 4*vehicle.max_thrust_per_rotor_n,
                                  PidSettings(1.5,0,0,1,0), PidSettings(4,1,0,3,1))
    settings = InternalControlSettings((4,4,4), (2,2,2), (PidSettings(.05,0,0,.1,0),)*3)
    codec = RcCodec(altitude.max_thrust_n, settings.max_rates_rad_s, config.rc)
    controller = PositionController(altitude, PidSettings(.8,0,0,1,0),
                                    PidSettings(2,0,0,1.5,0), radians(15),codec)
    mission = PositionMission(controller, SoftwareRc(codec))
    provider = create_flight_command_provider(config.control, mission, settings, vehicle, dt)
    final = SimulationRunner().run(DroneEnvironment(PyBulletPhysics(config, vehicle)), config.simulation.max_steps,
                                   pace_wall_time=pace, command_provider=provider, consumers=consumers,
                                   stop_when=lambda observation: mission.completed)
    if not mission.completed:
        raise PositionDemoTimeoutError(f'Position mission exceeded {duration:g} s (phase: {mission.phase}, waypoint: {mission.index})')
    return PositionDemoResult(final, mission.transitions)
