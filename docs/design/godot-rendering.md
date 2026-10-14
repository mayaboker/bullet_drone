# Independent Godot FPV rendering

Status: **Implemented and verified**

[Design menu](index.md) · [Implementation plan](../../plan/0007-multi-drone-godot-rendering.md)

Physics remains single-drone. Each process publishes one configured stable `drone_id`; the externally launched Godot application displays many publishers in a shared visual world. Python owns the UDP socket and never manages the viewer process. Godot creates visual geometry only, with no gravity, collisions or vehicle dynamics.

## Contracts and units

`ObservationConsumer.reset(observation)`, `consume(observation)`, and idempotent `close()` form the runner boundary. The runner resets consumers after the environment and command provider, delivers every completed step, and closes all consumers, provider and environment on completion, failed initialization, stepping failure or interruption. Cleanup failures cannot replace the original failure; successful runs propagate the first cleanup failure after attempting all cleanup.

`RenderConsumer` resolves observations with `SnapshotBuilder`, schedules updates, and delegates to the small `Renderer.reset(initial_snapshot)`, `render(snapshot)`, `close()` contract. `UdpRenderer` is the concrete transport adapter. Physics and control do not import rendering adapters.

Immutable `RenderSnapshot` contains drone ID, episode ID, completed step index, simulation time in seconds, resolved world position in meters, normalized body-to-world XYZW quaternion and per-field source provenance. `altitude_m` is position Z. Selected position supplies world XY, selected altitude supplies world Z, and selected attitude supplies orientation. Each selector independently accepts `ground_truth` or recognizes `sensor`. This milestone supports ground truth only: any sensor selection raises `UnsupportedRenderSourceError` during configuration before physics/network acquisition. No sensor value substitutes for physics state and no sensor fallback is performed.

The wire uses PyBullet coordinates: right-handed Z-up world, body X forward/Y left/Z up. Godot converts position `(x,y,z)` to `(x,z,-y)` and quaternion `(qx,qy,qz,qw)` to `(qx,qz,-qy,qw)`. Camera mount position is in body meters. Its body forward vector is `(cos(tilt),0,-sin(tilt))`; its up vector is `(sin(tilt),0,cos(tilt))`. Converting these vectors builds the camera basis with local -Z forward. Pose composition applies the drone orientation and body mount once.

## Configuration and execution

The standalone [render profile](../../configs/render-godot.yaml) defaults to drone_1, ground truth for all fields, UDP 127.0.0.1:9870, 60 Hz publication, 640×480 pixels, 75° **vertical** FOV, a (0.15,0,0) m body offset, and 10° downward tilt. Configuration rejects unknown fields, blank IDs, nonfinite values, invalid ports/FOV, nonpositive rates, and invalid dimensions. Snapshot construction rejects zero quaternions and normalizes valid nonzero quaternions.

Start Godot 4.3 or newer, then the simulation in another terminal:

```bash
godot --path renderers/godot
uv run examples/hover/main.py --renderer godot --render-config configs/render-godot.yaml
# Or gravity-only core simulation:
uv run bullet-drone --config configs/basic.yaml --renderer godot
```

A custom receiver port uses `godot --path renderers/godot -- --port=9871` and the matching YAML UDP port. The receiver binds loopback. For multiple simulations, copy the profile and give each publisher a unique drone ID. Their physics worlds are independent; shared rendering does not add inter-drone physical interaction. The VS Code **Run Godot and 3 drones** task launches three hover examples in parallel with unique IDs and staggered world XY positions (0,0), (1.5,0.25), (3,0.5) m. All start at Z=0.015 m, take off to 3 m, hold for 20 s, and land/disarm. Their three FPV panels share the same viewer. The **Run Godot and 6 position drones** task adds three mirrored publishers on negative-Y pads (0,-0.75), (1.5,-1), (3,-1.25) m while retaining the original three starts. Each owns a unique drone ID and FPV panel, and returns to its own pad. Pad markings have radius 0.32 m, leaving separation between the closest pair.

Both CLIs also accept `--renderer pybullet` and `--renderer none`. No renderer option preserves existing GUI/headless defaults. Godot overrides physics GUI mode to DIRECT and enables wall-time pacing. None is fast headless. Explicit `--headless` conflicts with Godot/PyBullet, and `--render-config` requires Godot. Python does not need a graphical display to publish to Godot.

