# Bullet Drone

A Python package for quadcopter simulation using PyBullet. The first milestone
simulates a bundled racer drone URDF falling onto the ground. It provides a Click CLI,
validated YAML configuration, GUI/headless modes, and Loguru diagnostics.
Rotor dynamics and sensor models are planned for later milestones.

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
racer model without motor forces; no Gymnasium dependency is required. Front
propellers (+X) are orange and rear propellers are blue. The model is adapted
from [gym-pybullet-drones](https://github.com/learnsyslab/gym-pybullet-drones/blob/01563120e060c9233a61f9cf00e6d4e5a8b331ab/gym_pybullet_drones/assets/racer.urdf);
see the bundled [asset notes](src/bullet_drone/assets/racer/README.md) for provenance.

## Verification

```bash
uv run --locked pytest -q
```

Tests cover configuration validation, lifecycle, analytical free fall, ground
contact, pacing, command behavior, and failure/interruption cleanup.

## Design

Start with the [design menu](docs/design/index.md) and
[initial architecture](docs/design/architecture.md).
