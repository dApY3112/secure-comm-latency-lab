"""Plot summary CSV files with matplotlib."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def _metric_available(df: pd.DataFrame, metric: str) -> bool:
    count_column = f"{metric}_count"
    return count_column in df.columns and pd.to_numeric(df[count_column], errors="coerce").fillna(0).sum() > 0


def _labels(df: pd.DataFrame) -> list[str]:
    labels: list[str] = []
    for _, row in df.iterrows():
        profile = str(row["network_profile"])
        path = str(row["path"])
        labels.append(path if profile == "baseline" else f"{path}\n{profile}")
    return labels


def _plot_metric(
    *,
    summary: pd.DataFrame,
    measurement_type: str,
    metric: str,
    ylabel: str,
    title: str,
    output_path: Path,
) -> Path | None:
    mean_col = f"{metric}_mean"
    low_col = f"{metric}_ci95_low"
    high_col = f"{metric}_ci95_high"
    count_col = f"{metric}_count"

    subset = summary[
        (summary["measurement_type"] == measurement_type)
        & (pd.to_numeric(summary.get(count_col), errors="coerce").fillna(0) > 0)
    ].copy()
    if subset.empty:
        return None

    subset[mean_col] = pd.to_numeric(subset[mean_col], errors="coerce")
    subset = subset.dropna(subset=[mean_col])
    if subset.empty:
        return None

    subset = subset.sort_values(["network_profile", "path"])
    x_positions = range(len(subset))
    means = subset[mean_col].tolist()

    yerr = None
    if low_col in subset.columns and high_col in subset.columns:
        lows = pd.to_numeric(subset[low_col], errors="coerce")
        highs = pd.to_numeric(subset[high_col], errors="coerce")
        if lows.notna().any() and highs.notna().any():
            lower = [max(0.0, mean - low) if pd.notna(low) else 0.0 for mean, low in zip(means, lows, strict=True)]
            upper = [max(0.0, high - mean) if pd.notna(high) else 0.0 for mean, high in zip(means, highs, strict=True)]
            yerr = [lower, upper]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(list(x_positions), means, yerr=yerr, capsize=4 if yerr else 0)
    ax.set_xticks(list(x_positions), _labels(subset))
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def generate_plots(summary_path: str | Path, output_dir: str | Path) -> list[Path]:
    """Generate academic-style PNG plots from a summary CSV."""
    summary = pd.read_csv(summary_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    figures: list[Path] = []
    plot_specs = [
        (
            "http_timing",
            "latency_ms",
            "Latency (ms)",
            "HTTP response time by path",
            output / "http_latency_by_path.png",
        ),
        (
            "ping",
            "latency_ms",
            "RTT (ms)",
            "Ping round-trip time by path",
            output / "ping_rtt_by_path.png",
        ),
        (
            "iperf3",
            "throughput_mbps",
            "Throughput (Mbit/s)",
            "iperf3 throughput by path",
            output / "throughput_by_path.png",
        ),
        (
            "ping",
            "packet_loss_percent",
            "Packet loss (%)",
            "Packet loss by path and profile",
            output / "packet_loss_by_path_profile.png",
        ),
    ]
    for measurement_type, metric, ylabel, title, path in plot_specs:
        if _metric_available(summary, metric):
            figure = _plot_metric(
                summary=summary,
                measurement_type=measurement_type,
                metric=metric,
                ylabel=ylabel,
                title=title,
                output_path=path,
            )
            if figure is not None:
                figures.append(figure)
    return figures
