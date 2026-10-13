# Requirements: version 0.1.0

Status: **Draft proposed scope**, not a released baseline.

[Design menu](../../index.md) · [Architecture](../../architecture.md)

The first version establishes a single-quadcopter simulator with independently consumable state, camera images, and telemetry. These requirements capture the initial architecture proposal and require review before implementation.

| Category | Document | ID prefix |
| --- | --- | --- |
| Physics | [Physics requirements](physics.md) | PHY |
| Software | [Software requirements](software.md) | SW |
| Architecture and integration | [Architecture requirements](architecture.md) | ARC |
| Sensors | [Sensor requirements](sensors.md) | SEN |

Each requirement has a stable category ID and proposed acceptance evidence. Target version and document revision are distinct: this folder describes release scope, while the architecture document can be revised during design. Carry IDs into later version folders and describe any changed scope there. Add categories such as control or performance when their scope is agreed. Sensors are planned as a separate milestone after the basic gravity-only entry point.

Numerical tolerances, vehicle parameters, supported platforms, and performance budgets remain open. Requirements depending on them cannot be considered accepted until those values are specified and checked.
