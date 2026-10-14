# Zenoh Learning Roadmap: Drone Telemetry, Shared Memory, and MCAP

**Target system:** PyBullet physics + Godot camera + Python detector + ADRC controller + MCAP recorder  
**Transport:** Pure Zenoh (no ROS 2 required)  
**Structured telemetry:** MessagePack  
**Camera:** Raw image payloads, with Zenoh shared memory where practical  
**Target:** 640 × 480 RGB8 at 60 FPS to both detector and recorder

## Overview

Learn Zenoh by building small working experiments before integrating Godot.

| Module | Focus | Deliverable | Difficulty |
|---|---|---|---|
| 1 | Fundamentals | Python publisher/subscriber | Easy |
| 2 | Deployment | Peer mode and client/router operation | Easy |
| 3 | MessagePack and QoS | Multi-topic 240 Hz telemetry and measurements | Medium |
| 4 | Shared memory | One 60 FPS image publisher, two subscribers | Medium–hard |
| 5 | MCAP | Dynamic topic recording and replay | Medium |
| 6 | Godot integration | C++ GDExtension camera publisher | Hard |

## Module 1 — Zenoh fundamentals

**Learn:** sessions, publishers, subscribers, key expressions, and simple message payloads.

Install in a virtual environment:

```bash
mkdir -p zenoh-telemetry-lab && cd zenoh-telemetry-lab
python3 -m venv .venv
source .venv/bin/activate
pip install eclipse-zenoh msgpack
```

Create `publisher.py`:

```python
import time
import msgpack
import zenoh

with zenoh.open(zenoh.Config()) as session:
    pub = session.declare_publisher("drone/physics/state")
    for i in range(1000):
        state = {
            "frame": i,
            "position": [i * 0.01, 0.0, 10.0],
            "velocity": [1.0, 0.0, 0.0],
        }
        pub.put(msgpack.packb(state, use_bin_type=True))
        time.sleep(0.1)
```

Create `subscriber.py`:

```python
import msgpack
import zenoh

with zenoh.open(zenoh.Config()) as session:
    with session.declare_subscriber("drone/physics/**") as sub:
        for sample in sub:
            data = msgpack.unpackb(sample.payload.to_bytes(), raw=False)
            print(sample.key_expr, data)
```

Run subscriber and publisher in separate terminals. Then try two subscribers, launching in different orders, another topic (`drone/imu`), and the wildcard subscription `drone/**`.

**Completion criterion:** Two subscribers receive live messages from multiple topics without manually registering topics at the transport level.

## Module 2 — Zenoh deployment and discovery

**Learn:** peer versus client/router mode, discovery, key-expression routing, and JSON5 configuration.

Compare:

```text
Peer mode:      PyBullet <----> Detector <----> Recorder

Router mode:              zenohd
                      /      |      \
                PyBullet  Detector  Recorder
```

For a router-based setup, start a Zenoh router (`zenohd`) and connect clients using a configuration file such as:

```json5
{
  mode: "client",
  connect: { endpoints: ["tcp/127.0.0.1:7447"] },
  scouting: { multicast: { enabled: false } }
}
```

**Exercises:** Compare peer and router deployments; restart a publisher; test discovery, reconnection, and topic filters; learn which endpoint settings apply on different hosts.

**Completion criterion:** Three independent processes communicate reliably through one router and can recover from a restarted publisher.

## Module 3 — MessagePack, QoS, and performance

**Build these streams:**

| Topic | Frequency | Example payload |
|---|---:|---|
| `drone/physics/state` | 240 Hz | position, orientation, velocity |
| `drone/imu` | 200 Hz | accelerometer, gyroscope |
| `drone/controller/rc` | 100 Hz | roll, pitch, yaw, throttle |
| `drone/vision/detections` | 60 Hz | bounding boxes, confidence |
| `drone/events` | Event driven | collisions, tracking events |

Use MessagePack for structured telemetry. Record message sequence number, simulation timestamp, and (for performance tests) publisher monotonic timestamp.

Measure:
- Publication and reception rates
- Bytes per second
- Latency distribution (p50/p95/p99)
- Inter-arrival jitter
- Sequence gaps and dropped messages
- Queue depth and backpressure

**Exercises:** Add a second subscriber that intentionally runs slowly; compare different reliability and congestion configurations; investigate whether a slow recorder affects a control subscriber. Measure one-way latency only with a common/synchronized clock.

**Completion criterion:** Sustained 240 Hz physics telemetry with observable, bounded queue behavior and explicit missing-message metrics.

## Module 4 — Zenoh shared-memory camera streaming

**Goal:** Publish **640 × 480 RGB8 images at 60 FPS** to *two local subscribers* (detector simulator and recorder simulator).

Start with a NumPy-generated image, not Godot, to isolate the transport cost.

```text
Image Generator (60 FPS)
          |
     Zenoh SHM
       /     \
Detector     Recorder
Subscriber   Subscriber
```

**Key topics:** shared-memory providers and allocation, explicit versus transparent SHM, buffer ownership/lifetime, allocation exhaustion, asynchronous processing, and backpressure.

**Raw data budget:**
- RGB8 frame: 640 × 480 × 3 = **921,600 bytes**
- At 60 FPS: **55.3 MB/s** payload throughput
- A 64 MiB SHM pool fits roughly 72 raw frame payloads before allocator overhead; actual usable count depends on fragmentation and retained references.

