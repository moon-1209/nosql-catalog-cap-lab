extends GutTest

const MainScene: PackedScene = preload("res://scenes/main.tscn")
const S := Config.RobotState
const EXAMPLE: String = '{"type":"transcript","utt_id":3,"clip_id":"A_07_r","text":"...","intent":"hoi_phong","intent_conf":1.0,"slots":{},"response":"...","stt_ms":500,"audio_s":2,"effective_snr_db":20}'


class FakeStt:
	extends SttClient
	var sent: Array = []
	var online: bool = true

	func _process(_delta: float) -> void:
		pass

	func is_server_connected() -> bool:
		return online

	func send_utterance(utt_id: int, clip_id: String, distance_m: float, snr_db: float, noise: String) -> bool:
		if not online:
			return false
		sent.append(SttClient.build_utterance(utt_id, clip_id, distance_m, snr_db, noise))
		return true


# --- parse_transcript ---

func test_parse_transcript_example() -> void:
	var r: Dictionary = SttClient.parse_transcript(EXAMPLE)
	assert_true(r["ok"], r["error"])
	assert_eq(r["utt_id"], 3)
	assert_eq(r["clip_id"], "A_07_r")
	assert_eq(r["intent"], "hoi_phong")
	assert_almost_eq(r["stt_ms"], 500.0, 1e-6)
	assert_almost_eq(float(r["effective_snr_db"]), 20.0, 1e-6)


func test_parse_transcript_nulls_from_server_without_nlu() -> void:
	var r: Dictionary = SttClient.parse_transcript('{"type":"transcript","utt_id":1,"clip_id":"A_07_r","text":"phòng hai trăm","intent":null,"intent_conf":null,"slots":null,"response":null,"stt_ms":300.5,"audio_s":3.84,"effective_snr_db":null}')
	assert_true(r["ok"], r["error"])
	assert_eq(r["intent"], "")
	assert_eq(r["response"], "")
	assert_eq(r["slots"], {})
	assert_null(r["effective_snr_db"])
	assert_eq(r["text"], "phòng hai trăm")


func test_parse_transcript_errors() -> void:
	var cases: Dictionary = {
		"abc": "invalid json",
		"[1]": "invalid json",
		'{"utt_id":1}': "missing field: type",
		'{"type":"detections","utt_id":1}': "invalid field: type",
		'{"type":"transcript","utt_id":1,"clip_id":"A","text":"x","stt_ms":1}': "missing field: audio_s",
		'{"type":"transcript","utt_id":-1,"clip_id":"A","text":"x","stt_ms":1,"audio_s":1}': "invalid field: utt_id",
		'{"type":"transcript","utt_id":1.5,"clip_id":"A","text":"x","stt_ms":1,"audio_s":1}': "invalid field: utt_id",
		'{"type":"transcript","utt_id":1,"clip_id":"","text":"x","stt_ms":1,"audio_s":1}': "invalid field: clip_id",
		'{"type":"transcript","utt_id":1,"clip_id":"A","text":5,"stt_ms":1,"audio_s":1}': "invalid field: text",
		'{"type":"transcript","utt_id":1,"clip_id":"A","text":"x","stt_ms":-1,"audio_s":1}': "invalid field: stt_ms",
		'{"type":"transcript","utt_id":1,"clip_id":"A","text":"x","stt_ms":1,"audio_s":1,"intent":3}': "invalid field: intent",
		'{"type":"transcript","utt_id":1,"clip_id":"A","text":"x","stt_ms":1,"audio_s":1,"slots":[]}': "invalid field: slots",
	}
	for text: String in cases:
		var r: Dictionary = SttClient.parse_transcript(text)
		assert_false(r["ok"], text)
		assert_eq(r["error"], cases[text], text)


func test_parse_server_error() -> void:
	var r: Dictionary = SttClient.parse_transcript('{"type":"error","utt_id":7,"message":"clip not found: A_99_n"}')
	assert_false(r["ok"])
	assert_eq(r["type"], "error")
	assert_eq(r["utt_id"], 7)
	assert_eq(r["error"], "clip not found: A_99_n")


