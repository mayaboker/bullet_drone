# Target contact event

Status: Pending
Implementation commit: Pending

Goal: Give the current SITL launcher a red-truck contact oracle for the target mission.

Implementation: Add a target scene collider and publish a validated, latched contact event through the existing renderer telemetry endpoint. Do not expose physics feedback as an App LOS input.

Interfaces: Target-scene launcher option and target-contact ZeroMQ topic.

Verification: Collider contact/near-miss tests and launcher integration.

Verification outcome: Target collider and image-transport focused tests passed. Renderer build/export and isolated camera transport passed. Live launcher check could not start because another Betaflight SITL already owns port 5761.

Scope/defaults: Target enabled only for target-mission launch; existing launcher path stays unchanged by default.
