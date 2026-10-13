# Three-drone VS Code launch task

Status: Completed
Implementation commit: Pending

## Goal and defaults

Add a VS Code group task launching the Godot viewer and three independent hover simulations. Place drones one after another along body/world +X with a small Y offset: (0,0,0.015), (1.5,0.25,0.015), (3,0.5,0.015) meters. Use unique drone_1/2/3 publisher IDs. Launch processes in parallel; spatial offsets do not imply delayed launches.

## Implementation steps and interfaces

1. Add optional hover CLI `--initial-position X Y Z` and `run_hover_demo(initial_position_m=...)`, preserving the existing default and validating before resources open.
2. Add drone_2 and drone_3 render profiles with existing camera/source defaults.
3. Add separate three-drone launch tasks and a parallel Godot-and-three-drones group; retain existing tasks.
4. Document positions, independent-world semantics, and task selection.

## Verification

Validate task JSON/dependencies, profile IDs and command targets. Check CLI forwarding and invalid positions before physics, plus completed hover missions at all offsets. Run the existing Python suite.

## Scope and status

No changes to physics/control algorithms or UDP schema. All drones take off to world Z=3 m and land/disarm after their 20 s hover. Each publisher owns an independent physics world; inter-drone contacts are not simulated. No commit or push requested.

Outcome: Implemented the three independent drone tasks and parallel `Run Godot and 3 drones` group, two unique render profiles and validated initial-world-position CLI/API override. Existing defaults and tasks are retained.

Verification: 217 Python tests passed, including CLI forwarding and invalid initial positions rejected before physics acquisition. Parsed all three task commands through the hover CLI, validated their positions and unique IDs, and checked JSON/dependency references. Ran all three complete missions at the configured offsets: each finished at 33.229 simulated seconds, landed at Z=0.01349 m with motors off, retaining horizontal offsets within 0.000035 m. Whitespace checks passed.

Implementation commit remains Pending; no commit requested.
