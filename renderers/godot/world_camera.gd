extends Camera3D
# Display-only orbit camera. Receives visual positions, never touches physics.
var target = Vector3(0, 1, 0)
var distance = 4.0
var yaw = -0.65
var pitch = 0.4
var dragging = false

func _ready():
	name = "WorldCamera"
	near = 0.02
	far = 150
	current = true
	update_pose()

func frame_positions(positions: Array):
	if not positions.is_empty():
		var bounds = AABB(positions[0], Vector3.ZERO)
		for position in positions:
			bounds = bounds.expand(position)
		target = bounds.get_center()
	update_pose()

func update_pose():
	var direction = Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))
	position = target + direction * distance
	look_at(target, Vector3.UP)

func _unhandled_input(event):
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			dragging = event.pressed
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			distance = maxf(0.5, distance * 0.85)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			distance = minf(100.0, distance / 0.85)
	elif event is InputEventMouseMotion and dragging:
		yaw -= event.relative.x * 0.005
		pitch = clampf(pitch + event.relative.y * 0.005, 0.05, 1.4)
	update_pose()

func _notification(what):
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		dragging = false
