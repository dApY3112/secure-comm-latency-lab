"""WireGuard path measurement mode."""

from __future__ import annotations

from pathlib import Path

from secure_comm_latency_lab.runners.base import BaseRunner
from secure_comm_latency_lab.utils.commands import command_available, run_command, validate_interface_name


class WireGuardRunner(BaseRunner):
    """Run measurements while assuming the user-managed WireGuard route is active."""

    path_name = "wireguard"

    def raw_context(self) -> dict[str, object]:
        """Collect non-sensitive local interface status when possible."""
        interface = self.config.paths.wireguard.interface
        context: dict[str, object] = {"wireguard_interface": interface}
        try:
            validate_interface_name(interface)
        except ValueError as exc:
            context["wireguard_status_error"] = str(exc)
            return context

        sysfs_path = Path("/sys/class/net") / interface
        context["interface_exists_sysfs"] = sysfs_path.exists()

        if command_available("wg"):
            result = run_command(["wg", "show", interface], timeout_seconds=5)
            context["wg_show_returncode"] = result.returncode
            if result.ok:
                context["wg_show"] = result.stdout[:2000]
            else:
                context["wg_show_error"] = (result.stderr or result.stdout)[:1000]
        else:
            context["wg_available"] = False

        return context
