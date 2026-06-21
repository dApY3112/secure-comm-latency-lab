#!/usr/bin/env bash
set -euo pipefail

INTERFACE="eth0"
APPLY=0

usage() {
  cat <<'USAGE'
Usage: teardown_netem.sh --interface IFACE [--apply]

Default mode is dry-run and prints the tc teardown command only.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interface)
      INTERFACE="${2:?missing interface}"
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

CMD=(tc qdisc del dev "$INTERFACE" root)

if [[ "$APPLY" -eq 1 ]]; then
  echo "Removing root qdisc from interface '$INTERFACE'."
  sudo "${CMD[@]}" || true
else
  printf 'Dry run. Review before applying:\n  sudo'
  printf ' %q' "${CMD[@]}"
  printf '\n'
fi