func test_client_emits_signals() -> void:
	var c := SttClient.new()
	add_child_autofree(c)
	c.set_process(false)
	watch_signals(c)
	c.handle_message(EXAMPLE)
	c.handle_message('{"type":"error","utt_id":4,"message":"stt busy"}')
	assert_signal_emit_count(c, "transcript_received", 1)
	assert_signal_emitted_with_parameters(c, "error_received", [4, "stt busy"])


func test_build_utterance_matches_contract() -> void:
	assert_eq(SttClient.build_utterance(7, "A_07_n", 1.4, 20.0, "babble"),
			{"type": "utterance", "utt_id": 7, "clip_id": "A_07_n", "distance_m": 1.4, "snr_db": 20.0, "noise": "babble"})


# --- hàm thuần của dialogue_manager ---

func test_timeout_logic() -> void:
	assert_false(DialogueManager.is_timed_out(-1, 999999), "không chờ")
	assert_false(DialogueManager.is_timed_out(10000, 10000))
	assert_true(DialogueManager.is_timed_out(10000, 10001))


func test_accepts_only_waiting_utt_while_thinking() -> void:
	var r: Dictionary = {"utt_id": 3}
	assert_true(DialogueManager.accepts(r, 3, S.THINK))
	assert_false(DialogueManager.accepts({"utt_id": 2}, 3, S.THINK), "utt_id cũ bị bỏ")
	assert_false(DialogueManager.accepts(r, 3, S.ARRIVED), "đã timeout ➔ bỏ")


func test_clip_id_parts() -> void:
	assert_eq(DialogueManager.clip_speaker("A_C03_r"), "A")
	assert_eq(DialogueManager.clip_take("A_C03_r"), "r")
	assert_eq(DialogueManager.clip_take("B_07_n"), "n")
	assert_eq(DialogueManager.clip_take(""), "")


func test_dialogue_states_and_names() -> void:
	for s: int in [S.LISTEN, S.THINK, S.RESPOND]:
		assert_true(Main.is_dialogue_state(s))
	for s: int in [S.SEARCH, S.APPROACH, S.ARRIVED]:
		assert_false(Main.is_dialogue_state(s))
	assert_eq(Config.state_name(S.LISTEN), "LISTEN")
	assert_eq(Config.state_name(S.THINK), "THINK")
	assert_eq(Config.state_name(S.RESPOND), "RESPOND")


# --- phụ đề, log, overlay ---

func test_subtitle_lines() -> void:
	assert_eq(Subtitle.format_lines("phòng 205", "Dạ, phòng 205 ở tầng 2."),
			PackedStringArray(["Nghe được: phòng 205", "Robot: Dạ, phòng 205 ở tầng 2."]))
	assert_eq(Subtitle.format_lines("", Subtitle.SORRY)[0], "")


func test_subtitle_timer_emits_finished() -> void:
	var sub := (load("res://scenes/subtitle.tscn") as PackedScene).instantiate() as Subtitle
	add_child_autofree(sub)
	watch_signals(sub)
	sub.show_reply("a", "b", 0.2)
	assert_true(sub.is_showing())
	await wait_seconds(0.35)
	assert_false(sub.is_showing())
	assert_signal_emit_count(sub, "finished", 1)
	var reply := sub.get_node("Panel/Box/Reply") as Label
	assert_gte(reply.get_theme_font_size("font_size"), 22, "chữ ≥ 22 px")


func test_dialogue_log_row_escapes() -> void:
	var line: String = DialogueLogger.format_row({"utt_id": 1, "clip_id": "A_07_r", "hyp_text": 'phòng 205, "đi" đường nào',
			"distance_m": 1.4, "error": ""})
	assert_eq(line.get_slice(",", 1), "1")
	assert_true(line.contains('"phòng 205, ""đi"" đường nào"'))
	assert_eq(DialogueLogger.COLUMNS.size(), 21, "14 cột G16 + 7 cột G22")
	assert_eq(DialogueLogger.COLUMNS[13], "error", "cột cũ giữ nguyên vị trí")


