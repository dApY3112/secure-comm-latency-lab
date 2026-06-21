#!/usr/bin/env bash
set -euo pipefail

APPLY=0

usage() {
  cat <<'USAGE'
Usage: setup_wireguard_lab.sh [--apply]

This is a local-only WireGuard lab template. It does not create public VPN
credentials, does not contact a provider, and does not modify routing by
default. Review the printed checklist and adapt it to an isolated Linux lab.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cat <<'CHECKLIST'
Local WireGuard lab checklist:

1. Create two Linux network namespaces, for example wg-client and wg-server.
2. Connect them with a veth pair.
3. Generate throwaway local WireGuard keys inside the lab only.
4. Configure wg0 on each namespace with private RFC1918 addresses.
5. Start a local HTTP or iperf3 server inside wg-server.
6. Run sclab from wg-client or route test traffic through wg0.

Example commands to adapt manually:

  ip netns add wg-client
  ip netns add wg-server
  ip link add veth-client type veth peer name veth-server
  ip link set veth-client netns wg-client
  ip link set veth-server netns wg-server
  ip netns exec wg-client wg genkey
  ip netns exec wg-server wg genkey

This script intentionally avoids generating or installing configs for you.
CHECKLIST

if [[ "$APPLY" -eq 1 ]]; then
  cat >&2 <<'NOTICE'

--apply was provided, but this project keeps WireGuard setup as a reviewed
local-lab template. Apply the checklist manually on a Linux host you control.
NOTICE
else
  echo
  echo "Dry run only. No system networking changes were made."
fi
