#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

mission=${1:?Usage: run_app_after_sitl.sh hover-land|target-hit}
if [[ "$mission" != hover-land && "$mission" != target-hit ]]; then
  echo "Unknown mission: $mission" >&2
  exit 2
fi

for attempt in {1..120}; do
  if ss -ltn | awk '$4 ~ /:5761$/ { msp=1 } $4 ~ /:5762$/ { mavlink=1 } END { exit !(msp && mavlink) }'; then
    exec uv run --project ../bullet_app --locked bullet-app --mode manual --mission "$mission"
  fi
  sleep 0.5
done

echo 'Timed out waiting for Betaflight MSP (5761) and MAVLink (5762) listeners' >&2
exit 1
