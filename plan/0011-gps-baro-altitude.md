# GPS SITL barometer altitude

## Goal

Keep GPS telemetry available while making Betaflight use the barometer alone for its altitude estimate in GPS SITL profiles.

## Implementation steps

1. Set `altitude_source = BARO_ONLY` in both GPS profiles.
2. Update the README and SITL bridge documentation to describe the altitude source.
3. Verify the profile commands and their placement before `save`.

## Interface changes

The GPS SITL profiles change their Betaflight altitude estimator setting. GPS acquisition and MAVLink GPS telemetry remain enabled. Running SITL processes require restart to load the changed profile.

## Verification

Both GPS profiles contain one `set altitude_source = BARO_ONLY` command before `save`.
The pinned MAVLink GPS firmware accepted its profile in an isolated `--config`
run (exit code 0). The non-MAVLink GPS binary is absent from this checkout, so
its live load was not checked. `git diff --check` passed. The target-hit SITL
stack was then restarted with the edited GPS profile and an automatic mission
was run. Takeoff and hover were normal, but target-hit still failed with
`LOS recovery_timeout`; the reported yaw rose to about 0.39 rad while the
mission commanded yaw. The App pane was returned to manual mode afterward.

## Scope and defaults

Only the GPS profiles change. Non-GPS profiles retain Betaflight defaults. GPS heading correction remains active.

## Status

Implemented; profile load and live target-hit rerun checked (mission still fails).

## Implementation commit

Pending (no commit requested).
