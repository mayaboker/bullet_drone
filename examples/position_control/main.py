"""Entry point: uv run examples/position_control/main.py [--headless]."""

from collections.abc import Sequence
from pathlib import Path
import sys

# Direct file execution needs the repository root to import the examples package.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import click
from loguru import logger

from bullet_drone.config import ConfigurationError
from examples.position_control.cli import ControlChainCliParser
from examples.position_control.demo import run_control_chain


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = ControlChainCliParser().parse(argv)
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except (click.Abort, KeyboardInterrupt):
        click.echo("Control-chain example interrupted.", err=True)
        return 130
    if isinstance(options, int):
        return options

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{level}: {message}", diagnose=False)
    try:
        position_options = {} if options.initial_position_m is None else {"initial_position_m": options.initial_position_m}
        position_options["trace_path"] = options.trace_path
        if options.renderer is None and options.render_config is None:
            result = run_control_chain(gui=not options.headless, **position_options)
        else:
            result = run_control_chain(gui=not options.headless, renderer=options.renderer,
                                    render_config=options.render_config, headless=options.headless, **position_options)
        state = result.observation.ground_truth
        logger.info("Control-chain example completed at {:.3f} s; landed and disarmed; final position {} m",
                    state.simulation_time_s, state.position_m)
        logger.info("Verified {} settled waypoints; recorded {} complete control-chain samples",
                    len(result.arrivals), len(result.samples))
        return 0
    except ConfigurationError as exc:
        click.UsageError(str(exc)).show()
        return 2
    except KeyboardInterrupt:
        logger.info("Control-chain example interrupted; resources closed")
        return 130
    except Exception:
        logger.exception("Control-chain example failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
