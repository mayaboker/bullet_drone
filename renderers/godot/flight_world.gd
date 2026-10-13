extends Node3D
# Procedural, visual-only flight course. No collision bodies or physics effects.
const GRASS = Color(0.24, 0.38, 0.25)
const ASPHALT = Color(0.14, 0.19, 0.23)
const CHALK = Color(0.59, 0.7, 0.72)
const ORANGE = Color(1.0, 0.47, 0.12)
const BLUE = Color(0.12, 0.65, 0.95)
const MINT = Color(0.28, 0.87, 0.67)
# PyBullet world XY meters, matching the six position-flight tasks.
const PAD_POSITIONS_M = [Vector2(0, 0), Vector2(1.5, 0.25), Vector2(3, 0.5),
	Vector2(0, -0.75), Vector2(1.5, -1), Vector2(3, -1.25)]

func _ready():
	name = "FlightWorld"
	build_lighting()
	build_ground()
	build_landing_pads()
	build_gates()
	build_markers()
	build_landscape()

func material(color: Color) -> StandardMaterial3D:
	var surface = StandardMaterial3D.new()
	surface.albedo_color = color
	surface.roughness = 0.9
	return surface

func shape(mesh: Mesh, pos: Vector3, color: Color) -> MeshInstance3D:
	var node = MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = material(color)
	add_child(node)
	node.position = pos
	return node

func box(pos: Vector3, size: Vector3, color: Color) -> MeshInstance3D:
	var mesh = BoxMesh.new()
	mesh.size = size
	return shape(mesh, pos, color)

func cylinder(pos: Vector3, radius: float, height: float, color: Color, top_radius: float = -1.0):
	var mesh = CylinderMesh.new()
	mesh.top_radius = radius if top_radius < 0 else top_radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 16
	return shape(mesh, pos, color)

func label(text: String, pos: Vector3, color: Color = Color.WHITE) -> Label3D:
	var node = Label3D.new()
	node.text = text
	node.font_size = 48
	node.pixel_size = 0.006
	node.modulate = color
	node.outline_size = 8
	node.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(node)
	node.position = pos
	return node

func build_lighting():
	var sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38, -35, 0)
	sun.light_color = Color(1.0, 0.92, 0.8)
	sun.light_energy = 1.15
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 70
	add_child(sun)
	var sky_material = ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.2, 0.43, 0.68)
	sky_material.sky_horizon_color = Color(0.76, 0.85, 0.86)
	sky_material.ground_horizon_color = Color(0.76, 0.85, 0.86)
	sky_material.ground_bottom_color = GRASS
	sky_material.sun_angle_max = 5
	var sky = Sky.new()
	sky.sky_material = sky_material
	var environment = WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_SKY
	environment.environment.sky = sky
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color(0.73, 0.84, 1.0)
	environment.environment.ambient_light_energy = 0.45
	add_child(environment)

func build_ground():
	box(Vector3(0, -0.065, 0), Vector3(180, 0.1, 180), GRASS)
	# Large color patches give the field depth without textures or randomness.
	for x in range(-40, 61, 10):
		for z in [-25, -15, 15, 25]:
			var tone = GRASS.lightened(0.035 * ((x / 10 + z) % 3 + 1))
			box(Vector3(x, -0.012, z), Vector3(9.8, 0.005, 9.8), tone)
	box(Vector3(9, -0.008, 0), Vector3(36, 0.01, 8), ASPHALT)
	for x in range(-9, 28):
		box(Vector3(x, 0.0, 0), Vector3(0.012, 0.002, 8), CHALK.darkened(0.25))
	for z in range(-4, 5):
		box(Vector3(9, 0.0, z), Vector3(36, 0.002, 0.012), CHALK.darkened(0.25))
	for z in [-4.1, 4.1]:
		box(Vector3(9, 0.006, z), Vector3(36, 0.008, 0.09), BLUE)
	for x in range(5, 27, 2):
		box(Vector3(x, 0.007, 0), Vector3(0.7, 0.01, 0.06), ORANGE)
	label("BULLET / FLIGHT FIELD", Vector3(5, 0.8, -4.7), BLUE)

