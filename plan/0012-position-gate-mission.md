# Position-controlled gate course example

Status: Completed
Implementation commit: `d99106e7a15fee202e0c77c72dfaa3fac5996082`

## Goal and defaults

Add a separate position-based example: each drone takes off from its own initial XY pad to 3 m, flies through the current three gates (world X=7,14,21 m), returns through them, aligns above its own pad, lands and disarms. Three-drone tasks use the existing IDs and pads (0,0), (1.5,.25), (3,.5) m. Ground-truth feedback and ideal actuator models remain the default.

## Implementation steps

1. Add a reusable XY position→velocity→acceleration cascade using the common PID; reuse altitude control for vertical force. Convert desired world force into bounded Angle RPY/thrust with explicit yaw and tilt compensation. Keep mission sequencing separate.
2. Create examples/position with its own mission, composition, Click parser and main entry point. Issue all control through the joystick interface and existing stabilization/mixer. Preserve the hover example unchanged.
3. Use settled waypoints beyond each gate, then reversed waypoints back to the home pad. Hold each drone's initial Y; keep yaw zero on both legs (return flight is backward). Wait for position/velocity dwell before advancing; land only after returning to home XY. Finish with motors off and timeout after 180 simulated seconds if incomplete.
4. Add standalone and three-drone Godot position-mission tasks while retaining existing hover tasks. Reject unsuitable launch positions before resource acquisition.
5. Document controller units, course coordinates, mission lifecycle, limits and visual-only geometry.

## Interfaces and scope

Reusable PositionController returns SI JoystickInput with Angle RPY and collective thrust. It does not own mission state, joystick or physics. Existing altitude, physics, runner, command and UDP contracts remain unchanged. PositionMission implements HighLevelController and owns the joystick. Demo returns final observation and immutable transition records.

No obstacle avoidance, planner, sensors, inter-drone collisions, changing gate scenery or physical course objects. Gate centers and clearances match the current decorative course; each drone remains in an independent physics world. Position feedback is world Z-up ground truth. Limit horizontal speed to 1 m/s and tilt to 15 degrees; landing descent to .5 m/s. Takeoff starts near the flat ground, before gate one, within the gate corridor.

## Verification

Controller direction/yaw/tilt/thrust, invalid inputs and PID reset checks. Mission episode/replay/dwell/return-to-home and cleanup/timeout/interrupt tests. Real headless trajectories for all three pads: outward and return crossings inside each gate opening at ~3 m, own-pad touchdown and motors off. CLI help/import/usage and task commands; full Python suite. Visible Godot preview of the new mission if feasible.

## Outcome

Implemented the reusable XYZ-to-Angle/thrust position controller, independent example/mission/CLI, own-pad return/landing and three-drone Godot group task. Existing hover behavior is unchanged.

Verification: 240 Python tests passed. Position tests validate yaw-independent world force direction, tilt/thrust limits, PID reset, validation before updates/resources, joystick lifecycle/replay/new-episode reset, interrupted arrival dwell, home alignment before landing, timeout/failure/KeyboardInterrupt cleanup, CLI import/help and task commands. Real physics trajectories from all three pads cross each gate plane outward and inward with altitude within 0.1 m of 3 m and inside frame clearance; all land on their own pad and stop all motors.

Three actual paced Godot publishers also completed simultaneously: pad 1 at 68.179 s, pad 2 at 65.179 s, pad 3 at 62.183 s. Final XY error below 0.00001 m and Z≈0.01349 m. Captured and inspected the live world/FPV course screenshot at /tmp/bullet-drone-position-course.png. Viewer confirmed all three returned to ground. Whitespace checks passed.

Implementation committed as `d99106e7a15fee202e0c77c72dfaa3fac5996082` at the user’s request. No push requested.
