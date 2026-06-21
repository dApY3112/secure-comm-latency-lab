"""Tor SOCKS proxy path measurement mode."""

from __future__ import annotations

from collections.abc import Mapping

from secure_comm_latency_lab.runners.base import BaseRunner


class TorRunner(BaseRunner):
    """Run HTTP timing through a local Tor SOCKS proxy."""

    path_name = "tor"

    def http_proxies(self) -> Mapping[str, str]:
        """Route HTTP(S) requests through the configured SOCKS proxy."""
        proxy = self.config.paths.tor.socks_proxy
        return {"http": proxy, "https": proxy}

    def supports_ping(self) -> bool:
        """ICMP ping is not supported through a SOCKS proxy."""
        return False

    def supports_iperf3(self) -> bool:
        """iperf3 is not routed through Tor SOCKS by this safe implementation."""
        return False

    def raw_context(self) -> dict[str, object]:
        """Collect optional local Tor metadata when explicitly enabled."""
        tor_config = self.config.paths.tor
        context: dict[str, object] = {
            "tor_socks_proxy": tor_config.socks_proxy,
            "tor_control_metadata_enabled": tor_config.collect_circuit_metadata,
        }
        if not tor_config.collect_circuit_metadata:
            return context

        try:
            from stem.control import Controller
        except ImportError:
            context["tor_control_error"] = "Optional package 'stem' is not installed"
            return context

        try:
            with Controller.from_port(port=tor_config.control_port) as controller:
                controller.authenticate()
                circuits = []
                for circuit in controller.get_circuits():
                    circuits.append(
                        {
                            "id": circuit.id,
                            "status": circuit.status,
                            "purpose": circuit.purpose,
                            "path_nicknames": [entry[1] for entry in circuit.path],
                        }
                    )
                context["tor_circuits"] = circuits[:20]
        except Exception as exc:  # pragma: no cover - depends on local Tor daemon.
            context["tor_control_error"] = str(exc)
        return context
