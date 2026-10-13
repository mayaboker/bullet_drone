# Position PID and virtual-joystick control-chain example

Status: Completed
Implementation commit: Pending

## Goal and defaults

Create a new example in examples/position_control that explicitly exercises and verifies position PID → desired velocity → velocity PID → Angle RPY/collective thrust → virtual joystick → attitude/rate stabilization → mixer → motor dynamics → propeller forces → PyBullet. Preserve the gate-course and hover examples.

## Implementation steps and interfaces

1. Expose immutable last-update outputs on altitude/position controllers (velocity target, acceleration and joystick input), clearing them on reset. Keep existing input()/thrust() signatures and numerical behavior unchanged.
2. Add a new example mission: takeoff to 3 m, move on X and Y around a 2 m square, climb to 4 m, vary yaw through 0/90/180/-90 degrees, return to starting XY/3 m/zero yaw, land and disarm. Require settled position, velocity and heading before advancing.
3. Compose through existing project contracts, with read-only probes around stabilization, ideal motor dynamics and propeller model. Record immutable per-step samples linking feedback, PID output, joystick commands, requested/allocated wrench, target/actual rotor speeds and propeller outputs to completed physics-step identity.
4. Add optional CSV trace recording through an observation consumer, separate from diagnostics. Provide independent CLI/main and VS Code standalone/headless/Godot task launchers.
5. Validate the complete flight and each link's data/units/identity, opposite XY motion, altitude/yaw, return/landing/disarm, invalid inputs, resets, cleanup/timeout/interruption, and import-safe CLI behavior. Update design/plan menus.

## Scope and defaults

240 Hz ideal physics, ground-truth feedback, existing shared PID/stabilization gains, horizontal speed 1 m/s, tilt 15°, landing descent .5 m/s; timeout 120 s. Use the existing SoftwareJoystick as virtual joystick. No direct pose/velocity mutation, new physics, sensors, external dependencies or gate-mission changes. CSV is optional; samples are returned for reproducible verification.

## Verification

Focused controller-output and chain tests plus full Python suite; headless CLI run with CSV and inspection of row/step identity. Optional Godot run uses existing render contracts. No commit or push requested.

## Outcome

Implemented the independent examples/position_control mission, CLI/composition, passive stage probes, immutable sample recorder, optional CSV and automatic chain verification. Added immutable last-output records to altitude/position controllers without changing existing return values. Added standalone GUI, headless, Godot publisher and grouped Godot launch tasks.

Verification: 259 Python tests passed. New tests cover all six settled XYZ/yaw goals, bidirectional XY movement, all stabilization torque axes, controller-output immutability/reset/invalid-input preservation, per-step identities, joystick-to-PID preservation, stabilization/mixer/actuator/propeller links, CSV completeness, corrupted-link detection, heading dwell/replay/new episodes, timeout/control/CSV failure and KeyboardInterrupt cleanup, import-safe CLI and forwarding. Existing six gate/hover/physics tests remain passing.

Default headless CLI with CSV completed at 28.9625 simulated seconds, produced 6,951 data rows, settled at all six waypoints, returned within approximately 0.000128 m XY error and landed at Z≈0.01349 m with all motors off. Task commands, labels and dependency references validated. Actual paced Godot run also completed with automatic chain checks; inspected /tmp/bullet-drone-control-chain.png showing world and attached camera views during heading change. Whitespace checks passed.

Implementation commit remains Pending; no commit or push requested.