func test_overlay_stt_text() -> void:
	assert_eq(ViewOverlay.stt_connection_text(true), "STT: đã kết nối")
	assert_eq(ViewOverlay.stt_connection_text(false), "STT: mất kết nối")


# --- tích hợp với main.tscn (STT giả, không ghi file) ---

func _main() -> Array:
	var main := MainScene.instantiate() as Main
	main.seed = 3
	for n: String in ["RunLogger", "DialogueLogger"]:
		main.get_node(n).free()
	var old: Node = main.get_node("SttClient")
	main.remove_child(old)
	old.free()
	var fake := FakeStt.new()
	fake.name = "SttClient"
	main.add_child(fake)
	main.move_child(fake, 0)
	add_child_autofree(main)
	main.vision.set_process(false)
	var dm := main.get_node("DialogueManager") as DialogueManager
	return [main, dm, fake]


func _transcript(utt_id: int) -> Dictionary:
	return SttClient.parse_transcript(JSON.stringify({"type": "transcript", "utt_id": utt_id, "clip_id": "A_07_r",
			"text": "phòng khám số hai trăm linh năm", "intent": "hoi_phong", "intent_conf": 1.0, "slots": {"room": "205"},
			"response": "Dạ, phòng 205 ở tầng 2.", "stt_ms": 320.0, "audio_s": 3.8, "effective_snr_db": 17.1}))


func test_full_turn_listen_think_respond_arrived() -> void:
	var parts: Array = _main()
	var main: Main = parts[0]
	var dm: DialogueManager = parts[1]
	var fake: FakeStt = parts[2]
	watch_signals(dm)
	main.state = S.ARRIVED
	dm.npc.state = Npc.TALK
	dm._on_talk_started("A_07_r")
	assert_eq(main.state, S.LISTEN)
	dm.npc.state = Npc.WAIT_REPLY
	dm._on_utterance_finished("A_07_r")
	assert_eq(main.state, S.THINK)
	assert_eq(fake.sent.size(), 1)
	var msg: Dictionary = fake.sent[0]
	assert_eq(msg["utt_id"], dm.utt_id)
	assert_eq(msg["noise"], "babble")
	assert_almost_eq(float(msg["snr_db"]), Config.DEFAULT_SNR_DB, 1e-6)
	assert_almost_eq(float(msg["distance_m"]), main.human_distance(), 1e-4, "khoảng cách thật XZ")
	# Transcript cũ bị bỏ, transcript đúng ➔ RESPOND.
	dm._on_transcript(_transcript(dm.utt_id - 1))
	assert_eq(main.state, S.THINK)
	dm._on_transcript(_transcript(dm.utt_id))
	assert_eq(main.state, S.RESPOND)
	assert_true(dm.subtitle.is_showing())
	assert_eq((dm.subtitle.get_node("Panel/Box/Heard") as Label).text, "Nghe được: phòng khám số hai trăm linh năm")
	assert_eq((dm.subtitle.get_node("Panel/Box/Reply") as Label).text, "Robot: Dạ, phòng 205 ở tầng 2.")
	var row: Dictionary = get_signal_parameters(dm, "turn_completed")[0]
	assert_eq(row["intent_pred"], "hoi_phong")
	assert_eq(row["speaker"], "A")
	assert_eq(row["error"], "")
	dm.subtitle.time_left = 0.01
	await wait_process_frames(3)
	assert_eq(main.state, S.ARRIVED)
	assert_eq(dm.npc.state, Npc.IDLE)
	assert_eq(dm.npc.turns_done, 1)


