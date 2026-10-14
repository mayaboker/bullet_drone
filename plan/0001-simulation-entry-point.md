# 0001: First simulation entry point

Status: **Completed**  
Implementation commit: `b1bbc0ef32c344ed3f295db1933bc72fd73383a0` (`project init`)  
Record: **Saved retrospectively from the agreed design and implemented baseline**

[Plan menu](README.md) · [Entry-point design](../docs/design/simulation-entry-point.md)

## Goal

Run a configurable fixed-step PyBullet simulation from `main.py`, with GUI and headless modes and no Gymnasium dependency.

## Implementation steps

1. Make `main.py` the composition point; instantiate a Click-based `CliParser` helper that returns arguments.
2. Safely load YAML and validate settings before opening a physics connection.
3. Separate the runner, drone environment, physics backend, and immutable data contracts.
4. Create a ground plane and drone body, reset, and execute a finite number of gravity-only steps. The initial baseline also contains the later racer URDF replacement and front/rear propeller colors.
5. Use the built-in PyBullet GUI with wall-time pacing when configured; run headlessly without pacing otherwise.
6. Configure Loguru once in `main.py`, report completion/errors, and close resources on success, failure, and interruption.
7. Add example YAML, a VS Code basic task, setup instructions, and behavior tests.

## Interfaces and defaults

- `reset()` and `step(action=None)` return `DroneObservation` with ground truth and empty sensor readings. The initial milestone accepts only `None` actions; later plans extend this contract.
- Physics owns time and state; the runner owns the loop. Imports do not start simulation or configure logging.
- Example settings: 240 Hz, 1,200 steps, 1 kg mass, initial altitude 1 m, and gravity `(0, 0, -9.81)` m/s². GUI is optional and defaults to off when omitted.
- Rotor forces, sensor models, feedback control, and independent rendering are outside this milestone.

## Verification outcome

The initial baseline passed 48 tests after the racer asset update. GUI/headless runs completed 1,200 steps, package builds succeeded, and installed-wheel checks verified bundled model assets. Tests covered validation, lifecycle, gravity/contact, immutable observations, pacing, and failure/interruption cleanup.
