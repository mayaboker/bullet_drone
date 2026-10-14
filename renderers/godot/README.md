# Godot FPV viewer

Requires Godot 4.3+ with OpenGL compatibility rendering. From the repository root:

```bash
godot --path renderers/godot
uv run examples/hover/main.py --renderer godot --render-config configs/render-godot.yaml
```

The application listens on loopback UDP 9870. Override with `-- --port=9871`
and match the publisher YAML. Multiple publishers must use distinct drone IDs.
The world camera fills the window; labeled FPV panels appear at the top left.
A top-right FPS indicator shows the viewer’s render frame rate.
Right-drag in the world view to orbit and scroll to zoom; scroll over the panels
to browse additional drones. The window stays open after publishers stop; tiles show STALE after two seconds.

The outdoor course has colored gates, numbered landing pads, trees, hills and
sunlight with shadows. The scenery is visual-only; PyBullet retains flat-ground
physics.

See [render contracts and configuration](../../docs/design/godot-rendering.md).

Checks:

```bash
godot --headless --path renderers/godot --script test_registry.gd
uv run renderers/godot/smoke_test.py
```

The smoke test owns a temporary visible viewer on port 19870, sends two publishers,
checks world camera, FPV panels, resizing, zoom and staleness behavior, and saves `/tmp/bullet-drone-godot.png`.
It requires a desktop display; the registry check needs no display.
