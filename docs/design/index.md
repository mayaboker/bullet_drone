# Design documents

This folder contains the design for a Python package that simulates a quadcopter using PyBullet. The entry-point, ideal rotor, internal stabilization, and altitude demo, position gate mission, and Godot rendering milestones are implemented; broader architecture, sensor designs, and release requirements remain drafts. Each document states its implementation status.

## Architecture

- [Wheel packaging and library usage](../packaging-and-library-usage.md): wheel contents, uv installation into a separate project, public imports and runnable simulation examples.

- [Initial architecture](architecture.md): project goals, component diagram, responsibilities, interfaces, and open decisions.
- [First simulation entry point](simulation-entry-point.md): Click CLI, YAML configuration, GUI/headless modes, environment lifecycle, gravity-only stepping, and Loguru diagnostics.
- [Rotor forces and ideal hover](rotor-forces-and-hover.md): motor mixer, bounded commands, independent force models, equilibrium verification, and complete force roadmap.
- [Internal flight control](internal-flight-control.md): API-only Angle/Acro stabilization, common PID, high-level command contract, controller selector, and ideal motor/propeller boundaries.
- [Altitude hover demo](altitude-hover-demo.md): software joystick, altitude cascade, takeoff to 3 m, 20 s hover, landing/disarm, and example entry point.
- [Position PID and virtual-joystick chain](position-control-chain.md): a new XYZ/yaw flight example with desired-velocity PID, per-stage telemetry and automatic full-chain checks.
- [Position-controlled gate course](position-gate-demo.md): XYZ control through the joystick, gate traversal, return-to-home-pad landing, and three-/six-drone tasks.
- [Independent Godot FPV rendering](godot-rendering.md): configurable pose sources, UDP snapshots, lifecycle, world camera and top-left multi-publisher FPV panels, frames and verification.
- [Sensors and drone observations](sensors.md): IMU, barometer, rangefinder, noise models, and separation of ground truth from measurements.
- [Project guidance](../../AGENTS.md): SOLID rules, library choices, and development workflow.
- [Domain glossary](../../CONTEXT.md): shared terminology used by the design.

## Requirements by target version

| Target version | Overview | Physics | Software | Architecture and integration | Sensors |
| --- | --- | --- | --- | --- | --- |
| 0.1.0 (draft) | [Version scope](requirements/v0.1.0/index.md) | [Physics requirements](requirements/v0.1.0/physics.md) | [Software requirements](requirements/v0.1.0/software.md) | [Architecture requirements](requirements/v0.1.0/architecture.md) | [Sensor requirements](requirements/v0.1.0/sensors.md) |

Create a new version folder when a new release scope is agreed. Each version has its own overview and category documents. Keep requirement IDs stable; record additions, changes, and removals in the new version rather than silently rewriting a released baseline.
