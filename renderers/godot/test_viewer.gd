extends SceneTree
const Viewer = preload("res://viewer.gd")
func _initialize():
	call_deferred("check")
func check():
	var viewer = Viewer.new()
	root.add_child(viewer)
	print("Viewer ready")
	await create_timer(3).timeout
	print("Checking tiles: ", viewer.tiles.keys())
	assert(viewer.tiles.size() == 2, "Two UDP publishers must create two views")
	assert(viewer.fps_label.text.begins_with("Render: "))
	assert(viewer.fps_label.text.ends_with(" FPS"))
	assert(viewer.fps_label.text.get_slice(" ", 1).to_int() > 0)
	assert(viewer.fps_panel.anchor_right == 1.0)
	assert(viewer.fps_panel.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	assert(viewer.fps_label.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	assert(viewer.grid.columns == 1)
	assert(root.get_camera_3d() == viewer.world_camera)
	assert(viewer.preview_scroll.position == Vector2(12,12))
	assert(viewer.preview_scroll.size.x <= root.size.x * 0.4)
	var a = viewer.tiles["alpha"]
	var b = viewer.tiles["bravo"]
	assert(a.title.text == "Camera: fpv / Drone: alpha")
	assert(b.title.text == "Camera: fpv / Drone: bravo")
	assert(a.viewport != b.viewport and a.camera != b.camera)
	assert(a.viewport.size == Vector2i(640, 480))
	assert(b.viewport.size == Vector2i(320, 240))
	assert(a.camera.fov == 75 and b.camera.fov == 60)
	assert(a.viewport.world_3d == b.viewport.world_3d)
	assert(a.camera.position.is_equal_approx(Vector3(0.15,3,0)))
	assert((-a.camera.basis.z).is_equal_approx(Vector3(cos(deg_to_rad(10)), -sin(deg_to_rad(10)), 0)))
	assert(viewer.grid.get_child(0) == a.tile)
	var original_distance = viewer.world_camera.distance
	var wheel = InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	wheel.pressed = true
	viewer.world_camera._unhandled_input(wheel)
	assert(viewer.world_camera.distance < original_distance)
	viewer.world_camera.distance = original_distance
	viewer.world_camera.update_pose()
	var original_size = root.size
	root.size = Vector2i(1000,700)
	viewer.layout()
	assert(viewer.preview_scroll.size.x <= 400)
	await process_frame
	assert(abs(viewer.fps_panel.get_global_rect().end.x - (root.size.x - 12)) < 1)
	root.size = original_size
	viewer.layout()
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/bullet-drone-godot.png")
	await create_timer(2.1).timeout
	assert(viewer.registry.stale("alpha", Time.get_ticks_msec() / 1000.0))
	print("Two-view UDP/grid/staleness smoke checks passed; /tmp/bullet-drone-godot.png")
	quit()
