extends Node3D
const Registry = preload("res://registry.gd")
const WorldCamera = preload("res://world_camera.gd")
const FlightWorld = preload("res://flight_world.gd")
var registry = Registry.new()
var udp = PacketPeerUDP.new()
var tiles: Dictionary = {}
var grid: GridContainer
var waiting: Label
var preview_scroll: ScrollContainer
var world_camera: Camera3D
var fps_label: Label
var fps_panel: PanelContainer
var _fps_elapsed = 0.0

func material(color: Color) -> StandardMaterial3D:
	var m = StandardMaterial3D.new()
	m.albedo_color = color
	return m

func box(parent: Node3D, pos: Vector3, size: Vector3, color: Color):
	var node = MeshInstance3D.new()
	var mesh = BoxMesh.new()
	mesh.size = size
	node.mesh = mesh
	node.material_override = material(color)
	parent.add_child(node)
	node.position = pos

func _ready():
	var port = 9870
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--port="):
			port = int(arg.trim_prefix("--port="))
	var error = udp.bind(port, "127.0.0.1")
	if error != OK:
		push_error("Cannot bind UDP viewer port %s: %s" % [port, error])
		get_tree().quit(1)
		return
	add_child(FlightWorld.new())
	world_camera = WorldCamera.new()
	add_child(world_camera)
	var canvas = CanvasLayer.new()
	add_child(canvas)
	fps_panel = PanelContainer.new()
	fps_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(fps_panel)
	fps_panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	fps_panel.offset_left = -176
	fps_panel.offset_right = -12
	fps_panel.offset_top = 12
	fps_panel.offset_bottom = 48
	var fps_style = StyleBoxFlat.new()
	fps_style.bg_color = Color(0.025, 0.04, 0.07, 0.9)
	fps_style.content_margin_left = 12
	fps_style.content_margin_right = 12
	fps_style.content_margin_top = 6
	fps_style.content_margin_bottom = 6
	fps_panel.add_theme_stylebox_override("panel", fps_style)
	fps_label = Label.new()
	fps_label.text = "Render: 0 FPS"
	fps_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fps_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	fps_label.add_theme_font_size_override("font_size", 16)
	fps_panel.add_child(fps_label)
	preview_scroll = ScrollContainer.new()
	preview_scroll.position = Vector2(12, 12)
	preview_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	canvas.add_child(preview_scroll)
	grid = GridContainer.new()
	grid.columns = 1
	grid.add_theme_constant_override("v_separation", 12)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	preview_scroll.add_child(grid)
	var controls = Label.new()
	controls.text = "WORLD CAMERA · Right-drag: orbit · Wheel: zoom"
	controls.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(controls)
	controls.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	controls.offset_left = 12
	controls.offset_top = -32
	controls.offset_right = 650
	controls.offset_bottom = -12
	waiting = Label.new()
	waiting.text = "Waiting for drone publishers · UDP 127.0.0.1:%d" % port
	canvas.add_child(waiting)
	waiting.position = Vector2(20, 20)
	get_viewport().size_changed.connect(layout)
	layout()

