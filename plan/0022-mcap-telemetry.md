# Optional MCAP physics telemetry adapter

Status: Completed
Implementation commit: Pending

## Goal and steps

Integrate sibling mcap_bug as an optional telemetry dependency. Add constants and
schemas for ground truth/sensors, an observation adapter that combines physics
with optional caller samples into one frame, and --mcap PATH to the main CLI.
Start recording before physics acquisition, expose nonfatal runtime recording
health, and finalize through the existing consumer lifecycle. Update usage/design.

## Interfaces and scope/defaults

Ground-truth/sensors are automatic when recording is enabled. The simulation and
joystick APIs do not change. Sensor slots remain unavailable; preserve future
measurement identities. No rendering, controller or physics changes. Local commit
was later requested with the workspace update; no push is requested.
The generic service is implemented under mcap_bug plan 0001; Lab integration is
under drone_lab plan 0005. Update pyproject.toml and uv.lock together.

## Verification

Adapter identity/schema/optional-dependency tests, full existing suite, CLI MCAP
readback, lifecycle/error cases, documentation links and git diff --check.

## Outcome

Added optional telemetry dependency/source and synchronized lock, physics topic
constants/schemas, observation recorder, nonfatal recording diagnostics and
--mcap PATH. Initial observations and default sensors/ground truth are automatic,
with optional application samples submitted in the same frame. Updated design
and usage documents; existing low-level and joystick interfaces remain intact.

Verification: 274 library tests passed; the service suite passed 17 tests and Lab
68 tests. CLI MCAP readback verified timestamps, schemas and explicit whole-frame
headless gaps; no semaphore/worker leaks were observed after cleanup fixes.
Confirmed normal imports without MCAP dependencies and actionable startup error
when the extra is missing, then restored the extra. Built the library wheel.
Paced 240 Hz Lab recordings had zero drops; final full readback verified all 6,952
frames. Final benchmark p99 0.270 ms and deadline-miss increase 0.187 percentage
points passed the agreed targets. Links, syntax, lock and whitespace checks passed.
Local commit is now requested; implementation commit remains Pending until Git
supplies its hash.
