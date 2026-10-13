"""Composition: existing controller contracts plus passive tracing adapters."""
from dataclasses import dataclass
from math import ceil, radians
from pathlib import Path

from bullet_drone.actuators import IdealMotorDynamics
from bullet_drone.composition import FlightCommandProvider
from bullet_drone.config import ConfigurationError, DroneSettings, SimulationConfig, SimulationSettings, _number
from bullet_drone.controllers import AltitudeController, IdealStateFeedback, InternalControlSettings, InternalFlightController, PidSettings, PositionController
from bullet_drone.environment import DroneEnvironment
from bullet_drone.joystick import SoftwareJoystick
from bullet_drone.mixer import MotorMixer
from bullet_drone.models import DroneObservation, Vector3
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.propellers import IdealPropellerModel
from bullet_drone.rendering.composition import compose_rendering
from bullet_drone.runner import SimulationRunner
from bullet_drone.vehicle import load_racer_parameters
from examples.position_control.mission import Arrival, ControlChainMission
from examples.position_control.probes import MotorProbe, PropellerProbe, StabilizationProbe
from examples.position_control.verification import ChainVerification, verify_chain
from examples.position_control.trace import ChainRecorder, ChainSample


class ControlChainTimeoutError(RuntimeError):
    """Flight did not finish in its simulation-time budget."""


@dataclass(frozen=True, slots=True)
class ControlChainResult:
    observation: DroneObservation
    arrivals: tuple[Arrival, ...]
    samples: tuple[ChainSample, ...]
    verification: ChainVerification


def run_control_chain(*, gui: bool = True, headless: bool = False, renderer: str | None = None,
                      render_config: Path | None = None, trace_path: Path | None = None,
                      initial_position_m: Vector3 = (0.,0.,.015), max_duration_s: float = 120.) -> ControlChainResult:
    duration = _number(max_duration_s,'chain.max_duration_s',positive=True)
    drone = DroneSettings(1.,initial_position_m)
    if not 0 <= drone.initial_position_m[2] <= .03:
        raise ConfigurationError('Control-chain example requires ground-level initial Z in 0..0.03 m')
    gui, pace, render_consumers = compose_rendering(renderer,render_config,gui=gui,headless=headless)
    dt = 1/240
    config = SimulationConfig(SimulationSettings(dt,ceil(duration/dt),(0.,0.,-9.81),gui),drone)
    vehicle = load_racer_parameters()
    altitude = AltitudeController(drone.mass_kg,9.81,4*vehicle.max_thrust_per_rotor_n,
                                  PidSettings(1.5,0,0,1,0),PidSettings(4,1,0,3,1))
    position = PositionController(altitude,PidSettings(.8,0,0,1,0),PidSettings(2,0,0,1.5,0),radians(15))
    mission = ControlChainMission(position,SoftwareJoystick())
    settings = InternalControlSettings((4,4,4),(2,2,2),(PidSettings(.05,0,0,.1,0),)*3)
    stabilization = StabilizationProbe(InternalFlightController(settings))
    provider = FlightCommandProvider(mission,stabilization,IdealStateFeedback(),MotorMixer(vehicle),dt)
    motors = MotorProbe(IdealMotorDynamics(vehicle.max_speed_rad_s))
    propellers = PropellerProbe(IdealPropellerModel(vehicle))
    recorder = ChainRecorder(mission,provider,stabilization,motors,propellers,trace_path)
    physics = PyBulletPhysics(config,vehicle,motor_dynamics=motors,propeller_model=propellers)
    final = SimulationRunner().run(DroneEnvironment(physics),config.simulation.max_steps,
                                   pace_wall_time=pace,command_provider=provider,
                                   consumers=(recorder,*render_consumers),stop_when=lambda obs: mission.completed)
    if not mission.completed:
        raise ControlChainTimeoutError(f'Control-chain example exceeded {duration:g} s (phase {mission.phase}, waypoint {mission.index})')
    arrivals, samples = tuple(mission.arrivals), tuple(recorder.samples)
    verification = verify_chain(final,arrivals,samples,vehicle)
    return ControlChainResult(final,arrivals,samples,verification)
