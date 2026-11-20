extends GutTest

const RobotScene: PackedScene = preload("res://scenes/robot.tscn")
const OverlayScene: PackedScene = preload("res://scenes/view_overlay.tscn")


func test_set_command_clamps_example() -> void:
	var robot := RobotScene.instantiate() as Robot
	add_child_autofree(robot)
	robot.set_command(2.0, -3.0)
	assert_almost_eq(robot.get_command().x, 0.8, 1e-6)
	assert_almost_eq(robot.get_command().y, -1.5, 1e-6)


func test_clamp_command_bounds() -> void:
	assert_eq(Robot.clamp_command(-0.5, 0.0), Vector2(0.0, 0.0), "không lùi")
	assert_almost_eq(Robot.clamp_command(0.3, 5.0).y, Config.OMEGA_MAX, 1e-6)
	assert_almost_eq(Robot.clamp_command(0.3, 0.5).x, 0.3, 1e-6)
	assert_almost_eq(Robot.clamp_command(0.3, 0.5).y, 0.5, 1e-6)


func test_camera_viewport() -> void:
	var robot := RobotScene.instantiate() as Robot
	add_child_autofree(robot)
	var vp: SubViewport = robot.get_camera_viewport()
	assert_eq(vp.size, Vector2i(Config.IMG_W, Config.IMG_H))
	assert_eq(vp.render_target_update_mode, SubViewport.UPDATE_ALWAYS)
	var cam := vp.get_node("RobotCamera") as Camera3D
	assert_almost_eq(cam.fov, 70.0, 1e-6)
	await wait_physics_frames(2)
	assert_almost_eq(cam.global_position.y, 1.2, 1e-4, "camera cao 1.2 m")


func test_front_obstacle_distance_inf_without_hit() -> void:
	var robot := RobotScene.instantiate() as Robot
	add_child_autofree(robot)
	await wait_physics_frames(2)
	assert_eq(robot.front_obstacle_distance(), INF)


func test_front_obstacle_distance_with_wall() -> void:
	# Đặt ở x = 50 để không chồng lên robot của test trước (chưa kịp giải phóng).
	var robot := RobotScene.instantiate() as Robot
	robot.position = Vector3(50, 0, 0)
	add_child_autofree(robot)
	var wall := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2, 2, 0.2)
	cs.shape = box
	wall.add_child(cs)
	add_child_autofree(wall)
	wall.position = Vector3(50, 0.5, -1.05)  # mặt tường ở z = -0.95, đầu tia ở z = -0.25
	await wait_physics_frames(3)
	assert_almost_eq(robot.front_obstacle_distance(), 0.7, 1e-3)


func test_moves_forward_along_minus_z() -> void:
	var robot := RobotScene.instantiate() as Robot
	add_child_autofree(robot)
	robot.set_command(0.5, 0.0)
	await wait_seconds(1.0)
	assert_almost_eq(robot.global_position.x, 0.0, 1e-3)
	assert_between(-robot.global_position.z, 0.4, 0.6)


func test_positive_omega_turns_left() -> void:
	# Mục 2.4: omega > 0 ➔ quay trái ➔ hướng trước (−Z) lệch về −X.
	var robot := RobotScene.instantiate() as Robot
	add_child_autofree(robot)
	robot.set_command(0.0, 1.0)
	await wait_seconds(0.5)
	var forward: Vector3 = -robot.global_transform.basis.z
	assert_lt(forward.x, 0.0)


func test_norm_to_pixel_example() -> void:
	var r: Rect2 = ViewOverlay.norm_to_pixel({"x1": 0.25, "y1": 0.25, "x2": 0.75, "y2": 0.75}, Vector2(320, 240))
	assert_eq(r.position, Vector2(80, 60))
	assert_eq(r.end, Vector2(240, 180))


func test_norm_to_pixel_full_frame() -> void:
	var r: Rect2 = ViewOverlay.norm_to_pixel({"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0}, Vector2(320, 240))
	assert_eq(r, Rect2(0, 0, 320, 240))


func test_overlay_texts() -> void:
	assert_eq(ViewOverlay.label_text({"conf": 0.87}), "person 0.87")
	assert_eq(ViewOverlay.connection_text(true), "YOLO: đã kết nối")
	assert_eq(ViewOverlay.connection_text(false), "YOLO: mất kết nối")


func test_overlay_layout_top_right() -> void:
	var overlay := OverlayScene.instantiate() as ViewOverlay
	add_child_autofree(overlay)
	assert_eq(overlay.size, Vector2(320, 240))
	assert_eq(overlay.anchor_left, 1.0)
	assert_eq(overlay.offset_right, -16.0)
	assert_eq(overlay.offset_top, 16.0)
	overlay.show_detections([{"x1": 0.25, "y1": 0.25, "x2": 0.75, "y2": 0.75, "conf": 0.87}], "SEARCH", true)
	await wait_process_frames(2)
	pass_test("show_detections không lỗi")
