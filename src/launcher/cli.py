"""Launcher options without starting simulation resources."""
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import click
from bullet_simulation_protocol import validate_endpoint
from bullet_simulation_protocol.state import DEFAULT_CONTROL_ENDPOINT


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _checkout_asset(relative_path: str) -> Path | None:
    """Use source-checkout defaults without assuming they exist in a wheel."""
    candidate = PROJECT_ROOT / relative_path
    return candidate if candidate.is_file() else None


DEFAULT_SITL_BINARY = _checkout_asset('bin/betaflight_mavlink_gps_SITL.elf')
DEFAULT_SITL_PROFILE = _checkout_asset('configs/betaflight-mavlink.config')
DEFAULT_SITL_GPS_PROFILE = _checkout_asset('configs/betaflight-mavlink-gps.config')
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
    target_spawn_config: Path | None = None
    render_monitor: str | None = None
    render_half: str | None = None
    gps: bool = False
    simulation_control_endpoint: str = DEFAULT_CONTROL_ENDPOINT


class CliParser:
    def parse(self, argv: Sequence[str] | None = None) -> Options | int:
        @click.command()
        @click.option('--sitl/--no-sitl', default=True, help='Start Betaflight SITL (external controller owns MSP).')
        @click.option('--render/--no-render', default=True, help='Start the Godot renderer.')
        @click.option('--sitl-binary', type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_SITL_BINARY)
        @click.option('--sitl-profile', type=click.Path(exists=True, dir_okay=False, path_type=Path))
        @click.option('--gps/--no-gps', default=False,
                      help='Enable Betaflight virtual GPS; --no-gps still sends test latitude/longitude in FDM.')
        @click.option('--render-config', type=click.Path(exists=True, dir_okay=False, path_type=Path),
                      default=DEFAULT_RENDER_CONFIG)
        @click.option('--renderer', type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_RENDERER)
        @click.option('--target-scene', is_flag=True, help='Enable the red-truck physics collider and contact event.')
        @click.option('--target-spawn-config', type=click.Path(exists=True, dir_okay=False, path_type=Path),
                      help='YAML initial position and yaw for the target-scene drone.')
        @click.option('--render-monitor', help='XRandR monitor name for the Godot window (e.g. DP-1-0).')
        @click.option('--render-half', type=click.Choice(['top', 'bottom']),
                      help='Use the top or bottom half of --render-monitor.')
        @click.option('--simulation-control-endpoint', default=DEFAULT_CONTROL_ENDPOINT,
                      help='Loopback ZeroMQ simulation command endpoint.')
        def command(sitl, render, sitl_binary, sitl_profile, gps, render_config, renderer, target_scene,
                    target_spawn_config, render_monitor, render_half, simulation_control_endpoint):
            """Run a persistent PyBullet simulation with optional SITL and rendering."""
            if sitl_profile is None:
                sitl_profile = DEFAULT_SITL_GPS_PROFILE if gps else DEFAULT_SITL_PROFILE
            if target_scene and (not sitl or not render):
                raise click.UsageError('--target-scene requires --sitl and --render')
            if target_spawn_config is not None and not target_scene:
                raise click.UsageError('--target-spawn-config requires --target-scene')
            if render_half and not render_monitor:
                raise click.UsageError('--render-half requires --render-monitor')
            if sitl and (sitl_binary is None or sitl_profile is None):
                raise click.UsageError('SITL requires --sitl-binary and --sitl-profile')
            if render and (renderer is None or render_config is None):
                raise click.UsageError('Rendering requires --renderer and --render-config')
            try:
                validate_endpoint(simulation_control_endpoint)
            except ValueError as error:
                raise click.UsageError(str(error)) from error
            return Options(sitl=sitl, render=render, sitl_binary=sitl_binary, sitl_profile=sitl_profile,
                           render_config=render_config, renderer=renderer, target_scene=target_scene,
                           target_spawn_config=target_spawn_config, render_monitor=render_monitor,
                           render_half=render_half, gps=gps,
                           simulation_control_endpoint=simulation_control_endpoint)

        return command.main(args=argv, prog_name='launcher', standalone_mode=False)
