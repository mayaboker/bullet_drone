# Wheel packaging and external library-usage guide

Status: Completed
Implementation commit: `6e8b39b7791eed487a9e6fcc0cc9e9e9addab9fb`

## Goal and implementation steps

Create docs/packaging-and-library-usage.md with verified instructions for building a wheel, inspecting included files, creating a separate uv project and importing/using the simulation library. Link it from README.md and the design menu.

Explain uv_build, version naming, Python 3.12+, dependency installation, wheel/module/asset/metadata contents and excluded repository folders. Include complete 240-step headless Python and YAML/installed-CLI examples, lifecycle cleanup, public controller/joystick imports and the separate repository requirement for examples/Godot.

## Interfaces and scope/defaults

Documentation only. No packaging configuration, library API or dependency changes. Use current 0.1.0 wheel and existing source layout. Do not publish, commit or push.

## Verification

Build into a temporary directory, inspect archive/metadata, create a separate temporary uv project, install the wheel, and run the documented Python and CLI examples outside the source repository. Verify packaged assets, 240 completed steps, one simulated second and resource cleanup. Check document links and whitespace.

## Outcome

Created the wheel-packaging and external-project usage guide and linked it from README.md and the design menu. It covers current wheel contents/exclusions, dependency/version behavior, uv installation, complete programmatic and YAML/CLI examples, controllers/joystick imports, lifecycle and separate Godot/example resources.

Verification: built a fresh 0.1.0 wheel in /tmp/bullet-drone-packaging-guide-gn4xz6lf/dist, inspected inclusion/exclusion claims, and installed it with uv add in an independent temporary Python 3.12 project. Verified imports resolve to that project's site-packages rather than the source tree. Both exact documented simulation examples completed 240 steps and one simulated second, loading the packaged racer assets. The controller-import snippet succeeded, and an in-process check confirmed the physics client disconnected after runner completion. All local guide/README/menu links and whitespace checks passed.

No packaging, library API or dependency changes. Implementation committed as `6e8b39b7791eed487a9e6fcc0cc9e9e9addab9fb`. No push requested.
