# 0002: Mixer and ideal rotor hover

Status: **Completed**  
Implementation commit: `bd284097d1d9e9ffc90f05f8c701b35561ba075e` (`Add motor mixer and ideal rotor hover simulation`)  
Record: **Saved retrospectively from the agreed implementation plan**

[Plan menu](README.md) · [Rotor-force design and roadmap](../docs/design/rotor-forces-and-hover.md)

## Goal

Demonstrate open-loop hover with a bounded motor mixer and ideal rotor thrust/reaction torque while preserving gravity-only mode and the observation API.

## Implementation steps

1. Add the agent rule that each physical effect has its own named method or focused module, independently verified, and save a roadmap covering the course's full force inventory.
2. Read racer geometry, spin signs, coefficients, and nominal capacity into shared `VehicleParameters`. Convert RPM-squared coefficients to rad/s-squared once.
3. Add `WrenchCommand`, `MotorAllocation`, and episode-scoped `RotorCommand` records.
4. Implement allocation of total thrust and body torque. Clamp collective to capacity, uniformly scale torque corrections to preserve feasible collective, and report achieved output and saturation.
5. Calculate thrust and reaction yaw torque independently. Apply thrust at rotor positions and let PyBullet generate roll/pitch lever-arm torque; apply reaction torque separately.
6. Extend environment/backend stepping to accept rotor commands. Validate commands before force application; publish actual speeds and stop motors on reset or `None` commands.
7. Inject a hover command provider through `main.py`; add optional `flight.mode`, GUI/headless hover examples, and a VS Code hover task.
8. Update designs, requirements, glossary, and usage documentation; verify physical response, constraints, and failure paths.

## Interfaces and defaults

- Mixer input is requested thrust in N and body torque in N·m, not net force after gravity/drag. Output includes ordered speeds in rad/s, achieved wrench, and saturation.
- Rotor order is prop0–prop3, with reaction yaw signs `(+1, -1, +1, -1)` and URDF rotor lever arms. Hardware capacity is independent of YAML mass.
- `flight.mode` defaults to `gravity`; `hover` requires downward vertical gravity and requests `T = mg` with zero torque from level rest.
- Motors respond instantaneously. KV, battery behavior, motor lag, feedback control, sensor models, drag, and advanced aerodynamics remain outside this milestone.

## Verification outcome

82 tests passed. Checks covered five-second hover within 1 mm at every step, equal thrust/torque cancellation, quantitative roll/pitch/yaw response, body-frame force rotation, saturation and achieved output, mass-dependent demand, stale/invalid commands, and failure cleanup. Real GUI/headless runs maintained position `(0, 0, 1)` for 1,200 steps. Package builds and an installed-wheel hover check passed.
