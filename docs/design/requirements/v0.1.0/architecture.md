# Architecture and integration requirements: 0.1.0

Status: **Draft**  
[Version overview](index.md) · [Architecture](../../architecture.md)

| ID | Requirement | Proposed acceptance evidence |
| --- | --- | --- |
| ARC-001 | Keep physics, rendering, recording, plotting, and orchestration responsibilities separate using the documented SOLID principles. | Dependency review confirms the runner uses contracts and physics imports no display, plotting, or recording implementation. |
| ARC-002 | Make physics the sole authority for physical state and simulation time. | Rendering and plotting do not mutate authoritative state or change a trajectory for an identical command sequence. |
| ARC-003 | Support a separate renderer process with its own client and a scene mirror driven by snapshots. | A renderer process receives scene setup and snapshots, produces matching frames, and owns no authoritative physics handles. |
| ARC-004 | Support attached and tracking camera modes through a camera configuration interface. | Known drone poses produce the expected camera transforms for both modes. |
| ARC-005 | Expose rendered image buffers through a frame delivery interface usable by a separate display or recording consumer. | A consumer receives dimensions, pixel format, snapshot identity, and valid buffers without connecting to physics. |
| ARC-006 | Include sufficient scene data to render movable objects beyond the drone and maintain scene revision consistency. | Changing a visible object pose is reflected in the image; an unknown revision triggers scene loading or an explicit rejection. |
| ARC-007 | Decouple physics step rate from render and plot refresh rates using bounded consumer delivery. | A slow visual consumer causes counted visual update drops while completed physics steps remain unchanged. |
| ARC-008 | Make telemetry overflow and recording failures explicit, with a lossless offline policy and mandatory-recorder failure handling. | A full recording queue pauses at a step boundary without dropping samples; required recorder failure stops the run and reports incompleteness. |
| ARC-009 | Correlate commands, telemetry, snapshots, and frames by episode and step identity. | After reset, delayed old-episode observations are rejected and new frames correlate to the new episode. |
| ARC-010 | Isolate optional rendering and live plotting failures from physics while reporting them. | Terminating a renderer or failing a plot consumer produces a reported consumer failure; a headless run can continue. |
| ARC-011 | Keep contracts independent of backend and transport details. | A test double can replace an adapter without changing runner behavior; no client IDs, raw pointers, or library-owned objects appear in contracts. |

Process transport, queue capacities, shutdown timeout, image encodings, and buffer release protocol must be specified in a later design revision before integration acceptance.
