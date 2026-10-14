# Godot render FPS indicator

Status: Completed
Implementation commit: `6e8b39b7791eed487a9e6fcc0cc9e9e9addab9fb`

## Goal and steps

Add a readable top-right FPS overlay to the Godot world camera view. Display the engine's renderer frame rate, with a dark background and refresh every .25 s. Keep it visible before/after publishers, anchored on resize, and ignore mouse input so camera controls still work.

## Interfaces and scope

Viewer-only change; no Python, UDP, physics or camera-settings changes. The metric is global Godot render FPS, not the 240 Hz simulation rate or publisher update rate. Existing drone panels and titles remain unchanged. Committed at the user’s request; no push requested.

## Verification

Godot import/parse plus the existing visible two-publisher smoke check. Verify populated FPS text, top-right placement after resize, mouse pass-through and screenshot appearance. No new standalone test suite required.

## Outcome

Added a top-right dark-backed `Render: N FPS` overlay using Engine.get_frames_per_second(), refreshed every .25 s. Panel and label ignore mouse input, and resize anchors preserve the 12 px right margin. Documented the distinction from simulation and publisher rates.

Verification: Godot 4.3 editor import/parse and the visible two-publisher smoke passed, including positive numeric FPS text, right anchoring after resize, input pass-through and existing camera/panel/staleness checks. Captured and inspected /tmp/bullet-drone-godot.png; the indicator reads Render: 60 FPS and does not obscure camera panels. Whitespace checks passed. Python is unchanged.

Implementation committed as `6e8b39b7791eed487a9e6fcc0cc9e9e9addab9fb`. No push requested.
