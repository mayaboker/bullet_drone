import pytest

from bullet_drone.config import DroneSettings, SimulationConfig, SimulationSettings


@pytest.fixture
def config():
    return SimulationConfig(
        SimulationSettings(timestep_s=1 / 240, max_steps=1200, gravity_m_s2=(0, 0, -9.81)),
        DroneSettings(mass_kg=1, initial_position_m=(0, 0, 1)),
    )
