# README simulation and renderer task table

Status: Completed
Implementation commit: Pending

## Goal and steps

Add a main README table of the primary VS Code tasks that launch simulation with a renderer. Use exact task labels and short descriptions identifying PyBullet/Godot and the flight behavior. Include the four main PyBullet tasks and the five grouped Godot launchers, plus instructions for Tasks: Run Task.

## Interfaces and scope

Documentation only; no task definitions, application interfaces or defaults change. Existing individual publisher tasks remain documented by their scenario sections. No commit or push requested.

## Verification

Compare every table task name with .vscode/tasks.json and confirm rendering mode/group dependencies. Check Markdown table structure and whitespace.

## Outcome

Added the nine primary rendered-simulation launchers in a two-column README table, with task-selection instructions. Verified all labels against tasks.json and confirmed each Godot group includes the viewer with parallel dependencies. No task definitions changed. Whitespace checks passed; implementation commit remains Pending.
