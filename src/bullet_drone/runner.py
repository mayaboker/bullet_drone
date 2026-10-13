"""Fixed-step orchestration, with optional wall-clock pacing."""

import time

from loguru import logger

from bullet_drone.contracts import CommandProvider, SimulationEnvironment
from bullet_drone.models import DroneObservation


class SimulationRunner:
    def run(
        self, environment: SimulationEnvironment, max_steps: int,
        pace_wall_time: bool = False,
        command_provider: CommandProvider | None = None,
    ) -> DroneObservation:
        try:
            if type(max_steps) is not int or max_steps <= 0:
                raise ValueError("max_steps must be a positive integer")
            observation = environment.reset()
            if command_provider is not None:
                command_provider.reset(observation)
            start = time.monotonic()
            for _ in range(max_steps):
                if command_provider is None:
                    observation = environment.step()
                else:
                    observation = environment.step(command_provider.command(observation))
                if pace_wall_time:
                    remaining = start + observation.ground_truth.simulation_time_s - time.monotonic()
                    if remaining > 0:
                        time.sleep(remaining)
        except BaseException:
            # Attempt every cleanup; preserve the original failure/interrupt.
            for resource in (command_provider, environment):
                if resource is not None:
                    try:
                        resource.close()
                    except BaseException:
                        logger.exception("Simulation resource cleanup failed while handling a failure")
            raise
        else:
            failure = None
            for resource in (command_provider, environment):
                if resource is not None:
                    try:
                        resource.close()
                    except BaseException as exc:
                        if failure is None:
                            failure = exc
                        else:
                            failure.add_note(f"Additional resource cleanup failure: {exc}")
            if failure is not None:
                raise failure
            return observation
