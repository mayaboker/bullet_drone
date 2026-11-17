"""Launcher options without starting simulation resources."""
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import click


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SITL_BINARY = PROJECT_ROOT / 'bin/betaflight_mavlink_gps_SITL.elf'
DEFAULT_RENDER_CONFIG = PROJECT_ROOT / 'external_render/configs/physics.json'
DEFAULT_RENDERER = PROJECT_ROOT / 'external_render/dist/linux-x86_64/render'


@dataclass(frozen=True, slots=True)
class Options:
    sitl: bool = True
    render: bool = True
    sitl_binary: Path = DEFAULT_SITL_BINARY
    render_config: Path = DEFAULT_RENDER_CONFIG
    renderer: Path = DEFAULT_RENDERER
    target_scene: bool = False


class CliParser:
    def parse(self, argv: Sequence[str] | None = None) -> Options | int:
        @click.command()
        @click.option('--sitl/--no-sitl', default=True, help='Start Betaflight SITL (external controller owns MSP).')
        @click.option('--render/--no-render', default=True, help='Start the Godot renderer.')
        @click.option('--sitl-binary', type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_SITL_BINARY)
        @click.option('--render-config', type=click.Path(exists=True, dir_okay=False, path_type=Path),
                      default=DEFAULT_RENDER_CONFIG)
        @click.option('--renderer', type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_RENDERER)
        @click.option('--target-scene', is_flag=True, help='Enable the red-truck physics collider and contact event.')
        def command(sitl, render, sitl_binary, render_config, renderer, target_scene):
            """Run a persistent PyBullet simulation with optional SITL and rendering."""
            if target_scene and (not sitl or not render):
                raise click.UsageError('--target-scene requires --sitl and --render')
            return Options(sitl, render, sitl_binary, render_config, renderer, target_scene)

        return command.main(args=argv, prog_name='simulation-launcher', standalone_mode=False)
