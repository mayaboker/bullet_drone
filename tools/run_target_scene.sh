#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

usage() {
  cat >&2 <<'EOF'
Usage: run_target_scene.sh [options] [-- extra-launcher-args...]

Options:
  --isaac            Use Isaac Sim renderer (Godot is the default)
  --isaac-physics    Use Isaac PhysX physics (implies --isaac, requires python.sh)
  --isaac-headless   Run Isaac renderer without GUI (implies --isaac)
  --world <path>     USD world file for Isaac renderer (implies --isaac)
  -h, --help         Show this help

The script starts bullet_visual in the background, then runs the launcher
with SITL and the target scene. Start bullet_app from the bullet_ng workspace
after SITL is ready.

Examples:
  tools/run_target_scene.sh                           # Godot
  tools/run_target_scene.sh --isaac                   # Isaac renderer, PyBullet physics
  tools/run_target_scene.sh --isaac-physics            # Isaac renderer + Isaac PhysX
  tools/run_target_scene.sh --isaac --world ~/ov/rivermark.usd
EOF
  exit 2
}

isaac=false
isaac_physics=false
isaac_headless=false
world=""
extra_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --isaac) isaac=true; shift ;;
    --isaac-physics) isaac_physics=true; isaac=true; shift ;;
    --isaac-headless) isaac_headless=true; isaac=true; shift ;;
    --world) [[ $# -lt 2 ]] && usage; world="$2"; isaac=true; shift 2 ;;
    --) shift; extra_args=("$@"); break ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

# Auto-detect SITL binary: prefer beta_client build, fall back to in-tree
sitl_binary=""
for candidate in \
    ../beta_client/bin/betaflight_*_SITL \
    bin/betaflight_*_SITL.elf; do
  if [[ -x "$candidate" ]]; then
    sitl_binary="$candidate"
    break
  fi
done
if [[ -z "$sitl_binary" ]]; then
  echo "No SITL binary found in ../beta_client/bin/ or bin/" >&2
  exit 1
fi

# Start bullet_visual for target detection
uv run --project ../bullet_visual --locked bullet-visual --config ../bullet_visual/config/zmq.yaml &
visual_pid=$!
cleanup() {
  kill "$visual_pid" 2>/dev/null || true
  wait "$visual_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

launcher_args=(
  --sitl
  --sitl-binary "$sitl_binary"
  --render
  --target-scene
)
if $isaac; then
  launcher_args+=(--renderer-backend isaac)
  $isaac_headless && launcher_args+=(--isaac-headless)
  [[ -n "$world" ]] && launcher_args+=(--world "$world")
fi
$isaac_physics && launcher_args+=(--physics-backend isaac)
launcher_args+=("${extra_args[@]+"${extra_args[@]}"}")

if $isaac_physics; then
  # Isaac physics imports require Isaac Sim's python.sh
  PYTHON_SH="${PYTHON_SH:-$HOME/isaacsim6.2/python.sh}"
  if [[ ! -x "$PYTHON_SH" ]]; then
    echo "python.sh not found at $PYTHON_SH — set PYTHON_SH to override" >&2
    exit 1
  fi
  export PYTHONPATH="src:libs/bullet_simulation_protocol/src:libs/bullet_image_transport/src${PYTHONPATH:+:$PYTHONPATH}"
  exec "$PYTHON_SH" -m launcher "${launcher_args[@]}"
else
  exec uv run --frozen --extra render --extra sitl --extra mavlink \
    launcher "${launcher_args[@]}"
fi
