"""Physics observation adapter for the optional independent mcap_bug service."""

from loguru import logger

from bullet_drone.config import ConfigurationError
from bullet_drone.models import DroneObservation
from bullet_drone.telemetry.topics import (
    GROUND_TRUTH_SCHEMA, GROUND_TRUTH_TOPIC, SENSORS_SCHEMA, SENSORS_TOPIC,
)


def create_mcap_recorder(path, **kwargs):
    """Load the optional dependency only when explicitly requested."""
    try:
        from mcap_bug import McapRecorder
    except ImportError as exc:
        raise ConfigurationError("MCAP recording requires the telemetry extra: uv sync --extra telemetry") from exc
    return McapRecorder(path, **kwargs)


class McapObservationRecorder:
    """Automatically add physics topics and submit optional caller data atomically.

    Configure/start before acquiring physics resources. reset/consume implement
    the observation-consumer lifecycle; record_observation also accepts samples
    built by an application adapter. No command path is introduced here.
    """

    def __init__(self, recorder):
        self.recorder = recorder
        self.ground_truth_topic = recorder.register_topic(GROUND_TRUTH_TOPIC, GROUND_TRUTH_SCHEMA)
        self.sensors_topic = recorder.register_topic(SENSORS_TOPIC, SENSORS_SCHEMA)
        self._reported_error = None

    def start(self) -> None:
        try:
            self.recorder.start()
        except (RuntimeError, OSError, ValueError) as exc:
            raise ConfigurationError(f"Cannot start MCAP recording: {exc}") from exc

    def reset(self, observation: DroneObservation) -> None:
        self.record_observation(observation)

    def consume(self, observation: DroneObservation) -> None:
        self.record_observation(observation)

    def record_observation(self, observation: DroneObservation, extras=()) -> bool:
        from mcap_bug import FrameIdentity
        state = observation.ground_truth
        identity = FrameIdentity(state.episode_id, state.step_index, round(state.simulation_time_s * 1e9))
        physics = self.ground_truth_topic.sample({
            "position_m": state.position_m, "orientation_xyzw": state.orientation_xyzw,
            "linear_velocity_m_s": state.linear_velocity_m_s,
            "angular_velocity_rad_s": state.angular_velocity_rad_s,
            "rotor_speeds_rad_s": state.rotor_speeds_rad_s,
        })
        admitted = self.recorder.submit_frame(identity, (physics, self.sensors_topic.sample(observation.sensors), *extras))
        if not admitted:
            error = self.recorder.statistics.error
            if error is not None and error != self._reported_error:
                self._reported_error = error
                logger.error("MCAP recording disabled; physics continues: {}", error)
        return admitted

    @property
    def statistics(self):
        return self.recorder.statistics

    def close(self) -> None:
        self.recorder.close()
        stats = self.recorder.statistics
        if not stats.complete:
            logger.warning("MCAP recording incomplete: {} dropped frames; {}",
                           stats.dropped_frames, stats.error or "see recorded gaps")
