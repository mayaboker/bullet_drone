# FlightLens attitude, commands and wind comparison

Goal: add a FlightLens Controls & Wind tab to inspect attitude, control effort and wind, with optional two-recording overlay.
Steps:
1. Read validated RC and wind topics and retain platform mappings; build immutable measured attitude, body yaw-rate, acknowledged command and wind series independently of Qt.
2. Add a focused tab showing roll/pitch angle commands and measured angles, measured yaw heading, body yaw-rate command/measurement, requested thrust and world wind velocity. Clearly show source, units and missing channels.
3. Permit selecting a second recording/episode for an optional overlay with independent asynchronous loading, cancellation and error preservation. Use recorded simulation time, without arrival-based alignment or automatic wind classification.
4. Update documentation and verify analytical conversions, command identities, missing/foreign records, UI episode selection, loading lifecycle and existing overview/export behavior.
Interfaces: append optional immutable controls data to Episode; extend scalar topic reader; add tab and comparison file/episode controls. No physics/publisher/schema/dependency changes.
Scope/defaults: primary flight follows the existing file/episode selection. Optional comparison uses native simulation seconds; labels distinguish files and recorded wind conditions. Never invent yaw angle commands, actual thrust or timestamps for unacknowledged RC packets. Preserve existing overview.
Verification: all 47 FlightLens checks passed, including quaternion axes/world-to-body rates, non-default RC channel mapping, acknowledged command timing, owner/episode isolation, missing/expired commands, Acro units, rejected/missing wind, heading wrapping, linked plots, comparison episode switching, async cancellation/failure preservation, and overview/export regressions. Both real MCAP recordings loaded and rendered with 4,435 and 15,309 matched command samples and 367 and 1,263 wind samples. Inspected /tmp/flight-lens-controls-wind.png and adjusted the wind legend to two columns. Both available recordings contain constant world-X wind of -4 m/s; no calm run was present.
Status: Complete; implemented, verified and committed.
Implementation commit: e3e9b3bf82a90efbcc0f21b8b2dba142173cbf85 (flight_lens).
