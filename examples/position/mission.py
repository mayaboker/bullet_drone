"""Position waypoint mission; control law and physics are separate components."""
from dataclasses import dataclass
from enum import StrEnum
from math import dist, hypot

from loguru import logger
from bullet_drone.commands import HighLevelCommand, InvalidCommandError, RcInput, _finite, _values
from bullet_drone.contracts import RcInterface, LifecycleError
from bullet_drone.controllers.position import PositionController
from bullet_drone.controllers.geometry import yaw_from_quaternion
from bullet_drone.models import DroneObservation, Vector3

# Matches the visual course in renderers/godot/flight_world.gd: 7 + index * 7.
GATE_X_M = (7.0, 14.0, 21.0)


class PositionPhase(StrEnum):
    SETTLE = 'settle'
    TAKEOFF = 'takeoff'
    OUTBOUND = 'outbound'
    RETURN = 'return'
    LAND = 'land'
    DISARMED = 'disarmed'
    COMPLETE = 'complete'


@dataclass(frozen=True, slots=True)
class PositionTransition:
    phase: PositionPhase
    waypoint_index: int
    simulation_time_s: float
    position_m: Vector3


class PositionMission:
    """Visit gate waypoints and return to reset-time home before landing.

    World +X route, fixed yaw zero, 3 m altitude and independent home Y lanes.
    Arrival requires 12 cm XYZ error and <=.15 m/s for .5 continuous seconds.
    Touchdown additionally requires own-pad XY <=12 cm and <=.05 m/s.
    """
    def __init__(self, controller: PositionController, rc: RcInterface):
        self.controller, self.rc = controller, rc
        self._closed = False
        self._episode = None
        self._next_step = 0
        self.phase = PositionPhase.SETTLE
        self.home: Vector3 = (0,0,0)
        self.waypoints: tuple[Vector3, ...] = ()
        self.index = 0
        self._since = 0.0
        self._last_time = 0.0
        self._dwell_since = None
        self._transitions = []

    @property
    def completed(self) -> bool:
        return self.phase == PositionPhase.COMPLETE

    @property
    def transitions(self) -> tuple[PositionTransition, ...]:
        return tuple(self._transitions)

    def reset(self, observation: DroneObservation) -> None:
        if self._closed:
            raise LifecycleError('Cannot reset a closed position mission')
        state = observation.ground_truth
        self.home = _values(state.position_m, 3, 'home_position_m')
        self._since = self._last_time = _finite(state.simulation_time_s, 'simulation_time_s')
        self.controller.reset()
        self.rc.reset(observation)
        x, y, _ = self.home
        self.waypoints = ((x,y,3.), *((gate+1,y,3.) for gate in GATE_X_M),
                          *((gate-1,y,3.) for gate in reversed(GATE_X_M)), (x,y,3.))
        self.index = 0
        self.phase = PositionPhase.SETTLE
        self._dwell_since = None
        self._transitions = [PositionTransition(self.phase, self.index, self._since, self.home)]
        self._episode = state.episode_id
        self._next_step = state.step_index + 1

    def command(self, observation: DroneObservation, dt_s: float) -> HighLevelCommand:
        if self._closed or self._episode is None:
            raise LifecycleError('Position mission must be reset before use')
        state = observation.ground_truth
        if state.episode_id != self._episode or state.step_index + 1 != self._next_step:
            raise InvalidCommandError('Position mission observation belongs to another episode/step')
        dt = _finite(dt_s, 'dt_s')
        t = _finite(state.simulation_time_s, 'simulation_time_s')
        position = _values(state.position_m, 3, 'position_m')
        velocity = _values(state.linear_velocity_m_s, 3, 'linear_velocity_m_s')
        if dt <= 0 or t < self._last_time:
            raise InvalidCommandError('Positive dt and nondecreasing simulation time required')
        self._advance(t, position, velocity)
        if self.phase in (PositionPhase.SETTLE, PositionPhase.DISARMED, PositionPhase.COMPLETE):
            value = RcInput()
        else:
            landing = self.phase == PositionPhase.LAND
            target = (*self.home[:2], 0.) if landing else self.waypoints[self.index]
            value = self.controller.input(target, position, velocity, dt,
                                          measured_yaw_rad=yaw_from_quaternion(state.orientation_xyzw),
                                          descent_speed_limit_m_s=.5 if landing else None)
        self.rc.set_input(value)
        result = self.rc.command(observation, dt)
        self._next_step += 1
        self._last_time = t
        return result

    def _advance(self, t: float, position: Vector3, velocity: Vector3) -> None:
        if self.phase == PositionPhase.SETTLE:
            if t - self._since >= .5:
                self._transition(PositionPhase.TAKEOFF, t, position)
        elif self.phase in (PositionPhase.TAKEOFF, PositionPhase.OUTBOUND, PositionPhase.RETURN):
            arrived = dist(position, self.waypoints[self.index]) <= .12 and hypot(*velocity) <= .15
            if self._dwell(arrived, t, .5):
                if self.index == len(self.waypoints) - 1:
                    self._transition(PositionPhase.LAND, t, position)
                else:
                    self.index += 1
                    self._transition(PositionPhase.OUTBOUND if self.index <= len(GATE_X_M) else PositionPhase.RETURN, t, position)
        elif self.phase == PositionPhase.LAND:
            landed = position[2] <= .02 and dist(position[:2], self.home[:2]) <= .12 and hypot(*velocity) <= .05
            if self._dwell(landed, t, .5):
                self.controller.reset()
                self._transition(PositionPhase.DISARMED, t, position)
        elif self.phase == PositionPhase.DISARMED and t - self._since >= 1:
            self._transition(PositionPhase.COMPLETE, t, position)

    def _dwell(self, condition: bool, t: float, duration: float) -> bool:
        if not condition:
            self._dwell_since = None
            return False
        if self._dwell_since is None:
            self._dwell_since = t
        return t - self._dwell_since >= duration

    def _transition(self, phase: PositionPhase, t: float, position: Vector3) -> None:
        self.phase, self._since, self._dwell_since = phase, t, None
        self._transitions.append(PositionTransition(phase, self.index, t, position))
        logger.info('Position mission: {} waypoint {} at {:.3f} s', phase, self.index, t)

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._episode = None
            self.rc.close()
