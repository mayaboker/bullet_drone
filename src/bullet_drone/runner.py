"""Fixed-step orchestration, with optional wall-clock pacing."""

import time

from loguru import logger

from bullet_drone.contracts import SimulationEnvironment
from bullet_drone.models import DroneObservation


class SimulationRunner:
    def run(
        self, environment: SimulationEnvironment, max_steps: int,
        pace_wall_time: bool = False,
    ) -> DroneObservation:
        try:
            if type(max_steps) is not int or max_steps <= 0:
                raise ValueError("max_steps must be a positive integer")
            observation = environment.reset()
            start = time.monotonic()
            for _ in range(max_steps):
                observation = environment.step()
                if pace_wall_time:
                    remaining = start + observation.ground_truth.simulation_time_s - time.monotonic()
                    if remaining > 0:
                        time.sleep(remaining)
        except BaseException:
            # Preserve the original failure/interrupt if cleanup also fails.
            try:
                environment.close()
            except Exception:
                logger.exception("Environment cleanup failed while handling a simulation failure")
            raise
        else:
            environment.close()
            return observation
