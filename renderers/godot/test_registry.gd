extends SceneTree
const Registry = preload("res://registry.gd")
func packet(id="one", stream="a", sequence=0):
	return {"version":1,"stream_id":stream,"sequence":sequence,
	"snapshot":{"drone_id":id,"episode_id":"episode","step_index":sequence,"simulation_time_s":0.0,"position_m":[1,2,3],"orientation_xyzw":[0,0,0,1],"sources":{"position":"ground_truth","altitude":"ground_truth","attitude":"ground_truth"}},
	"camera":{"width_px":640,"height_px":480,"fov_y_deg":75,"mount_position_body_m":[0.15,0,0],"downward_tilt_deg":10}}
func _initialize():
	var r = Registry.new()
	assert(r.accept(packet(), 0))
	assert(not r.accept(packet(), 0.1))
	assert(not r.accept(packet("one", "b"), 1))
	assert(r.accept(packet("two"), 1))
	assert(r.stale("one", 2.1))
	assert(r.accept(packet("one", "b"), 2.1))
	assert(not r.accept(packet("one", "a", 20), 2.2))
	assert(not r.accept({}, 2.2))
	assert(Registry.position([1,2,3]).is_equal_approx(Vector3(1,3,-2)))
	var basis = Registry.camera_basis(10)
	assert((-basis.z).is_equal_approx(Vector3(cos(deg_to_rad(10)), -sin(deg_to_rad(10)), 0)))
	assert(is_equal_approx(basis.determinant(), 1.0))
	var yaw = Registry.orientation([0,0,sin(PI/4),cos(PI/4)])
	assert((yaw * Vector3.RIGHT).is_equal_approx(Vector3(0,0,-1)))
	var roll = Registry.orientation([sin(PI/4),0,0,cos(PI/4)])
	assert((roll * Vector3(0,0,-1)).is_equal_approx(Vector3.UP))
	var pitch = Registry.orientation([0,sin(PI/4),0,cos(PI/4)])
	assert((pitch * Vector3.RIGHT).is_equal_approx(Vector3.DOWN))
	for key in ["position_m", "orientation_xyzw", "sources", "step_index"]:
		var invalid = packet()
		invalid.snapshot[key] = null
		assert(not Registry.valid(invalid))
	assert(r.accept(packet("two", "a", 3), 3.0))
	assert(not r.accept(packet("two", "a", 2), 3.0))
	assert(r.drones["two"].packet.sequence == 3)
	print("Registry and coordinate checks passed")
	quit()
