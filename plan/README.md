# Plans

| Plan | Description | Status | Implementation commit |
| --- | --- | --- | --- |
| [0001 Launcher MAVLink profile](0001-launcher-mavlink-profile.md) | Enable UART2 telemetry for the standalone controller. | Implemented; verified in SITL | Pending (no commit requested) |
| [0002 Target contact event](0002-target-contact-event.md) | Add target-enabled launcher collider and contact event. | Pending; focused tests passed, live SITL check blocked by occupied port | Pending |
| [0003 Target mission stack task](0003-target-stack-task.md) | Launch scene, Visual, target-hit App, and View in separate task terminals. | Implemented; static checks passed | `96868e7`, `c8b7738`, `2dd072c` (`bullet_ng`), `d776638`, `cc73c5b` (`bullet_ng`) |
| [0004 Hover/land workspace stack](0004-hover-land-workspace-stack.md) | Launch SITL, renderer, manual hover/land App, and View from the workspace. | Implemented; static checks passed | `d77663839740c9637c43d1b0ff969323d7ed3b35`, `cc73c5bba3d046599e78b028b3bd8902d052407a` (`bullet_ng`) |
| [0005 tmux hover/land launch](0005-tmux-hover-launch.md) | Place the renderer in the top half of the tmuxp stack's monitor. | Implemented; focused and live checks passed | `8d99ee2620ed4de2b990b779fca17aa4650d7dee` (`bullet_drone`), `3651d5bfff7d1ac0b92a36252ab1bc5bd7c9ce44` (`bullet_ng`) |
| [0006 View bbox MAVLink codec](0006-view-bbox-codec.md) | Share the validated V2_EXTENSION fid/bbox payload. | Implemented; focused and live checks passed | `f8bda7817b29fbcea5184c13c2f1562914b71b0d` |
| [0007 Packaged simulation launcher](0007-packaged-launcher.md) | Move the persistent launcher into an installable `launcher` command. | Implemented; focused, wheel, and live checks passed | `94aba8064be722c11696a4808405b98524de118f` (bullet_drone), `712111a722f41c9e62425a2deb3c5b3d8d9be480` (bullet_ng), `6741a1c25f8496d61e0b21af1554229a52037b56` (bullet_app) |
| [0008 SITL MAVLink shared boot clock](0008-sitl-mavlink-shared-clock.md) | Align TIMESYNC and ATTITUDE to one SITL clock for LOS acquisition. | Implemented; build and live target hit passed | `404d7b3` |
| [0009 Workspace-owned Bullet App launch](0009-workspace-owned-app-launch.md) | Move the App wait-and-run helper into `bullet_ng` launch tooling. | Implemented; static and stubbed launch checks passed | `e4b1d1f` (`bullet_ng`), `c42106e` (`bullet_drone`) |
| [0010 Launcher virtual GPS](0010-launcher-virtual-gps.md) | Enable opt-in virtual GPS for workspace SITL mission stacks. | Implemented; 39 simulator tests and config checks passed | Pending (no commit requested) |
| [0011 GPS SITL barometer altitude](0011-gps-baro-altitude.md) | Use barometer-only altitude estimation in GPS SITL profiles. | Implemented; profile load passed, target-hit rerun still failed | Pending (no commit requested) |

| [0012 NWU GPS frame](0012-nwu-gps-frame.md) | Align GPS and attitude world references. | Implemented; frame checks pass, live mission failures remain | Pending |
| [0013 GPS coordinates in disabled FDM](0013-no-gps-fdm-coordinates.md) | Keep lat/lon in launcher FDM while Betaflight GPS stays disabled. | Implemented; 48 focused tests passed | Pending (no commit requested) |
| [0014 Ground truth MCAP publication](0014-ground-truth-mcap.md) | Publish 30 Hz physics position and velocity for MCAP and FlightLens. | Implemented | Pending (no commit requested) |
| [0015 Simulation control and state](0015-simulation-control-state.md) | Control launcher lifecycle over ZMQ and publish current state for View. | Pending | Pending |
| [0016 Configure target-scene starting yaw](0016-target-scene-start-yaw.md) | Keep the drone at the origin while configuring its initial orientation in YAML. | Implemented; 60 focused tests and live startup passed | Pending (no commit requested) |
| [0017 Merge Alice Isaac backend](0017-merge-alice-isaac-backend.md) | Add optional Isaac physics and rendering while retaining spawn and simulation control. | Implemented; 13 launcher tests passed | `ddb00b3` |
