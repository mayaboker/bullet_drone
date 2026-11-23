# NWU simulation GPS frame

## Goal and scope
Adopt North–West–Up for all simulation worlds, preserving local geometry and standard geographic/ENU GPS output. Keep BARO_ONLY altitude and mission attitude conventions.

## Implementation
Convert GPS position and velocity from NWU to ENU. Migrate geographic example feedback to NWU. Decode Bullet FDM attitude without the Gazebo world rotation in the Bullet firmware patch; bump compatibility to V2 and rebuild. Update direction tests and documentation.

## Verification
- 75 focused tests passed; 3 existing opt-in tests skipped.
- Both rebuilt GPS binaries passed the live coordinate, independent barometer, and restart tests (2 tests).
- Controlled forward-pitch test: GPS on and off both report yaw 0 degrees; prior GPS-on result was 90 degrees. Results: `/home/user/workspaces/bullet_ng/logs/nwu-heading-results.json`.
- Temporary direct-attitude build passed headings 0, +90, -90, 180 and combined (12,-8,35) degrees. Results: `/home/user/workspaces/bullet_ng/logs/nwu-direct-results.json`.
- GPS-enabled target-hit still failed with LOS recovery_timeout: `bullet_app_20261122T183256982901+0200_1716190.log`.
- GPS-disabled target-hit encountered LOS attitude_stale: `bullet_app_20261122T183428470433+0200_1717270.log`. This comparison is inconclusive; landing was interrupted and the stack reset.
- GPS point-to-point drifted during takeoff and was stopped; full mission validation remains failing. See `/home/user/workspaces/bullet_ng/logs/nwu-gps-point-to-point.log`.
- Restored GPS-enabled scene and manual App. No mission-specific heading offset was added.

The coordinate migration is verified, but it has not solved the mission failures. Further attitude/control and timing diagnosis is required before claiming full flight validation.

## Status
Implemented; coordinate checks pass, full flight validation remains failing.

## Implementation commit
Pending.
