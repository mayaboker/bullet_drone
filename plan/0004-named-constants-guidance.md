# Named constants guidance

## Goal
Require meaningful named constants instead of unexplained numeric literals.

## Implementation steps
Add repository guidance for descriptive UPPER_SNAKE_CASE constants, units in
names where applicable, and a grouped constants block immediately after imports.

## Interface changes
None.

## Verification
Read the updated AGENTS.md and confirm the rule specifies naming and placement.

## Scope/defaults
Guidance only; no existing code refactor, dependencies, commits, or pushes.

## Status
Implemented and verified.

Verification outcome: Read the updated Constants section; descriptive names,
units, UPPER_SNAKE_CASE and grouping immediately after imports are specified.
No tests run for this documentation-only change.

Implementation commit hash: `ef298d68646e69d828a97df85dceb7a7a29ef18d`.

## Repository snapshot record
Recorded snapshot: `ef298d68646e69d828a97df85dceb7a7a29ef18d` (bullet_drone repository). This is the new local
baseline containing the current implementation, not a recovered historical commit.
