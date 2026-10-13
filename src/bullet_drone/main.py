"""Application entry point and composition of simulation components."""

from collections.abc import Sequence
import sys

import click
from loguru import logger

from bullet_drone.cli import CliParser
from bullet_drone.config import ConfigurationError, YamlConfigLoader
from bullet_drone.environment import DroneEnvironment
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.runner import SimulationRunner


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = CliParser().parse(argv)
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except (click.Abort, KeyboardInterrupt):
        click.echo("Simulation interrupted.", err=True)
        return 130
    if isinstance(options, int):
        return options

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{level}: {message}", diagnose=False)
    try:
        config = YamlConfigLoader().load(options.config_path)
        environment = DroneEnvironment(PyBulletPhysics(config))
        logger.info("Starting {} simulation", "GUI" if config.simulation.gui else "headless")
        observation = SimulationRunner().run(
            environment, config.simulation.max_steps, pace_wall_time=config.simulation.gui,
        )
        state = observation.ground_truth
        logger.info(
            "Completed {} steps; simulated duration {:.6f} s; final position {} m",
            state.step_index, state.simulation_time_s, state.position_m,
        )
        return 0
    except ConfigurationError as exc:
        click.UsageError(str(exc)).show()
        return 2
    except KeyboardInterrupt:
        logger.info("Simulation interrupted; resources closed")
        return 130
    except Exception:
        logger.exception("Simulation failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
