# Workspace-owned Bullet App launch

Goal: Move the SITL listener wait and Bullet App startup out of `bullet_drone` and into `bullet_ng` launch tooling.

Implementation steps: Add a path-independent `bullet_ng/launch/run_app_after_sitl.sh` that validates hover-land or target-hit, waits up to 60 seconds for MSP 5761 and MAVLink 5762, then runs the manual App from its own checkout. Update both VS Code App tasks and both tmux App panes to use it. Delete `bullet_drone/tools/run_app_after_sitl.sh` and update launch documentation.

Interface changes: The workspace launch entry point becomes `bash launch/run_app_after_sitl.sh MISSION`. The mission names, port wait, timeout, and `bullet-app --mode manual --mission MISSION` behavior remain unchanged. The simulator launcher remains in `bullet_drone`.

Verification: `bash -n`, workspace JSON parsing, tmux YAML parsing, and `git diff --check` passed. Stubbed `ss`, `sleep`, and `uv` confirmed both mission commands run from the Bullet App checkout, invalid missions exit 2, and listener timeout exits 1 without starting SITL. No active task or tmux layout points to the removed drone script.

Scope/defaults: Use the workspace's existing `~/workspaces/bullet_ng` and `~/projects/bullet_app` layout. Preserve unrelated uncommitted workspace changes. No live SITL launch is required for the path move.

Status: Implemented and verified; no live SITL run. Implementation commit: Pending (no commit requested).
