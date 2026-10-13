"""Entry point: uv run examples/hover/main.py [--headless]."""

from collections.abc import Sequence
from pathlib import Path
import sys

# Direct file execution needs the repository root to import the examples package.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import click
from loguru import logger

from bullet_drone.config import ConfigurationError
from examples.hover.demo_cli import HoverDemoCliParser
from examples.hover.hover_demo import run_hover_demo


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = HoverDemoCliParser().parse(argv)
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except (click.Abort, KeyboardInterrupt):
        click.echo("Hover demo interrupted.", err=True)
        return 130
    if isinstance(options, int):
        return options

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{level}: {message}", diagnose=False)
    try:
        result = run_hover_demo(gui=not options.headless)
        state = result.observation.ground_truth
        logger.info("Hover demo completed at {:.3f} s; landed and disarmed; final height {:.4f} m",
                    state.simulation_time_s, state.position_m[2])
        return 0
    except ConfigurationError as exc:
        click.UsageError(str(exc)).show()
        return 2
    except KeyboardInterrupt:
        logger.info("Hover demo interrupted; resources closed")
        return 130
    except Exception:
        logger.exception("Hover demo failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
