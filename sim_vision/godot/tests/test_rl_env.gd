extends GutTest

const RobotScene: PackedScene = preload("res://scenes/robot.tscn")
const RoomScene: PackedScene = preload("res://scenes/room.tscn")
const HumanScene: PackedScene = preload("res://scenes/human.tscn")
const RLEnvBridge = preload("res://scripts/rl_env_bridge.gd")
const RLController = preload("res://scripts/rl_controller.gd")


func test_robot_lidar_fan_17_rays() -> void:
	var room := RoomScene.instantiate() as Room
	add_child_autofree(room)
	var robot := RobotScene.instantiate() as Robot
	add_child_autofree(robot)
	robot.global_position = Vector3(0.0, 0.0, 0.0)
	await wait_physics_frames(2)
	var readings: PackedFloat32Array = robot.get_lidar_readings()
	assert_eq(readings.size(), Robot.LIDAR_NUM_RAYS)
	for i: int in readings.size():
		assert_between(readings[i], 0.0, 1.0, "lidar ray %d normalized in [0, 1]" % i)
	assert_gt(robot.min_lidar_distance(), 0.5, "center of corridor is clear of walls")


func test_smart_floor1_destination_routing() -> void:
	# Floor 1 direct rooms & facilities
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "101", 1), "101")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "110", 1), "110")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "112", 1), "112")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "nha_thuoc", 1), "nha_thuoc")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "nha_ve_sinh", 1), "nha_ve_sinh")
	# Floor 1 lobby sub-counters map to tiep_don
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "bhyt", 1), "tiep_don")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "thu_ngan", 1), "tiep_don")
	# Floor 2–4 rooms/departments route to Elevator (thang_may)
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "301", 3), "thang_may")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "205", 1), "thang_may")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "401", 4), "thang_may")
	# Call staff & emergency route to nearest medical staff
	assert_eq(RLEnvBridge.resolve_destination_key("call_staff", "", 1), "staff")
	assert_eq(RLEnvBridge.resolve_destination_key("emergency", "101", 1), "staff")
	assert_eq(RLEnvBridge.resolve_destination_key("answer", "", 1), "")


func test_nlu_room_and_department_targets_are_routed() -> void:
	# NLU target ids (sim_vision/python/nlu/slots.py): room_<number> / dept_<slug>; floor comes from the room number
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "room_110", 1), "110")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "room_130", 1), "112", "floor-1 clinic alias")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "room_115", 1), "tiep_don", "result counter is in the lobby")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "room_205", 1), "thang_may", "floor-2 room: elevator first")
	assert_eq(RLEnvBridge.resolve_final_target("guide", "room_205", 1), "205")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "room_205", 1, 2), "205", "already on floor 2")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "dept_cap_cuu", 1), "101")
	assert_eq(RLEnvBridge.resolve_final_target("guide", "dept_tai_mui_hong", 1), "210")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "dept_tim_mach", 1), "thang_may", "floor 3 via the elevator")
	assert_eq(RLEnvBridge.resolve_final_target("guide", "room_302", 1), "302", "floor 3 is now simulated: room 302")
	assert_eq(RLEnvBridge.resolve_destination_key("guide", "room_302", 1, 3), "302", "already on floor 3")


func test_observation_vector_31_dims_and_bounds() -> void:
	var lidar := PackedFloat32Array()
	lidar.resize(Robot.LIDAR_NUM_RAYS)
	lidar.fill(0.8)
	var det := {"x1": 0.4, "y1": 0.1, "x2": 0.6, "y2": 0.7, "conf": 0.92}
	var obs: PackedFloat32Array = RLEnvBridge.build_observation(
		Vector3(0.0, 0.0, 0.0),
		0.0,
		Vector2(0.3, -0.4),
		lidar,
		det,
		RLEnvBridge.TaskPhase.GUIDE_ESCORT,
		Vector3(8.0, 0.0, -5.0),
		Vector3(0.0, 0.0, 1.5)
	)
	assert_eq(obs.size(), RLEnvBridge.OBS_DIM)
	assert_eq(obs[17], 1.0, "has_det = 1")
	assert_almost_eq(obs[18], 0.0, 1e-5, "cx - 0.5 = 0")
	assert_almost_eq(obs[19], 0.6, 1e-5, "h = 0.6")
	assert_eq(obs[23], 1.0, "GUIDE_ESCORT phase one-hot")
	for i: int in obs.size():
		assert_between(obs[i], -1.0, 1.0, "obs[%d] in [-1, 1]" % i)


