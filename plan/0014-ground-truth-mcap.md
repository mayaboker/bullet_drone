# Ground truth MCAP publication

## Goal
Publish physics position and velocity at 30 Hz for MCAP recording and FlightLens graphing.

## Implementation
Add a compact `analysis/physics/ground_truth` JSON topic to the renderer publisher, with simulation identity/time and NWU position/velocity. Extend ZMQ transport with an optional Unix-nanosecond publish header. Configure the bagger channel and FlightLens parser in their repositories.

## Interface
Three ZMQ frames: topic, little-endian unsigned 64-bit Unix publish nanoseconds, JSON payload. Existing two-frame topics remain unchanged. Renderer config gains `publish_rates_hz.ground_truth` (default 30).

## Verification
Bullet Drone renderer tests: 13 passed. MCAP Bagger pipeline tests: 18 passed.
Flight Lens standalone ground-truth reader test: 1 passed. Its full test suite
requires the missing `bullet_msgs` workspace dependency.

## Scope and defaults
Physics truth is sampled at 30 Hz. Godot owns no truth publication; the physics publisher on 5555 owns this topic.

## Status
Implemented.

## Implementation commit
Pending (no commit requested).
