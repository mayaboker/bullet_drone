# Configure target-scene starting yaw

Status: Implemented. Implementation commit: Pending (no commit requested).

## Goal
Keep the target-hit drone at its current world position `(0, 0, 0.015)` and allow its starting orientation to be set in a workspace YAML file.

## Implementation
- Add an optional initial yaw to `DroneSettings` and apply it when PyBullet resets the drone.
- Read a small target-scene spawn file containing a world position and yaw in degrees.
- Connect the target-hit workspace stack to a file with position `(0, 0, 0.015)` and yaw `90°`.
- Verify config validation, parsed pose, and physical initial orientation.

## Interface
`launcher --target-scene --target-spawn-config PATH` reads `initial_position_m` and `initial_yaw_deg`. Without the file, the original position and zero yaw remain.

## Verification
60 focused tests passed with two unrelated heavy-quad workspace tests deselected because their referenced files are missing at `/home/user/projects/config/`. Live launcher, SITL, renderer, and Visual startup succeeded at the origin with 90° yaw. Visual reported 508/508 frames with no target, as expected because the truck is at +X and the camera faces +Y. Processes closed cleanly.

## Scope and defaults
The truck stays fixed at world `(50, 0)`. No change to flight guidance. Implementation commit Pending until committed.
