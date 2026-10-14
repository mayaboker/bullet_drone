# Build a wheel and use Bullet Drone in another project

[Project README](../README.md) · [Design menu](design/index.md)

## Requirements and package configuration

Use Python **3.12 or newer** and [uv](https://docs.astral.sh/uv/). The existing `pyproject.toml` already configures the build:

```toml
[project]
name = "bullet-drone"
version = "0.1.0"
requires-python = ">=3.12"

[build-system]
requires = ["uv_build>=0.9.25,<0.10.0"]
build-backend = "uv_build"

[project.scripts]
bullet-drone = "bullet_drone.main:main"
```

This excerpt describes the existing configuration; it is not a replacement for the complete `pyproject.toml`. `uv_build` discovers `src/bullet_drone` from the distribution name. The distribution name is `bullet-drone`; the Python import name is `bullet_drone`.

## Build the wheel

From the Bullet Drone repository root:

```bash
uv build --wheel
```

The current version creates:

```text
dist/bullet_drone-0.1.0-py3-none-any.whl
```

The wheel contains the Python package and its resources. `py3-none-any` describes this package's pure Python wheel; the PyBullet dependency still needs a compatible native build for the destination platform. Building does not publish to PyPI or upload to GitHub.

To create both a wheel and source distribution, run `uv build` without `--wheel`. The `.tar.gz` is a source distribution, not the wheel described here.

For a new release, change `project.version` in `pyproject.toml`, synchronize the project lockfile with `uv lock`, and build again. The new wheel filename uses that version. Keep the version unchanged when reproducing an existing release. uv explains the workflow in its [building and publishing guide](https://docs.astral.sh/uv/guides/package/).

## What the wheel includes

| Repository location | Installed contents |
| --- | --- |
| `src/bullet_drone/*.py` | Simulation, configuration, CLI, state, joystick, mixer, actuator, propeller and physics modules |
| `src/bullet_drone/controllers/` | Shared PID, altitude, position and internal stabilization controllers |
| `src/bullet_drone/forces/` | Rotor thrust and reaction torque models |
| `src/bullet_drone/rendering/` | Render contracts, configuration, snapshots and UDP publication |
| `src/bullet_drone/assets/racer/` | Racer URDF, body mesh, four propeller meshes, asset README and upstream license |
| Generated `bullet_drone-0.1.0.dist-info/` | Package metadata, dependency requirements, wheel metadata, file records and console-script entry point |

The `src/` prefix is removed inside the wheel. Installed files appear under `bullet_drone/` in the environment's `site-packages`. The root README content is embedded in package metadata; it is not copied as a standalone root README file.

These repository directories are **not included in the wheel**:

```text
examples/           # Hover, gate missions and control-chain scenarios
renderers/godot/    # Godot project, visual world and camera UI
configs/           # Example simulation/render YAML files
tests/             # Development tests
docs/              # Repository documentation
plan/              # Implementation records
.vscode/           # Editor tasks
.venv/             # Development environment
```

`pyproject.toml` and `uv.lock` are not installed as files from this wheel. Runtime requirements are recorded in wheel metadata. Click, Loguru, PyBullet and PyYAML are installed by the package installer rather than bundled into the wheel. Development dependencies such as pytest are not installed by this package's runtime requirements. See uv's [file-inclusion rules](https://docs.astral.sh/uv/concepts/build-backend/#file-inclusion-and-exclusion).

Inspect the actual archive with Python's standard ZIP tools:

```bash
uv run python -m zipfile -l dist/bullet_drone-0.1.0-py3-none-any.whl
```

## Create a separate project and install the wheel

Run these commands in a parent directory outside the Bullet Drone repository:

```bash
uv init --python 3.12 my-drone-app
cd my-drone-app
uv add /absolute/path/to/bullet_drone/dist/bullet_drone-0.1.0-py3-none-any.whl
```

Replace `/absolute/path/to/bullet_drone` with the source repository's actual path. `uv add` creates/updates the new project's dependency configuration, lockfile and environment, and installs the wheel and its runtime dependencies. The new project's lockfile controls its own dependency resolution; the source repository's `uv.lock` is not shipped with the wheel.

Keep the wheel at the recorded path when recreating the environment. For a portable local-wheel project, copy it into a `vendor/` directory in the new project and use `uv add ./vendor/bullet_drone-0.1.0-py3-none-any.whl` instead.

You can check the import location:

```bash
uv run python -c "import bullet_drone; print(bullet_drone.__file__)"
```

It should point into the new environment's `site-packages`, not the source checkout. No `sys.path` modifications or `PYTHONPATH` pointing to the repository are required.

## Import and run the simulation library

In `my-drone-app`, create `simulate.py`:

```python
from bullet_drone import DroneEnvironment
from bullet_drone.config import DroneSettings, SimulationConfig, SimulationSettings
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.runner import SimulationRunner

config = SimulationConfig(
    simulation=SimulationSettings(
        timestep_s=1 / 240,
        max_steps=240,
        gravity_m_s2=(0.0, 0.0, -9.81),
        gui=False,
    ),
    drone=DroneSettings(
        mass_kg=1.0,
        initial_position_m=(0.0, 0.0, 1.0),
    ),
)

environment = DroneEnvironment(PyBulletPhysics(config))
observation = SimulationRunner().run(
    environment,
    max_steps=config.simulation.max_steps,
    pace_wall_time=False,
)

state = observation.ground_truth
print(f"Completed steps: {state.step_index}")
print(f"Simulation time: {state.simulation_time_s:.3f} s")
print(f"Position: {state.position_m} m")
```

Run it:

```bash
uv run python simulate.py
```

This runs one simulated second of headless gravity/contact physics with motors off, using the packaged racer model. Expect 240 completed steps and a simulated time of `1.000 s`. The body falls from its initial height and settles near the ground. It is a library-integration example, not a powered flight mission.

`SimulationRunner` owns environment cleanup on success, failure and interruption, so the script does not need an additional close call. `PyBulletPhysics` acquires its world on reset, loads the bundled URDF/meshes through package resources, and releases its client when closed. If you manage `reset()` and `step()` directly instead of using the runner, call `environment.close()` in a `finally` block.

`reset()` and `step()` return immutable `DroneObservation`. Read `observation.ground_truth` for position, body-to-world XYZW orientation, world velocities, actual rotor speeds, episode, step and simulation time. Sensor slots are currently separate and empty. Units are SI; the world is right-handed Z-up, with body X forward, Y left and Z up.

## Run the installed CLI with your own configuration

In the new project, create `simulation.yaml`:

```yaml
simulation:
  timestep_s: 0.004166666666666667
  max_steps: 240
  gravity_m_s2: [0.0, 0.0, -9.81]
  gui: false

drone:
  mass_kg: 1.0
  initial_position_m: [0.0, 0.0, 1.0]
```

Then run:

```bash
uv run bullet-drone --config simulation.yaml
```

The installed console script calls `bullet_drone.main:main`. It runs the same basic physics without a hover/position mission. You supply the YAML because repository `configs/` files are not included in the wheel.

To use the PyBullet GUI, set `gui: true` or pass `--renderer pybullet`. A working desktop display is required; the CLI paces visible simulation approximately to wall time.

## Build your application's control source

The wheel provides the reusable controllers and command interfaces:

```python
from bullet_drone.commands import HighLevelCommand, JoystickInput
from bullet_drone.composition import create_flight_command_provider
from bullet_drone.contracts import HighLevelController
from bullet_drone.controllers import (
    AltitudeController,
    InternalControlSettings,
    PidSettings,
    PositionController,
)
from bullet_drone.joystick import SoftwareJoystick
```

These imports are available in the new project. Define your own `HighLevelController` with `reset(observation)`, `command(observation, dt_s)` and `close()`. It can use `PositionController` for position/velocity PID and send its `JoystickInput` to `SoftwareJoystick`. Use `create_flight_command_provider()` with explicit stabilization settings and pass the resulting provider to `SimulationRunner.run(command_provider=...)`.

Angle RPY uses radians, desired velocity uses m/s, collective thrust uses newtons, and motor speeds use rad/s. Commands must match the observation's episode and next step. The command provider handles arm gating, stabilization and mixing; physics applies rotor forces and advances the world. Configure diagnostic logging in your application's entry point; keep telemetry recording separate.

See the [position/virtual-joystick control-chain guide](design/position-control-chain.md) and [internal control API](design/internal-flight-control.md) for the complete composition and lifecycle. The repository's `examples/position_control` contains a tested application composition, but importing `examples.position_control` is not supported by the installed wheel because examples are intentionally outside the packaged library. Port the application-specific mission into your own project if you want that behavior.

## Own the application loop with joystick-only commands

`bullet_drone.simulation.JoystickSimulation` is the public boundary for an
application that owns its runner and high-level controllers. Construct it with
`SimulationConfig`, `InternalControlSettings` and optional `VehicleParameters`.
It owns the joystick, stabilization, mixer, actuator/propeller models and physics;
it does not run a loop. Optional `stabilization`, `motor_dynamics` and
`propeller_model` contracts support model injection and passive probes.

```python
from bullet_drone.commands import JoystickInput
from bullet_drone.controllers import InternalControlSettings, PidSettings
from bullet_drone.simulation import JoystickSimulation

settings = InternalControlSettings(
    (4, 4, 4), (2, 2, 2), (PidSettings(.05, 0, 0, .1, 0),) * 3,
)
simulation = JoystickSimulation(config, settings)  # your SimulationConfig
try:
    observation = simulation.reset()
    # A disarmed command advances one step with zero motor targets.
    observation = simulation.step(JoystickInput())
    print(observation.ground_truth.position_m)
finally:
    simulation.close()
```

Your application repeats controller calculations using observation N and submits
one `JoystickInput` to receive observation N+1. It uses `simulation.timestep_s`
for control updates and owns recording, pacing, completion and cleanup. The facade
accepts joystick input only; rotor commands and wrenches cannot be submitted to
its `step()` method. `last_command` and `allocation` are read-only completed-step
diagnostics. Reset starts a new episode; runtime failure requires reset before
reuse, and close is terminal. Invalid joystick input is rejected before stepping.

Drone Lab uses this interface with its own runner and separate position/velocity
controllers. See [interface and cycle ownership](design/drone-lab-interface-and-cycle.md).
The preceding lower-level APIs remain supported for existing consumers.

## Godot and other repository resources

The wheel includes the Python UDP render publisher and render interfaces. It does not install the Godot executable, viewer project, visual scene, render YAML or VS Code tasks. To use Godot, keep a separate copy of `renderers/godot`, run it with Godot 4.3+, and supply your own render profile or use the library's defaults. See the [rendering guide](design/godot-rendering.md).

The Python package can run headless physics without launching Godot. Building the wheel does not change which files are packaged, copy example missions into the library, or publish an artifact; those would be separate changes.
