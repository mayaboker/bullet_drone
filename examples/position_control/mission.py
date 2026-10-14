"""Setpoint sequence and rc command source; no physics mutation."""
from dataclasses import dataclass
from math import dist, hypot, pi

from loguru import logger
from bullet_drone.commands import HighLevelCommand, InvalidCommandError, RcInput, _finite, _values
from bullet_drone.contracts import RcInterface, LifecycleError
from bullet_drone.controllers.geometry import attitude_error, from_rpy
from bullet_drone.controllers.position import PositionController
from bullet_drone.controllers.geometry import yaw_from_quaternion
from bullet_drone.models import DroneObservation, Quaternion, Vector3


@dataclass(frozen=True, slots=True)
class Waypoint:
    name: str
    position_m: Vector3
    yaw_rad: float


@dataclass(frozen=True, slots=True)
class Arrival:
    target: Waypoint
    simulation_time_s: float
    position_m: Vector3
    orientation_xyzw: Quaternion


class ControlChainMission:
    def __init__(self, controller: PositionController, rc: RcInterface):
        self.controller, self.rc = controller, rc
        self._closed = False
        self._episode = None
        self._next_step = 0
        self.phase = 'settle'
        self.home: Vector3 = (0,0,0)
        self.waypoints: tuple[Waypoint, ...] = ()
        self.index = 0
        self._since = self._last_time = 0.
        self._dwell_since = None
        self.arrivals: list[Arrival] = []
        self.last_feedback: DroneObservation | None = None
        self.last_command: HighLevelCommand | None = None
        self.active_target: Waypoint | None = None

    @property
    def completed(self):
        return self.phase == 'complete'

    def reset(self, observation: DroneObservation):
        if self._closed:
            raise LifecycleError('Cannot reset a closed chain mission')
        state = observation.ground_truth
        self.home = _values(state.position_m, 3, 'home_position_m')
        x, y, _ = self.home
        self.waypoints = (Waypoint('takeoff',(x,y,3),0), Waypoint('x_leg',(x+2,y,3),0),
                          Waypoint('y_leg',(x+2,y+2,3),pi/2), Waypoint('climb_and_return_x',(x,y+2,4),pi),
                          Waypoint('return_home',(x,y,3),-pi/2), Waypoint('align_home',(x,y,3),0))
        self.index = 0
        self.phase = 'settle'
        self._since = self._last_time = _finite(state.simulation_time_s, 'simulation_time_s')
        self._dwell_since = None
        self.arrivals = []
        self.last_feedback = self.last_command = self.active_target = None
        self.controller.reset()
        self.rc.reset(observation)
        self._episode = state.episode_id
        self._next_step = state.step_index + 1

    def command(self, observation: DroneObservation, dt_s: float):
        if self._closed or self._episode is None:
            raise LifecycleError('Chain mission must be reset before use')
        state = observation.ground_truth
        if state.episode_id != self._episode or state.step_index + 1 != self._next_step:
            raise InvalidCommandError('Chain mission observation is stale or from another episode')
        dt = _finite(dt_s, 'dt_s')
        t = _finite(state.simulation_time_s, 'simulation_time_s')
        pos = _values(state.position_m, 3, 'position_m')
        vel = _values(state.linear_velocity_m_s, 3, 'velocity_m_s')
        if dt <= 0 or t < self._last_time:
            raise InvalidCommandError('Positive dt and nondecreasing time required')
        heading = hypot(*attitude_error(state.orientation_xyzw, from_rpy((0,0,self.waypoints[self.index].yaw_rad))))
        if self.phase == 'settle' and t - self._since >= .5:
            self._transition('track', t)
        elif self.phase == 'track':
            arrived = dist(pos, self.waypoints[self.index].position_m) <= .12 and hypot(*vel) <= .15 and heading <= .05
            if self._dwell(arrived, t):
                self.arrivals.append(Arrival(self.waypoints[self.index],t,pos,state.orientation_xyzw))
                if self.index == len(self.waypoints)-1:
                    self._transition('land',t)
                else:
                    self.index += 1
                    self._dwell_since = None
                    logger.info('Control-chain target: {} at {:.3f} s',self.waypoints[self.index].name,t)
        elif self.phase == 'land':
            landed = pos[2] <= .02 and dist(pos[:2],self.home[:2]) <= .12 and hypot(*vel) <= .05
            if self._dwell(landed,t):
                self.controller.reset()
                self._transition('disarmed',t)
        elif self.phase == 'disarmed' and t - self._since >= 1:
            self._transition('complete',t)
        self.active_target = Waypoint('land',(*self.home[:2],0),0) if self.phase == 'land' else self.waypoints[self.index]
        if self.phase in ('track','land'):
            value = self.controller.input(self.active_target.position_m,pos,vel,dt,yaw_rad=self.active_target.yaw_rad,
                                          measured_yaw_rad=yaw_from_quaternion(state.orientation_xyzw),
                                          descent_speed_limit_m_s=.5 if self.phase=='land' else None)
        else:
            value = RcInput()
        self.rc.set_input(value)
        result = self.rc.command(observation,dt)
        self.last_feedback, self.last_command = observation, result
        self._next_step += 1
        self._last_time = t
        return result

    def _dwell(self, condition, t):
        if not condition:
            self._dwell_since = None
            return False
        if self._dwell_since is None:
            self._dwell_since = t
        return t - self._dwell_since >= .5

    def _transition(self, phase, t):
        self.phase, self._since, self._dwell_since = phase,t,None
        logger.info('Control-chain mission: {} at {:.3f} s',phase,t)

    def close(self):
        if not self._closed:
            self._closed = True
            self._episode = None
            self.rc.close()
