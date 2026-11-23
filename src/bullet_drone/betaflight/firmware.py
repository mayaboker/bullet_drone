"""Compatibility check for managed GPS SITL sessions."""
from pathlib import Path


GPS_FDM_MARKER = b'BULLET_GPS_FDM_V2'
LEGACY_GPS_FDM_MARKER = b'BULLET_GPS_FDM_V1'


def validate_gps_firmware(binary, profile_path, *, gps_enabled):
    """Fail before launching a mismatched firmware, profile, or sensor stream."""
    binary_data = Path(binary).read_bytes()
    if LEGACY_GPS_FDM_MARKER in binary_data:
        raise ValueError('Rebuild the GPS SITL binary for the NWU world frame (BULLET_GPS_FDM_V2)')
    compatible = GPS_FDM_MARKER in binary_data
    commands = [line.split('#', 1)[0].strip() for line in Path(profile_path).read_text().splitlines()]
    profile_gps = False
    provider = None
    for command in commands:
        if command in ('feature GPS', 'feature -GPS'):
            profile_gps = command == 'feature GPS'
        if command.startswith('set gps_provider = '):
            provider = command.removeprefix('set gps_provider = ')
    if (gps_enabled and not compatible) or profile_gps != gps_enabled or (gps_enabled and provider != 'VIRTUAL'):
        raise ValueError('GPS requires matching sensor settings, virtual-GPS profile and BULLET_GPS_FDM_V2 binary')
