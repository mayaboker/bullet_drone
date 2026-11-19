# View bbox MAVLink codec

Status: Implemented; focused and live checks passed
Implementation commit: Pending

Goal: Share a validated fid/bbox payload between Bullet App and Bullet View.

Implementation: Encode and decode a length-prefixed compact JSON dictionary for local MAVLink V2_EXTENSION message type 32768. Validate fid and optional pixel rectangle, including padded MAVLink payloads.

Interface: `bullet_simulation_protocol.view_bbox.encode_bbox`, `decode_bbox`, and `MESSAGE_TYPE`.

Verification: Four codec tests passed; a real pymavlink V2_EXTENSION round trip passed; live target stack showed the overlay.

Scope: No new port or renderer protocol change.

Verification outcome: Four codec tests and live target smoke passed. The broader bullet_drone suite has five unrelated failures in missing profile paths and an older position-square example.
