"""Safe command construction and optional dependency checks."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from typing import Sequence


OPTIONAL_TOOLS: dict[str, str] = {
    "ping": "ICMP latency and packet-loss measurements",
    "curl": "manual HTTP diagnostics",
    "iperf3": "throughput measurements",
    "tor": "local Tor SOCKS proxy service",
    "wg": "WireGuard interface inspection",
    "wg-quick": "manual WireGuard setup outside this tool",
    "tc": "Linux network emulation with netem",
}

_INTERFACE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


@dataclass(frozen=True)
class ToolStatus:
    """Availability status for one optional system tool."""

    name: str
    feature: str
    available: bool
    path: str | None


@dataclass(frozen=True)
class CommandResult:
    """Small wrapper around subprocess results."""

    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Return True when the command exited successfully."""
        return self.returncode == 0


def check_optional_tools() -> list[ToolStatus]:
    """Check optional command-line tools without failing on missing tools."""
    statuses: list[ToolStatus] = []
    for name, feature in OPTIONAL_TOOLS.items():
        path = shutil.which(name)
        statuses.append(
            ToolStatus(name=name, feature=feature, available=path is not None, path=path)
        )
    return statuses


def command_available(name: str) -> bool:
    """Return True if a command is available on PATH."""
    return shutil.which(name) is not None


def validate_interface_name(interface: str) -> str:
    """Validate a network interface token before including it in commands."""
    if not _INTERFACE_RE.fullmatch(interface):
        raise ValueError(f"Unsafe interface name: {interface!r}")
    return interface


def validate_nonnegative(value: float, name: str) -> float:
    """Validate a nonnegative numeric parameter."""
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def build_netem_command(
    *,
    interface: str,
    delay_ms: float,
    jitter_ms: float,
    loss_percent: float,
    bandwidth_mbit: float | None = None,
) -> list[str]:
    """Build a safe tc netem replace command without executing it."""
    validate_interface_name(interface)
    validate_nonnegative(delay_ms, "delay_ms")
    validate_nonnegative(jitter_ms, "jitter_ms")
    validate_nonnegative(loss_percent, "loss_percent")
    if loss_percent > 100:
        raise ValueError("loss_percent must be <= 100")
    if bandwidth_mbit is not None and bandwidth_mbit <= 0:
        raise ValueError("bandwidth_mbit must be positive when provided")

    command = [
        "tc",
        "qdisc",
        "replace",
        "dev",
        interface,
        "root",
        "netem",
        "delay",
        f"{delay_ms:g}ms",
        f"{jitter_ms:g}ms",
        "loss",
        f"{loss_percent:g}%",
    ]
    if bandwidth_mbit is not None:
        command.extend(["rate", f"{bandwidth_mbit:g}mbit"])
    return command


def build_netem_teardown_command(interface: str) -> list[str]:
    """Build a safe tc qdisc delete command without executing it."""
    validate_interface_name(interface)
    return ["tc", "qdisc", "del", "dev", interface, "root"]


def render_command(args: Sequence[str]) -> str:
    """Render command arguments for reviewable dry-run output."""
    return shlex.join(list(args))


def run_command(args: Sequence[str], *, timeout_seconds: float = 30.0) -> CommandResult:
    """Run a subprocess without invoking a shell."""
    if not args:
        raise ValueError("args must not be empty")
    normalized = tuple(str(part) for part in args)
    try:
        completed = subprocess.run(
            list(normalized),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        return CommandResult(
            args=normalized,
            returncode=127,
            stdout="",
            stderr=str(exc),
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            args=normalized,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=exc.stderr or f"Command timed out after {timeout_seconds} seconds",
        )
    return CommandResult(
        args=normalized,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
