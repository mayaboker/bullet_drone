# Drone Lab interface and cycle ownership guide

Status: Completed
Implementation commit: Pending

## Goal

Explain the interface between drone_lab and bullet_drone, who owns the current
execution loop, and the intended application-owned loop with joystick-only commands.

## Implementation steps

1. Inspect current application composition, mission callback, library runner,
   command provider and rendering consumer.
2. Add a focused design guide with current and proposed sequence diagrams,
   an ownership comparison, command/feedback contracts and rendering timing.
3. Link it from the design menu and existing control-flow document; verify links,
   source references, Markdown structure and whitespace.

## Interfaces and scope

Documentation only. Describe existing callback and step APIs accurately and mark
the joystick-only facade as proposed. Preserve the agreed target: drone_lab owns
the runner and separate position/velocity controllers; bullet_drone owns joystick
translation, stabilization and physics. No source, dependency or drone_lab changes.
No commits or pushes requested.

## Verification

Compare both sequence diagrams with source and the agreed control-flow design.
Validate relative links/code fences and run git diff --check. No runtime changes
require simulation tests.

## Outcome

Added the interface/cycle guide, two sequence diagrams and a Godot flow diagram;
linked it from the design menu and existing control-flow design. Compared current
callback, stepping, pacing, cleanup and rendering behavior against source in both
repositories. Verified relative links and balanced code fences in all five
affected documents and checked interface/timing references. git diff --check
passed. No runtime code changed; simulation tests were not run. No commit requested.
