# Target mission stack task

Status: Implemented; static checks passed
Implementation commits: `96868e7` (initial stack), `c8b7738` and `2dd072c` (`bullet_ng` workspace move), `d776638` and `cc73c5b` (`bullet_ng` shared launch updates)

Goal: Start the target scene, Visual, target-hit App, and View from one VS Code task, with a separate terminal for each process.

Implementation steps: Add four child tasks and a parallel compound task. Wait for SITL TCP listeners before launching App so the parallel start does not race SITL startup. Keep the existing combined target scene task available. Move the stack and child tasks to `bullet_ng.code-workspace` so the compound task is available at workspace level. Share the View child and generic SITL readiness helper with the hover/land stack.

Interface changes: Add a `Bullet: Run target mission stack` task in `bullet_ng.code-workspace`. The App child task explicitly selects `--mode manual --mission target-hit`, with `${workspaceFolder:bullet_drone}` as the working directory. Manual is the View-approval setting after the mission refactor.

Verification: Parse the task JSON, inspect task labels and commands, and check that the App wait script parses. Confirm existing live process configuration explains the reported hover-land behavior.

Scope/defaults: Local VS Code tasks only. No automatic flight command; View remains responsible for Arm and Start.

Verification outcome: Workspace JSON parsed; all four child tasks resolve to the named `bullet_drone` workspace folder with separate terminal panels, and the project task list has no duplicate stack. App wait script passed `bash -n`; cross-project `uv run --project ... --locked` commands passed `--help`; `git diff --check` passed. The full GUI flight was not launched during verification.
