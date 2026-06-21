# Secure Communication Latency Lab

Secure Communication Latency Lab is a small, ethical, reproducible Python
framework for measuring performance across latency-sensitive communication
paths:

- direct baseline communication
- a user-managed WireGuard tunnel
- HTTP requests sent through a local Tor SOCKS proxy

The framework records JSONL measurements for latency, jitter, packet loss,
throughput, and HTTP response time, then produces summary CSV files, clean
matplotlib figures, and Markdown reports.

## Research Motivation

Secure communication systems often require trade-offs between confidentiality,
anonymity, reliability, and responsiveness. This project provides a controlled
measurement harness for studying those trade-offs without crawling, scanning,
attacking, or collecting third-party sensitive data. It is designed as a compact
research software artifact suitable for a GitHub portfolio and for PhD
applications focused on low-latency secure communication systems.

This project demonstrates a small empirical framework for studying
latency-sensitive secure communication paths. It compares direct communication,
WireGuard-based tunneling, and Tor proxying under controlled measurement
settings, while emphasizing ethical experimentation and reproducibility. The
project connects privacy/anonymity research with practical network-performance
evaluation, which is relevant to secure communication systems where
confidentiality, anonymity, and low latency must be considered together.

## Ethical Scope

Use this project only on local, owned, or explicitly permitted systems. The
project must not be used to:

- scan arbitrary public IP ranges
- crawl onion services or darknet marketplaces
- deanonymize Tor users
- perform traffic correlation or fingerprinting
- bypass authentication or access control
- perform denial-of-service or stress testing against public services
- collect sensitive third-party data
- use real VPN provider credentials in the repository

System-level scripts are dry-run by default. Commands that alter networking,
such as `tc netem`, require an explicit `--apply` flag and should be reviewed
before use on a Linux host.

## Installation

Python 3.11 or newer is recommended.

```bash
git clone https://github.com/example/secure-comm-latency-lab.git
cd secure-comm-latency-lab
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,tor]"
```

The `tor` extra installs `stem` for optional local Tor ControlPort metadata.
The framework still works without it.

## Quick Start With Synthetic Data

The repository includes a small synthetic JSONL dataset. It is useful for
testing the analysis/report workflow without requiring WireGuard, Tor, iperf3,
or privileged Linux networking.

```bash
sclab summarize --input data/raw/synthetic_example.jsonl --output data/processed/summary.csv
sclab plot --summary data/processed/summary.csv --output reports/figures
sclab report --summary data/processed/summary.csv --figures reports/figures --output reports/example_report.md
```

Or run the convenience script:

```bash
bash scripts/run_example_experiment.sh
```

## Running a Local Measurement

Start with the example config:

```bash
sclab check
sclab run --config configs/example_experiment.yaml
```

The run command writes a timestamped JSONL file under `data/raw/`. You can then
summarize and report it:

```bash
sclab summarize --input data/raw/<your-run>.jsonl --output data/processed/summary.csv
sclab plot --summary data/processed/summary.csv --output reports/figures
sclab report --summary data/processed/summary.csv --figures reports/figures --output reports/example_report.md
```

By default, the example config measures a direct path against localhost. For a
real run, point `targets.http_url` and `targets.iperf_host` to services you own
or have permission to test.

## Optional WireGuard Path

The WireGuard runner assumes that you have already configured a local
WireGuard tunnel. It does not generate public VPN credentials and does not
modify routing. When enabled, it records interface status where available and
runs the same direct measurements through the host's current routing state.

Set this in your config after your local tunnel is up:

```yaml
paths:
  wireguard:
    enabled: true
    interface: "wg0"
```

The script `scripts/setup_wireguard_lab.sh` is intentionally a dry-run local
lab template. It prints a Linux network-namespace checklist rather than
creating credentials automatically.

## Optional Tor SOCKS Path

The Tor runner supports HTTP timing through a local SOCKS proxy, typically
`socks5h://127.0.0.1:9050`. It does not crawl onion services or attempt any
identity, circuit, or traffic-correlation analysis. Optional ControlPort
metadata is disabled by default and limited to basic local circuit descriptors
when the user's own Tor daemon exposes them.

```yaml
paths:
  tor:
    enabled: true
    socks_proxy: "socks5h://127.0.0.1:9050"
    collect_circuit_metadata: false
```

ICMP ping and iperf3 do not naturally run through a SOCKS proxy, so the Tor
runner records those measurement types as unsupported rather than pretending
they were measured through Tor.

## Network Condition Simulation

Linux `tc netem` profiles can be previewed with:

```bash
bash scripts/setup_netem.sh --interface eth0 --profile mobile_like
```

Apply only after review:

```bash
sudo bash scripts/setup_netem.sh --interface eth0 --profile mobile_like --apply
sudo bash scripts/teardown_netem.sh --interface eth0 --apply
```

The Python package also exposes command builders used by the tests, so command
construction is separate from command execution.

## Expected Outputs

- `data/raw/*.jsonl`: one stable-schema JSON object per measurement
- `data/processed/*.csv`: grouped summary statistics
- `reports/figures/*.png`: academic-style matplotlib plots
- `reports/*.md`: reproducible Markdown report with methodology, limitations,
  dependency status, figures, and ethical-use statement

## Development

```bash
pytest
ruff check .
```

The GitHub Actions workflow runs the test suite on Python 3.11.

## Limitations

- WireGuard and `tc netem` automation are Linux-oriented and may require root.
- Tor SOCKS support is limited to HTTP timing in this project.
- Internet paths are noisy; serious experiments should run multiple trials,
  control endpoint load, pin versions, and record host/network metadata.
- The included dataset is synthetic and must not be cited as real experimental
  evidence.

## Future Work

- Add containerized local HTTP and iperf3 fixtures for repeatable lab tests.
- Add richer experiment metadata such as CPU load and kernel/network versions.
- Add bootstrap confidence intervals and non-parametric comparisons.
- Add optional local dashboard export for inspecting run quality.
