"""Shared Click option declarations; parsing only."""
from pathlib import Path

def rendering_options():
    import click
    return [click.Option(['--renderer'], type=click.Choice(['godot', 'pybullet', 'none']), default=None),
            click.Option(['--render-config'], type=click.Path(exists=True, dir_okay=False, path_type=Path))]

