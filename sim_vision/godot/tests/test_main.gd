extends GutTest

const MainScene: PackedScene = preload("res://scenes/main.tscn")
const RoomScene: PackedScene = preload("res://scenes/room.tscn")
const CMD := {"state": Config.RobotState.APPROACH, "v": 0.5, "omega": 0.2, "target": {}}


func test_safety_too_close_to_human() -> void:
	var out: Dictionary = Main.apply_safety(CMD, 0.7, 2.0)
	assert_eq(out["v"], 0.0)
	assert_almost_eq(out["omega"], 0.2, 1e-6)
	assert_eq(out["state"], Config.RobotState.APPROACH)


func test_safety_obstacle_ahead() -> void:
	var out: Dictionary = Main.apply_safety(CMD, 2.0, 0.4)
	assert_eq(out["v"], 0.0)
	assert_almost_eq(out["omega"], 0.2, 1e-6)


func test_safety_clear_unchanged() -> void:
	assert_eq(Main.apply_safety(CMD, 2.0, 2.0), CMD)


func test_safety_no_obstacle_inf() -> void:
	assert_eq(Main.apply_safety(CMD, 2.0, INF), CMD)


func test_safety_thresholds_strict() -> void:
	# Điều kiện là "<": đúng bằng ngưỡng thì vẫn được tiến.
	assert_almost_eq(Main.apply_safety(CMD, Config.SAFE_DIST_HUMAN, 2.0)["v"], 0.5, 1e-6)
	assert_almost_eq(Main.apply_safety(CMD, 2.0, Config.SAFE_DIST_OBSTACLE)["v"], 0.5, 1e-6)


func test_safety_does_not_mutate_input() -> void:
	var cmd: Dictionary = CMD.duplicate()
	Main.apply_safety(cmd, 0.1, 0.1)
	assert_eq(cmd, CMD)


func _room() -> Room:
	var r := RoomScene.instantiate() as Room
	add_child_autofree(r)
	return r


func test_start_positions_separated_and_free() -> void:
	var r: Room = _room()
	var rects: Array[Rect2] = r.get_obstacle_footprints()
	for s: int in 50:
		var rng := RandomNumberGenerator.new()
		rng.seed = s
		var p: Dictionary = Main.pick_start_positions(r, rng)
		assert_eq(p["robot"], r.get_robot_dock()["position"], "seed %d: shift starts at the robot dock" % s)
		assert_true(Human.flat_distance(p["robot"], p["human"]) >= 3.5, "seed %d separation" % s)
		for key: String in ["robot", "human"]:
			var pos: Vector3 = p[key]
			assert_true(absf(pos.x) <= 11.4 and absf(pos.z) <= 8.4, "seed %d %s inside" % [s, key])
			assert_true(Room.is_clear(pos, rects, 0.6), "seed %d %s clear" % [s, key])
		assert_between(p["robot_yaw"], -PI, PI)


func test_start_positions_same_seed_same_result() -> void:
	var r: Room = _room()
	var a := RandomNumberGenerator.new()
	var b := RandomNumberGenerator.new()
	a.seed = 123
	b.seed = 123
	assert_eq(Main.pick_start_positions(r, a), Main.pick_start_positions(r, b))
	var c := RandomNumberGenerator.new()
	c.seed = 124
	assert_ne(Main.pick_start_positions(r, a), Main.pick_start_positions(r, c), "seed khác ➔ kết quả khác")


func test_camera_mode_cycles_and_toggles_ceiling() -> void:
	var main := MainScene.instantiate() as Main
	main.seed = 1
	for n: String in ["RunLogger", "DialogueLogger"]:
		var node: Node = main.get_node_or_null(NodePath(n))
		if node != null:
			node.free()
	add_child_autofree(main)
	main.vision.set_process(false)

	# 1. Ban đầu là FOLLOW (ở độ cao trong phòng < 3.2m trần nhà), trần nhà hiện để đúng không gian và không bị chói sáng
	assert_eq(main.camera_mode, Main.CameraMode.FOLLOW)
	assert_not_null(main.ceiling_mesh)
	assert_true(main.ceiling_mesh.visible, "Trần nhà phải hiện ở FOLLOW")
	assert_true(main.viewer_camera.global_position.y <= 2.8, "Camera FOLLOW phải ở dưới trần nhà")

	# 2. Đổi sang TOP_DOWN ➔ trần nhà tự ẩn để quan sát toàn bộ mặt bằng, góc nhìn vừa vặn (Y=13.0)
	main.camera_mode = Main.CameraMode.TOP_DOWN
	main._update_viewer_camera()
	assert_false(main.ceiling_mesh.visible, "Trần nhà phải ẩn ở TOP_DOWN")
	assert_almost_eq(main.viewer_camera.global_position.y, 13.0, 0.1)

	# 3. Đổi sang LOBBY ➔ trần nhà hiện lại, camera ở sảnh lễ tân
	main.camera_mode = Main.CameraMode.LOBBY
	main._update_viewer_camera()
	assert_true(main.ceiling_mesh.visible, "Trần nhà phải hiện ở LOBBY")
	assert_almost_eq(main.viewer_camera.global_position.x, -4.0, 0.1)
	assert_almost_eq(main.viewer_camera.global_position.z, 7.8, 0.1)

	# 4. Quay lại FOLLOW ➔ vị trí và tầm nhìn chuẩn, trần nhà vẫn hiện
	main.camera_mode = Main.CameraMode.FOLLOW
	main._update_viewer_camera()
	assert_true(main.ceiling_mesh.visible, "Trần nhà giữ hiện khi về FOLLOW")


func test_wall_transparency_when_occluded() -> void:
	var main := MainScene.instantiate() as Main
	main.seed = 1
	for n: String in ["RunLogger", "DialogueLogger"]:
		var node: Node = main.get_node_or_null(NodePath(n))
		if node != null:
			node.free()
	add_child_autofree(main)
	main.vision.set_process(false)

	# Robot ở trong phòng cấp cứu 101 tại (-7.0, 0.0, -5.5), camera ở hành lang (-7.0, 1.5, 0.0)
	# Tường hành lang bắc NorthCorrWall2 ở Z = -2.0 chắn giữa camera và robot
	main.robot.global_position = Vector3(-7.0, 0.0, -5.5)
	main.viewer_camera.global_position = Vector3(-7.0, 1.5, 0.0)
	main.camera_mode = Main.CameraMode.FOLLOW
	main._update_wall_transparency()

	assert_gt(main._occluding_walls.size(), 0, "Tường chắn giữa camera và robot phải được phát hiện")
	var wall: MeshInstance3D = main._occluding_walls[0]
	assert_not_null(wall.material_override, "Tường chắn phải được gán material_override trong suốt")
	var mat: StandardMaterial3D = wall.material_override as StandardMaterial3D
	assert_eq(mat.transparency, BaseMaterial3D.TRANSPARENCY_ALPHA)
	assert_almost_eq(mat.albedo_color.a, 0.22, 0.01)

	# Camera di chuyển vào cùng phòng (-7.0, 1.5, -4.0) ➔ không còn vật cản
	main.viewer_camera.global_position = Vector3(-7.0, 1.5, -4.0)
	main._update_wall_transparency()
	assert_eq(main._occluding_walls.size(), 0, "Không còn tường chắn khi camera nhìn trực tiếp")
	assert_null(wall.material_override, "material_override của tường phải được xóa")
