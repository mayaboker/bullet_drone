# Distinct colors for overlapping FlightLens curves

Goal: distinguish every data curve on a graph by color instead of dash patterns.
Steps: define stable A-measured/A-estimated/B-measured/B-estimated colors and six distinct wind colors; use solid data lines in Velocity, Controls & Wind and the overview; update captions and documentation; run existing UI checks and inspect an overlaid preview.
Interfaces: plotting style only; no numerical, recording or data changes.
Scope/defaults: A measured/truth blue, A command/IMU green, B measured/truth amber, B command/IMU purple. Wind uses six distinct colors, with legend names retaining run and axis. Keep this mapping stable across tabs and episode switches. No automatic commits.
Verification: 42 existing GUI/control/velocity checks passed. Loaded no_wind.mcap and wind-2.mcap and verified every data curve on each Controls & Wind and Velocity graph has a unique color and solid pen. Visually inspected /tmp/flight-lens-velocity-colors.png. Whitespace checks passed.
Status: Implemented and verified; uncommitted.
Implementation commit: Pending.
