# Plans

| Plan | Description | Status | Implementation commit |
| --- | --- | --- | --- |
| [0001 Launcher MAVLink profile](0001-launcher-mavlink-profile.md) | Enable UART2 telemetry for the standalone controller. | Implemented; verified in SITL | Pending (no commit requested) |
| [0002 Target contact event](0002-target-contact-event.md) | Add target-enabled launcher collider and contact event. | Pending; focused tests passed, live SITL check blocked by occupied port | Pending |
| [0003 Target mission stack task](0003-target-stack-task.md) | Launch scene, Visual, target-hit App, and View in separate task terminals. | Implemented; static checks passed | `96868e7`, `c8b7738`, `2dd072c` (`bullet_ng`), `d776638`, `cc73c5b` (`bullet_ng`) |
| [0004 Hover/land workspace stack](0004-hover-land-workspace-stack.md) | Launch SITL, renderer, manual hover/land App, and View from the workspace. | Implemented; static checks passed | `d77663839740c9637c43d1b0ff969323d7ed3b35`, `cc73c5bba3d046599e78b028b3bd8902d052407a` (`bullet_ng`) |
| [0005 tmux hover/land launch](0005-tmux-hover-launch.md) | Place the renderer in the top half of the tmuxp stack's monitor. | Implemented; focused and live checks passed | `8d99ee2620ed4de2b990b779fca17aa4650d7dee` (`bullet_drone`), `3651d5bfff7d1ac0b92a36252ab1bc5bd7c9ce44` (`bullet_ng`) |
