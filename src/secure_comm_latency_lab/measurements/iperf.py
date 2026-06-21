"""iperf3 throughput measurement."""

from __future__ import annotations

import json

from secure_comm_latency_lab.models import MeasurementResult
from secure_comm_latency_lab.utils.commands import command_available, run_command


def _extract_iperf_metrics(data: dict[str, object], protocol: str) -> tuple[float | None, float | None, float | None]:
    end = data.get("end")
    if not isinstance(end, dict):
        return None, None, None

    candidates: list[object]
    if protocol == "udp":
        candidates = [end.get("sum"), end.get("sum_received"), end.get("sum_sent")]
    else:
        candidates = [end.get("sum_received"), end.get("sum_sent"), end.get("sum")]

    summary = next((candidate for candidate in candidates if isinstance(candidate, dict)), None)
    if summary is None:
        return None, None, None

    bits_per_second = summary.get("bits_per_second")
    throughput_mbps = (
        float(bits_per_second) / 1_000_000.0 if isinstance(bits_per_second, int | float) else None
    )
    jitter_ms = summary.get("jitter_ms")
    lost_percent = summary.get("lost_percent")
    return (
        throughput_mbps,
        float(jitter_ms) if isinstance(jitter_ms, int | float) else None,
        float(lost_percent) if isinstance(lost_percent, int | float) else None,
    )


def measure_iperf3(
    *,
    experiment_name: str,
    path_name: str,
    network_profile: str,
    host: str,
    port: int,
    duration_seconds: int,
    protocol: str = "tcp",
    raw_context: dict[str, object] | None = None,
) -> MeasurementResult:
    """Measure TCP or UDP throughput with iperf3 JSON output."""
    target = f"{host}:{port}"
    raw: dict[str, object] = {"command": "iperf3", **(raw_context or {})}
    if not command_available("iperf3"):
        return MeasurementResult(
            experiment_name=experiment_name,
            path=path_name,
            network_profile=network_profile,
            measurement_type="iperf3",
            target=target,
            success=False,
            error="Optional tool 'iperf3' is not available on PATH",
            raw=raw,
        )

    command = ["iperf3", "-J", "-c", host, "-p", str(port), "-t", str(duration_seconds)]
    if protocol == "udp":
        command.append("-u")

    result = run_command(command, timeout_seconds=duration_seconds + 10)
    try:
        data = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        data = {}

    throughput_mbps, jitter_ms, packet_loss_percent = _extract_iperf_metrics(data, protocol)
    error = None
    if not result.ok:
        error = result.stderr.strip() or data.get("error") if isinstance(data, dict) else None
        error = str(error or "iperf3 failed")

    return MeasurementResult(
        experiment_name=experiment_name,
        path=path_name,
        network_profile=network_profile,
        measurement_type="iperf3",
        target=target,
        success=result.ok,
        throughput_mbps=throughput_mbps,
        jitter_ms=jitter_ms,
        packet_loss_percent=packet_loss_percent,
        error=error,
        raw={**raw, "args": list(result.args), "returncode": result.returncode},
    )
