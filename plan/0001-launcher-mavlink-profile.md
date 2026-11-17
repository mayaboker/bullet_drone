# Launcher MAVLink profile

Status: Implemented; focused tests and two-process SITL flight passed. Implementation commit: Pending (no commit requested).

Goal: Let a separately started controller read MAVLink telemetry from the launcher's single Betaflight SITL.

Implementation: Select the existing MAVLink-enabled SITL profile and reserve its UART2 TCP port. Keep the launcher physics and renderer lifecycle unchanged.

Interface: MAVLink telemetry is available on TCP 5762 while MSP RC remains on TCP 5761.

Verification: Three focused launcher tests passed. The separate app connected to the single SITL on MSP 5761 and MAVLink 5762 and completed its flight. No commit requested.
