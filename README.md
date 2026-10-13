# Bullet Drone

A Python package for quadcopter simulation using PyBullet. The first milestone
simulates a bundled racer drone URDF with gravity and ideal rotor forces. It provides a Click CLI,
validated YAML configuration, GUI/headless modes, and Loguru diagnostics.
It provides an API for internal Angle/Acro
stabilization with a shared PID implementation and caller-supplied high-level
RPY/thrust control. A software-joystick altitude demo takes off to 3 m, hovers for 20 seconds,
then lands and disarms. Motor lag, electrical dynamics, and sensor models
are planned for later milestones.

## Setup

Use Python 3.12 and uv:

```bash
uv sync --locked
```

## Run

GUI mode opens PyBullet's built-in viewer for a five-second simulation:

```bash
uv run --locked bullet-drone --config configs/basic.yaml
```

Headless mode runs the same fixed-step physics without a display or wall-time pacing:

```bash
uv run --locked bullet-drone --config configs/headless.yaml
```

The module entry point is also available:

```bash
uv run --locked python -m bullet_drone.main --config configs/headless.yaml
```

Set `simulation.gui` in YAML to select the mode. GUI mode requires a working
desktop display and closes when the configured steps finish. Ctrl+C interrupts
the run and releases the physics client.

`main.py` constructs the argument-parser helper and simulation components.
`DroneEnvironment.reset()` and `step()` return immutable `DroneObservation`
records containing `ground_truth` and an empty `sensors` group. The body is a
racer model driven by ideal instantaneous motors; no Gymnasium dependency is required. Front
propellers (+X) are orange and rear propellers are blue. The model is adapted
from [gym-pybullet-drones](https://github.com/learnsyslab/gym-pybullet-drones/blob/01563120e060c9233a61f9cf00e6d4e5a8b331ab/gym_pybullet_drones/assets/racer.urdf);
see the bundled [asset notes](src/bullet_drone/assets/racer/README.md) for provenance.

## Takeoff and altitude hover example

```bash
uv run examples/hover/main.py
uv run examples/hover/main.py --headless
```

The demo starts on the ground, takes off to 3 m, and holds altitude for 20
simulated seconds after settling. It then lands, disarms, and finishes with
motors off. GUI mode is paced; `--headless` needs no display. The altitude
controller commands the existing internal stabilization through a software
joystick interface. VS Code’s **Run hover simulation** task runs this example.
See [the mission, tuning, and API](docs/design/altitude-hover-demo.md).

## Godot FPV viewer

Start Godot 4.3+ separately, then run the hover example:

```bash
godot --path renderers/godot
uv run examples/hover/main.py --renderer godot --render-config configs/render-godot.yaml
```

In VS Code, use **Tasks: Run Task → Run Godot and drone** to start both.
The **Run Godot viewer** and **Run drone with Godot** tasks also run independently.
Godot must be available on PATH.

Use **Run Godot and 3 drones** for three simultaneous hover missions, with
separate **Run drone 1/2/3 with Godot** tasks available. Initial world positions
are `(0, 0, 0.015)`, `(1.5, 0.25, 0.015)`, and `(3, 0.5, 0.015)` meters: spaced
along +X with a small +Y offset. Each has a unique drone ID and FPV panel.
Each simulation owns its own physics world.

The visual flight field includes colored gates, landing pads, trees and distant
hills, with a meter grid and height markers.
Each camera defaults to 640×480 and 75° vertical FOV. Godot shows a full-window world
camera with titled drone FPV panels at the top left. Right-drag orbits the world
view and the mouse wheel zooms; separate publishers need unique `drone_id`
values in their render profiles. Physics runs in DIRECT mode with wall-time
pacing. The viewer remains open when the simulation ends.
Both simulation entry points support `--renderer godot|pybullet|none`.
See [configuration, coordinate frames and verification](docs/design/godot-rendering.md).

## Internal control API

Optional YAML `control.backend` defaults to `internal`. Selecting `betaflight`
raises an unsupported-controller error before simulation startup; the CLI returns 2.
The main CLI runs the simulation; hover scenarios have separate example entry points. Stabilization is available through
`create_flight_command_provider()` with a caller-supplied `HighLevelController`
and explicit gains/limits. Angle commands use radians; Acro commands use body
rates in rad/s; collective thrust uses newtons. Physics accepts injected ideal
motor and propeller components and records actual rotor speeds.

See [the API, frames, lifecycle, and composition example](docs/design/internal-flight-control.md)
and [the implementation plan with reference image](plan/0003-internal-flight-control.md).

## Verification

```bash
uv run --locked pytest -q
```

Tests cover configuration validation, lifecycle, free fall, ground contact,
five-second hover, torque directions and magnitudes, allocation limits, stale
commands, body-frame thrust, altitude takeoff/20 s hover/landing/disarm,
software joystick and arm gating, and failure/interruption cleanup.

## Design

Start with the [design menu](docs/design/index.md) and
[initial architecture](docs/design/architecture.md).
