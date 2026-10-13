"""Click helper for the position control-chain example; parsing only."""

from collections.abc import Sequence
from dataclasses import dataclass

import click
from pathlib import Path
from bullet_drone.rendering.cli import rendering_options


@dataclass(frozen=True, slots=True)
class ControlChainOptions:
    headless: bool
    renderer: str | None = None
    render_config: Path | None = None
    initial_position_m: tuple[float, float, float] | None = None
    trace_path: Path | None = None


class ControlChainCliParser:
    def __init__(self) -> None:
        self._command = click.Command(
            "position-control-chain",
            callback=lambda headless, renderer, render_config, initial_position, trace: ControlChainOptions(
                headless, renderer, render_config, initial_position or None, trace),
            params=[click.Option(
                ["--headless"], is_flag=True,
                help="Run without a display or wall-clock pacing.",
            ), click.Option(
                ["--initial-position"], type=float, nargs=3, default=None, metavar="X Y Z",
                help="Initial PyBullet world position in meters (default: 0 0 0.015).",
            ), click.Option(["--trace"], type=click.Path(dir_okay=False,path_type=Path),
                            help="Optional CSV file with completed-step control-chain telemetry.")] + rendering_options(),
            help="Exercise position/velocity PID, virtual joystick, stabilization, mixer and physics.",
        )

    def parse(self, argv: Sequence[str] | None = None) -> ControlChainOptions | int:
        return self._command.main(args=argv, prog_name="position-control-chain", standalone_mode=False)
