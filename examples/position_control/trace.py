"""Completed-step control-chain telemetry, separate from diagnostic logging."""
import csv
from dataclasses import dataclass
from pathlib import Path

from bullet_drone.commands import HighLevelCommand, MotorAllocation, WrenchCommand
from bullet_drone.contracts import LifecycleError
from bullet_drone.controllers.position import PositionControlOutput
from bullet_drone.models import ControlFeedback, DroneState, PropellerOutput, RotorSpeeds
from examples.position_control.mission import Waypoint


@dataclass(frozen=True, slots=True)
class ChainSample:
    state: DroneState
    feedback_state: DroneState
    target: Waypoint
    command: HighLevelCommand
    position_output: PositionControlOutput | None
    stabilization_feedback: ControlFeedback | None
    stabilization_wrench: WrenchCommand | None
    allocation: MotorAllocation | None
    motor_targets_rad_s: RotorSpeeds
    motor_actual_rad_s: RotorSpeeds
    propellers: PropellerOutput


def csv_row(sample: ChainSample) -> dict:
    s, f, command, output, allocation = (sample.state, sample.feedback_state, sample.command,
                                         sample.position_output, sample.allocation)
    row = dict(episode_id=s.episode_id, step_index=s.step_index, simulation_time_s=s.simulation_time_s,
               feedback_step_index=f.step_index, feedback_time_s=f.simulation_time_s,
               target_name=sample.target.name, target_yaw_rad=sample.target.yaw_rad,
               armed=command.armed, mode=command.mode, thrust_n=command.thrust_n,
               requested_thrust_n=allocation.requested.thrust_n if allocation else None,
               achieved_thrust_n=allocation.achieved.thrust_n if allocation else None,
               saturated=allocation.saturated if allocation else False)
    vectors = {'position_m':s.position_m, 'velocity_m_s':s.linear_velocity_m_s,
               'feedback_position_m':f.position_m, 'feedback_velocity_m_s':f.linear_velocity_m_s,
               'target_position_m':sample.target.position_m, 'rpy_rad':command.rpy,
               'velocity_target_m_s':output.velocity_target_m_s if output else None,
               'acceleration_m_s2':output.acceleration_m_s2 if output else None,
               'body_rates_rad_s':sample.stabilization_feedback.body_rates_rad_s if sample.stabilization_feedback else None,
               'requested_torque_nm':allocation.requested.torque_nm if allocation else None,
               'achieved_torque_nm':allocation.achieved.torque_nm if allocation else None,
               'reaction_torque_nm':sample.propellers.reaction_torque_nm}
    for name, values in vectors.items():
        for index, axis in enumerate('xyz'):
            row[f'{name}_{axis}'] = values[index] if values is not None else None
    for index in range(4):
        row[f'orientation_xyzw_{index}'] = s.orientation_xyzw[index]
        row[f'motor_target_{index}_rad_s'] = sample.motor_targets_rad_s[index]
        row[f'motor_actual_{index}_rad_s'] = sample.motor_actual_rad_s[index]
        for axis, force in zip('xyz',sample.propellers.forces_n[index]):
            row[f'rotor_force_{index}_{axis}_n'] = force
    return row


class ChainRecorder:
    def __init__(self, mission, provider, stabilization, motors, propellers, csv_path: Path | None = None):
        self.mission, self.provider = mission, provider
        self.stabilization, self.motors, self.propellers = stabilization, motors, propellers
        self.csv_path = csv_path
        self.samples: list[ChainSample] = []
        self._file = self._writer = None
        self._closed = False
        self._active = False

    def reset(self, observation):
        if self._closed:
            raise LifecycleError('Cannot reset a closed chain recorder')
        if self._file is not None:
            self._file.close()
        self.samples = []
        self._writer = None
        self._active = True
        if self.csv_path is not None:
            self._file = self.csv_path.open('w',newline='',encoding='utf-8')

    def consume(self, observation):
        if not self._active or self._closed:
            raise LifecycleError('Chain recorder is not active')
        state = observation.ground_truth
        feedback = self.mission.last_feedback
        command = self.mission.last_command
        if feedback is None or command is None or self.propellers.output is None:
            raise RuntimeError('Control-chain trace has missing completed-step data')
        if command.episode_id != state.episode_id or command.step_index != state.step_index or feedback.ground_truth.step_index != state.step_index-1:
            raise RuntimeError('Control-chain trace does not match completed physics step')
        sample = ChainSample(state,feedback.ground_truth,self.mission.active_target,command,
                             self.mission.controller.last_output if command.armed else None,
                             self.stabilization.feedback,self.stabilization.wrench,self.provider.allocation,
                             self.motors.targets,self.motors.actual,self.propellers.output)
        self.samples.append(sample)
        if self._file is not None:
            row = csv_row(sample)
            if self._writer is None:
                self._writer = csv.DictWriter(self._file,fieldnames=list(row))
                self._writer.writeheader()
            self._writer.writerow(row)

    def close(self):
        if not self._closed:
            self._closed = True
            self._active = False
            if self._file is not None:
                self._file.close()