## Wire and scheduling

Each UTF-8 JSON UDP datagram has `version: 1`, UUID `stream_id`, monotonic integer `sequence`, `snapshot` (the snapshot dataclass fields), and `camera` (the camera profile fields). Every packet repeats the camera settings so a late viewer can initialize immediately. Altitude is conveyed through resolved position Z, avoiding a second inconsistent altitude field. The sequence is scoped to the publisher stream and continues across episode resets. Drone/episode/step/time identify the pose for a future image-buffer consumer.

Publication is scheduled by simulation time independently of physics frequency. At 240 Hz physics/60 Hz render, every fourth completed step is sent. Initial and final observations are attempted, with no repeated final packet when already sent. A missed scheduling interval sends the latest observation once, then advances the deadline; no backlog is replayed. The UDP socket is nonblocking. There are no ACKs or heartbeat messages and no claim that a viewer is available. Transport errors emit a diagnostic once and physics continues. Invalid data/configuration remains an explicit error. Missing/closed Godot does not prevent simulation completion.

## Viewer registry and display

Godot drains queued datagrams and applies the newest accepted pose per drone each frame. Schema errors, malformed JSON, nonnormalized quaternions and non-increasing sequences are rejected. A drone ID belongs to its accepted stream while received within the last two seconds, measured on the receiver's clock. A second active publisher with the same drone ID is rejected. After the owner becomes stale, another stream may take over; the old stream is retired and its late packets remain rejected. Stale models and tiles remain visible and are labeled STALE. These rules do not depend on simulation clocks, which may differ between processes.

Each drone owns one model, camera and SubViewport. Viewports share the same World3D so each camera can see other drone models. Models have racer-sized bodies/rotors; +X front rotors are orange and rear rotors blue. The procedural flight world includes an asphalt course with a meter grid, colored numbered gates ahead along +X, six numbered landing pads matching the position-task launch positions, trees, a spectator shelter, a static windsock and distant grassy hills. Sky lighting and warm sunlight add shadows and depth cues; distance/height markers remain for measurement. Scenery construction lives in `flight_world.gd`, separate from receiver, drone and camera orchestration.

These course objects are visual-only: gates, trees, pads, hills and the windsock have no collision bodies and do not modify the flat-ground PyBullet world, sensor readings, or wind inputs. Pad markings remain approximately flush with ground Z=0. The procedural sky uses Godot’s [ProceduralSkyMaterial](https://docs.godotengine.org/en/4.3/classes/class_proceduralskymaterial.html); no external assets or dependencies are required. A full-window world camera follows the center of the displayed drone positions. Right-drag orbits around that center and the mouse wheel zooms; these controls change rendering only. World-view models show their drone IDs. A top-right `Render: N FPS` overlay displays Godot’s global rendered frame rate, refreshed every 0.25 s. This measures viewer rendering throughput, independently of physics frequency and UDP publication rate. The overlay remains visible when publishers stop, anchors on resize, and passes mouse input through to camera controls.

FPV panels appear in a scrollable stack at the top left, sorted by drone ID. Each title is `Camera: fpv / Drone: <drone_id>`, with altitude, step and stale status below. The panel area is at most 400 pixels wide and 40% of the window width, leaving the world view visible. Additional panels scroll vertically. Window resizing scales images while preserving camera aspect ratio; configured camera resolution and vertical FOV remain independent of panel size.

This milestone displays images in Godot only. Python image return, arbitrary scene asset loading, camera sensors, interpolation, telemetry storage and multiple physics drones are later work.

## Verification

```bash
uv run pytest -q
godot --headless --path renderers/godot --script test_registry.gd
uv run renderers/godot/smoke_test.py
```

The visible smoke test uses two real Python UDP publishers, checks independent camera settings/viewports, shared world, spectator camera, top-left panels, titles, resize/zoom behavior and staleness, captures `/tmp/bullet-drone-godot.png`, and closes its test-owned viewer. Production simulation leaves the user-owned viewer open. Registry tests verify known yaw and camera tilt conversion, ordering, duplicate ownership, takeover and retired packets. Python tests cover source rejection, immutable normalized poses, codec, scheduling, mode conflicts and cleanup failures. The hover mission with publication enabled still completes landing/disarm at 33.229 simulated seconds with motors off.
