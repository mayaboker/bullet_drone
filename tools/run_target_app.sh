#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

for attempt in {1..120}; do
  if ss -ltn | awk '$4 ~ /:5761$/ { msp=1 } $4 ~ /:5762$/ { mavlink=1 } END { exit !(msp && mavlink) }'; then
    exec uv run --project ../bullet_app --locked bullet-app --mode auto --mission target-hit
  fi
  sleep 0.5
done

echo 'Timed out waiting for Betaflight MSP (5761) and MAVLink (5762) listeners' >&2
exit 1
