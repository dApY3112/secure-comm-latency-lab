"""Time helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing Z."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp_for_filename() -> str:
    """Return a filesystem-safe UTC timestamp."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
