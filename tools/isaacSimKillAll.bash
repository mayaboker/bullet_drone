#!/usr/bin/env bash
# Kill all processes spawned by Terminal #1 (run_target_scene.sh --isaac-physics)
set -euo pipefail

killed=0

kill_pattern() {
  local pattern="$1"
  local pids
  pids=$(pgrep -f "$pattern" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    echo "Killing $pattern: $pids"
    kill $pids 2>/dev/null || true
    ((killed += $(echo "$pids" | wc -w)))
  fi
}

# Isaac Sim renderer (python.sh running isaac/main.py)
kill_pattern 'isaac/main\.py'
kill_pattern 'isaacsim'
kill_pattern 'omni\.kit'

# Betaflight SITL
kill_pattern 'betaflight.*SITL'

# bullet_visual
kill_pattern 'bullet-visual'
kill_pattern 'bullet_visual'

# The launcher itself
kill_pattern 'launcher.*--isaac'
kill_pattern 'run_target_scene\.sh'

if [[ "$killed" -eq 0 ]]; then
  echo "No matching processes found."
else
  echo "Sent SIGTERM to $killed process(es)."
fi