func test_shared_team_reward_and_tether_shaping() -> void:
	# 1. Verbal answer completion (+10 R_team)
	var r_ans: Dictionary = RLEnvBridge.compute_step_reward(1.2, 1.2, RLEnvBridge.TaskPhase.APPROACH_PATIENT, 1.2, 2.0, "answer")
	assert_eq(r_ans["r_team"], RLEnvBridge.REWARD_ANSWER)
	assert_gt(float(r_ans["total"]), 9.9)

	# 2. Call staff / emergency completion (+20 R_team)
	var r_staff: Dictionary = RLEnvBridge.compute_step_reward(1.4, 1.2, RLEnvBridge.TaskPhase.CALL_STAFF, 0.0, 2.0, "call_staff")
	assert_eq(r_staff["r_team"], RLEnvBridge.REWARD_CALL_STAFF)
	assert_gt(float(r_staff["total"]), 20.0)

	# 3. Guide arrival with patient in tether (+30 R_team)
	var r_guide: Dictionary = RLEnvBridge.compute_step_reward(1.3, 1.0, RLEnvBridge.TaskPhase.GUIDE_ESCORT, 1.5, 2.0, "guide_completed")
	assert_eq(r_guide["r_team"], RLEnvBridge.REWARD_GUIDE_ARRIVED)
	assert_eq(r_guide["r_tether"], RLEnvBridge.BONUS_TETHER_GOOD)
	assert_gt(float(r_guide["total"]), 30.0)

	# 4. Outrunning elderly patient (> 2.5m tether) pauses progress reward and penalizes tether
	var r_stretch: Dictionary = RLEnvBridge.compute_step_reward(5.0, 4.5, RLEnvBridge.TaskPhase.GUIDE_ESCORT, 3.1, 2.0, "")
	assert_eq(r_stretch["r_progress"], 0.0, "progress paused when elderly patient left behind")
	assert_eq(r_stretch["r_tether"], RLEnvBridge.PENALTY_TETHER_STRETCH)

	# 5. Collision penalty when min_lidar < COLLISION_LIDAR_M
	var r_col: Dictionary = RLEnvBridge.compute_step_reward(3.0, 3.0, RLEnvBridge.TaskPhase.APPROACH_PATIENT, 0.0, 0.15, "")
	assert_true(bool(r_col["collided"]))
	assert_lt(float(r_col["total"]), -4.9)


func test_escorted_patient_follows_and_rl_controller_pauses_when_far() -> void:
	var human := HumanScene.instantiate() as Human
	add_child_autofree(human)
	human.global_position = Vector3(0.0, 0.0, 2.0)
	RLEnvBridge.step_escorted_patient(human, Vector3(0.0, 0.0, 0.0), 1.0)
	assert_lt(human.global_position.z, 2.0, "patient walked closer to robot")

	var lidar := PackedFloat32Array()
	lidar.resize(Robot.LIDAR_NUM_RAYS)
	lidar.fill(1.0)
	# When patient is > 2.5m behind, robot waits (v = 0)
	var wait_cmd: Vector2 = RLController.step_towards_goal_with_lidar(
		Vector3(0.0, 0.0, 0.0), 0.0, Vector3(0.0, 0.0, -5.0), lidar, 3.0, true
	)
	assert_eq(wait_cmd, Vector2.ZERO, "robot waits when escorted elderly patient is > 2.5m behind")
