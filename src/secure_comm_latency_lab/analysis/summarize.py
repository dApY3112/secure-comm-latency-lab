"""Summarize JSONL measurement logs."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import pandas as pd

GROUP_COLUMNS = ["experiment_name", "path", "network_profile", "measurement_type"]
METRIC_COLUMNS = ["latency_ms", "throughput_mbps", "jitter_ms", "packet_loss_percent"]


def load_jsonl(path: str | Path) -> pd.DataFrame:
    """Load measurement JSONL into a pandas DataFrame."""
    records: list[dict[str, object]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"JSONL line {line_number} must contain an object")
            records.append(record)
    return pd.DataFrame.from_records(records)


def _ci95(series: pd.Series) -> tuple[float | None, float | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    count = len(values)
    if count < 2:
        return None, None
    std = float(values.std(ddof=1))
    margin = 1.96 * std / math.sqrt(count)
    mean = float(values.mean())
    return mean - margin, mean + margin


def _metric_stats(series: pd.Series, prefix: str) -> dict[str, float | int | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {
            f"{prefix}_count": 0,
            f"{prefix}_mean": None,
            f"{prefix}_median": None,
            f"{prefix}_std": None,
            f"{prefix}_min": None,
            f"{prefix}_max": None,
            f"{prefix}_ci95_low": None,
            f"{prefix}_ci95_high": None,
        }
    ci_low, ci_high = _ci95(values)
    return {
        f"{prefix}_count": int(len(values)),
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_median": float(values.median()),
        f"{prefix}_std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        f"{prefix}_min": float(values.min()),
        f"{prefix}_max": float(values.max()),
        f"{prefix}_ci95_low": ci_low,
        f"{prefix}_ci95_high": ci_high,
    }


def _ensure_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = None
    return df


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute grouped summary statistics for stable measurement columns."""
    if df.empty:
        return pd.DataFrame()

    df = _ensure_columns(df.copy(), [*GROUP_COLUMNS, "success", *METRIC_COLUMNS])
    df["success"] = df["success"].fillna(False).astype(bool)

    rows: list[dict[str, object]] = []
    grouped = df.groupby(GROUP_COLUMNS, dropna=False, sort=True)
    for group_values, group in grouped:
        row = dict(zip(GROUP_COLUMNS, group_values, strict=True))
        row["count_total"] = int(len(group))
        row["count_success"] = int(group["success"].sum())
        row["success_rate"] = float(group["success"].mean())
        for metric in METRIC_COLUMNS:
            row.update(_metric_stats(group[metric], metric))
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_jsonl(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """Load JSONL logs, compute a summary, and write CSV output."""
    summary = compute_summary(load_jsonl(input_path))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output, index=False)
    return summary
