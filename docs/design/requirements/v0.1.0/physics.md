# Physics requirements: 0.1.0

Status: **Draft**  
[Version overview](index.md) · [Architecture](../../architecture.md)

| ID | Requirement | Proposed acceptance evidence |
| --- | --- | --- |
| PHY-001 | Use PyBullet to advance one configured rigid-body quadcopter and its collision world. | A headless run produces state changes and ground contact without loading rendering or plotting adapters. |
| PHY-002 | Advance simulation by one configured fixed duration per successful step. | Step index and simulation time match the number of completed steps; observing and rendering do not advance them. |
| PHY-003 | Calculate thrust and signed reaction torque from four rotor speeds, configured coefficients, positions, and spin directions. | Symmetric input produces the expected total thrust and torque cancellation; asymmetric input produces the expected torque direction. |
| PHY-004 | Make mass, inertia, rotor geometry, speed limits, gravity, and initial state configurable and validate them. | Invalid values are rejected before world creation or state advancement. |
| PHY-005 | Publish pose, world-frame linear/angular velocity, actual rotor speeds, episode identity, step index, and simulation time using the architecture's units and frame conventions. | Known translations and rotations verify component values and quaternion mapping. |
| PHY-006 | Reject invalid, nonfinite, incorrectly sized, out-of-range, or stale rotor commands before stepping. | Observation before and after each rejected command is unchanged. |
| PHY-007 | Reset to declared initial conditions with a new episode identity, step zero, and simulation time zero. | A reset discards previous command effects and returns the configured initial state. |
| PHY-008 | Support repeatable experiments within declared tolerances in the same supported environment. | Runs with the same configuration, seed, and command sequence yield comparable trajectories. Tolerances remain to be agreed. |
| PHY-009 | Demonstrate gravity and hover behavior against analytical expectations. | Free fall before contact and balanced thrust against weight agree within declared tolerances; contact prevents ground penetration within an agreed tolerance. |

The initial proposal uses instantaneous rotor response. Motor lag, aerodynamic drag, wind, and battery behavior are outside this draft baseline. Vehicle parameters, solver settings, step duration, and validation tolerances must be selected before acceptance.
