# Configurable internal-controller rate P gains

## Goal
Expose roll/pitch/yaw rate P gains in physics YAML and trial the heavy-quad profile at [0.08, 0.08, 0.05].

## Implementation
- Add optional control.rate_kp, three finite nonnegative numbers in roll/pitch/yaw order, with legacy defaults [0.05, 0.05, 0.05]. Reject booleans.
- Derive effective external-runner internal settings from the existing baseline, replacing only PID kp. Use the same settings during construction, reset, spawn and rollback, and in startup/MCAP configuration snapshots.
- Update the heavy-quad profile and document units, restart behavior and recorded verification. Betaflight retains firmware stabilization; no application MAVLink changes.

## Interfaces and defaults
ControlSettings.rate_kp and optional YAML control.rate_kp. Existing profiles retain behavior on omission. All other gains and limits remain unchanged. No runtime editing or commits requested.

## Verification
Configuration validation/defaults, effective runner settings and snapshots, reset/spawn/rollback preservation, Betaflight isolation and relevant existing suites. Compare baseline and trial simulation response; distinguish controlled response experiments from a complete target-hit scenario recording.

Results: 109 relevant tests passed, covering configuration, internal control,
external-runner settings and snapshot identity, spawn/reset and failed-candidate
preservation, RC simulation, Betaflight isolation and analysis publication.
Source distribution and wheel built successfully into /tmp/rate-p-gains-dist.

A controlled headless heavy-quad 8-degree step comparison recorded baseline and
trial MCAPs at /tmp/rate-p-response/{baseline,trial}.mcap. Both roll and pitch
gave identical results: peak 12.606 degrees at kp=0.05 versus 11.950 degrees at
kp=0.08; settling within 5% of the RC-quantized 8.01-degree target improved from
11.925 s to 7.629 s after the step. Each recording contains 7,204 messages;
packets were schema-validated and MCAP readback passed CRC validation. Metrics
and reproduction script: /tmp/rate-p-response/metrics.json and
/tmp/rate_p_response.py. The experiment used ideal aerodynamic forces and
altitude feedback to isolate attitude response. It does not establish full
approach performance with vision/wind, and no existing recording was changed.
The trial still overshoots; a new complete target-hit scenario remains necessary
to validate the flight tune.

## Status
Implemented; tests, build and controlled response experiment passed. Full approach tune remains unvalidated.

## Implementation commit
`ef298d68646e69d828a97df85dceb7a7a29ef18d`

## Repository snapshot record
Recorded snapshot: `ef298d68646e69d828a97df85dceb7a7a29ef18d` (bullet_drone repository). This is the new local
baseline containing the current implementation, not a recovered historical commit.
