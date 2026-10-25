# FlightLens VS Code task

Goal: add a FlightLens: Open task alongside Bullet: Run all.
Steps: register the existing FlightLens project in the shared uv workspace; update the lockfile; add a process task using its documented uv command; update workspace task documentation; verify configuration and dependency resolution.
Interface changes: one additional VS Code task opens the desktop MCAP viewer.
Scope/defaults: retain Run all, use the shared workspace environment and FlightLens default file chooser; do not start a flight or change application code.
Verification: uv lock and locked full-workspace sync dry-run passed; validated task JSON, package registration and CLI entry point. GUI not launched; dependencies install when the task runs.
Status: Implemented and verified; workspace implementation remains outside a Git repository. Plan saved in bullet_drone commit 28e1dc85dd1b0cd9f5339946a0f425532bb27735; this is not the workspace implementation commit.
Implementation commit: Pending.
