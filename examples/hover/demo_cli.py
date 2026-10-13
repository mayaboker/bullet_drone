"""Click helper for the hover example; parsing only."""

from collections.abc import Sequence
from dataclasses import dataclass

import click
from pathlib import Path
from bullet_drone.rendering.cli import rendering_options


@dataclass(frozen=True, slots=True)
class HoverDemoOptions:
    headless: bool
    renderer: str | None = None
    render_config: Path | None = None
    initial_position_m: tuple[float, float, float] | None = None


class HoverDemoCliParser:
    def __init__(self) -> None:
        self._command = click.Command(
            "hover-demo",
            callback=lambda headless, renderer, render_config, initial_position: HoverDemoOptions(
                headless, renderer, render_config, initial_position or None),
            params=[click.Option(
                ["--headless"], is_flag=True,
                help="Run without a display or wall-clock pacing.",
            ), click.Option(
                ["--initial-position"], type=float, nargs=3, default=None, metavar="X Y Z",
                help="Initial PyBullet world position in meters (default: 0 0 0.015).",
            )] + rendering_options(),
            help="Take off to 3 m, hover for 20 s, then land and disarm.",
        )

    def parse(self, argv: Sequence[str] | None = None) -> HoverDemoOptions | int:
        return self._command.main(args=argv, prog_name="hover-demo", standalone_mode=False)
