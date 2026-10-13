import copy
import subprocess
import sys

import pytest
import yaml

from bullet_drone.cli import CliOptions, CliParser
from bullet_drone.config import ConfigurationError, YamlConfigLoader


def valid_data():
    return {
        "simulation": {"timestep_s": 1 / 240, "max_steps": 240, "gravity_m_s2": [0, 0, -9.81]},
        "drone": {"mass_kg": 1, "initial_position_m": [0, 0, 1]},
    }


def write_config(tmp_path, data):
    path = tmp_path / "simulation.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def test_config_and_cli_helper(tmp_path):
    path = write_config(tmp_path, valid_data())
    options = CliParser().parse(["--config", str(path)])
    assert options == CliOptions(path)
    config = YamlConfigLoader().load(options.config_path)
    assert config.simulation.gui is False
    assert config.drone.initial_position_m == (0.0, 0.0, 1.0)


@pytest.mark.parametrize("section,key,value", [
    ("simulation", "timestep_s", 0),
    ("simulation", "timestep_s", -1),
    ("simulation", "timestep_s", True),
    ("simulation", "timestep_s", float("nan")),
    ("simulation", "timestep_s", float("inf")),
    ("simulation", "max_steps", 0),
    ("simulation", "max_steps", True),
    ("simulation", "max_steps", 1.5),
    ("simulation", "gui", "false"),
    ("simulation", "gravity_m_s2", [0, 0]),
    ("simulation", "gravity_m_s2", [0, False, -9.81]),
    ("simulation", "gravity_m_s2", [0, 0, float("inf")]),
    ("drone", "mass_kg", -1),
    ("drone", "mass_kg", "1"),
    ("drone", "initial_position_m", "0, 0, 1"),
    ("drone", "initial_position_m", [0, 0, float("nan")]),
    ("drone", "unknown", 1),
])
def test_invalid_values(tmp_path, section, key, value):
    data = valid_data()
    data[section][key] = value
    with pytest.raises(ConfigurationError):
        YamlConfigLoader().load(write_config(tmp_path, data))


@pytest.mark.parametrize("data", [None, [], {"simulation": []}, {**valid_data(), "extra": 1}])
def test_invalid_root_or_missing_fields(tmp_path, data):
    with pytest.raises(ConfigurationError):
        YamlConfigLoader().load(write_config(tmp_path, data))


def test_missing_and_malformed_yaml(tmp_path):
    data = copy.deepcopy(valid_data())
    del data["drone"]["mass_kg"]
    with pytest.raises(ConfigurationError, match="missing"):
        YamlConfigLoader().load(write_config(tmp_path, data))
    path = tmp_path / "bad.yaml"
    path.write_text("simulation: [")
    with pytest.raises(ConfigurationError, match="Cannot read YAML"):
        YamlConfigLoader().load(path)
    with pytest.raises(ConfigurationError, match="Cannot read YAML"):
        YamlConfigLoader().load(tmp_path / "absent.yaml")


@pytest.mark.parametrize("arguments,expected", [(["--help"], 0), ([], 2), (["--unknown"], 2)])
def test_module_help_and_usage(arguments, expected):
    result = subprocess.run(
        [sys.executable, "-m", "bullet_drone.main", *arguments],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == expected
    assert "pybullet build time" not in result.stderr
    assert "Starting" not in result.stderr


def test_main_import_has_no_startup_side_effects():
    result = subprocess.run(
        [sys.executable, "-c", (
            "from loguru import logger; "
            "logger.add = logger.remove = lambda *a, **kw: (_ for _ in ()).throw(AssertionError('logging configured')); "
            "import bullet_drone.main; import sys; "
            "assert 'pybullet' not in sys.modules; assert not any(name == 'examples' or name.startswith('examples.') for name in sys.modules)"
        )], capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""



def test_simulation_config_rejects_legacy_flight_scenario(tmp_path):
    data = valid_data()
    assert not hasattr(YamlConfigLoader().load(write_config(tmp_path, data)), "flight")
    data["flight"] = {"mode": "hover"}
    with pytest.raises(ConfigurationError, match="unknown keys: flight"):
        YamlConfigLoader().load(write_config(tmp_path, data))
