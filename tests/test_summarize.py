import json
from pathlib import Path

import pandas as pd

from secure_comm_latency_lab.analysis.summarize import compute_summary, summarize_jsonl


def test_compute_summary_groups_metrics() -> None:
    df = pd.DataFrame(
        [
            {
                "experiment_name": "demo",
                "path": "direct",
                "network_profile": "baseline",
                "measurement_type": "http_timing",
                "success": True,
                "latency_ms": 10.0,
            },
            {
                "experiment_name": "demo",
                "path": "direct",
                "network_profile": "baseline",
                "measurement_type": "http_timing",
                "success": True,
                "latency_ms": 20.0,
            },
            {
                "experiment_name": "demo",
                "path": "tor",
                "network_profile": "baseline",
                "measurement_type": "ping",
                "success": False,
                "error": "unsupported",
            },
        ]
    )

    summary = compute_summary(df)
    direct = summary[
        (summary["path"] == "direct") & (summary["measurement_type"] == "http_timing")
    ].iloc[0]

    assert direct["count_total"] == 2
    assert direct["count_success"] == 2
    assert direct["latency_ms_mean"] == 15.0
    assert direct["latency_ms_count"] == 2
    assert pd.notna(direct["latency_ms_ci95_low"])


def test_summarize_jsonl_writes_csv(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.jsonl"
    output_path = tmp_path / "summary.csv"
    rows = [
        {
            "experiment_name": "demo",
            "path": "direct",
            "network_profile": "baseline",
            "measurement_type": "ping",
            "target": "127.0.0.1",
            "success": True,
            "latency_ms": 1.0,
            "throughput_mbps": None,
            "jitter_ms": 0.1,
            "packet_loss_percent": 0.0,
            "status_code": None,
            "error": None,
            "raw": {},
        }
    ]
    input_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    summary = summarize_jsonl(input_path, output_path)

    assert output_path.exists()
    assert len(summary) == 1
    assert summary.iloc[0]["packet_loss_percent_mean"] == 0.0
