# Software requirements: 0.1.0

Status: **Draft**  
[Version overview](index.md) · [Architecture](../../architecture.md)

| ID | Requirement | Proposed acceptance evidence |
| --- | --- | --- |
| SW-001 | Deliver an installable Python package with declared metadata and a build system. | Install the built package in a clean supported environment and import its public interface. |
| SW-002 | Use uv for dependency and environment management and commit the dependency lockfile. | A clean checkout synchronizes using the checked-in lockfile; locked checks fail on inconsistent metadata. |
| SW-003 | Permit headless physics use without optional plotting or display dependencies. | Run a minimal experiment with only the core dependency set. |
| SW-004 | Expose documented initialize, reset, step, observe, and close lifecycle behavior. | Contract checks exercise valid lifecycle sequences, invalid calls, and repeated close. |
| SW-005 | Publish backend-independent immutable or copied data contracts with explicit units, frames, and schema versions for transported/recorded data. | Consumers interpret samples without PyBullet imports; later steps do not mutate earlier observations. |
| SW-006 | Record ordered telemetry with run metadata and expose flush/completeness outcomes. | Read back a finite run and verify sample identities, applied commands, configuration, seed, and backend version; injected write failure is reported. |
| SW-007 | Support live and offline plots of position, orientation, velocities, and rotor speeds against simulation time. | Both paths consume the same telemetry contract and label quantities and units. |
| SW-008 | Report validation, lifecycle, backend, rendering, transport, and recording failures distinctly enough for callers to apply the specified recovery policy. | Controlled failures produce actionable errors and no falsely successful physics sample. |
| SW-009 | Release clients, queues, files, and worker processes on shutdown, including failure paths. | Repeated start/stop and failed-run checks leave no owned workers or open recording resources. |

Python version, supported operating systems, storage format, plotting library, and concrete tool versions remain open design decisions.
