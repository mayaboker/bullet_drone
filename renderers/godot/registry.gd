extends RefCounted
# Receiver-time ownership; physics coordinates remain unchanged on the wire.
const STALE_SECONDS = 2.0
var drones: Dictionary = {}

static func numeric(value) -> bool:
	return (value is float or value is int) and is_finite(float(value))

static func vector(value, count: int) -> bool:
	if not value is Array or value.size() != count:
		return false
	for entry in value:
		if not numeric(entry):
			return false
	return true

static func identifier(value) -> bool:
	return value is String and not value.strip_edges().is_empty() and value.length() <= 128

static func valid(packet) -> bool:
	if not packet is Dictionary or packet.get("version") != 1:
		return false
	if not identifier(packet.get("stream_id")) or not numeric(packet.get("sequence")):
		return false
	var sequence = packet.sequence
	if sequence < 0 or sequence != floor(sequence):
		return false
	var s = packet.get("snapshot")
	var c = packet.get("camera")
	if not s is Dictionary or not c is Dictionary:
		return false
	if not identifier(s.get("drone_id")) or not identifier(s.get("episode_id")):
		return false
	if not numeric(s.get("step_index")) or s.step_index < 0 or s.step_index != floor(s.step_index):
		return false
	if not numeric(s.get("simulation_time_s")) or s.simulation_time_s < 0:
		return false
	if not vector(s.get("position_m"), 3) or not vector(s.get("orientation_xyzw"), 4):
		return false
	var q: Array = s.orientation_xyzw
	var norm = Quaternion(q[0], q[1], q[2], q[3]).length()
	if not is_finite(norm) or abs(norm - 1.0) > 0.001:
		return false
	var sources = s.get("sources")
	if not sources is Dictionary:
		return false
	for name in ["position", "altitude", "attitude"]:
		if sources.get(name) != "ground_truth":
			return false
	for name in ["width_px", "height_px"]:
		if not numeric(c.get(name)) or c[name] != floor(c[name]) or c[name] <= 0 or c[name] > 8192:
			return false
	return numeric(c.get("fov_y_deg")) and c.fov_y_deg > 0 and c.fov_y_deg < 180 and vector(c.get("mount_position_body_m"), 3) and numeric(c.get("downward_tilt_deg")) and abs(c.downward_tilt_deg) < 90

func accept(packet, now: float) -> bool:
	if not valid(packet):
		return false
	var id: String = packet.snapshot.drone_id
	if not drones.has(id):
		drones[id] = {"stream": packet.stream_id, "sequence": -1, "received": now, "retired": {}}
	var entry: Dictionary = drones[id]
	if entry.retired.has(packet.stream_id):
		return false
	if packet.stream_id != entry.stream:
		if now - entry.received <= STALE_SECONDS:
			return false
		entry.retired[entry.stream] = true
		entry.stream = packet.stream_id
		entry.sequence = -1
	if packet.sequence <= entry.sequence:
		return false
	entry.sequence = packet.sequence
	entry.received = now
	entry.packet = packet
	return true

func stale(id: String, now: float) -> bool:
	return now - drones[id].received > STALE_SECONDS

static func position(v: Array) -> Vector3:
	return Vector3(v[0], v[2], -v[1])

static func orientation(q: Array) -> Quaternion:
	return Quaternion(q[0], q[2], -q[1], q[3]).normalized()

static func camera_basis(tilt_deg: float) -> Basis:
	var tilt = deg_to_rad(tilt_deg)
	var forward = Vector3(cos(tilt), -sin(tilt), 0)
	var up = Vector3(sin(tilt), cos(tilt), 0)
	return Basis(forward.cross(up), up, -forward)
