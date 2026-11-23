# Merge Alice Isaac backend into Bob launcher

## Goal

Add Alice's optional Isaac physics and renderer while preserving Bob's target spawn, GPS, and ZeroMQ simulation lifecycle.

## Implementation steps

1. Merge `origin/alice` into `bob` and combine CLI options and backend selection.
2. Keep simulation Reset as the supported stateful path; retain the workspace-owned App launcher helper deletion.
3. Update the target-scene script and documentation, then test combined options and existing launcher behavior.

## Interface changes

The launcher accepts `--renderer-backend`, `--physics-backend`, `--isaac-headless`, and `--world`. Existing defaults remain Godot and PyBullet.

## Verification

The focused launcher suite passed (13 tests), `bash -n tools/run_target_scene.sh` passed, and the changed modules compiled. The full Drone suite reported 665 passed, 8 skipped, and 6 failures in existing workspace path/profile and position-square tests. Isaac Sim runtime was not available for a live backend check.

## Scope and defaults

Isaac remains optional. Its target contact remains unimplemented as described in Alice's release log.

## Status

Implemented. Implementation commit: `ddb00b3`.
