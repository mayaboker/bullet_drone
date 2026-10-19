# App flight channel

`examples.external_rc.main` owns a separate caller-paced 240 Hz `RcSimulation`
loop. Existing square missions are unchanged. It uses `SimulationControl` for
Godot lifecycle, `FlightReceiver`/`FlightLease` for local app intent and
`RenderPublisher` for 120 Hz feedback plus camera-paced poses. Runtime physics
code has no networking imports. This example is headless; Godot owns rendering.

Godot Start requires a fresh inactive/disarmed readiness packet for the current
physics/episode identity. Start resets physics, creates a fresh episode and
leases it to that app identity. Physics waits frozen up to 0.5 wall seconds for
the first active packet for the new episode. Disarmed active packets step physics
for sensor warmup. Thereafter the latest accepted full 18-channel RC frame drives
each step. The app owns ARM/Angle selection. Sequence must increase, issue time
cannot be future and validity is at most 100 ms. Wrong topics, ids, invalid,
expired and reordered packets are rejected. A lease cannot change owner while
running. Active=false withdraws the episode; expiry is checked before each step.
Stop freezes the pose; it does not land or run a hidden position controller.

`flight/drone_1/config` advertises mass, gravity, thrust authority, RC scales and
mapping, rates, camera calibration and `attitude_model=ideal`. Feedback includes
barometer altitude and ideal body-to-world XYZW attitude, applied arm/mode/RC
sequence, owner and lifecycle reason. It intentionally excludes XY control
feedback. Attitude is not an estimator reconstructed from raw IMU.

Each reset/step stamps one source containing physics/episode/stream ids, step,
simulation time and Linux monotonic measurement microseconds. That source is
reused by feedback and pose v3; the renderer emits descriptor v2 with the same
source and capture_ns=measurement_us*1000. Integer microseconds remain exactly
representable through Godot JSON; the SHM binary header remains v1. Legacy
examples still publish pose v2 and descriptor v1 with arrival-time capture.

Telemetry ports default to 5555 (physics feedback/config/pose), 5556 (images),
5557 (Godot lifecycle), 5558 (app status/bbox), 5559 (app RC). App control runs
100 Hz; sensor feedback 120 Hz. Packet freshness uses wall monotonic time;
mission durations use simulation time. A slow UI never advances physics beyond
the RC expiry lease. Godot detects truck contact and physics confirms terminal
completion as described below; no landing or physical target body is included.

## Renderer collision termination

`ScenarioTermination` retains a bounded one-second source history. The lifecycle
SUB accepts exact `render/drone_1/collision` reports from the live controller,
matching the current episode/stream and a known source stamp. A valid proposal
is processed before stepping/RC expiry, ends the lease and freezes physics. The
first accepted end wins; stopped episodes cannot be reclassified by late reports.

The external runner emits state v2 with `terminal_result`, plus repeated
`scenario/ended` on telemetry port 5555 every 100 ms. Other examples retain state
v1. The result identifies success/target_hit, the original source/contact position
and the actual final frozen source; physics is not rewound. Reset/Start clears
history and result. Godot retries proposals on 5557 every 100 ms with a stable,
episode-specific event ID; after one second without confirmation it requests
ordinary Stop and shows failure rather than success.

The app latches COMPLETED and stops LOS/active RC; late subscribers recover the
result from repeated events/state or the target_hit stopped feedback. The
recorder queues the terminal event before closing and drains final diagnostics
for 250 ms. Geometry and impact response stay outside the physics library.
