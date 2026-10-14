# Optional MCAP physics telemetry

Status: **Implemented**. See [plan 0022](../../plan/0022-mcap-telemetry.md) for
verification and [design menu](index.md) for component boundaries.

The independent sibling `mcap_bug` package owns the writer process and MCAP files.
Bullet Drone owns the adapter and physics topic definitions. The adapter observes
immutable `DroneObservation` values; it introduces no flight command interface.

## Enable recording

From Bullet Drone:

```bash
uv sync --locked --extra telemetry
uv run --locked --extra telemetry bullet-drone --config configs/headless.yaml --headless --mcap /tmp/physics.mcap
```

MCAP dependencies are optional and loaded only when requested. Include
`--extra telemetry` on uv runs so synchronization retains them. The output's parent
directory must exist and the file must not already exist. Startup failure is a
configuration error before physics acquisition. Existing CLI behavior without
`--mcap` is unchanged.

## Automatic topics and extensions

[`telemetry/topics.py`](../../src/bullet_drone/telemetry/topics.py) defines:

| Constant | Topic | Data |
| --- | --- | --- |
| `GROUND_TRUTH_TOPIC` | `physics/ground_truth` | World position/linear/angular velocity, body-to-world XYZW quaternion and actual rotor speeds. |
| `SENSORS_TOPIC` | `physics/sensors` | IMU, barometer and rangefinder slots, preserving future reading identities/timestamps. |

The service wraps these payloads with required run/episode/step identity and
`timestamp_ns`, an integer count of episode-local simulation nanoseconds. Units
and frames are described in payload schemas. Sensors currently contain `null`:
recording does not implement sensor models or fabricate measurements.

[`McapObservationRecorder`](../../src/bullet_drone/telemetry/mcap.py) registers
both topics, provides `start/reset/consume/close`, and records step zero as well as
every successfully completed observation. Its `record_observation(observation,
extras=())` method combines default physics samples and application samples into
one frame. Applications register their extra topic handles through the same
recorder before startup. The caller runner owns when observations are submitted.

```python
from bullet_drone.telemetry.mcap import McapObservationRecorder, create_mcap_recorder

EXTRA_TOPIC = "application/error"
recorder = create_mcap_recorder("flight.mcap")
physics = McapObservationRecorder(recorder)
extra = recorder.register_topic(EXTRA_TOPIC, {"type": "number"}, source_feedback=True)
# Start under an if __name__ == "__main__" guard before running the simulation.
physics.start()
# Later: physics.reset(initial_observation)
# physics.record_observation(result, (
#     extra.sample(error, source_step_index=feedback.ground_truth.step_index,
#                  source_timestamp_ns=round(feedback.ground_truth.simulation_time_s * 1e9)),
# ))
# In cleanup: physics.close()
```

## Synchronization and performance policy

Data comes from one completed step per frame. Lab control data can additionally
reference the preceding feedback step/time. MCAP timestamps use simulation time
with recorded offsets across resets, while payload timestamps remain local to
each episode. The service embeds the full JSON schemas in the file.

The adapter snapshots and nonblockingly submits data; a spawned worker validates,
encodes and writes it. Overflow drops a whole frame and records the gap. Runtime
writer failure disables recording and reports the error while physics continues.
The adapter warns on incomplete close, and statistics remain available through
`statistics`. Existing mandatory CSV failure behavior is independent of this
best-effort MCAP policy.

Unpaced headless flights can outrun the writer and contain reported gaps. To
verify the 240 Hz target, Drone Lab provides a paced DIRECT-physics benchmark.
The initial two-pair benchmark recorded every frame, with capture/submission p99
0.288–0.298 ms and missed-deadline increase about 0.108 percentage points.
These are measured scheduling results, not a hard real-time guarantee.

The final one-pair rerun on the completed code also passed: p99 0.270 ms,
missed-deadline increase 0.187 percentage points, and all 6,952 frames written.

See the [generic service API](../../../mcap_bug/README.md) and
[Lab integration](../../../drone_lab/docs/mcap-telemetry.md).
