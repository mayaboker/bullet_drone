# Joystick-only simulation interface

Status: Completed
Implementation commit: Pending

## Goal

Implement the agreed application/library boundary: drone_lab owns its run loop
and position/velocity control, and bullet_drone advances one step per joystick
command and exposes immutable physics feedback.

## Steps and interfaces

1. Add public JoystickSimulation with reset() -> DroneObservation,
   step(JoystickInput) -> DroneObservation, close(), fixed timestep and read-only
   last command/allocation diagnostics. Compose existing joystick, provider,
   stabilization, mixer, environment and physics internally.
2. Retain injectable stabilization/motor/propeller contracts for passive probes;
   preserve all existing low-level library/example APIs.
3. Verify input rejection without stepping, one-step identity, disarm/reset,
   runtime failure and resource cleanup, and complete both repositories' tests.
4. Update the control-flow/interface guides and public library usage documentation
   to describe implemented ownership and imports.

## Scope/defaults

Coordinate with drone_lab plan 0002. Keep existing units, ground-truth feedback,
fixed 240 Hz application timestep, gains, missions and rendering configuration.
No new physics, sensors, transport or dependencies. No commits or pushes requested.

## Verification

Focused facade/controller/runner tests plus full existing suites; run actual
headless takeoff and position CLI flights with CSV and chain verification. Verify
documentation links and git diff --check in both repositories.

## Outcome

Implemented public bullet_drone.simulation.JoystickSimulation and migrated Drone
Lab under its plan 0002. Preserved existing library APIs and dependencies. Updated
the control-flow/interface guides and library usage documentation.

Verification: 270 bullet_drone tests and 60 drone_lab tests passed. Headless
position CLI/CSV completed all six targets and landing/disarm at 28.9625 s with
6,951 samples; takeoff CLI/CSV completed a 20 s hover and landing/disarm at
33.2292 s with 7,975 samples. The actual wall-time-paced Godot position viewer
verification passed on isolated UDP port 19881; its captured world/FPV image was
inspected. Documentation links and whitespace checks passed in both repositories.
No commit or push requested; implementation commit remains Pending.
