from bullet_drone.config import ControlSettings, DroneSettings, SimulationConfig, SimulationSettings
from bullet_drone.physics import PyBulletPhysics
from bullet_drone.vehicle import load_racer_parameters
from math import pi, sqrt
import pytest


def test_target_contact_is_opt_in_and_requires_overlap():
    config = SimulationConfig(SimulationSettings(1 / 240, 100, (0., 0., -9.81), gui=False),
                              DroneSettings(1.0, (0., 0., 0.1)), control=ControlSettings('internal'))
    with_target = PyBulletPhysics(config, load_racer_parameters(), target_scene=True)
    try:
        with_target.reset()
        assert not with_target.target_contact()
        p = with_target._p
        p.resetBasePositionAndOrientation(with_target._body, [50., 0., 5.55], [0., 0., 0., 1.],
                                          physicsClientId=with_target._client)
        with_target.step()
        assert with_target.target_contact()
    finally:
        with_target.close()


def test_physics_applies_configured_starting_yaw():
    config = SimulationConfig(SimulationSettings(1 / 240, 100, (0., 0., -9.81), gui=False),
                              DroneSettings(1.0, (0., 0., 0.1), initial_yaw_rad=pi / 2),
                              control=ControlSettings('internal'))
    physics = PyBulletPhysics(config, load_racer_parameters())
    try:
        assert physics.reset().orientation_xyzw == pytest.approx((0., 0., sqrt(0.5), sqrt(0.5)))
    finally:
        physics.close()
