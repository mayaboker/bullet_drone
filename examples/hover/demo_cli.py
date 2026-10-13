"""Click helper for the hover example; parsing only."""

from collections.abc import Sequence
from dataclasses import dataclass

import click


@dataclass(frozen=True, slots=True)
class HoverDemoOptions:
    headless: bool


class HoverDemoCliParser:
    def __init__(self) -> None:
        self._command = click.Command(
            "hover-demo",
            callback=lambda headless: HoverDemoOptions(headless),
            params=[click.Option(
                ["--headless"], is_flag=True,
                help="Run without a display or wall-clock pacing.",
            )],
            help="Take off to 3 m, hover for 20 s, then land and disarm.",
        )

    def parse(self, argv: Sequence[str] | None = None) -> HoverDemoOptions | int:
        return self._command.main(args=argv, prog_name="hover-demo", standalone_mode=False)
