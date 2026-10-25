# FlightLens VS Code task

Goal: add a FlightLens: Open task alongside Bullet: Run all.
Steps: register the existing FlightLens project in the shared uv workspace; update the lockfile; add a process task using its documented uv command; update workspace task documentation; verify configuration and dependency resolution.
Interface changes: one additional VS Code task opens the desktop MCAP viewer.
Scope/defaults: retain Run all, use the shared workspace environment and FlightLens default file chooser; do not start a flight or change application code.
Verification: uv lock and locked full-workspace sync dry-run passed; validated task JSON, package registration and CLI entry point. GUI not launched; dependencies install when the task runs.
Status: Implemented and verified; uncommitted.
Implementation commit: Pending.
