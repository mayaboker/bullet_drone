# GPS coordinates in GPS-disabled FDM

## Goal

Include synthetic latitude and longitude in launcher FDM packets with `--no-gps` for coordinate testing, while keeping Betaflight GPS disabled and barometer altitude unchanged.

## Implementation

- Sample ideal GPS in the SITL launcher for both `--gps` and `--no-gps`.
- Add an explicit coordinates-only encoder mode: pack longitude and latitude, barometer-derived position Z, and ground-truth ENU velocity.
- Keep `--no-gps` on the GPS-disabled Betaflight profile.
- Update focused tests and user documentation.

## Verification

Focused encoder, GPS, backend, and launcher tests passed (48 tests). `git diff --check` passed.

## Status

Implemented; focused checks passed.

## Implementation commit

Pending (no commit requested).
