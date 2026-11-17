# Target mission stack task

Status: Pending
Implementation commit: Pending

Goal: Start the target scene, Visual, target-hit App, and View from one VS Code task, with a separate terminal for each process.

Implementation steps: Add four child tasks and a parallel compound task. Wait for SITL TCP listeners before launching App so the parallel start does not race SITL startup. Keep the existing combined target scene task available.

Interface changes: Add a `Bullet: Run target mission stack` task in `bullet_drone/.vscode/tasks.json`. The App child task explicitly selects `--mode auto --mission target-hit`.

Verification: Parse the task JSON, inspect task labels and commands, and check that the App wait script parses. Confirm existing live process configuration explains the reported hover-land behavior.

Scope/defaults: Local VS Code tasks only. No automatic flight command; View remains responsible for Arm and Start.

Verification outcome: Task JSON parsed; four child tasks, separate terminal panels, and target App arguments checked. App wait script passed `bash -n`; cross-project `uv run --project ... --locked` commands passed `--help`; `git diff --check` passed. The full GUI flight was not launched during verification.
