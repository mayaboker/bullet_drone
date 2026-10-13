"""Entry point: uv run examples/position/main.py [--headless]."""

from collections.abc import Sequence
from pathlib import Path
import sys

# Direct file execution needs the repository root to import the examples package.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import click
from loguru import logger

from bullet_drone.config import ConfigurationError
from examples.position.cli import PositionDemoCliParser
from examples.position.demo import run_position_demo


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = PositionDemoCliParser().parse(argv)
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except (click.Abort, KeyboardInterrupt):
        click.echo("Position demo interrupted.", err=True)
        return 130
    if isinstance(options, int):
        return options

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{level}: {message}", diagnose=False)
    try:
        position_options = {} if options.initial_position_m is None else {"initial_position_m": options.initial_position_m}
        if options.renderer is None and options.render_config is None:
            result = run_position_demo(gui=not options.headless, **position_options)
        else:
            result = run_position_demo(gui=not options.headless, renderer=options.renderer,
                                    render_config=options.render_config, headless=options.headless, **position_options)
        state = result.observation.ground_truth
        logger.info("Position demo completed at {:.3f} s; landed and disarmed; final position {} m",
                    state.simulation_time_s, state.position_m)
        return 0
    except ConfigurationError as exc:
        click.UsageError(str(exc)).show()
        return 2
    except KeyboardInterrupt:
        logger.info("Position demo interrupted; resources closed")
        return 130
    except Exception:
        logger.exception("Position demo failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
