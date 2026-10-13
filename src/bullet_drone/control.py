"""Open-loop demonstration command sources; no feedback controller yet."""

from bullet_drone.commands import RotorCommand, WrenchCommand
from bullet_drone.config import ConfigurationError
from bullet_drone.mixer import MotorMixer
from bullet_drone.models import DroneObservation, Vector3


class HoverCommandProvider:
    def __init__(self, mixer: MotorMixer, mass_kg: float, gravity_m_s2: Vector3) -> None:
        if gravity_m_s2[0] != 0 or gravity_m_s2[1] != 0 or gravity_m_s2[2] >= 0:
            raise ConfigurationError("Hover mode requires downward vertical gravity")
        self.allocation = mixer.mix(WrenchCommand(mass_kg * -gravity_m_s2[2]))

    def command(self, observation: DroneObservation) -> RotorCommand:
        state = observation.ground_truth
        return RotorCommand(self.allocation.speeds_rad_s, state.episode_id, state.step_index + 1)
