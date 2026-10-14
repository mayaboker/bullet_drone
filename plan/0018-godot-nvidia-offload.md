# NVIDIA environment for Godot tasks

Status: Completed
Implementation commit: `a892227962aa74e1c680481979471ae799060d43`

## Goal and steps

Set __NV_PRIME_RENDER_OFFLOAD=1 and __GLX_VENDOR_LIBRARY_NAME=nvidia for the Run Godot viewer VS Code process task. All grouped Godot simulation tasks already depend on this viewer and inherit its launch behavior. Document the task environment and equivalent direct shell command.

## Scope and interfaces

Only the Godot task environment and usage documentation change. Preserve cwd, args, groups and Python simulation task environments. No renderer code, dependencies, global shell settings or smoke-test launcher changes. Committed at the user’s request; no push requested.

## Verification

Parse tasks.json, validate exact string environment values and confirm all Godot group dependencies reference the configured viewer. Check documentation and whitespace. Hardware selection is not claimed without a GPU runtime check.

## Outcome

Updated the shared Godot task with both exact string environment values, preserving its cwd/args. All 5 grouped Godot launchers reference this task. Validated JSON and confirmed Python task environments are unchanged. Documented the equivalent direct command. Whitespace checks passed. No GPU runtime test was performed; implementation committed as `a892227962aa74e1c680481979471ae799060d43`.
