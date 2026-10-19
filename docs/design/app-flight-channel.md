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
the RC expiry lease. No collision/landing/physical target body is included.
