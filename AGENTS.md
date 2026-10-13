# Project guidance

These instructions apply throughout this repository.

## SOLID design guide

- **Single responsibility:** separate CLI parsing, configuration loading, simulation orchestration, environment lifecycle, physics, rendering, and telemetry.
- **Open/closed:** extend physics models and consumers through focused interfaces without rewriting orchestration.
- **Liskov substitution:** implementations must preserve interface units, lifecycle, stepping semantics, and error behavior.
- **Interface segregation:** keep interfaces small; physics consumers must not depend on rendering or plotting operations.
- **Dependency inversion:** orchestration depends on project-owned contracts; concrete library integrations stay in adapters.

Prefer simple composition and small contracts. Introduce abstractions only when they express a real component boundary.

## Libraries and tooling

- Use `src/bullet_drone/main.py` as the application entry point. Its `main()` function constructs and uses a CLI helper, loads configuration, wires components, and starts the runner.
- Use **Click** inside a `CliParser` helper class. The helper returns parsed arguments; it must not launch simulation, load YAML, or configure logging.
- Use **Loguru** for application diagnostics. Configure logging once at the application entry point. Library components must not configure global sinks.
- Keep diagnostic logging separate from simulation telemetry recording. Do not use diagnostic messages as the telemetry storage format.
- Use **uv** for dependency management and command execution. Update `pyproject.toml` and `uv.lock` together when dependencies change.
- Keep headless physics independent of optional rendering and plotting dependencies.
- Keep ground-truth `DroneState` independent of noisy sensor readings. Sensor classes live in a separate sensors package and use project-owned data and read-only scene queries; sensor noise must never modify physics state. See the [sensor design](docs/design/sensors.md).

## Workflow and scope

- Read the [design menu](docs/design/index.md) and relevant design documents before changing architecture or interfaces.
- Keep design documents current when interfaces or architecture change.
- Implement only the authorized milestone. Add advanced physics in later steps rather than expanding a basic entry-point change.
- Validate behavior appropriate to the change, including lifecycle and cleanup when changing simulation execution.

The [first simulation entry-point design](docs/design/simulation-entry-point.md) defines the next simulation milestone. This guidance file does not itself authorize its implementation or dependency installation.