func create_drone(id: String):
	var model = Node3D.new()
	add_child(model)
	box(model, Vector3.ZERO, Vector3(0.12, 0.025, 0.09), Color(0.13, 0.14, 0.17))
	for x in [-0.085, 0.085]:
		for z in [-0.0675, 0.0675]:
			box(model, Vector3(x / 2, 0, z / 2), Vector3(0.09, 0.012, 0.015), Color(0.2, 0.2, 0.22))
			var rotor = MeshInstance3D.new()
			var mesh = CylinderMesh.new()
			mesh.top_radius = 0.045
			mesh.bottom_radius = 0.045
			mesh.height = 0.004
			rotor.mesh = mesh
			rotor.material_override = material(Color(1, 0.35, 0.02) if x > 0 else Color(0.05, 0.3, 1))
			model.add_child(rotor)
			rotor.position = Vector3(x, 0.018, z)
	var world_label = Label3D.new()
	world_label.text = id
	world_label.font_size = 32
	world_label.pixel_size = 0.003
	world_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	model.add_child(world_label)
	world_label.position = Vector3(0, 0.18, 0)
	var tile = PanelContainer.new()
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.025, 0.04, 0.07, 0.95)
	style.border_color = Color(0.15, 0.6, 0.95)
	style.set_border_width_all(2)
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 6
	style.content_margin_bottom = 8
	tile.add_theme_stylebox_override("panel", style)
	grid.add_child(tile)
	var content = VBoxContainer.new()
	tile.add_child(content)
	var title = Label.new()
	title.text = "Camera: fpv / Drone: %s" % id
	title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	content.add_child(title)
	var label = Label.new()
	label.add_theme_font_size_override("font_size", 13)
	content.add_child(label)
	var texture = TextureRect.new()
	texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	texture.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(texture)
	var viewport = SubViewport.new()
	viewport.world_3d = get_viewport().world_3d
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	var camera = Camera3D.new()
	camera.keep_aspect = Camera3D.KEEP_HEIGHT
	camera.near = 0.02
	camera.far = 150
	viewport.add_child(camera)
	camera.current = true
	texture.texture = viewport.get_texture()
	tiles[id] = {"model": model, "tile": tile, "label": label, "title": title, "texture": texture, "viewport": viewport, "camera": camera}
	layout()

func layout():
	var window = get_viewport().get_visible_rect().size
	preview_scroll.size = Vector2(minf(400, maxf(1, window.x * 0.4)), maxf(1, window.y - 60))
	var ids = tiles.keys()
	ids.sort()
	for index in range(ids.size()):
		var entry = tiles[ids[index]]
		grid.move_child(entry.tile, index)
		# Leave room for the scrollbar and frame; preserve each camera's aspect.
		var width = maxf(1, preview_scroll.size.x - 34)
		var resolution = entry.viewport.size
		entry.texture.custom_minimum_size = Vector2(width, width * resolution.y / maxf(1, resolution.x))

func apply_packet(id: String):
	if not tiles.has(id):
		create_drone(id)
	var packet = registry.drones[id].packet
	var s = packet.snapshot
	var c = packet.camera
	var entry = tiles[id]
	var pose = Transform3D(Basis(Registry.orientation(s.orientation_xyzw)), Registry.position(s.position_m))
	entry.model.transform = pose
	entry.viewport.size = Vector2i(c.width_px, c.height_px)
	entry.camera.fov = c.fov_y_deg
	layout()
	entry.camera.transform = pose * Transform3D(Registry.camera_basis(c.downward_tilt_deg), Registry.position(c.mount_position_body_m))

func _process(delta):
	_fps_elapsed += delta
	if _fps_elapsed >= 0.25:
		fps_label.text = "Render: %d FPS" % Engine.get_frames_per_second()
		_fps_elapsed = fmod(_fps_elapsed, 0.25)
	var now = Time.get_ticks_msec() / 1000.0
	var changed: Dictionary = {}
	while udp.get_available_packet_count() > 0:
		var packet = JSON.parse_string(udp.get_packet().get_string_from_utf8())
		if registry.accept(packet, now):
			changed[packet.snapshot.drone_id] = true
	for id in changed:
		apply_packet(id)
	var positions: Array = []
	for id in tiles:
		positions.append(tiles[id].model.position)
	world_camera.frame_positions(positions)
	waiting.visible = tiles.is_empty()
	for id in tiles:
		var entry = registry.drones[id]
		var s = entry.packet.snapshot
		tiles[id].label.text = "%s · %.2f m · step %d%s" % [id, s.position_m[2], s.step_index, " · STALE" if registry.stale(id, now) else ""]

func _exit_tree():
	udp.close()
