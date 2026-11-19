"""Launcher options without starting simulation resources."""
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import click


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _checkout_asset(relative_path: str) -> Path | None:
    """Use source-checkout defaults without assuming they exist in a wheel."""
    candidate = PROJECT_ROOT / relative_path
    return candidate if candidate.is_file() else None


DEFAULT_SITL_BINARY = _checkout_asset('bin/betaflight_mavlink_gps_SITL.elf')
DEFAULT_SITL_PROFILE = _checkout_asset('configs/betaflight-mavlink.config')
DEFAULT_RENDER_CONFIG = _checkout_asset('external_render/configs/physics.json')
DEFAULT_RENDERER = _checkout_asset('external_render/dist/linux-x86_64/render')


@dataclass(frozen=True, slots=True)
class Options:
    sitl: bool = True
    render: bool = True
    sitl_binary: Path | None = DEFAULT_SITL_BINARY
    sitl_profile: Path | None = DEFAULT_SITL_PROFILE
    render_config: Path | None = DEFAULT_RENDER_CONFIG
    renderer: Path | None = DEFAULT_RENDERER
    target_scene: bool = False
    render_monitor: str | None = None
    render_half: str | None = None


class CliParser:
    def parse(self, argv: Sequence[str] | None = None) -> Options | int:
        @click.command()
        @click.option('--sitl/--no-sitl', default=True, help='Start Betaflight SITL (external controller owns MSP).')
        @click.option('--render/--no-render', default=True, help='Start the Godot renderer.')
        @click.option('--sitl-binary', type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_SITL_BINARY)
        @click.option('--sitl-profile', type=click.Path(exists=True, dir_okay=False, path_type=Path),
                      default=DEFAULT_SITL_PROFILE)
        @click.option('--render-config', type=click.Path(exists=True, dir_okay=False, path_type=Path),
                      default=DEFAULT_RENDER_CONFIG)
        @click.option('--renderer', type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_RENDERER)
        @click.option('--target-scene', is_flag=True, help='Enable the red-truck physics collider and contact event.')
        @click.option('--render-monitor', help='XRandR monitor name for the Godot window (e.g. DP-1-0).')
        @click.option('--render-half', type=click.Choice(['top', 'bottom']),
                      help='Use the top or bottom half of --render-monitor.')
        def command(sitl, render, sitl_binary, sitl_profile, render_config, renderer, target_scene, render_monitor,
                    render_half):
            """Run a persistent PyBullet simulation with optional SITL and rendering."""
            if target_scene and (not sitl or not render):
                raise click.UsageError('--target-scene requires --sitl and --render')
            if render_half and not render_monitor:
                raise click.UsageError('--render-half requires --render-monitor')
            if sitl and (sitl_binary is None or sitl_profile is None):
                raise click.UsageError('SITL requires --sitl-binary and --sitl-profile')
            if render and (renderer is None or render_config is None):
                raise click.UsageError('Rendering requires --renderer and --render-config')
            return Options(sitl, render, sitl_binary, sitl_profile, render_config, renderer, target_scene,
                           render_monitor, render_half)

        return command.main(args=argv, prog_name='launcher', standalone_mode=False)
