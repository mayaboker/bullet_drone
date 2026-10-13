# 0004: Altitude takeoff, hover, landing, and disarm demo

Status: Completed

Implementation commit: `ffeef6ed717f0bd02a2d8c20c29b524234a8f77d`

## Goal

Add `examples/hove_demo.py` as a thin entry point for an automated flight through a software joystick interface: settle disarmed, take off to 3 m, hover for 20 seconds after settling, descend, disarm after estimated touchdown, and stop after one second with motors off.

## Implementation steps and interface changes

1. Add immutable JoystickInput (mode, RPY, collective N, armed) and JoystickInterface; SoftwareJoystick accepts inputs and produces episode/step-scoped HighLevelCommand. Reset starts disarmed with zero inputs; no physical device dependency.
2. Add HighLevelCommand.armed with backward-compatible default True and strict boolean validation. Provider validates commands first; disarmed commands bypass stabilization/mixing and return zero motor targets. Arming transitions clear stabilization history.
3. Add reusable AltitudeController using common PID: altitude error → bounded desired vertical velocity → acceleration → collective `mass*(gravity+acceleration)`, clamped to capacity. Feedback is ideal ground truth, RPY stays level with zero yaw.
4. Keep mission sequencing/timing separate from altitude control, joystick translation, stabilization, mixing, and physics.
5. Add optional runner stop_when(observation), evaluated after completed steps; preserve default fixed-step behavior and all cleanup guarantees.
6. Add reusable package demo composition and thin import-safe example entry point. Default paced GUI; --headless selects unpaced headless. Click helper only parses; Loguru sinks configured only at the example entry point. Preserve existing main.py CLI.
7. Update architecture/control documentation, design and plan menus, and verification outcome.

## Mission defaults and scope

Use 1 kg, 240 Hz, initial position (0, 0, 0.015) m, flat ground at world Z=0, target world Z=3 m. Settle disarmed for 0.5 s. Hover starts after height error <=0.05 m and |vertical speed|<=0.1 m/s for 1 continuous second, then lasts 20 simulated seconds. Descend toward altitude zero with speed capped at 0.5 m/s. Estimate touchdown at body Z<=0.02 m and |vertical speed|<=0.05 m/s for 0.5 continuous seconds. Disarm, hold zero commands for 1 s, and stop. Failure to complete within 45 simulated seconds reports runtime failure after cleanup.

Example tuning: altitude P=1.5 s^-1, max vertical speed=1 m/s; velocity PID=(4,1,0), acceleration limit=3 m/s^2, integral contribution limit=1 m/s^2. Internal attitude P=(4,4,4), rate limits=(2,2,2) rad/s, rate PID=(0.05,0,0), torque limits=0.1 N*m.

Altitude-only control with level attitude; defer horizontal position hold, physical joystick, noisy sensors, motor lag, Betaflight and a contact-sensor API. Touchdown is a state-threshold estimate for this flat-ground model. No dependency changes are required. The user subsequently authorized implementation and metadata commits; pushing remains outside scope.

## Verification

Baseline: 140 tests pass. Prototype feasibility: hover starts at 5.18 s, landing at 25.18 s, disarm at 32.23 s; maximum hover error 1.74 cm.

Test joystick translation/reset/invalid input/identity; disarm with nonzero demands and rearming reset; altitude direction/gravity compensation/limits/reset/mass scaling; full headless mission with 20 s hover and motors off; interrupted dwell periods, timeout, stop predicate failure/interruption and cleanup. Run full suite and `uv run examples/hove_demo.py --headless`; document ideal-profile tuning.

Outcome: `uv run pytest -q` passed **184 tests**. `uv run examples/hove_demo.py --headless` completed successfully: hover at 5.179 s, landing at 25.179 s, disarm at 32.225 s, and final observation at 33.229 s with body height about 0.0135 m and zero rotor speeds. The full-flight test verifies altitude within 5 cm (observed maximum error about 1.74 cm), 20 s hovering, and at least 1 s motors off. Timeout, interruption, stop-predicate, joystick, arming, altitude, and entry-point checks pass. Existing 140 tests remain passing. `git diff --check` passed. No dependency changes were made. Plans 0004–0006 were committed together after the user requested it; the recorded hash identifies the implementation commit.


## Follow-up location

[Plan 0005](0005-isolate-hover-examples.md) isolates hover scenario code in `examples/hover`. The current altitude demo entry point is `examples/hover/main.py`, with mission/composition/CLI helpers in that folder. Verification above records the original implementation command. Reusable altitude control and joystick components remain in the simulation library.
