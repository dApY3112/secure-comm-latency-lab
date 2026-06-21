#!/usr/bin/env bash
set -euo pipefail

INTERFACE="eth0"
PROFILE="baseline"
APPLY=0

usage() {
  cat <<'USAGE'
Usage: setup_netem.sh --interface IFACE --profile PROFILE [--apply]

Profiles:
  baseline        delay=0ms jitter=0ms loss=0% bandwidth=unlimited
  mobile_like     delay=40ms jitter=10ms loss=0.5% bandwidth=20mbit
  satellite_like  delay=600ms jitter=40ms loss=1.0% bandwidth=10mbit

Default mode is dry-run and prints the tc command only.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interface)
      INTERFACE="${2:?missing interface}"
      shift 2
      ;;
    --profile)
      PROFILE="${2:?missing profile}"
      shift 2
      ;;
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

case "$PROFILE" in
  baseline)
    DELAY=0
    JITTER=0
    LOSS=0
    BANDWIDTH=""
    ;;
  mobile_like)
    DELAY=40
    JITTER=10
    LOSS=0.5
    BANDWIDTH="20mbit"
    ;;
  satellite_like)
    DELAY=600
    JITTER=40
    LOSS=1.0
    BANDWIDTH="10mbit"
    ;;
  *)
    echo "Unknown profile: $PROFILE" >&2
    usage >&2
    exit 2
    ;;
esac

CMD=(tc qdisc replace dev "$INTERFACE" root netem delay "${DELAY}ms" "${JITTER}ms" loss "${LOSS}%")
if [[ -n "$BANDWIDTH" ]]; then
  CMD+=(rate "$BANDWIDTH")
fi

if [[ "$APPLY" -eq 1 ]]; then
  echo "Applying netem profile '$PROFILE' to interface '$INTERFACE'."
  sudo "${CMD[@]}"
else
  printf 'Dry run. Review before applying:\n  sudo'
  printf ' %q' "${CMD[@]}"
  printf '\n'
fi
