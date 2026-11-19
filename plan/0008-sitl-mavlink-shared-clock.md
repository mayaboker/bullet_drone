# SITL MAVLink shared boot clock

Goal: stop MAVLink ATTITUDE stamps from mapping into the future after TIMESYNC, allowing Bullet App LOS acquisition.

Implementation: extend the pinned GPS SITL patch so `millis64()` derives from the same scaled `micros64()` accumulator as TIMESYNC. Send 64-bit microseconds in TIMESYNC to avoid the 32-bit `micros()` wrap. Rebuild the GPS/MAVLink SITL binary, restart the target stack, and update the bridge documentation and Bullet App investigation report with the outcome.

Interfaces: MAVLink message IDs and formats stay the same. TIMESYNC `tc1` and ATTITUDE `time_boot_ms` share one boot clock; the installed SITL binary changes.

Verification: apply-check the patch against the pinned clean source, build the GPS/MAVLink SITL binary, measure mapped ATTITUDE ages with live 50 Hz MAVLink telemetry, and run an automatic target flight. Stop Bullet App after the run and record any separate mission failure.

Scope/defaults: preserve the existing uncommitted Bullet App changes. Restart the running target stack to load the rebuilt binary. No commit or push requested.

Status: Implemented. The patch applied to the clean pinned source, the GPS/MAVLink binary built, and the source checkout was restored clean. The rebuilt stack produced 429 mapped ATTITUDE samples aged 5.8–26.8 ms with no future samples. Bullet App then reached LOS commit, reported a hit, disarmed, and exited successfully with zero ATTITUDE mapping rejections. The App process is stopped. Implementation commit: Pending (no commit requested).
