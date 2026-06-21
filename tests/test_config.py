from pathlib import Path

import pytest

from secure_comm_latency_lab.config import LabConfig, load_config


def test_example_config_loads() -> None:
    config = load_config(Path("configs/example_experiment.yaml"))

    assert config.experiment.name == "local_secure_comm_latency_demo"
    assert config.experiment.repetitions == 3
    assert config.paths.enabled_names() == ["direct"]
    assert config.measurements.ping.enabled is True
    assert config.active_profiles()[0].name == "baseline"


def test_config_rejects_no_enabled_paths() -> None:
    with pytest.raises(ValueError):
        LabConfig.model_validate(
            {
                "experiment": {"name": "bad_demo", "repetitions": 1, "output_dir": "data/raw"},
                "targets": {"http_url": "http://127.0.0.1:8000", "iperf_host": "127.0.0.1"},
                "paths": {
                    "direct": {"enabled": False},
                    "wireguard": {"enabled": False},
                    "tor": {"enabled": False},
                },
            }
        )


def test_config_rejects_unsafe_experiment_name() -> None:
    with pytest.raises(ValueError):
        LabConfig.model_validate(
            {
                "experiment": {"name": "../bad", "repetitions": 1, "output_dir": "data/raw"},
                "targets": {"http_url": "http://127.0.0.1:8000", "iperf_host": "127.0.0.1"},
                "paths": {"direct": {"enabled": True}},
            }
        )
