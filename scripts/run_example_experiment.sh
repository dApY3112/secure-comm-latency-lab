#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

python -m secure_comm_latency_lab.cli summarize \
  --input "$ROOT_DIR/data/raw/synthetic_example.jsonl" \
  --output "$ROOT_DIR/data/processed/summary.csv"

python -m secure_comm_latency_lab.cli plot \
  --summary "$ROOT_DIR/data/processed/summary.csv" \
  --output "$ROOT_DIR/reports/figures"

python -m secure_comm_latency_lab.cli report \
  --summary "$ROOT_DIR/data/processed/summary.csv" \
  --figures "$ROOT_DIR/reports/figures" \
  --output "$ROOT_DIR/reports/example_report.md"
