"""Timed takeoff/hover/landing mission, issuing commands through a joystick."""

from dataclasses import dataclass
from enum import StrEnum

from loguru import logger

from bullet_drone.commands import HighLevelCommand, InvalidCommandError, JoystickInput, _finite
from bullet_drone.config import _number
from bullet_drone.contracts import JoystickInterface, LifecycleError
from bullet_drone.controllers.altitude import AltitudeController
from bullet_drone.models import DroneObservation


class MissionPhase(StrEnum):
    SETTLE = "settle"
    TAKEOFF = "takeoff"
    HOVER = "hover"
    LAND = "land"
    DISARMED = "disarmed"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class HoverMissionSettings:
    target_altitude_m: float = 3.0
    settle_duration_s: float = 0.5
    hover_duration_s: float = 20.0
    altitude_tolerance_m: float = 0.05
    hover_speed_tolerance_m_s: float = 0.1
    hover_settle_duration_s: float = 1.0
    descent_speed_limit_m_s: float = 0.5
    touchdown_height_m: float = 0.02
    touchdown_speed_tolerance_m_s: float = 0.05
    touchdown_duration_s: float = 0.5
    disarmed_duration_s: float = 1.0

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, _number(getattr(self, name), f"mission.{name}", positive=True))


@dataclass(frozen=True, slots=True)
class MissionTransition:
    phase: MissionPhase
    simulation_time_s: float


class HoverMissionController:
    """High-level source; ideal height/vertical-speed feedback, level attitude.

    All timers use simulation time. Touchdown is a threshold estimate for the
    current flat ground and racer body, not a contact sensor or general terrain.
    """

    def __init__(self, altitude: AltitudeController, joystick: JoystickInterface,
                 settings: HoverMissionSettings = HoverMissionSettings()) -> None:
        self._altitude = altitude
        self._joystick = joystick
        self.settings = settings
        self._closed = False
        self._episode_id: str | None = None
        self._next_step = 0
        self._phase = MissionPhase.SETTLE
        self._phase_since_s = 0.0
        self._last_time_s = 0.0
        self._dwell_since_s: float | None = None
        self._transitions: list[MissionTransition] = []

    @property
    def phase(self) -> MissionPhase:
        return self._phase

    @property
    def completed(self) -> bool:
        return self._phase == MissionPhase.COMPLETE

    @property
    def transitions(self) -> tuple[MissionTransition, ...]:
        return tuple(self._transitions)

    def reset(self, observation: DroneObservation) -> None:
        if self._closed:
            raise LifecycleError("Cannot reset a closed hover mission")
        self._episode_id = None
        self._altitude.reset()
        self._joystick.reset(observation)
        state = observation.ground_truth
        self._phase = MissionPhase.SETTLE
        self._phase_since_s = _finite(state.simulation_time_s, "simulation_time_s")
        self._last_time_s = self._phase_since_s
        self._dwell_since_s = None
        self._transitions = [MissionTransition(self._phase, self._phase_since_s)]
        self._episode_id = state.episode_id
        self._next_step = state.step_index + 1

    def command(self, observation: DroneObservation, dt_s: float) -> HighLevelCommand:
        if self._closed or self._episode_id is None:
            raise LifecycleError("Hover mission must be reset before use")
        state = observation.ground_truth
        if state.episode_id != self._episode_id or state.step_index + 1 != self._next_step:
            raise InvalidCommandError("Mission observation is stale or belongs to another episode/step")
        dt_s = _finite(dt_s, "dt_s")
        t = _finite(state.simulation_time_s, "simulation_time_s")
        z = _finite(state.position_m[2], "altitude_m")
        vz = _finite(state.linear_velocity_m_s[2], "vertical_velocity_m_s")
        if dt_s <= 0 or t < self._last_time_s:
            raise InvalidCommandError("Mission requires positive dt_s and nondecreasing simulation time")
        self._advance(t, z, vz)
        armed = self._phase in (MissionPhase.TAKEOFF, MissionPhase.HOVER, MissionPhase.LAND)
        thrust = 0.0
        if armed:
            landing = self._phase == MissionPhase.LAND
            thrust = self._altitude.thrust(
                0.0 if landing else self.settings.target_altitude_m, z, vz, dt_s,
                self.settings.descent_speed_limit_m_s if landing else None,
            )
        self._joystick.set_input(JoystickInput("angle", (0.0, 0.0, 0.0), thrust, armed))
        result = self._joystick.command(observation, dt_s)
        self._next_step += 1
        self._last_time_s = t
        return result

    def _advance(self, t: float, z: float, vz: float) -> None:
        s = self.settings
        elapsed = t - self._phase_since_s
        match self._phase:
            case MissionPhase.SETTLE:
                if elapsed >= s.settle_duration_s:
                    self._transition(MissionPhase.TAKEOFF, t)
            case MissionPhase.TAKEOFF:
                settled = abs(z - s.target_altitude_m) <= s.altitude_tolerance_m and abs(vz) <= s.hover_speed_tolerance_m_s
                if self._dwell(settled, t, s.hover_settle_duration_s):
                    self._transition(MissionPhase.HOVER, t)
            case MissionPhase.HOVER:
                if elapsed >= s.hover_duration_s:
                    self._transition(MissionPhase.LAND, t)
            case MissionPhase.LAND:
                landed = z <= s.touchdown_height_m and abs(vz) <= s.touchdown_speed_tolerance_m_s
                if self._dwell(landed, t, s.touchdown_duration_s):
                    self._transition(MissionPhase.DISARMED, t)
            case MissionPhase.DISARMED:
                if elapsed >= s.disarmed_duration_s:
                    self._transition(MissionPhase.COMPLETE, t)

    def _dwell(self, condition: bool, t: float, duration_s: float) -> bool:
        if not condition:
            self._dwell_since_s = None
            return False
        if self._dwell_since_s is None:
            self._dwell_since_s = t
        return t - self._dwell_since_s >= duration_s

    def _transition(self, phase: MissionPhase, t: float) -> None:
        self._phase = phase
        self._phase_since_s = t
        self._dwell_since_s = None
        self._transitions.append(MissionTransition(phase, t))
        if phase == MissionPhase.DISARMED:
            self._altitude.reset()
        logger.info("Hover mission: {} at {:.3f} s", phase, t)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._episode_id = None
        self._joystick.close()
