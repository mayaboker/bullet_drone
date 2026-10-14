"""Click is an argument-parsing helper, not the application entry point."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import click
from bullet_drone.rendering.cli import rendering_options


@dataclass(frozen=True, slots=True)
class CliOptions:
    config_path: Path
    renderer: str | None = None
    render_config: Path | None = None
    headless: bool = False
    mcap_path: Path | None = None


class CliParser:
    def __init__(self) -> None:
        self._command = click.Command(
            "bullet-drone",
            callback=lambda config, renderer, render_config, headless, mcap: CliOptions(config, renderer, render_config, headless, mcap),
            params=[click.Option(
                ["--config"], required=True,
                type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path),
                help="Path to the simulation YAML configuration.",
            ), click.Option(["--headless"], is_flag=True),
                click.Option(["--mcap"], type=click.Path(dir_okay=False, path_type=Path),
                             help="Optional MCAP file (requires the telemetry extra).")
            ] + rendering_options(),
            help="Run a drone simulation in GUI or headless mode.",
        )

    def parse(self, argv: Sequence[str] | None = None) -> CliOptions | int:
        """Return options, or Click's exit code for a help request."""
        return self._command.main(
            args=argv, prog_name="bullet-drone", standalone_mode=False,
        )
