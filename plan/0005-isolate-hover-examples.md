# 0005: Isolate hover examples

Status: Completed

Implementation commit: `ffeef6ed717f0bd02a2d8c20c29b524234a8f77d`

## Goal

Put hover demonstration code under `examples/hover`, leaving `src/bullet_drone` for reusable simulation and control components. Preserve the 3 m takeoff, 20 s hover, landing/disarm behavior.

## Steps and interfaces

1. Move altitude demo composition, mission sequencing, example CLI helper, and main.py entry point (renamed in the workspace) into the examples/hover package. Keep generic PID, altitude/internal controllers, joystick, contracts, physics, and runner in the library.
2. Update imports, tests, current documentation, commands, and example execution paths. Support direct script and module execution without library imports of examples.
3. Interpret all hover files to include legacy open-loop hover: move its provider and sample configs to examples/hover and supply open_loop_main.py. Remove hover selection and FlightSettings from the core configuration/main CLI, keeping core-to-example dependencies forbidden.
4. Keep recorded historical plans intact, recording the new location in this refactor plan. Update design and plan menus.

## Scope/defaults

No force/model or dependency changes. The user subsequently authorized implementation and metadata commits; pushing remains outside scope. Public hover-example imports change to examples.hover. Reusable simulation/control APIs retain their behavior; FlightSettings and flight.mode are removed because scenario selection belongs to examples. Old YAML flight sections are rejected. The main CLI remains gravity-only. Earlier user changes remain intact.

## Verification

Run the existing tests with imports adjusted for moved modules, plus package-boundary and direct/module example smoke checks. Verify CLI help/import safety and full headless takeoff/hover/landing/disarm. Check no simulation-package imports refer to examples.

Outcome: `uv run pytest -q` passed **188 tests**. Direct and module altitude examples completed at 33.229 s, landed/disarmed with zero motors. The moved headless open-loop example completed 1,200 steps at (0,0,1) m, and the main simulation CLI passed its headless smoke check. CLI help works for both example modules and direct execution outside the repository. The built wheel contains only the reusable library and excludes all hover example modules. No src/bullet_drone imports refer to examples or removed hover modules. `git diff --check` passed. No dependency changes were made. Plans 0004–0006 were committed together after the user requested it; the recorded hash identifies the implementation commit.


## Follow-up removal

[Plan 0006](0006-remove-open-loop-example.md) removes the relocated legacy open-loop example and configs. Only the altitude-controlled example remains supported; verification above records the earlier refactor state.
