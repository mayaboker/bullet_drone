# Six-drone position mission with mirrored pads

Status: Completed
Implementation commit: `91644751a68d664c76f6527756299d626ecfee27`

## Goal and defaults

Add three drones on the opposite side of the existing group and a task launching all six position missions with Godot. Retain current starts for drones 1–3: (0,0), (1.5,.25), (3,.5). Drones 4–6 start at (0,-.75), (1.5,-1), (3,-1.25), all at Z=.015 m. This reflects the original group across Y=-.375 m, leaving a .75 m gap between the closest pair so the centerline drone is not duplicated. All lanes fit the existing |Y|<=1.3 m mission corridor.

## Implementation steps and interfaces

1. Add render profiles for drone_4/5/6 with unchanged camera and ground-truth defaults.
2. Add independent position tasks and `Run Godot and 6 position drones`, depending on the viewer and all six publishers in parallel. Retain existing tasks and positions.
3. Draw six labeled pads at matching world coordinates; shrink pad radius to .32 m to leave separation between the closest pair. Keep physics, controller, gate geometry and mission unchanged.
4. Update usage documentation and verify all six routes/own-pad landings and visual registration.

## Verification

Extend real trajectory coverage to mirrored lanes: both-way gate crossings, opening clearance, own-pad landing and motors off. Validate task commands, six unique IDs and all dependencies. Godot import/registry checks and visible six-publisher run with screenshot inspection. Full Python suite.

## Scope

Six independent single-drone worlds share one visual viewer. No formation controller, inter-drone collision or mission changes. Committed at the user’s request; no push requested.

## Outcome

Implemented drone_4/5/6 profiles, their independent position-flight tasks and the parallel `Run Godot and 6 position drones` launcher. Preserved all original positions and tasks. Godot has six distinct labeled pads with 0.32 m radius and matching coordinate conversion.

Verification: 243 Python tests passed, including both-way gate crossings, opening clearance, own-pad touchdown and motors off for all six starts. Task parsing verified six unique publisher IDs and matching positions/dependencies. Godot editor import/parse and registry checks passed.

Ran all six actual paced mission publishers simultaneously with a viewer on isolated port 19872. All processes returned success; the viewer verified six distinct registrations and each landing position against its own visual pad. New drones completed at 68.179, 65.179 and 62.183 simulated seconds with XY errors below 0.00001 m and Z≈0.01349 m. Captured and inspected /tmp/bullet-drone-six-position.png and /tmp/bullet-drone-six-position-panels.png, including cameras 4–6 and both flight lanes. Whitespace checks passed.

Implementation committed as `91644751a68d664c76f6527756299d626ecfee27`.
