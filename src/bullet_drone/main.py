"""Application entry point and composition of simulation components."""

from collections.abc import Sequence
import sys

import click
from loguru import logger

from bullet_drone.cli import CliParser
from bullet_drone.config import ConfigurationError, YamlConfigLoader
from bullet_drone.control import HoverCommandProvider
from bullet_drone.environment import DroneEnvironment
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.mixer import MotorMixer
from bullet_drone.runner import SimulationRunner
from bullet_drone.vehicle import load_racer_parameters


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
        vehicle = load_racer_parameters()
        provider = None
        if config.flight.mode == "hover":
            provider = HoverCommandProvider(MotorMixer(vehicle), config.drone.mass_kg, config.simulation.gravity_m_s2)
            allocation = provider.allocation
            logger.info("Hover rotor speeds {} rad/s", allocation.speeds_rad_s)
            if allocation.saturated:
                logger.warning(
                    "Hover request saturated: requested {} N, available {} N",
                    allocation.requested.thrust_n, allocation.achieved.thrust_n,
                )
        environment = DroneEnvironment(PyBulletPhysics(config, vehicle))
        logger.info("Starting {} {} simulation", "GUI" if config.simulation.gui else "headless", config.flight.mode)
        observation = SimulationRunner().run(
            environment, config.simulation.max_steps, pace_wall_time=config.simulation.gui,
            command_provider=provider,
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
