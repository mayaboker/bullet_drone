# 0006: Remove the open-loop hover example

Status: Completed

Implementation commit: `ffeef6ed717f0bd02a2d8c20c29b524234a8f77d`

## Goal and scope

Remove the legacy open-loop hover demonstration, keeping the altitude-controlled takeoff/20 s hover/landing/disarm example as the supported hover entry point. Preserve reusable simulation/control code and independent mixer/physics equilibrium verification. No dependency changes are required. The user subsequently authorized implementation and metadata commits; pushing remains outside scope.

## Implementation steps and interface changes

1. Delete examples/hover/open_loop.py, open_loop_main.py, and their YAML configs; remove their example imports and execution tests.
2. Rewrite physics equilibrium checks to use MotorMixer and RotorCommand directly rather than the removed demonstration provider. Retain mass scaling, motor reset, and force-failure cleanup coverage.
3. Remove now-unused core CliParser example customization. Keep the simulation CLI and the altitude demo interfaces unchanged.
4. Point the VS Code hover task to examples/hover/main.py and update current documentation/run commands. Preserve historical plan records, adding a removal note to plan 0005.

## Verification

Run the full suite and headless altitude demo. Search current code/tests/docs/tasks for dangling open-loop provider/module/config references. Verify that the only hover example entry point still performs the complete mission with motors off.

Outcome: `uv run pytest -q` passed **186 tests**. The headless altitude demo completed at 33.229 s, landed/disarmed with motors off. Independent five-second physics equilibrium, mass scaling, rotor reset, and force-failure cleanup checks pass using direct mixer/rotor commands. Searches found no removed provider/module/config references in current examples, tests, library, docs, README, or VS Code tasks. `git diff --check` passed. No dependencies changed. Plans 0004–0006 were committed together after the user requested it; the recorded hash identifies the implementation commit.
