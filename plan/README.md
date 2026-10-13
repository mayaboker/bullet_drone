# Implementation plans

Save agreed implementation plans here before implementation. This index records each plan's scope, status, and implementation commit. Design documents under `docs/design/` describe the architecture; these records describe the work for a milestone.

| Plan | Short description | Status | Implementation commit |
| --- | --- | --- | --- |
| [0001: Simulation entry point](0001-simulation-entry-point.md) | Click helper, YAML configuration, GUI/headless stepping, immutable observations, and cleanup. | Completed | `b1bbc0ef32c344ed3f295db1933bc72fd73383a0` |
| [0002: Mixer and ideal hover](0002-mixer-and-ideal-hover.md) | Bounded motor allocation, independent rotor force models, and an open-loop hover demonstration. | Completed | `bd284097d1d9e9ffc90f05f8c701b35561ba075e` |
| [0003: Internal flight control](0003-internal-flight-control.md) | Internal Angle/Acro stabilization, common PID, high-level interface, backend selector, and ideal actuator boundaries. | Completed (uncommitted) | Pending |

These first two records were saved retrospectively from the agreed designs and completed work. The first commit is the initial project baseline, which also includes the racer URDF update. Future plans are saved before implementation, with `Pending` in the commit column, then updated with the actual implementation hash after committing. A subsequent documentation commit stores that metadata; its hash does not replace the implementation hash.
