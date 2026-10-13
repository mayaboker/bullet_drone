# Bullet Drone

A Python package for quadcopter simulation using PyBullet. The first milestone
simulates a bundled racer drone URDF with gravity and ideal rotor forces. It provides a Click CLI,
validated YAML configuration, GUI/headless modes, and Loguru diagnostics.
It can demonstrate open-loop hover and provides an API for internal Angle/Acro
stabilization with a shared PID implementation and caller-supplied high-level
RPY/thrust control. Motor lag, electrical dynamics, high-level hover control,
and sensor models are planned for later milestones.

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

Ideal hover balances weight using the mixer and four rotor speeds:

```bash
uv run --locked bullet-drone --config configs/hover.yaml
uv run --locked bullet-drone --config configs/hover-headless.yaml
```

In VS Code select **Terminal → Run Task → Run hover simulation** for the GUI
demo. It starts level at one metre and holds that height for five seconds without
a feedback controller. `flight.mode` selects `hover` or `gravity` (the default
when omitted). Saturation is reported if the requested lift exceeds motor capacity.

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

## Internal control API

Optional YAML `control.backend` defaults to `internal`. Selecting `betaflight`
raises an unsupported-controller error before simulation startup; the CLI returns 2.
The CLI still runs gravity or open-loop hover. Stabilization is available through
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
commands, body-frame thrust, and failure/interruption cleanup.

## Design

Start with the [design menu](docs/design/index.md) and
[initial architecture](docs/design/architecture.md).
