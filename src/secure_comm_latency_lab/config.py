"""Experiment configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator


class ExperimentSettings(BaseModel):
    """Top-level experiment metadata."""

    model_config = ConfigDict(extra="forbid")

    name: str
    repetitions: int = Field(ge=1, le=10000)
    output_dir: Path = Path("data/raw")
    random_seed: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Keep file-friendly experiment names."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("experiment.name must not be empty")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if any(char not in allowed for char in cleaned):
            raise ValueError("experiment.name may contain only letters, numbers, '_' and '-'")
        return cleaned


class TargetConfig(BaseModel):
    """Targets that the user owns or has permission to test."""

    model_config = ConfigDict(extra="forbid")

    http_url: HttpUrl
    iperf_host: str
    iperf_port: int = Field(default=5201, ge=1, le=65535)


class DirectPathConfig(BaseModel):
    """Direct baseline path configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True


class WireGuardPathConfig(BaseModel):
    """WireGuard measurement mode configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    interface: str = "wg0"
    notes: str | None = None


class TorPathConfig(BaseModel):
    """Tor SOCKS proxy measurement mode configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    socks_proxy: str = "socks5h://127.0.0.1:9050"
    control_port: int = Field(default=9051, ge=1, le=65535)
    collect_circuit_metadata: bool = False

    @field_validator("socks_proxy")
    @classmethod
    def validate_socks_proxy(cls, value: str) -> str:
        """Require a SOCKS proxy URI for Tor HTTP timing."""
        if not value.startswith(("socks5://", "socks5h://")):
            raise ValueError("Tor socks_proxy must start with socks5:// or socks5h://")
        return value


class PathConfigs(BaseModel):
    """All path configurations."""

    model_config = ConfigDict(extra="forbid")

    direct: DirectPathConfig = Field(default_factory=DirectPathConfig)
    wireguard: WireGuardPathConfig = Field(default_factory=WireGuardPathConfig)
    tor: TorPathConfig = Field(default_factory=TorPathConfig)

    def enabled_names(self) -> list[str]:
        """Return names of paths enabled for this experiment."""
        names: list[str] = []
        if self.direct.enabled:
            names.append("direct")
        if self.wireguard.enabled:
            names.append("wireguard")
        if self.tor.enabled:
            names.append("tor")
        return names


class PingMeasurementConfig(BaseModel):
    """ICMP ping measurement settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    count: int = Field(default=5, ge=1, le=100)
    timeout_seconds: float = Field(default=10.0, gt=0, le=300)


class HttpTimingMeasurementConfig(BaseModel):
    """HTTP response-time measurement settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    timeout_seconds: float = Field(default=10.0, gt=0, le=300)


class IperfMeasurementConfig(BaseModel):
    """iperf3 throughput measurement settings."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    duration_seconds: int = Field(default=5, ge=1, le=3600)
    protocol: Literal["tcp", "udp"] = "tcp"


class MeasurementConfigs(BaseModel):
    """All measurement settings."""

    model_config = ConfigDict(extra="forbid")

    ping: PingMeasurementConfig = Field(default_factory=PingMeasurementConfig)
    http_timing: HttpTimingMeasurementConfig = Field(default_factory=HttpTimingMeasurementConfig)
    iperf3: IperfMeasurementConfig = Field(default_factory=IperfMeasurementConfig)


class NetworkProfile(BaseModel):
    """A network-condition label and optional tc netem parameters."""

    model_config = ConfigDict(extra="forbid")

    name: str
    delay_ms: float = Field(default=0.0, ge=0)
    jitter_ms: float = Field(default=0.0, ge=0)
    loss_percent: float = Field(default=0.0, ge=0, le=100)
    bandwidth_mbit: float | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def validate_profile_name(cls, value: str) -> str:
        """Keep profile labels stable for file and plot names."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("profile name must not be empty")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if any(char not in allowed for char in cleaned):
            raise ValueError("profile name may contain only letters, numbers, '_' and '-'")
        return cleaned


class NetworkConditionsConfig(BaseModel):
    """Optional Linux tc netem condition labels."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    interface: str = "eth0"
    profiles: list[NetworkProfile] = Field(
        default_factory=lambda: [NetworkProfile(name="baseline")]
    )


class LabConfig(BaseModel):
    """Complete experiment configuration."""

    model_config = ConfigDict(extra="forbid")

    experiment: ExperimentSettings
    targets: TargetConfig
    paths: PathConfigs = Field(default_factory=PathConfigs)
    measurements: MeasurementConfigs = Field(default_factory=MeasurementConfigs)
    network_conditions: NetworkConditionsConfig = Field(default_factory=NetworkConditionsConfig)

    @field_validator("paths")
    @classmethod
    def validate_at_least_one_path(cls, value: PathConfigs) -> PathConfigs:
        """Require at least one enabled path."""
        if not value.enabled_names():
            raise ValueError("at least one communication path must be enabled")
        return value

    def active_profiles(self) -> list[NetworkProfile]:
        """Return network profile labels used for measurement grouping."""
        if self.network_conditions.enabled:
            return self.network_conditions.profiles
        return [NetworkProfile(name="baseline")]


def load_config(path: str | Path) -> LabConfig:
    """Load a YAML experiment config and validate it with Pydantic."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config file {config_path} must contain a YAML mapping")
    try:
        return LabConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid config file {config_path}: {exc}") from exc
