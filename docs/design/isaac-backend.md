# Optional Isaac backend

The persistent launcher defaults to PyBullet physics and the Godot renderer. `--physics-backend isaac` selects Alice's `IsaacPhysics`; `--renderer-backend isaac` selects `IsaacRenderer`. The renderer can run headless and load a USD world through `--isaac-headless` and `--world`.

The launcher still builds one `SimulationConfig`, including target-scene initial position and yaw, GPS sensor settings, and SITL control settings. Both physics backends feed the same `DroneEnvironment` and Betaflight bridge. The simulation Start, Stop, and Reset service remains the lifecycle owner; Reset restarts the selected physics backend and SITL. The older terminal `reset` shortcut is omitted because it bypassed this service and its state transitions.

Isaac physics currently reports no target or terrain contact. A target-hit mission can track visually, but Isaac contact cannot confirm a hit yet. The PyBullet target scene retains contact detection.
