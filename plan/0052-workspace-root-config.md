# Move the shared basic physics profile to the workspace root

Goal: make the shared basic.yaml live at the workspace root and use it for Run All.
Steps: move the YAML to the parent workspace; update the renderer launcher path; update active docs and callers/tests that reference the old file location; preserve historical plan records.
Interfaces: no loader or YAML schema changes; callers pass the new relative/absolute path to the existing config loader.
Scope/defaults: workspace root basic.yaml is the single active profile; no duplicate or compatibility symlink remains under bullet_drone/configs. The Run All launcher resolves the root file absolutely. Runtime behavior/settings are unchanged.
Verification: Static reference scan confirms active code/docs/tests use the workspace-root path; `git diff --check` passed in affected repos. Tests were not run.
Status: Implemented; uncommitted.
Implementation commit: Pending.
