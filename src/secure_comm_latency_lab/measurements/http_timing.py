"""HTTP response-time measurement."""

from __future__ import annotations

import time
from typing import Mapping

from secure_comm_latency_lab.models import MeasurementResult


def measure_http_timing(
    *,
    experiment_name: str,
    path_name: str,
    network_profile: str,
    url: str,
    timeout_seconds: float,
    proxies: Mapping[str, str] | None = None,
    raw_context: dict[str, object] | None = None,
) -> MeasurementResult:
    """Measure HTTP response time with requests."""
    raw: dict[str, object] = {"proxies_enabled": proxies is not None, **(raw_context or {})}
    try:
        import requests
    except ImportError:
        return MeasurementResult(
            experiment_name=experiment_name,
            path=path_name,
            network_profile=network_profile,
            measurement_type="http_timing",
            target=url,
            success=False,
            error="Python package 'requests' is not installed",
            raw=raw,
        )

    start = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout_seconds, proxies=dict(proxies or {}))
        elapsed_ms = (time.perf_counter() - start) * 1000.0
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return MeasurementResult(
            experiment_name=experiment_name,
            path=path_name,
            network_profile=network_profile,
            measurement_type="http_timing",
            target=url,
            success=False,
            latency_ms=elapsed_ms,
            error=str(exc),
            raw=raw,
        )

    return MeasurementResult(
        experiment_name=experiment_name,
        path=path_name,
        network_profile=network_profile,
        measurement_type="http_timing",
        target=url,
        success=True,
        latency_ms=elapsed_ms,
        status_code=response.status_code,
        raw={
            **raw,
            "requests_elapsed_ms": response.elapsed.total_seconds() * 1000.0,
            "response_bytes": len(response.content),
        },
    )
