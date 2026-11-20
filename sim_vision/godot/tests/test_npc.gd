extends GutTest

const HumanScene: PackedScene = preload("res://scenes/human.tscn")
const S := Config.RobotState
const TEST_DIR: String = "user://test_voices"

var robot_state: int = S.ARRIVED


# --- next_state (bảng ví dụ G15.3) ---

func test_next_state_examples() -> void:
	assert_eq(Npc.next_state(Npc.IDLE, S.ARRIVED, 1.5, 0.0, 0), Npc.NOTICE)
	assert_eq(Npc.next_state(Npc.IDLE, S.APPROACH, 1.5, 0.0, 0), Npc.IDLE)
	assert_eq(Npc.next_state(Npc.IDLE, S.ARRIVED, 1.5, 3.0, 0), Npc.IDLE, "đang cooldown")
	assert_eq(Npc.next_state(Npc.TALK, S.ARRIVED, 3.5, 0.0, 0), Npc.IDLE, "robot bỏ đi")


func test_next_state_boundaries() -> void:
	assert_eq(Npc.next_state(Npc.IDLE, S.ARRIVED, Config.TALK_TRIGGER_DIST, 0.0, 0), Npc.NOTICE, "đúng 2.0 m vẫn nói")
	assert_eq(Npc.next_state(Npc.IDLE, S.ARRIVED, 2.01, 0.0, 0), Npc.IDLE)
	assert_eq(Npc.next_state(Npc.IDLE, S.ARRIVED, 1.0, 0.0, Config.MAX_TURNS), Npc.IDLE, "hết lượt")
	assert_eq(Npc.next_state(Npc.TALK, S.LISTEN, 3.0, 0.0, 0), Npc.TALK, "đúng 3.0 m chưa tính là bỏ đi")
	assert_eq(Npc.next_state(Npc.WAIT_REPLY, S.THINK, 5.0, 0.0, 0), Npc.WAIT_REPLY)
	assert_eq(Npc.next_state(Npc.NOTICE, S.SEARCH, 5.0, 0.0, 0), Npc.NOTICE)
	for rs: int in [S.SEARCH, S.APPROACH, S.LISTEN, S.THINK, S.RESPOND]:
		assert_eq(Npc.next_state(Npc.IDLE, rs, 1.0, 0.0, 0), Npc.IDLE, "chỉ bắt đầu khi ARRIVED")


# --- góc quay ---

func test_shortest_turn_170_to_minus_170() -> void:
	var d: float = Npc.shortest_turn(deg_to_rad(170.0), deg_to_rad(-170.0))
	assert_almost_eq(rad_to_deg(d), 20.0, 1e-4, "quay 20°, không quay 340°")
	assert_almost_eq(rad_to_deg(Npc.shortest_turn(deg_to_rad(-170.0), deg_to_rad(170.0))), -20.0, 1e-4)


func test_shortest_turn_range() -> void:
	for a: int in range(-720, 721, 37):
		for b: int in range(-360, 361, 45):
			var d: float = Npc.shortest_turn(deg_to_rad(a), deg_to_rad(b))
			assert_true(absf(d) <= PI + 1e-6)
			assert_almost_eq(wrapf(deg_to_rad(a) + d - deg_to_rad(b), -PI, PI), 0.0, 1e-4)


func test_yaw_towards_faces_plus_z() -> void:
	assert_almost_eq(Npc.yaw_towards(Vector3.ZERO, Vector3(0, 0, 2)), 0.0, 1e-6)
	assert_almost_eq(Npc.yaw_towards(Vector3.ZERO, Vector3(2, 5, 0)), PI / 2, 1e-6)
	assert_almost_eq(absf(Npc.yaw_towards(Vector3(1, 0, 1), Vector3(1, 0, -3))), PI, 1e-6)


# --- chọn clip ---

func _clips() -> Dictionary:
	return {
		"A_07_r": {"speaker": "A", "intent": "hoi_phong"},
		"A_07_n": {"speaker": "A", "intent": "hoi_phong"},
		"A_25_r": {"speaker": "A", "intent": "cap_cuu"},
		"B_01_r": {"speaker": "B", "intent": "dang_ky_kham"},
	}


func test_pick_clip_speaker_and_fresh_intent() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var used: Array[String] = ["hoi_phong"]
	for i: int in 10:
		assert_eq(Npc.pick_clip(_clips(), "A", used, rng), "A_25_r")
	assert_eq(Npc.pick_clip(_clips(), "B", [] as Array[String], rng), "B_01_r")
	assert_eq(Npc.pick_clip(_clips(), "C", [] as Array[String], rng), "")
	var all_used: Array[String] = ["hoi_phong", "cap_cuu"]
	assert_true(Npc.pick_clip(_clips(), "A", all_used, rng).begins_with("A_"), "dùng hết ➔ chọn lại từ đầu")


func test_pick_clip_deterministic_with_seed() -> void:
	var a := RandomNumberGenerator.new()
	var b := RandomNumberGenerator.new()
	a.seed = 42
	b.seed = 42
	for i: int in 5:
		assert_eq(Npc.pick_clip(_clips(), "A", [] as Array[String], a), Npc.pick_clip(_clips(), "A", [] as Array[String], b))


