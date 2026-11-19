# tmux hover/land launch

Status: Implemented; focused and live checks passed
Implementation commits: `8d99ee2620ed4de2b990b779fca17aa4650d7dee` (`bullet_drone`), `3651d5bfff7d1ac0b92a36252ab1bc5bd7c9ce44` (`bullet_ng`)

Goal: Launch the existing manual hover/land stack in a reusable tmuxp session with the renderer in the top half of the requested monitor.

Implementation steps: Add an optional named render monitor to the simulation launcher, resolve it through XRandR with primary-screen fallback, and pass window placement to Godot. The workspace tmuxp launcher supplies the monitor name.

Interface changes: `simulation-launcher --render-monitor NAME [--render-half top|bottom]`; default launch behavior remains unchanged.

Verification: Focused CLI and monitor-placement tests, shell/config checks, and live launch when the required ports are free.

Scope/defaults: Godot uses the top half of DP-1-0 when launched through the tmuxp stack, alongside View in the bottom half; a missing monitor falls back to the primary screen.

Verification outcome: Focused monitor and launcher tests passed (8); the live tmuxp launch placed Godot at 1940,37 in the top half of DP-1-0 and exited cleanly after interruption. `git diff --check` passed.
