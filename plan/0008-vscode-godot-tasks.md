# VS Code Godot and drone tasks

Status: Completed
Implementation commit: Pending

## Goal

Provide separate VS Code tasks for the Godot viewer and one Godot-enabled hover simulation, plus a group task that launches both.

## Implementation steps

1. Retain existing simulation tasks.
2. Add a process task invoking Godot with the repository renderer project.
3. Add a process task invoking the hover entry point through uv with the Godot render profile.
4. Add a compound task with parallel dependencies so the persistent viewer does not block simulation startup.
5. Document task names and validate JSON, commands, and dependency references.

## Interface changes and defaults

Only `.vscode/tasks.json` and usage documentation change; simulation interfaces remain unchanged. Use repository-root working directories and dedicated terminals. One drone uses configs/render-godot.yaml. The Godot viewer remains open after the hover mission ends.

## Verification

Validated JSON parsing, unique labels, dependency references, parallel launch, and all referenced project/script/profile paths. No application changes or new tests required.

## Scope

No dependency installation, application changes, commit, or push.
