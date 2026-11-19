"""Resolve named XRandR monitors to Godot window arguments."""

import re
import subprocess

from loguru import logger


WINDOW_MARGIN_PX = 20
MAX_WINDOW_WIDTH_PX = 1000
MAX_WINDOW_HEIGHT_PX = 900
MONITOR_PATTERN = re.compile(
    r'^\s*\d+:\s+(\+\*|\+)\S*\s+(\d+)/\d+x(\d+)/\d+([+-]\d+)([+-]\d+)\s+(\S+)\s*$')


def parse_monitors(output: str) -> tuple[dict[str, tuple[int, int, int, int]], str | None]:
    monitors = {}
    primary = None
    for line in output.splitlines():
        match = MONITOR_PATTERN.match(line)
        if match is None:
            continue
        marker, width, height, x, y, name = match.groups()
        monitors[name] = (int(x), int(y), int(width), int(height))
        if marker == '+*':
            primary = name
    return monitors, primary


def godot_window_args(requested: str, half: str | None = None) -> list[str]:
    if half not in (None, 'top', 'bottom'):
        raise ValueError(f'Invalid monitor half: {half}')
    try:
        output = subprocess.run(['xrandr', '--listmonitors'], check=True,
                                capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        logger.warning('Cannot query XRandR monitors for {}: {}', requested, error)
        return []
    monitors, primary = parse_monitors(output)
    selected = requested if requested in monitors else primary
    if selected != requested:
        logger.warning('Monitor {} unavailable; using primary monitor {}', requested, selected)
    if selected is None:
        return []
    x, y, width, height = monitors[selected]
    if half is not None:
        top_height = height // 2
        if half == 'bottom':
            y += top_height
            height -= top_height
        else:
            height = top_height
    window_width = min(MAX_WINDOW_WIDTH_PX, width - 2 * WINDOW_MARGIN_PX)
    window_height = min(MAX_WINDOW_HEIGHT_PX, height - 2 * WINDOW_MARGIN_PX)
    if window_width <= 0 or window_height <= 0:
        logger.warning('Monitor {} has no usable window area', selected)
        return []
    return ['--windowed', '--position', f'{x + WINDOW_MARGIN_PX},{y + WINDOW_MARGIN_PX}',
            '--resolution', f'{window_width}x{window_height}']
