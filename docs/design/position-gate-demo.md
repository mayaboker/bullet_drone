# Position-controlled gate-course example

Status: **Implemented and verified**

[Design menu](index.md) · [Implementation plan](../../plan/0012-position-gate-mission.md) · [Internal control](internal-flight-control.md) · [Godot world](godot-rendering.md)

## Run

```bash
uv run examples/position/main.py --headless
uv run examples/position/main.py --renderer godot --render-config configs/render-godot.yaml
```

Start Godot separately or select VS Code **Run Godot and 3 position drones**. This task launches the viewer and three independent mission processes using drone_1/2/3 and initial positions (0,0,0.015), (1.5,0.25,0.015), (3,0.5,0.015) m. The individual **Run position drone 1/2/3 with Godot** tasks are also available. **Run position gate mission** uses the PyBullet GUI. Existing hover tasks and examples retain their behavior.

The **Run Godot and 6 position drones** task also launches drones 4–6, each
with its own render profile and camera panel. The extra pads have XY positions
(0,-0.75), (1.5,-1), (3,-1.25) m, with initial Z=0.015 m. The original pads
and three-drone tasks are retained. Reflecting the original trio across
Y=-0.375 m produces this opposite-side group and a 0.75 m gap for the closest
pair. All lanes fit the gate corridor; six smaller, separately labeled landing
pads match the task coordinates. **Run position drone 4/5/6 with Godot** starts
these publishers individually. Scroll the preview panel stack for later IDs.

CLI options are `--headless`, `--renderer godot|pybullet|none`, `--render-config PATH`, and `--initial-position X Y Z`. No renderer option preserves GUI mode; headless and none run unpaced. Godot uses DIRECT physics and wall-time pacing. Argument/configuration failures return 2, runtime failures/timeouts 1, interruption 130, completion 0. Importing the entry point performs no work or logging setup.

## Route and landing

The mission records its home XY from the initial observation, settles disarmed for 0.5 s, then arms and takes off vertically to world Z=3 m. It holds its home Y lane and visits X=8,15,22 m: one meter beyond each gate at X=7,14,21 m. It returns via X=20,13,6 m and then home XY at 3 m. Yaw stays zero; return travel is backward. Every airborne arrival requires XYZ error <=0.12 m and total speed <=0.15 m/s continuously for 0.5 s. Losing either tolerance resets that dwell.

Landing begins only after settling above the original pad. The controller holds home XY while descending toward Z=0 with a 0.5 m/s descent limit. Touchdown requires height <=0.02 m, home XY error <=0.12 m and total speed <=0.05 m/s continuously for 0.5 s. It then disarms, waits one simulated second with motors off, and completes. Touchdown uses the existing flat-ground racer height threshold; it is not a contact sensor. A 180 s budget raises `PositionDemoTimeoutError` after resources close if unfinished.

Launches require X<6 m, |Y|<=1.3 m, and ground-level Z in [0,0.03] m, validated before acquiring physics/network resources. These conditions match the current visual gate corridor and leave clearance for the racer. Gates have a 3.5 m lateral opening and a 5 m upper frame. The mission constants match `flight_world.gd`'s `7 + index * 7` gate positions. Future scene changes must update the route together.

## Reusable position controller

`PositionController(altitude, position_pid, velocity_pid, max_tilt_rad)` belongs in `bullet_drone.controllers`. Its `input(target_position_m, position_m, velocity_m_s, dt_s, yaw_rad=0, descent_speed_limit_m_s=None)` returns armed `JoystickInput` in Angle mode. It has no episode, mission, joystick, physics or rendering ownership. Its immutable `last_output` exposes desired XYZ velocity, raw acceleration and joystick input for the separate [control-chain verification example](position-control-chain.md); reset clears it. `reset()` clears all horizontal and altitude PID histories.

The XY cascade uses the common scalar PID independently per axis: position error produces velocity in m/s, velocity error produces acceleration in m/s². Horizontal velocity magnitude is bounded so diagonal travel stays within the configured speed. The reused altitude controller produces requested world vertical force including gravity compensation. Horizontal force is mass times acceleration, scaled to satisfy the tilt limit relative to vertical force. Convert the resulting world-force direction to body-to-world ZYX roll/pitch for the requested absolute yaw; thrust magnitude includes horizontal and vertical components, clipped to vehicle capacity. This compensates the requested tilt; attitude tracking has transient lag. There is no force or gravity applied by the controller itself.

The example uses XY position Kp=0.8 s⁻¹, velocity Kp=2 s⁻¹, speed limit 1 m/s, per-axis acceleration limit 1.5 m/s², and total tilt limit 15°. Altitude and internal attitude/rate gains match the hover example. Feedback comes from immutable ground-truth world position/velocity. This is an ideal-model demonstration rather than a noisy navigation estimator or universal vehicle tuning.

## Composition and lifecycle

`examples/position` owns its CLI, composition and `PositionMission`, which implements the existing `HighLevelController` contract. The mission translates each position-controller output through `JoystickInterface.set_input()` and `command()`. The existing command provider handles arm gating, stabilization and mixing. Physics, actuator, propeller and runner contracts remain unchanged; no library code imports examples.

The mission validates episode, next-step identity, positive dt and nondecreasing simulation time before advancing. Reset restores timers, waypoints and controller state for the new episode/home. Close is idempotent and closes its owned joystick. The runner closes provider, physics and optional rendering consumers on completion, initialization/stepping/control failure, timeout and KeyboardInterrupt.

`run_position_demo()` returns immutable `PositionDemoResult`: final observation and transition records carrying phase, waypoint index, time and actual position. Phase transitions report diagnostics through Loguru; they are not a telemetry store.

## Boundaries and verification

Each drone owns an independent physics world. Gates and other Godot scenery are decorative; no inter-drone or gate collision, obstacle avoidance, path planner, wind or sensor estimator is included. The example actively closes XY position error and returns each drone to its own pad. The hover example remains a separate altitude-only scenario.

Tests verify world-force directions under different yaw headings, tilt/collective limits, PID reset and invalid-input rejection, joystick/episode lifecycle, interrupted arrival dwell, home alignment before landing, timeout/failure/interruption cleanup, and CLI/task behavior. Full real PyBullet trajectories for all six pads verify six gate-plane crossings per drone (outbound and return), inside opening clearances near 3 m, own-pad touchdown and zero final rotor speeds.

Verified complete mission durations are approximately 68.179 s, 65.179 s and
62.183 s from pads 1, 2 and 3 respectively. Each ended at Z≈0.01349 m with
XY landing error below 0.00001 m and all four rotor speeds zero. The complete
Python suite passes 240 tests. Three actual wall-time-paced Godot publishers
were run together on an isolated test port; all completed and the live course
view was captured and visually inspected at `/tmp/bullet-drone-position-course.png`.
