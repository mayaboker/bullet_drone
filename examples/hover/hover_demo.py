"""Reusable composition for the ideal-racer altitude demonstration."""

from dataclasses import dataclass
from math import ceil
from bullet_drone.rendering.composition import compose_rendering

from bullet_drone.composition import create_flight_command_provider
from bullet_drone.config import DroneSettings, SimulationConfig, SimulationSettings, _number
from bullet_drone.controllers import InternalControlSettings, PidSettings
from bullet_drone.controllers.altitude import AltitudeController
from bullet_drone.environment import DroneEnvironment
from examples.hover.hover_mission import HoverMissionController, MissionTransition
from bullet_drone.rc import RcCodec, SoftwareRc
from bullet_drone.models import DroneObservation
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.runner import SimulationRunner
from bullet_drone.vehicle import load_racer_parameters


class HoverDemoTimeoutError(RuntimeError):
    """The demonstration did not finish landing and disarming within its budget."""


@dataclass(frozen=True, slots=True)
class HoverDemoResult:
    observation: DroneObservation
    transitions: tuple[MissionTransition, ...]


def run_hover_demo(*, gui: bool = True, max_duration_s: float = 45.0,
                   renderer: str | None = None, render_config=None, headless: bool = False,
                   initial_position_m: tuple[float, float, float] = (0.0, 0.0, 0.015)) -> HoverDemoResult:
    """Run the fixed ideal-profile example; timeout and failures close resources."""
    duration = _number(max_duration_s, "demo.max_duration_s", positive=True)
    gui, pace, consumers = compose_rendering(renderer, render_config, gui=gui, headless=headless)
    dt = 1 / 240
    config = SimulationConfig(
        SimulationSettings(dt, ceil(duration / dt), (0.0, 0.0, -9.81), gui),
        DroneSettings(1.0, initial_position_m),
    )
    vehicle = load_racer_parameters()
    altitude = AltitudeController(
        config.drone.mass_kg, -config.simulation.gravity_m_s2[2],
        4 * vehicle.max_thrust_per_rotor_n,
        PidSettings(1.5, 0.0, 0.0, 1.0, 0.0),
        PidSettings(4.0, 1.0, 0.0, 3.0, 1.0),
    )
    stabilization = InternalControlSettings(
        (4.0, 4.0, 4.0), (2.0, 2.0, 2.0),
        (PidSettings(0.05, 0.0, 0.0, 0.1, 0.0),) * 3,
    )
    codec = RcCodec(altitude.max_thrust_n, stabilization.max_rates_rad_s, config.rc)
    mission = HoverMissionController(altitude, SoftwareRc(codec), rc_codec=codec)
    provider = create_flight_command_provider(config.control, mission, stabilization, vehicle, dt)
    final = SimulationRunner().run(
        DroneEnvironment(PyBulletPhysics(config, vehicle)), config.simulation.max_steps,
        pace_wall_time=pace, command_provider=provider, consumers=consumers,
        stop_when=lambda observation: mission.completed,
    )
    if not mission.completed:
        raise HoverDemoTimeoutError(f"Hover demo did not complete within {duration:g} s (phase: {mission.phase})")
    return HoverDemoResult(final, mission.transitions)
