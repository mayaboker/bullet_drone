# Launcher virtual GPS

## Goal

Allow the workspace SITL launcher to supply virtual GPS measurements so Betaflight can emit GPS_RAW_INT and GLOBAL_POSITION_INT.

## Implementation steps

1. Add an opt-in `--gps` launcher option that selects the existing virtual-GPS firmware profile.
2. Build the matching GPS sensor in the launcher and encode its readings in the FDM stream.
3. Enable `--gps` in both workspace mission stacks and document the option.

## Interface changes

The launcher gains `--gps`; without it the current GPS-disabled behavior remains.

## Scope and defaults

The opt-in GPS origin is latitude 0 degrees, longitude 0 degrees, altitude 100 m MSL. A GPS-capable SITL binary and matching profile are required.

## Verification

Passed: 39 focused simulator tests, workspace launch configuration checks, and GPS-capable SITL binary/profile validation. A live check was not run because ports 5761 and 5762 were already occupied.

## Status

Implemented. Implementation commit: Pending (no commit requested).