# --- tích hợp với human.tscn ---

func _write_voice(id: String, seconds: float) -> void:
	DirAccess.make_dir_recursive_absolute(TEST_DIR)
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = 16000
	wav.stereo = false
	var data := PackedByteArray()
	data.resize(int(seconds * 16000) * 2)
	wav.data = data
	wav.save_to_wav(TEST_DIR.path_join(id + ".wav"))
	var f := FileAccess.open(TEST_DIR.path_join("clips.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify({id: {"speaker": "A", "intent": "hoi_phong", "duration_s": seconds}}))
	f.close()


func _setup(robot_pos: Vector3) -> Array:
	var human := HumanScene.instantiate() as Human
	add_child_autofree(human)
	var robot := Node3D.new()
	add_child_autofree(robot)
	robot.global_position = robot_pos
	var npc := human.get_node("Npc") as Npc
	npc.voices_dir = TEST_DIR
	robot_state = S.ARRIVED
	npc.setup(robot, func() -> int: return robot_state)
	return [human, robot, npc]


func test_scene_has_voice_player() -> void:
	var human := HumanScene.instantiate() as Human
	add_child_autofree(human)
	var voice := human.get_node("Head/Voice") as AudioStreamPlayer3D
	assert_eq(voice.attenuation_model, AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE)
	assert_eq(voice.unit_size, 5.0, "không suy giảm trong 5 m (tai ở camera góc phòng), người dùng thấy NPC quá nhỏ")
	assert_between((human.get_node("Head") as Node3D).position.y, 1.45, 1.75)
	assert_eq((human.get_node("Npc") as Npc).state, Npc.IDLE)


func test_notice_turns_then_talks_then_waits() -> void:
	_write_voice("A_07_r", 0.3)
	var parts: Array = _setup(Vector3(1.5, 0, 0))
	var human: Human = parts[0]
	var npc: Npc = parts[2]
	watch_signals(npc)
	await wait_process_frames(2)
	assert_eq(npc.state, Npc.NOTICE)
	await wait_seconds(Config.TURN_DURATION_S + 0.15)
	assert_eq(npc.state, Npc.TALK)
	assert_almost_eq(human.rotation.y, PI / 2, 0.02, "mặt hướng về robot (+X)")
	assert_signal_emitted_with_parameters(npc, "talk_started", ["A_07_r"])
	await wait_for_signal(npc.utterance_finished, 3.0)
	assert_eq(npc.state, Npc.WAIT_REPLY)
	assert_signal_emitted_with_parameters(npc, "utterance_finished", ["A_07_r"])
	npc.on_reply_shown()
	assert_eq(npc.state, Npc.IDLE)
	assert_eq(npc.turns_done, 1)
	assert_almost_eq(npc.cooldown_left, Config.NPC_COOLDOWN_S, 1e-6)
	await wait_process_frames(3)
	assert_eq(npc.state, Npc.IDLE, "MAX_TURNS = 1 ➔ không nói lại")


func test_robot_leaves_during_talk_stops_audio() -> void:
	_write_voice("A_07_r", 5.0)
	var parts: Array = _setup(Vector3(0, 0, 1.5))
	var robot: Node3D = parts[1]
	var npc: Npc = parts[2]
	watch_signals(npc)
	await wait_seconds(Config.TURN_DURATION_S + 0.2)
	assert_eq(npc.state, Npc.TALK)
	robot.global_position = Vector3(0, 0, 3.5)
	await wait_process_frames(2)
	assert_eq(npc.state, Npc.IDLE)
	assert_false((npc.get_node(^"../Head/Voice") as AudioStreamPlayer3D).playing)
	assert_signal_emitted(npc, "talk_aborted")
	assert_signal_not_emitted(npc, "utterance_finished")


func test_walking_paused_and_resumed() -> void:
	_write_voice("A_07_r", 0.2)
	var parts: Array = _setup(Vector3(0, 0, 1.2))
	var human: Human = parts[0]
	var npc: Npc = parts[2]
	human.waypoints = [Vector3(0, 0, 0), Vector3(0, 0, -2)] as Array[Vector3]
	human.walks = true
	await wait_process_frames(2)
	assert_false(human.walks, "dừng đi khi NOTICE")
	await wait_for_signal(npc.utterance_finished, 3.0)
	npc.on_reply_shown()
	assert_true(human.walks, "đi tiếp sau khi robot trả lời")


func test_missing_clip_returns_to_idle() -> void:
	var parts: Array = _setup(Vector3(1.0, 0, 0))
	var npc: Npc = parts[2]
	npc.clip_id = "Z_99_r"
	await wait_seconds(Config.TURN_DURATION_S + 0.15)
	assert_eq(npc.state, Npc.IDLE)
	assert_gt(npc.cooldown_left, 0.0)
	assert_push_error("cannot load voice clip")


func test_not_arrived_no_talk() -> void:
	var parts: Array = _setup(Vector3(1.0, 0, 0))
	var npc: Npc = parts[2]
	robot_state = S.APPROACH
	await wait_process_frames(3)
	assert_eq(npc.state, Npc.IDLE)
