"""Base runner shared by direct, WireGuard, and Tor paths."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from secure_comm_latency_lab.config import LabConfig
from secure_comm_latency_lab.measurements.http_timing import measure_http_timing
from secure_comm_latency_lab.measurements.iperf import measure_iperf3
from secure_comm_latency_lab.measurements.ping import measure_ping
from secure_comm_latency_lab.models import MeasurementResult, unsupported_result


class BaseRunner:
    """Run enabled measurement types for one communication path."""

    path_name = "base"

    def __init__(self, config: LabConfig, network_profile: str = "baseline") -> None:
        self.config = config
        self.network_profile = network_profile

    def raw_context(self) -> dict[str, object]:
        """Return runner-specific metadata to attach to measurement records."""
        return {}

    def http_proxies(self) -> Mapping[str, str] | None:
        """Return optional HTTP proxies for this path."""
        return None

    def supports_ping(self) -> bool:
        """Return True when this path can run system ping as implemented."""
        return True

    def supports_iperf3(self) -> bool:
        """Return True when this path can run iperf3 as implemented."""
        return True

    def run_once(self) -> Iterable[MeasurementResult]:
        """Run each enabled measurement once and yield JSONL-ready records."""
        context = self.raw_context()
        experiment_name = self.config.experiment.name

        if self.config.measurements.ping.enabled:
            if self.supports_ping():
                yield measure_ping(
                    experiment_name=experiment_name,
                    path_name=self.path_name,
                    network_profile=self.network_profile,
                    host=self.config.targets.iperf_host,
                    count=self.config.measurements.ping.count,
                    timeout_seconds=self.config.measurements.ping.timeout_seconds,
                    raw_context=context,
                )
            else:
                yield unsupported_result(
                    experiment_name=experiment_name,
                    path=self.path_name,
                    network_profile=self.network_profile,
                    measurement_type="ping",
                    target=self.config.targets.iperf_host,
                    reason=f"{self.path_name} runner does not support ICMP ping",
                    raw=context,
                )

        if self.config.measurements.http_timing.enabled:
            yield measure_http_timing(
                experiment_name=experiment_name,
                path_name=self.path_name,
                network_profile=self.network_profile,
                url=str(self.config.targets.http_url),
                timeout_seconds=self.config.measurements.http_timing.timeout_seconds,
                proxies=self.http_proxies(),
                raw_context=context,
            )

        if self.config.measurements.iperf3.enabled:
            target = f"{self.config.targets.iperf_host}:{self.config.targets.iperf_port}"
            if self.supports_iperf3():
                yield measure_iperf3(
                    experiment_name=experiment_name,
                    path_name=self.path_name,
                    network_profile=self.network_profile,
                    host=self.config.targets.iperf_host,
                    port=self.config.targets.iperf_port,
                    duration_seconds=self.config.measurements.iperf3.duration_seconds,
                    protocol=self.config.measurements.iperf3.protocol,
                    raw_context=context,
                )
            else:
                yield unsupported_result(
                    experiment_name=experiment_name,
                    path=self.path_name,
                    network_profile=self.network_profile,
                    measurement_type="iperf3",
                    target=target,
                    reason=f"{self.path_name} runner does not support iperf3 through SOCKS",
                    raw=context,
                )
