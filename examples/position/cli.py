"""Click helper for the position example; parsing only."""

from collections.abc import Sequence
from dataclasses import dataclass

import click
from pathlib import Path
from bullet_drone.rendering.cli import rendering_options


@dataclass(frozen=True, slots=True)
class PositionDemoOptions:
    headless: bool
    renderer: str | None = None
    render_config: Path | None = None
    initial_position_m: tuple[float, float, float] | None = None


class PositionDemoCliParser:
    def __init__(self) -> None:
        self._command = click.Command(
            "position-demo",
            callback=lambda headless, renderer, render_config, initial_position: PositionDemoOptions(
                headless, renderer, render_config, initial_position or None),
            params=[click.Option(
                ["--headless"], is_flag=True,
                help="Run without a display or wall-clock pacing.",
            ), click.Option(
                ["--initial-position"], type=float, nargs=3, default=None, metavar="X Y Z",
                help="Initial PyBullet world position in meters (default: 0 0 0.015).",
            )] + rendering_options(),
            help="Take off, traverse the gates, return to the home pad, then land and disarm.",
        )

    def parse(self, argv: Sequence[str] | None = None) -> PositionDemoOptions | int:
        return self._command.main(args=argv, prog_name="position-demo", standalone_mode=False)
