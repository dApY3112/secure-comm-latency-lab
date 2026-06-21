import shutil

import pytest

from secure_comm_latency_lab.utils.commands import (
    build_netem_command,
    build_netem_teardown_command,
    check_optional_tools,
    render_command,
)


def test_build_netem_command_is_argument_list() -> None:
    command = build_netem_command(
        interface="eth0",
        delay_ms=40,
        jitter_ms=10,
        loss_percent=0.5,
        bandwidth_mbit=20,
    )

    assert command[:7] == ["tc", "qdisc", "replace", "dev", "eth0", "root", "netem"]
    assert "40ms" in command
    assert "0.5%" in command
    assert "20mbit" in command
    assert render_command(command).startswith("tc qdisc replace")


def test_build_netem_rejects_unsafe_interface() -> None:
    with pytest.raises(ValueError):
        build_netem_command(
            interface="eth0;rm -rf /",
            delay_ms=0,
            jitter_ms=0,
            loss_percent=0,
        )


def test_build_netem_rejects_invalid_loss() -> None:
    with pytest.raises(ValueError):
        build_netem_command(
            interface="eth0",
            delay_ms=0,
            jitter_ms=0,
            loss_percent=101,
        )


def test_build_teardown_command_is_safe_list() -> None:
    assert build_netem_teardown_command("wg0") == ["tc", "qdisc", "del", "dev", "wg0", "root"]


def test_missing_optional_dependencies_do_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: None)

    statuses = check_optional_tools()

    assert statuses
    assert all(status.available is False for status in statuses)
