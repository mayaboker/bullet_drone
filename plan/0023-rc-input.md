# 18-channel RC interface migration

Status: Completed
Implementation commit: cd5d4497bc270373af3596843f3e3218e74a4d20

## Goal and scope
Replace the public joystick boundary with RcInput/RcSimulation in Bullet Drone
and migrate Drone Lab and library examples. Preserve application cycle ownership,
read-only feedback, physics, Godot UDP and MCAP service. Commit and push authorized after implementation verification.

## Steps and interfaces
1. Immutable 18 integer channels, 1000..2000, AETR1234. Configurable arm/mode
   channels default CH5/CH6, high >=1500 arms/selects angle. Safe centered default
   frame with low throttle/AUX. Validated YAML/API RC settings and shared encoder.
2. Decode RC within SoftwareRc; angle roll/pitch limit 45 degrees, yaw body rate;
   acro all body rates scaled by internal limits, throttle by vehicle capacity.
   Add optional internal SI yaw-rate override preserving legacy SI heading.
3. Migrate simulation, contracts, local velocity/controller heading tracking
   (wrapped error gain 4/s, measured yaw for force conversion), library examples,
   tests and trace fields. Clamp calculated outputs, round to integer channels;
   reject invalid input before advancing physics. Remove old joystick API.
4. Update interface/flow docs and guidance. Validate all changed Mermaid blocks.

## Verification
Both full suites; channel validation/mapping/scaling/rounding; mixed angle/yaw
control and acro; lifecycle/disarm/mode/reset/failure behavior; actual headless
flights with tolerance-based arrival/landing checks; retained Godot checks;
Mermaid real parser/render and visual inspection, lock and whitespace checks.

## Defaults
No IO transport, failsafe, expo, deadband or recording topics. mcap_bug unchanged.
Preserve unrelated untracked files. Integer quantization may alter flight times.

## Outcome
Implemented RcInput, RcSettings, RcCodec, SoftwareRc and RcSimulation; removed
the old joystick public API and migrated both projects and the library examples.
The internal angle command supports explicit yaw-rate override; waypoint heading
tracking is an outer wrapped-error controller using measured heading. Configuration
permutes AETR within CH1..4 and assigns distinct arm/mode switches within CH5..18
so every default low-AUX frame remains disarmed.

Verification passed:
- Bullet Drone full suite: 298 tests, including actual hover/gate/control-chain
  trajectories and angle/acro RC turn-rate/neutral-stop physics checks.
- Drone Lab full suite: 51 tests, including six targets, landing/disarm, offset
  home, shared custom RC channel mapping/thresholds/angle scale and cleanup.
- Headless Drone Lab CLI: six settled targets, landed/disarmed at 29.025 simulated
  seconds, final position (-0.002736, 0.002741, 0.013490) m.
- Godot registry/coordinate, two-view UDP/grid/staleness smoke and actual RC flight
  viewer/landing checks; inspected the flight screenshot.
- All 11 Mermaid diagrams across affected files parsed/rendered with Mermaid
  11.17.2; inspected every generated image.
- Locked dependency checks in both projects, local Markdown links and whitespace.

No dependency changes. mcap_bug remains unchanged and the unrelated untracked
Zenoh document was preserved. The user subsequently requested commit and push;
the actual implementation hash is recorded above in a separate metadata commit.
