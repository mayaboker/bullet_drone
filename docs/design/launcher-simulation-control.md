# Launcher simulation control

The persistent launcher binds a loopback ZeroMQ REP socket at `tcp://127.0.0.1:5561` by default. Clients send one JSON frame using the shared `CommandRequest` contract:

```json
{"topic":"command","drone_id":"drone_1","payload":{"action":"stop"}}
```

Actions are `start`, `stop`, and `reset`. Replies are `{"success":true}` or `{"success":false,"reason":"..."}`. A request is handled at a launcher loop boundary; queue age above one second is rejected. The client must not retry automatically after a timeout because the operation may already have run.

The launcher starts in `running`. Stop changes to `stopped_reset_required`; the vehicle remains fixed while simulation time, sensor sampling, and SITL FDM input continue. Start requires `stopped_ready`. Reset is accepted only while stopped, changes to `resetting`, restarts physics and sensors, and, in SITL mode, closes and restarts the owned Betaflight process and FDM bridge. It waits for MSP and MAVLink TCP listeners and a fresh renderer image before returning success, then enters `stopped_ready`. Failure enters `error`; Reset may be retried. Reset clears the previous target-contact event. In `--no-sitl` mode it resets physics without firmware.

With rendering enabled, the launcher publishes `simulation/drone_1/state` on the renderer telemetry PUB endpoint (`tcp://127.0.0.1:5555` by default). The two-frame message contains the topic and JSON payload:

```json
{"schema_version":1,"drone_id":"drone_1","session_id":"0123456789abcdef0123456789abcdef","episode_id":"...","state":"running","revision":0}
```

States are `running`, `stopped_reset_required`, `resetting`, `stopped_ready`, and `error`. `session_id` changes on launcher restart, `episode_id` changes on physics reset, and `revision` increments on every state transition. Publication happens immediately after transitions and at 2 Hz for late subscribers. When rendering is disabled there is no telemetry PUB or state topic, but the command REP service still works.

Resetting SITL closes Bullet App's MSP and MAVLink connections. Bullet App does not support reconnecting or resetting its mission via MAVLink, so restart Bullet App before another flight. The Simulation tab's Start action only advances physics; it does not arm or start a mission.
