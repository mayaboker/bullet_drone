# Repair FlightLens MCAP frame lookup

Goal: restore exact recorded event image decoding.
Steps: reproduce against existing recordings and reader tests; use the installed MCAP reader API parameter names and its exclusive end bound in frame lookup and MP4 iteration; run FlightLens checks and decode real recorded frames.
Interface changes: none; retain exact timestamp/sequence identity matching.
Scope/defaults: FlightLens reader and identical MP4 reader call only; no recordings modified, dependency changes or automatic commits.
Verification: reproduced the TypeError with reader tests and both existing recordings. After repair, all 36 FlightLens tests passed, including offscreen GUI preview and MP4 checks. Decoded first/last event frames from both real recordings (640 x 480; 1,110 and 3,829 frame references). Original recordings unchanged.
Status: Complete; implemented, verified and committed.
Implementation commit: d6e87440a15d353749764ef422075cab0cab44c0 (flight_lens initial repository commit).
