# Hover/land workspace stack

Status: Pending
Implementation commit: Pending

Goal: Start the hover/land mission with manual View approval from one workspace-level VS Code task.

Implementation steps: Add a compound task for SITL, renderer, App and View in separate terminals. Reuse a generic App startup helper that waits for the SITL MSP and MAVLink listeners. Share the View child task with the target stack.

Interface changes: Add `Bullet: Run hover/land mission stack` to `bullet_ng.code-workspace`, with App launched as `--mode manual --mission hover-land`.

Verification: Parse workspace JSON, check dependencies and command arguments, and validate helper shell syntax. Do not start a second live SITL during task configuration checks.

Scope/defaults: The hover profile remains the packaged 20 m / 10 s default. View sends Arm and Start; no Visual process is needed.

Verification outcome: Workspace JSON parsed; the hover stack has the expected launcher, manual hover/land App, and shared View children in separate terminals. The target stack still resolves. Helper shell syntax and mission validation passed; `git diff --check` passed. No live stack was started for this task-only change.
