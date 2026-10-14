"""Validate observed links and physical wrench balance after resources close."""
from dataclasses import dataclass
from math import dist, hypot, isclose

from bullet_drone.rc import RcCodec
from bullet_drone.controllers.geometry import attitude_error, from_rpy


class ControlChainVerificationError(RuntimeError):
    """An observed control-chain link or flight acceptance condition failed."""


@dataclass(frozen=True, slots=True)
class ChainVerification:
    completed_steps: int
    settled_waypoints: int
    max_arrival_error_m: float
    max_heading_error_rad: float


def require(condition: bool, reason: str):
    if not condition:
        raise ControlChainVerificationError(reason)


def verify_chain(final, arrivals, samples, vehicle, rc_codec=None) -> ChainVerification:
    require(len(arrivals)==6, 'Flight did not settle at every requested waypoint')
    require(len(samples)==final.ground_truth.step_index, 'Trace is missing completed physics steps')
    home = arrivals[0].target.position_m[:2]
    require(dist(final.ground_truth.position_m[:2],home)<.12 and final.ground_truth.position_m[2]<=.02,
            'Flight did not land on its original pad')
    require(final.ground_truth.rotor_speeds_rad_s==(0,0,0,0), 'Final motors are not stopped')
    require(samples and not samples[-1].command.armed, 'Final RC command is not disarmed')
    heading_errors = [hypot(*attitude_error(a.orientation_xyzw,from_rpy((0,0,a.target.yaw_rad)))) for a in arrivals]
    errors = [dist(a.position_m,a.target.position_m) for a in arrivals]
    require(max(errors)<=.12 and max(heading_errors)<=.05, 'Waypoint position or heading tolerance failed')
    codec = rc_codec if rc_codec is not None else RcCodec(4*vehicle.max_thrust_per_rotor_n)
    torques = [0.,0.,0.]
    angles = [0.,0.,0.]
    for index, sample in enumerate(samples,1):
        command, allocation, pid = sample.command,sample.allocation,sample.position_output
        require(sample.state.episode_id==sample.feedback_state.episode_id==command.episode_id,
                'Trace episode identity mismatch')
        require(sample.state.step_index==command.step_index==index and sample.feedback_state.step_index==index-1,
                'Command/feedback/physics step identity mismatch')
        require(sample.motor_actual_rad_s==sample.state.rotor_speeds_rad_s==sample.motor_targets_rad_s,
                'Ideal motor target/actual/physics speed mismatch')
        require(all(0<=speed<=vehicle.max_speed_rad_s for speed in sample.motor_actual_rad_s), 'Motor limit violation')
        if not command.armed:
            require(all(speed==0 for speed in sample.motor_actual_rad_s), 'Disarmed motors are running')
            require(pid is None and allocation is None and sample.stabilization_wrench is None,
                    'Disarmed trace contains stale controller output')
            require(all(force==(0,0,0) for force in sample.propellers.forces_n), 'Disarmed propellers produce force')
            continue
        require(pid is not None and allocation is not None and sample.stabilization_wrench is not None,
                'Armed trace has a missing control stage')
        require(codec.decode(pid.rc_input,command.episode_id,command.step_index)==command,
                'RC decoding differs from the recorded controller frame')
        require(allocation.requested==sample.stabilization_wrench and isclose(allocation.requested.thrust_n,command.thrust_n),
                'Stabilization-to-mixer wrench mismatch')
        require(allocation.speeds_rad_s==sample.motor_targets_rad_s, 'Mixer-to-motor target mismatch')
        require(hypot(*pid.velocity_target_m_s[:2])<=1+1e-12, 'Horizontal velocity target exceeds configured bound')
        forces = sample.propellers.forces_n
        require(all(force[0]==0 and force[1]==0 and force[2]>=0 for force in forces), 'Propeller force frame violation')
        require(isclose(sum(force[2] for force in forces),allocation.achieved.thrust_n,abs_tol=1e-8),
                'Actual propeller collective differs from achieved mixer collective')
        # Offset forces generate lever-arm torque; add reaction torque once.
        torque = list(sample.propellers.reaction_torque_nm)
        for position, force in zip(vehicle.rotor_positions_m,forces):
            torque[0] += position[1]*force[2]-position[2]*force[1]
            torque[1] += position[2]*force[0]-position[0]*force[2]
            torque[2] += position[0]*force[1]-position[1]*force[0]
        require(all(isclose(a,b,abs_tol=1e-8) for a,b in zip(torque,allocation.achieved.torque_nm)),
                'Actual propeller torque differs from achieved mixer torque')
        for axis in range(3):
            torques[axis] = max(torques[axis],abs(allocation.requested.torque_nm[axis]))
            angles[axis] = max(angles[axis],abs(command.yaw_rate_rad_s or 0) if axis == 2 else abs(command.rpy[axis]))
    require(all(angle>.01 for angle in angles) and all(torque>1e-6 for torque in torques),
            'Flight did not exercise roll, pitch and yaw stabilization')
    for axis in range(2):
        values = [sample.state.linear_velocity_m_s[axis] for sample in samples]
        require(min(values)<-.1 and max(values)>.1, 'Flight did not exercise opposite horizontal motion')
    return ChainVerification(len(samples),len(arrivals),max(errors),max(heading_errors))
