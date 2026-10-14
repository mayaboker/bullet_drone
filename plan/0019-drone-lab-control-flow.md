# Drone Lab control flow document

Status: Completed
Implementation commit: Pending

## Goal

Document the intended separation: drone_lab owns the runner and separate position
and velocity controllers; bullet_drone accepts flight commands only through its
joystick boundary and returns immutable physics feedback.

## Implementation steps

1. Create docs/design/drone-lab-control-flow.md with an ownership diagram,
   controller cascade, feedback fields/units/frames, and step sequence.
2. Describe the proposed joystick-only simulation boundary, arming, validation,
   reset and cleanup; distinguish existing behavior from future implementation.
3. Link the document from the design menu and verify source references, links,
   command-path consistency and whitespace.

## Interface changes

No executable interfaces change in this milestone. Document a proposed
bullet_drone boundary with reset() -> DroneObservation,
step(JoystickInput) -> DroneObservation, and close(). Rotor commands and force
application remain library internals. The position controller produces desired
world XYZ velocity; the velocity controller produces Angle-mode joystick input.

## Scope and defaults

Documentation only, in the bullet_drone repository. No drone_lab source changes,
dependency changes, commits or pushes. Use in-process calls, SI units, world Z-up
and existing ground-truth feedback; altitude is world Z. Sensor models and
transport are outside this milestone. Runner/controller/facade implementation is
future work.

## Verification

Check documented current APIs against both repositories, validate relative links,
inspect the diagram for ownership and joystick-only command flow, and run
git diff --check. Runtime tests are unnecessary for this documentation change.

## Outcome

Created the control-flow document and linked it from the design menu. Verified
current interfaces and ownership against both repositories, including internal
world-to-body angular-rate feedback conversion. Checked all relative links and
Markdown code fences in the four affected documents, the diagram's controller
cascade and proposed joystick signature, and feedback field references.
git diff --check passed. No executable code changed, so runtime tests were not run.
No commit was requested; the implementation commit remains Pending.
