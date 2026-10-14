# Implementation plans

Save agreed implementation plans here before implementation. This index records each plan's scope, status, and implementation commit. Design documents under `docs/design/` describe the architecture; these records describe the work for a milestone.

| Plan | Short description | Status | Implementation commit |
| --- | --- | --- | --- |
| [0001: Simulation entry point](0001-simulation-entry-point.md) | Click helper, YAML configuration, GUI/headless stepping, immutable observations, and cleanup. | Completed | `b1bbc0ef32c344ed3f295db1933bc72fd73383a0` |
| [0002: Mixer and ideal hover](0002-mixer-and-ideal-hover.md) | Bounded motor allocation, independent rotor force models, and an open-loop hover demonstration. | Completed | `bd284097d1d9e9ffc90f05f8c701b35561ba075e` |
| [0003: Internal flight control](0003-internal-flight-control.md) | Internal Angle/Acro stabilization, common PID, high-level interface, backend selector, and ideal actuator boundaries. | Completed | `f1da56732e54c6450aefd533401c4cd416ab2e23` |
| [0004: Altitude hover demo](0004-altitude-hover-demo.md) | Software joystick, altitude control, 3 m takeoff/20 s hover/landing/disarm, and example entry point. | Completed | `ffeef6ed717f0bd02a2d8c20c29b524234a8f77d` |
| [0005: Isolate hover examples](0005-isolate-hover-examples.md) | Move hover composition, mission and CLI code into examples/hover; keep the simulation library reusable. | Completed | `ffeef6ed717f0bd02a2d8c20c29b524234a8f77d` |
| [0006: Remove open-loop example](0006-remove-open-loop-example.md) | Remove the legacy demo and configs, retaining altitude hover and independent physics verification. | Completed | `ffeef6ed717f0bd02a2d8c20c29b524234a8f77d` |
| [0007: Multi-drone Godot rendering](0007-multi-drone-godot-rendering.md) | Independent UDP publishers, configurable pose sources, and labeled FPV camera grid. | Completed | `c5132cad658ce4aca69cf5b907c196ec18c1fe8b` |
| [0008: VS Code Godot tasks](0008-vscode-godot-tasks.md) | Separate viewer and one-drone tasks with a parallel group launcher. | Completed | `c5132cad658ce4aca69cf5b907c196ec18c1fe8b` |
| [0009: World camera and preview panels](0009-world-camera-preview-panels.md) | Full-window spectator camera with titled top-left drone FPV panels. | Completed | `c5132cad658ce4aca69cf5b907c196ec18c1fe8b` |
| [0010: Three-drone launch task](0010-three-drone-vscode-task.md) | Godot and three hover simulations with unique IDs and staggered initial positions. | Completed | `869f6b65bb079aa0c8f67dcfcae6947c4b5682e5` |
| [0011: Godot flight-course scenery](0011-godot-flight-world.md) | Outdoor course with gates, pads, trees, hills and sky lighting. | Completed | `7b564aca3f298052ad3971729cd64fef5bd9c76b` |
| [0012: Position gate mission](0012-position-gate-mission.md) | Position-controlled takeoff, gate traversal, return and own-pad landing, with three-drone tasks. | Completed | `d99106e7a15fee202e0c77c72dfaa3fac5996082` |
| [0013: Six mirrored position drones](0013-six-position-drones.md) | Three additional opposite-side pads and a six-drone position-flight launcher. | Completed | `91644751a68d664c76f6527756299d626ecfee27` |
| [0014: Position control-chain example](0014-position-control-chain-example.md) | Position/velocity PID through virtual joystick to physics, with per-stage trace and full-chain verification. | Completed | `43eff356d22f0fb20f4fe695dcf0463b84129e23` |
| [0015: Wheel and library guide](0015-wheel-and-library-guide.md) | Build contents, external uv installation, and runnable simulation-library examples. | Completed | `6e8b39b7791eed487a9e6fcc0cc9e9e9addab9fb` |
| [0016: README renderer task table](0016-readme-render-task-table.md) | Main VS Code simulation/render launchers with exact task names and short descriptions. | Completed | `00cb931dc1d681783c82b211a56220a88a3b6bda` |
| [0017: Godot render FPS](0017-godot-render-fps.md) | Top-right render-frame-rate overlay with resize anchoring and camera input pass-through. | Completed | `6e8b39b7791eed487a9e6fcc0cc9e9e9addab9fb` |

These first two records were saved retrospectively from the agreed designs and completed work. The first commit is the initial project baseline, which also includes the racer URDF update. Future plans are saved before implementation, with `Pending` in the commit column, then updated with the actual implementation hash after committing. A subsequent documentation commit stores that metadata; its hash does not replace the implementation hash.
