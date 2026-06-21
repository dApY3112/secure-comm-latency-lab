"""Shared data models for measurement records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now_iso() -> str:
    """Return a stable UTC timestamp string for JSONL records."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class MeasurementResult(BaseModel):
    """Stable schema for one measurement event."""

    model_config = ConfigDict(extra="forbid")

    timestamp_utc: str = Field(default_factory=utc_now_iso)
    experiment_name: str
    path: str
    network_profile: str = "baseline"
    measurement_type: str
    target: str
    success: bool
    latency_ms: float | None = None
    throughput_mbps: float | None = None
    jitter_ms: float | None = None
    packet_loss_percent: float | None = None
    status_code: int | None = None
    error: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    def to_json_line(self) -> str:
        """Serialize the result as one JSONL line."""
        return self.model_dump_json() + "\n"


def unsupported_result(
    *,
    experiment_name: str,
    path: str,
    network_profile: str,
    measurement_type: str,
    target: str,
    reason: str,
    raw: dict[str, Any] | None = None,
) -> MeasurementResult:
    """Build a schema-compatible record for unsupported safe measurements."""
    return MeasurementResult(
        experiment_name=experiment_name,
        path=path,
        network_profile=network_profile,
        measurement_type=measurement_type,
        target=target,
        success=False,
        error=reason,
        raw=raw or {},
    )
