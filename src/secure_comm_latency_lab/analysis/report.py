"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from secure_comm_latency_lab.utils.commands import check_optional_tools
from secure_comm_latency_lab.utils.time import utc_now_iso


def _format_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.3g}"
    return str(value)


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 40) -> str:
    """Render a compact Markdown table without requiring tabulate."""
    if df.empty:
        return "_No summary rows available._"
    visible = df.head(max_rows).copy()
    preferred_columns = [
        "experiment_name",
        "path",
        "network_profile",
        "measurement_type",
        "count_total",
        "count_success",
        "success_rate",
        "latency_ms_mean",
        "throughput_mbps_mean",
        "jitter_ms_mean",
        "packet_loss_percent_mean",
    ]
    columns = [column for column in preferred_columns if column in visible.columns]
    visible = visible[columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [
        "| " + " | ".join(_format_value(row[column]) for column in columns) + " |"
        for _, row in visible.iterrows()
    ]
    suffix = ""
    if len(df) > max_rows:
        suffix = f"\n\n_Table truncated to {max_rows} rows._"
    return "\n".join([header, separator, *rows]) + suffix


def _dependency_section() -> str:
    lines = ["| Tool | Available | Feature |", "| --- | --- | --- |"]
    for status in check_optional_tools():
        available = "yes" if status.available else "no"
        lines.append(f"| `{status.name}` | {available} | {status.feature} |")
    return "\n".join(lines)


def _figure_section(figures_dir: Path, report_path: Path) -> str:
    figures = sorted(figures_dir.glob("*.png"))
    if not figures:
        return "_No figures were generated._"
    lines: list[str] = []
    for figure in figures:
        try:
            relative = figure.relative_to(report_path.parent)
        except ValueError:
            relative = figure
        title = figure.stem.replace("_", " ").title()
        lines.append(f"- [{title}]({relative.as_posix()})")
    return "\n".join(lines)


def generate_report(
    *,
    summary_path: str | Path,
    figures_dir: str | Path,
    output_path: str | Path,
) -> Path:
    """Generate a Markdown report from summary CSV and figures."""
    summary = pd.read_csv(summary_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figures = Path(figures_dir)
    experiment_name = (
        str(summary["experiment_name"].dropna().iloc[0])
        if "experiment_name" in summary.columns and not summary.empty
        else "unknown"
    )

    content = f"""# Secure Communication Latency Lab Report

Generated: {utc_now_iso()}

Experiment: `{experiment_name}`

## Environment And Dependency Summary

{_dependency_section()}

## Methodology

Measurements are loaded from a stable JSONL schema and grouped by experiment,
communication path, network profile, and measurement type. Summary statistics
include count, mean, median, standard deviation, minimum, maximum, and an
approximate 95% confidence interval when at least two numeric samples are
available.

The direct path uses the host's normal routing. The WireGuard path assumes a
user-managed local tunnel is already configured and records interface status
where available. The Tor path measures HTTP timing through a local SOCKS proxy;
ICMP ping and iperf3 are marked unsupported for Tor because they do not
naturally run through SOCKS in this safe implementation.

## Summary Results

{dataframe_to_markdown(summary)}

## Figures

{_figure_section(figures, output)}

## Limitations

- Results depend on local host load, endpoint behavior, routing, and optional
  system tools.
- WireGuard and network emulation require a user-controlled Linux setup.
- Tor measurements are limited to HTTP timing through a local SOCKS proxy.
- The bundled example dataset is synthetic and should not be cited as real
  experimental evidence.

## Ethical-Use Statement

This project is intended only for controlled measurements on local, owned, or
explicitly permitted systems. It must not be used for public scanning, crawling
onion services, scraping darknet marketplaces, deanonymization, traffic
correlation, fingerprinting, bypassing access controls, denial-of-service
testing, or collecting sensitive third-party data.

## Relevance To Secure Communication Research

This project demonstrates a small empirical framework for studying
latency-sensitive secure communication paths. It compares direct communication,
WireGuard-based tunneling, and Tor proxying under controlled measurement
settings, while emphasizing ethical experimentation and reproducibility. The
project connects privacy/anonymity research with practical network-performance
evaluation, which is relevant to secure communication systems where
confidentiality, anonymity, and low latency must be considered together.
"""
    output.write_text(content, encoding="utf-8")
    return output
