"""Direct baseline communication path."""

from __future__ import annotations

from secure_comm_latency_lab.runners.base import BaseRunner


class DirectRunner(BaseRunner):
    """Run measurements without proxy or tunnel assumptions."""

    path_name = "direct"
