# World camera and top-left drone camera panels

Status: Completed
Implementation commit: `c5132cad658ce4aca69cf5b907c196ec18c1fe8b`

## Goal and scope

Display the shared world through a full-window spectator camera, with titled drone FPV preview panels at the top left, matching the other project's world/preview layout. Retain independent camera resolution/FOV, source handling, UDP ownership and stale status.

## Implementation steps and interfaces

1. Add a focused world Camera3D adapter with orbit/zoom controls and shared-drone framing.
2. Replace the full-window FPV grid with a bounded top-left scrollable panel stack, sorted by drone ID. Titles identify camera `fpv` and drone ID; status remains visible.
3. Preserve independent SubViewports and aspect ratio. Add world-view drone labels.
4. Update rendering documentation and visible smoke verification for world camera, panel placement, titles and resize behavior.

No Python or wire interface changes. Godot world camera is display-only. Right-drag orbits and wheel zooms, like the reference project at ../fly_smart-godot-render/godot/scripts/main.gd. Camera panels fit within 40% of window width (up to 400 pixels), with scroll for multiple drones; image resolution remains configured by each publisher.

## Verification

Godot registry tests; visible two-publisher smoke test, screenshot inspection, world camera/control and panel title/placement/resize checks. Python physics is unchanged.

## Outcome

Implemented a focused world-camera script and a full-window spectator view with top-left scrollable FPV panels. Camera/drone titles, world drone labels and stale status are visible. Publication and physics interfaces are unchanged.

Verification: Godot editor import/parse and registry tests passed. Visible two-publisher smoke passed for root world camera, FPV placement, sorted titles, independent viewports/FOV, camera mount, aspect-preserving resizing, wheel zoom and staleness. Captured and inspected /tmp/bullet-drone-godot.png: both titled FPV panels and both drones in the shared world view are visible. Whitespace checks passed.

Implementation committed as `c5132cad658ce4aca69cf5b907c196ec18c1fe8b`.
