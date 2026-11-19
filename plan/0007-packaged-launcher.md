# Packaged simulation launcher

Goal: make the persistent Bullet Drone simulation launcher the `launcher` command in the installed bullet-drone wheel while keeping SITL and Godot executables external.

Implementation: move the CLI and simulation loop into `src/launcher`; package its Python SITL and renderer supervision, publisher, feedback, and monitor helpers; retain compatibility imports used by other examples. Resolve checkout asset defaults only when present and accept explicit paths to the separately installed SITL binary/profile and renderer/config. Update project metadata, lockfile, task commands, scripts, tests, and docs.

Interfaces: add the `launcher` console command and `--sitl-profile`; remove `examples.simulation_launcher`. `--no-sitl` and `--no-render` do not require their disabled component's assets.

Verification: launcher CLI and process lifecycle tests, full relevant Bullet Drone tests, wheel install and `launcher --help` outside the checkout, and live SITL/render startup and cleanup.

Scope/defaults: one bullet-drone distribution containing `bullet_drone` and `launcher` Python modules. SITL and Godot binaries/configs remain outside the wheel. Existing checkout paths remain defaults when available; installed-wheel users supply explicit asset paths.

Status: Implemented. Focused tests passed (60); the full suite passed 643 tests with 8 skips and 5 failures in unchanged tests requiring missing workspace profiles or expecting unavailable Acro example calls. The wheel command and runtime imports worked outside the checkout, and both checkout and installed-wheel live SITL/render launches started and cleaned up successfully. Implementation commit: Pending.