**Benchmarks:** publisher cadence, per-subscriber frame count and sequence gaps, throughput, allocation failures, buffer retention time, and delivery latency. Run a sustained multi-minute test.

**Important caveats:** Both local subscribers must support/configure Zenoh SHM. Python bindings/build variants and SHM APIs can be version-dependent; consult the matching version's documentation. Zero-copy IPC does not eliminate GPU uploads, disk writes, or arbitrary application-side copies.

**Completion criterion:** Both subscribers sustain 60 FPS with measured loss/latency under normal load. A 60 FPS delivery rate alone does not demonstrate 60 FPS detector inference.

## Module 5 — Dynamic MCAP recording and playback

**Goal:** Subscribe to `drone/**` and record topics that appear dynamically at runtime.

```text
Zenoh publications -> dynamic topic/schema registry -> MCAP writer -> flight.mcap
                                                           |
                                                     MCAP reader/player
                                                           |
                                                     Zenoh republication
```

Install:

```bash
pip install mcap lz4
```

**Implement:**
1. A single dedicated MCAP writer process, subscribing to `drone/**`.
2. Topic-to-channel mapping created when a new topic appears.
3. MessagePack telemetry stored as original bytes (`message_encoding="msgpack"`).
4. Raw image payloads in dedicated camera channels, with frame metadata, pixel format, dimensions, and simulation timestamps.
5. A separate schema registry or an explicit schema-less convention: **MessagePack itself does not define a schema**.
6. Buffered recording, graceful `finish()`, sequence-gap metrics, and bounded overload behavior.
7. An MCAP reader that republishes selected topics with adjustable playback speed.

**Replay caveats:** Use a consistent simulation clock for timing; simple timed republishing is not deterministic simulator-state replay. Original payload bytes do not automatically restore Zenoh QoS or shared-memory publication semantics.

**Completion criterion:** Record and replay at least 30 seconds of multiple telemetry topics plus 60 FPS images; compare counts and timestamps.

## Module 6 — Godot + native Zenoh integration

**Goal:** Replace the synthetic camera publisher with a **Godot 4 C++ GDExtension** that publishes real camera frames.

```text
PyBullet -> Godot pose update -> Godot camera viewport
                                      |
                               GPU -> CPU readback
                                      |
                           C++ GDExtension / Zenoh
                                      |
                                 Zenoh SHM
                                   /    \
                             Detector   MCAP recorder
```

**Implementation order:**
1. Publish a small message from a Godot GDExtension using `zenoh-cpp`.
2. Publish one camera frame using a normal Zenoh payload.
3. Sustain 60 FPS; instrument Godot render time and readback time.
4. Introduce explicit shared-memory allocation, buffer reuse, and correct lifetime handling.
5. Investigate asynchronous GPU readback; avoid synchronous viewport `get_image()` on the performance-critical render path when it causes stalls.
6. Integrate Python detector and MCAP recorder as independent subscribers.

**Important:** Zenoh shared memory is CPU shared memory, not automatically a shared Vulkan/GPU texture. GPU readback and detector CPU-to-GPU transfer can still dominate latency.

**Completion criterion:** Godot publishes real frames at 60 FPS while both subscribers run independently, with measured end-to-end latency and no unintended render-loop blocking.

## Suggested repository structure

```text
zenoh-telemetry-lab/
├── pyproject.toml
├── config/
│   └── zenoh.json5
├── src/
│   └── telemetry/
│       ├── publisher.py
│       ├── subscriber.py
│       ├── recorder.py
│       └── player.py
├── examples/
│   ├── 01_hello_world/
│   ├── 02_multiple_topics/
│   ├── 03_messagepack_qos/
│   ├── 04_shared_memory/
│   ├── 05_mcap/
│   └── 06_godot/
└── tests/
```

## Design choices for the capstone

| Concern | Choice |
|---|---|
| Messaging | Pure Zenoh |
| Telemetry serialization | MessagePack |
| Topic names | `drone/**` |
| Recording | Single MCAP writer process |
| Structured metadata | Explicit topic/schema convention |
| Camera frames | Raw RGB8, Zenoh SHM on same host |
| Detector policy | Prefer newest frame; small bounded queue |
| Recorder policy | Dedicated bounded queue with drop/backpressure metrics |
| Playback | MCAP reader -> Zenoh publishers |
| ROS2 | Optional integration later; not needed for core project |

## Official references

- [Zenoh: Your First App](https://zenoh.io/docs/getting-started/first-app/)
- [Zenoh Deployment](https://zenoh.io/docs/getting-started/deployment/)
- [Zenoh Configuration](https://zenoh.io/docs/manual/configuration/)
- [Zenoh Python repository](https://github.com/eclipse-zenoh/zenoh-python)
- [Zenoh C++ repository](https://github.com/eclipse-zenoh/zenoh-cpp)
- [Zenoh shared-memory design](https://github.com/eclipse-zenoh/roadmap/blob/main/rfcs/ALL/SHM.md)
- [MCAP Python docs](https://mcap.dev/docs/python/)
- [Godot GDExtension documentation](https://docs.godotengine.org/en/stable/tutorials/scripting/gdextension/index.html)

---

**Capstone acceptance test:** One Godot publisher outputs 640 × 480 RGB8 at 60 FPS via Zenoh shared memory; a detector and an MCAP recorder independently receive the stream; telemetry is stored in MessagePack; the resulting MCAP recording can be inspected and replayed through Zenoh. Track performance and losses explicitly rather than assuming delivery or durability.
