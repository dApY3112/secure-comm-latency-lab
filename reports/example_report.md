# Secure Communication Latency Lab Report

Generated: 2026-06-21T13:00:37Z

Experiment: `synthetic_demo`

## Environment And Dependency Summary

| Tool | Available | Feature |
| --- | --- | --- |
| `ping` | yes | ICMP latency and packet-loss measurements |
| `curl` | yes | manual HTTP diagnostics |
| `iperf3` | no | throughput measurements |
| `tor` | no | local Tor SOCKS proxy service |
| `wg` | no | WireGuard interface inspection |
| `wg-quick` | no | manual WireGuard setup outside this tool |
| `tc` | no | Linux network emulation with netem |

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

| experiment_name | path | network_profile | measurement_type | count_total | count_success | success_rate | latency_ms_mean | throughput_mbps_mean | jitter_ms_mean | packet_loss_percent_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic_demo | direct | baseline | http_timing | 2 | 2 | 1 | 19.8 |  |  |  |
| synthetic_demo | direct | baseline | iperf3 | 1 | 1 | 1 |  | 942 |  |  |
| synthetic_demo | direct | baseline | ping | 1 | 1 | 1 | 0.31 |  | 0.04 | 0 |
| synthetic_demo | direct | mobile_like | ping | 1 | 1 | 1 | 42.8 |  | 8.1 | 0.5 |
| synthetic_demo | tor | baseline | http_timing | 1 | 1 | 1 | 143 |  |  |  |
| synthetic_demo | wireguard | baseline | http_timing | 1 | 1 | 1 | 24.9 |  |  |  |
| synthetic_demo | wireguard | baseline | iperf3 | 1 | 1 | 1 |  | 812 |  |  |
| synthetic_demo | wireguard | baseline | ping | 1 | 1 | 1 | 1.2 |  | 0.2 | 0 |
| synthetic_demo | wireguard | mobile_like | ping | 1 | 1 | 1 | 46.5 |  | 9.5 | 0.5 |

## Figures

- [Http Latency By Path](figures/http_latency_by_path.png)
- [Packet Loss By Path Profile](figures/packet_loss_by_path_profile.png)
- [Ping Rtt By Path](figures/ping_rtt_by_path.png)
- [Throughput By Path](figures/throughput_by_path.png)

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