func test_timeout_says_sorry_and_returns_to_arrived() -> void:
	var parts: Array = _main()
	var main: Main = parts[0]
	var dm: DialogueManager = parts[1]
	watch_signals(dm)
	main.state = S.LISTEN
	dm._on_utterance_finished("A_07_r")
	dm.deadline_ms = Time.get_ticks_msec() - 1
	await wait_process_frames(2)
	assert_eq(main.state, S.ARRIVED)
	assert_eq((dm.subtitle.get_node("Panel/Box/Reply") as Label).text, "Robot: " + Subtitle.SORRY)
	assert_eq(get_signal_parameters(dm, "turn_completed")[0]["error"], "timeout")
	dm._on_transcript(_transcript(dm.utt_id))
	assert_eq(main.state, S.ARRIVED, "transcript đến muộn sau timeout bị bỏ")


func test_server_error_and_disconnect() -> void:
	var parts: Array = _main()
	var main: Main = parts[0]
	var dm: DialogueManager = parts[1]
	var fake: FakeStt = parts[2]
	watch_signals(dm)
	main.state = S.LISTEN
	dm._on_utterance_finished("A_07_r")
	dm._on_stt_error(dm.utt_id + 5, "stt busy")
	assert_eq(main.state, S.THINK, "lỗi của utt khác bị bỏ")
	dm._on_stt_error(dm.utt_id, "stt busy")
	assert_eq(main.state, S.ARRIVED)
	assert_eq(get_signal_parameters(dm, "turn_completed")[0]["error"], "server: stt busy")
	fake.online = false
	main.state = S.LISTEN
	dm._on_utterance_finished("A_07_r")
	assert_eq(main.state, S.ARRIVED, "mất kết nối ➔ xin lỗi ngay, không treo")
	assert_eq(get_signal_parameters(dm, "turn_completed")[0]["error"], "stt disconnected")


func test_disconnect_while_thinking() -> void:
	var parts: Array = _main()
	var main: Main = parts[0]
	var dm: DialogueManager = parts[1]
	main.state = S.LISTEN
	dm._on_utterance_finished("A_07_r")
	dm._on_stt_connection_changed(false)
	assert_eq(main.state, S.ARRIVED)


func test_robot_held_still_in_dialogue_states() -> void:
	var parts: Array = _main()
	var main: Main = parts[0]
	var big_left := {"x1": 0.0, "y1": 0.1, "x2": 0.2, "y2": 0.4, "conf": 0.9}  # controller sẽ quay mạnh
	for s: int in [S.LISTEN, S.THINK, S.RESPOND]:
		main.state = s
		main.robot.set_command(0.3, 0.3)
		main._on_detections(1, [big_left], 20.0)
		assert_eq(main.state, s, Config.state_name(s))
		assert_eq(main.robot.get_command(), Vector2.ZERO, Config.state_name(s))
	main.state = S.ARRIVED
	main._on_detections(2, [big_left], 20.0)
	assert_ne(main.robot.get_command(), Vector2.ZERO, "ARRIVED ➔ controller chạy lại")


func test_talk_aborted_returns_to_arrived() -> void:
	var parts: Array = _main()
	var main: Main = parts[0]
	var dm: DialogueManager = parts[1]
	main.state = S.ARRIVED
	dm._on_talk_started("A_07_r")
	dm._on_talk_aborted("A_07_r")
	assert_eq(main.state, S.ARRIVED)


func test_reset_clears_dialogue() -> void:
	var parts: Array = _main()
	var main: Main = parts[0]
	var dm: DialogueManager = parts[1]
	main.state = S.LISTEN
	dm._on_utterance_finished("A_07_r")
	main.reset_positions()
	assert_eq(main.state, S.SEARCH)
	assert_eq(dm.deadline_ms, -1)
	assert_eq(dm.npc.state, Npc.IDLE)
	dm._on_transcript(_transcript(dm.utt_id))
	assert_eq(main.state, S.SEARCH, "transcript của lượt trước reset bị bỏ")
