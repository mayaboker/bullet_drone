# Simulation control and state publication

Status: Pending. Implementation commit: Pending.

## Goal
Let Bullet View start, stop, and reset the launcher simulation over loopback ZeroMQ, including a fresh Betaflight SITL process on reset, while displaying authoritative current state.

## Implementation
- Add a command REP service to the launcher at configurable TCP 5561 using the shared command request/reply contract.
- Keep startup running. Stop requires reset before start; reset is stopped-only and reinitializes physics, sensors, SITL, FDM, renderer contact and image episode.
- Publish state on `simulation/drone_1/state` at transitions and 2 Hz through the renderer telemetry publisher.
- Feed FDM while stopped using held physics observations so Betaflight remains responsive.
- Handle failures without losing the control service; report timeout as unknown without retry.

## Interface
State JSON contains `schema_version`, `drone_id`, `session_id`, `episode_id`, `state`, and `revision`. States: `running`, `stopped_reset_required`, `resetting`, `stopped_ready`, `error`.

## Verification
Focused launcher/control/render tests: 28 passed. A headless launcher completed Stop → rejected Start → Reset → Start → Stop over real ZeroMQ. The full repository suite had 659 passes, 8 skips and 5 failures in unrelated existing workspace-profile and position-square example tests. A live SITL reset was not run because the active mission stack owned ports 5761/5762 and UDP 9002–9004. Design and README were updated.

## Defaults
Launcher starts running. Control endpoint is `tcp://127.0.0.1:5561`; TCP 5560 remains Bullet Visual's bounding-box publisher. Reset remains stopped. Bullet App restart is manual.
