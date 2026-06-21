"""ICMP ping measurement."""

from __future__ import annotations

import math
import platform
import re

from secure_comm_latency_lab.models import MeasurementResult
from secure_comm_latency_lab.utils.commands import command_available, run_command

_PACKET_LOSS_RE = re.compile(r"(\d+(?:\.\d+)?)%\s*(?:packet )?loss", re.IGNORECASE)
_LINUX_RTT_RE = re.compile(
    r"(?:rtt|round-trip).*?=\s*([\d.]+)/([\d.]+)/([\d.]+)(?:/([\d.]+))?"
)
_WINDOWS_AVG_RE = re.compile(r"Average\s*=\s*(\d+(?:\.\d+)?)ms", re.IGNORECASE)


def _build_ping_command(host: str, count: int, timeout_seconds: float) -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return ["ping", "-n", str(count), "-w", str(int(timeout_seconds * 1000)), host]
    if system == "darwin":
        return ["ping", "-c", str(count), "-W", str(int(timeout_seconds * 1000)), host]
    return ["ping", "-c", str(count), "-W", str(max(1, math.ceil(timeout_seconds))), host]


def _parse_packet_loss(output: str) -> float | None:
    match = _PACKET_LOSS_RE.search(output)
    if not match:
        return None
    return float(match.group(1))


def _parse_rtt(output: str) -> tuple[float | None, float | None]:
    match = _LINUX_RTT_RE.search(output)
    if match:
        avg_ms = float(match.group(2))
        jitter_ms = float(match.group(4)) if match.group(4) is not None else None
        return avg_ms, jitter_ms
    match = _WINDOWS_AVG_RE.search(output)
    if match:
        return float(match.group(1)), None
    return None, None


def measure_ping(
    *,
    experiment_name: str,
    path_name: str,
    network_profile: str,
    host: str,
    count: int,
    timeout_seconds: float = 10.0,
    raw_context: dict[str, object] | None = None,
) -> MeasurementResult:
    """Measure ICMP round-trip time and packet loss with the system ping tool."""
    raw = {"command": "ping", **(raw_context or {})}
    if not command_available("ping"):
        return MeasurementResult(
            experiment_name=experiment_name,
            path=path_name,
            network_profile=network_profile,
            measurement_type="ping",
            target=host,
            success=False,
            error="Optional tool 'ping' is not available on PATH",
            raw=raw,
        )

    command = _build_ping_command(host, count, timeout_seconds)
    result = run_command(command, timeout_seconds=max(timeout_seconds * count + 2, 5))
    output = "\n".join(part for part in [result.stdout, result.stderr] if part)
    packet_loss = _parse_packet_loss(output)
    latency_ms, jitter_ms = _parse_rtt(output)
    success = result.ok and (packet_loss is None or packet_loss < 100)

    return MeasurementResult(
        experiment_name=experiment_name,
        path=path_name,
        network_profile=network_profile,
        measurement_type="ping",
        target=host,
        success=success,
        latency_ms=latency_ms,
        jitter_ms=jitter_ms,
        packet_loss_percent=packet_loss,
        error=None if success else output.strip()[:1000] or "ping failed",
        raw={**raw, "args": list(result.args), "returncode": result.returncode},
    )
