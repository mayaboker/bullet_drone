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