func build_landing_pads():
	var colors = [ORANGE, BLUE, MINT]
	for index in range(PAD_POSITIONS_M.size()):
		var home = PAD_POSITIONS_M[index]
		var pos = Vector3(home.x, 0.003, -home.y)
		var color = colors[index % colors.size()]
		cylinder(pos, 0.32, 0.005, color)
		cylinder(pos + Vector3(0, 0.003, 0), 0.275, 0.005, ASPHALT)
		for x in [-0.1, 0.1]:
			box(pos + Vector3(x, 0.008, 0), Vector3(0.035, 0.004, 0.24), Color.WHITE)
		box(pos + Vector3(0, 0.008, 0), Vector3(0.2, 0.004, 0.035), Color.WHITE)
		var sign = label("PAD %02d" % (index + 1), pos + Vector3(0, 0.08, 0.38), color)
		sign.pixel_size = 0.003

func build_gates():
	var colors = [ORANGE, BLUE, MINT]
	for index in range(3):
		var x = 7.0 + index * 7.0
		var color = colors[index]
		# Opening faces world/body +X: FPV sees nested gates at 3 m altitude.
		for z in [-1.75, 1.75]:
			box(Vector3(x, 2.5, z), Vector3(0.18, 5, 0.18), color)
			box(Vector3(x, 0.06, z), Vector3(0.75, 0.12, 0.75), ASPHALT)
			for h in range(1, 5):
				box(Vector3(x, h, z), Vector3(0.19, 0.15, 0.19), Color.WHITE)
		box(Vector3(x, 5, 0), Vector3(0.18, 0.2, 3.7), color)
		label("GATE %02d" % (index + 1), Vector3(x, 5.5, 0), color)

func build_markers():
	for x in range(0, 26, 5):
		for z in [-4.5, 4.5]:
			box(Vector3(x, 1.5, z), Vector3(0.045, 3, 0.045), CHALK)
			for h in range(1, 4):
				box(Vector3(x, h, z), Vector3(0.12, 0.035, 0.12), ORANGE)
				var marker = label("%dm / %dm" % [x, h], Vector3(x, h, z), CHALK)
				marker.pixel_size = 0.0035

func tree(pos: Vector3, height: float):
	cylinder(pos + Vector3(0, height * 0.25, 0), 0.12, height * 0.5, Color(0.34, 0.23, 0.17))
	for tier in range(3):
		var radius = height * (0.28 - tier * 0.06)
		var y = height * (0.48 + tier * 0.2)
		cylinder(pos + Vector3(0, y, 0), radius, height * 0.5, Color(0.12, 0.3 + tier * 0.045, 0.23), 0)

func build_landscape():
	for index in range(12):
		var x = -10 + index * 4.5
		for side in [-1, 1]:
			tree(Vector3(x, 0, side * (7.5 + (index % 3))), 3.0 + (index % 4) * 0.6)
	for index in range(7):
		var mesh = SphereMesh.new()
		mesh.radius = 1
		mesh.height = 2
		mesh.radial_segments = 16
		mesh.rings = 8
		var hill = shape(mesh, Vector3(35 + index * 8, -2, -35 + (index % 3) * 26), GRASS.darkened(0.08))
		hill.scale = Vector3(16, 6 + index % 4, 12)
	# A small spectator shelter and striped wind-direction mast beside the course.
	box(Vector3(-3, 2.4, -7), Vector3(4, 0.15, 3), BLUE.darkened(0.25))
	for x in [-4.6, -1.4]:
		for z in [-8.2, -5.8]:
			box(Vector3(x, 1.2, z), Vector3(0.08, 2.4, 0.08), CHALK)
	box(Vector3(-3, 0.6, -7), Vector3(2.8, 0.15, 0.6), Color(0.48, 0.32, 0.2))
	cylinder(Vector3(4, 2, 6), 0.045, 4, CHALK)
	for index in range(5):
		var sock = cylinder(Vector3(4.2 + index * 0.2, 4, 6), 0.15 - index * 0.016, 0.2, ORANGE if index % 2 == 0 else Color.WHITE)
		sock.rotation.z = PI / 2
