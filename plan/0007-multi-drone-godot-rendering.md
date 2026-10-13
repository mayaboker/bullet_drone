# Multi-drone Godot camera rendering

Status: Completed
Implementation commit: `c5132cad658ce4aca69cf5b907c196ec18c1fe8b`

## Goal and scope

Keep physics single-drone and provide a reusable, externally launched Godot viewer accepting many independent publishers. Display labeled FPV camera tiles, each 640×480 with 75° vertical FOV, forward mount (0.15, 0, 0) m and 10° downward tilt. Share a ground grid, markers and simple racer geometry with orange front and blue rear propellers. Do not add sensor estimation, Python image return, vehicle physics in Godot, or automatic viewer launch.

## Implementation steps and interfaces

1. Define validated immutable rendering configuration and RenderSnapshot, including drone/episode/step/time identity, resolved world pose and per-field provenance. Position selects XY; altitude supplies Z. Recognize sensor selection but reject it before resources open.
2. Add reset/render/close renderer and reset/consume/close observation-consumer contracts. Wire consumers into runner lifecycle without coupling orchestration to cameras or UDP.
3. Publish versioned JSON snapshots, repeated camera settings, UUID stream ID and increasing sequence via nonblocking UDP at 60 Hz simulation time. Attempt initial/final poses; no backlog or acknowledgements. Transport errors are diagnostics; invalid data is explicit.
4. Add --renderer godot|pybullet|none and --render-config to core and hover CLIs, preserving defaults. Godot uses DIRECT physics with wall-time pacing. Reject conflicting headless selections and profiles without Godot.
5. Build a Godot registry with independent shared-world SubViewport cameras, sorted square grid, packet validation and newest-state updates. Reject duplicate active IDs (2 s), permit stale takeover, retire previous streams, reject old sequences and retain stale tiles.
6. Update design documentation and examples.

Wire pose uses SI PyBullet Z-up, body X-forward/Y-left/Z-up, normalized body-to-world XYZW quaternion. Godot maps position (x,y,z) to (x,z,-y), quaternion (qx,qy,qz,qw) to (qx,qz,-qy,qw). Camera uses body forward/down tilt rather than assuming Godot -Z matches body +X.

## Verification

Python source/config/snapshot/codec/scheduling tests; runner lifecycle and absent-viewer completion; existing full suite and hover landing/disarm. Godot script checks for conversion, camera basis, independent viewports, ordering, collision/takeover/retired streams, grid and staleness. Visible two-publisher smoke test with screenshot inspection.

## Defaults

localhost UDP 9870; drone_1; all three sources ground_truth; 60 Hz publication. Viewer is user-owned, remains open after publishers finish. No dependencies added.

## Outcome

Implemented the reusable render boundary, validated profile, UDP adapter, runner consumer lifecycle, both CLI integrations and Godot registry/grid. No dependencies changed.

Verification: 213 Python tests passed; Godot 4.3 registry tests passed including yaw/roll/pitch and tilt conversion, malformed schema, ordering, collision, stale takeover and retired streams. Visible two-publisher UDP smoke passed with independent resolutions/FOV, shared world, sorted grid, camera mount and staleness. Captured and inspected /tmp/bullet-drone-godot.png; another drone is visible in the first camera. Smoke uses isolated port 19870 to avoid interference with running demos.

The actual wall-time-paced hover entry point completed with no viewer on production port 9870: hover began at 5.179 s, landing at 25.179 s, disarm at 32.225 s, completion at 33.229 s and final height 0.0135 m. An additional API verification confirmed all final rotor speeds are zero. Both CLI help commands and whitespace checks passed.

Implementation committed as `c5132cad658ce4aca69cf5b907c196ec18c1fe8b`.
