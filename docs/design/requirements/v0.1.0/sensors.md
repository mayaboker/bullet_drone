# Sensor requirements: 0.1.0

Status: **Draft; separate milestone after the basic entry point**  
[Version overview](index.md) · [Sensor design](../../sensors.md)

| ID | Requirement | Proposed acceptance evidence |
| --- | --- | --- |
| SEN-001 | Separate ground truth from simulated sensor measurements in `DroneObservation`. | Sensor sampling and changes to noise configuration do not change a physics trajectory. |
| SEN-002 | Provide separate IMU, barometer, and rangefinder classes in a sensors package through a small shared lifecycle contract. | Each model can be exercised independently using ground truth and narrow query substitutes. |
| SEN-003 | Produce IMU specific force and angular velocity in a declared sensor frame. | Level rest, free fall, known rotation, and initial unavailable acceleration have the expected outputs. |
| SEN-004 | Produce noisy barometric pressure and altitude derived using declared atmosphere/reference parameters. | Height changes pressure correctly; zero-noise conversions round-trip; invalid pressure is reported. |
| SEN-005 | Measure range using a read-only scene ray query with mounting direction and operating limits. | Known obstacles, tilted beams, misses, below-minimum hits, and self-hit exclusion behave as specified. |
| SEN-006 | Support configured fixed bias and per-sample Gaussian noise with independent reproducible random streams. | Zero-noise output is ideal; seeded sequences repeat and remain unchanged when another sensor is added or disabled. |
| SEN-007 | Sample on configurable simulation-step schedules and preserve individual measurement timestamps. | Mixed-rate checks verify sampling intervals, cached readings, disabled sensors, and episode reset. |
| SEN-008 | Publish immutable typed readings with identity, time, units, frame, and explicit validity. | Old records do not mutate; consumers distinguish unavailable data and no return from valid zero measurements. |
| SEN-009 | Keep sensors independent of renderer and backend-specific handles. | Headless tests use a scene-query substitute and require no display or sensor-side PyBullet imports. |

Concrete profiles and numerical acceptance tolerances remain to be specified before implementation.
