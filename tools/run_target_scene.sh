#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --project ../bullet_visual --locked bullet-visual --config ../bullet_visual/config/zmq.yaml &
visual_pid=$!
cleanup() {
  kill "$visual_pid" 2>/dev/null || true
  wait "$visual_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
uv run --frozen --extra render --extra sitl --extra mavlink \
  launcher --sitl --render --target-scene
