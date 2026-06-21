"""Optional traceroute helper for manual diagnostics."""

from __future__ import annotations

import platform

from secure_comm_latency_lab.models import MeasurementResult
from secure_comm_latency_lab.utils.commands import command_available, run_command


def measure_traceroute(
    *,
    experiment_name: str,
    path_name: str,
    network_profile: str,
    host: str,
    timeout_seconds: float = 30.0,
) -> MeasurementResult:
    """Run traceroute/tracert as a non-core diagnostic measurement."""
    system = platform.system().lower()
    command_name = "tracert" if system == "windows" else "traceroute"
    if not command_available(command_name):
        return MeasurementResult(
            experiment_name=experiment_name,
            path=path_name,
            network_profile=network_profile,
            measurement_type="traceroute",
            target=host,
            success=False,
            error=f"Optional tool '{command_name}' is not available on PATH",
            raw={"command": command_name},
        )

    command = [command_name, host]
    result = run_command(command, timeout_seconds=timeout_seconds)
    return MeasurementResult(
        experiment_name=experiment_name,
        path=path_name,
        network_profile=network_profile,
        measurement_type="traceroute",
        target=host,
        success=result.ok,
        error=None if result.ok else result.stderr.strip() or "traceroute failed",
        raw={
            "command": command_name,
            "args": list(result.args),
            "returncode": result.returncode,
            "stdout": result.stdout[:4000],
        },
    )
