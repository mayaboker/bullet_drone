# Implementation plans

| Plan | Description | Status | Implementation commit |
| --- | --- | --- | --- |
| [0003: control diagram SVG](0003-control-diagram-svg.md) | Replace obsolete PNG with current RC/internal-control diagram. | Implemented and verified; uncommitted | Pending |
| [0004: named constants guidance](0004-named-constants-guidance.md) | Require descriptive constants grouped after module imports. | Implemented and verified; uncommitted | Pending |
| [0005: altitude hold constants](0005-altitude-hold-constants.md) | Replace example magic numbers with named module constants. | Implemented and verified; uncommitted | Pending |
| [0006: position square](0006-position-square.md) | Separate XY position/velocity PIDs and fly a settled 3 m square through RC angle mode. | Implemented and verified; uncommitted | Pending |
| [0007: retire shared CLI/runner](0007-retire-cli-runner.md) | Remove shared execution entry point and dedicated tests; retain library verification and example loops. | Implemented and verified; uncommitted | Pending |
| [0008: Acro position square](0008-position-square-acro.md) | Fly the same square using upstream angle-to-rate conversion and Acro RC input. | Implemented and verified; uncommitted | Pending |
| [0009: force implementation chain](0009-force-chain-mapping.md) | Map course effects to implementation stages with a numbered table and SVG tips. | Complete; committed | `ac453654b7378854b8e449280df88016a2ab556b` |
| [0010: drone ID telemetry](0010-drone-id-telemetry.md) | Propagate configured drone identity into observations and MCAP schemas/payloads. | Complete; committed | `65830c3a85a7928ddcabf28cb6615be2e28fa187` |
| [0011: IMU and barometer](0011-imu-barometer-sensors.md) | Configurable sensor classes, typed observations and MCAP payloads. | Complete; committed | `84449a54c030f9393b41b8048bf31e9cd8caa381` |
| [0012: YAML configuration comments](0012-yaml-configuration-comments.md) | Require explanatory comments for every YAML configuration field. | Complete; committed | `5d9375636df529290aaecc92f450062fcc18b044` |
| [0013: basic YAML comments](0013-basic-yaml-comments.md) | Explain every existing basic configuration field with adjacent comments. | Complete; committed | `5d9375636df529290aaecc92f450062fcc18b044` |
| [0014: shared frame math](0014-shared-frame-math.md) | Give quaternion/frame math neutral ownership and preserve controller error behavior. | Complete; committed | `3f92fe2fbcde954e2ece0eee279424380325ae86` |
| [0015: real-time factor](0015-realtime-factor-logging.md) | Log simulated seconds per wall-clock second in all three examples. | Complete; committed | `eb83baa1dd7bc05b6d49a34b528815adcdb1f9c7` |
| [0016: configurable aerodynamics](0016-configurable-aerodynamics.md) | Add independent aerodynamic models, default-enabled YAML controls and repeatable wind. | Complete; committed | `7619e7dea916908c387b36ef22f404dafa600406` |
| [0017: telemetry recorder TODO](0017-telemetry-recorder-todo.md) | Document the future centralized simulation telemetry recorder milestone. | Complete; committed | `0e629400438b6f1d2fcbb4e37b40853ed3108aa7` |
| [0018: simulation telemetry schemas](0018-simulation-telemetry-schemas.md) | Replace MCAP with per-topic schemas, a common header and YAML topic selection. | Complete; committed | `0e629400438b6f1d2fcbb4e37b40853ed3108aa7` |
| [0019: PlotJuggler sender](0019-plotjuggler-sender.md) | Stream ground truth through a sender process with YAML, UDP layout and VS Code tasks. | Complete; committed | `dd15909896b0bb9a3a0590a6025700a9ec938f7d` |
| [0020: PlotJuggler profile](0020-plotjuggler-profile.md) | Save UDP timestamp preferences and use an isolated profile from the viewer task. | Complete; committed | `dd15909896b0bb9a3a0590a6025700a9ec938f7d` |
| [0021: Godot Zenoh rendering](0021-godot-zenoh-render.md) | Optional physics-driven camera poses, Godot bridge and SHM recording. | Complete; committed | `715c9fe249ad01795df73e72c0cd3544cfb07a7c` |
| [0022: Godot ZeroMQ rendering](0022-godot-zmq-render.md) | Local IPC transport experiment and NVIDIA performance comparison. | Complete; committed | `f9f4cc95c1b38a06b3d5d0c90d1f8b2755abfa1a` |
| [0023: ZMQ TCP and SHM](0023-zmq-tcp-shm.md) | Shared contracts, local TCP signaling, SHM images and live viewer. | Complete; committed | `2ec58b5318df28a2de180e0574358b4ae39cf2fd` |
| [0024: Godot simulation controls](0024-godot-simulation-controls.md) | PUB/SUB Start/Stop/Reset, stopped startup and authoritative UI state. | Complete; committed | `2ec58b5318df28a2de180e0574358b4ae39cf2fd` |
| [0025: PlotJuggler altitude window](0025-plotjuggler-altitude-window.md) | Save 0–5 m altitude bounds and a 360-second opening window/buffer; document live auto-fit. | Complete; committed | `20652a1a2f3bfbdc321f3d29340e8ed1612e7bd9` |
| [0026: pose ground-truth velocity](0026-pose-ground-truth-velocity.md) | Publish world linear velocity in pose v2 with shared/native validation and MCAP readback. | Complete; committed | `51e37e60078dc27a0996f3830acf80721b739a2b` |
| [0027: shared workspace environment](0027-shared-workspace-environment.md) | One Python 3.12 uv environment, lockfile and build/run configuration across six sibling projects. | Implemented; verified with Godot 4.7 | Pending |
