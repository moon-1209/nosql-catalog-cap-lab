extends GutTest
## G22: tts_client (parse_audio, pcm16_to_stream), robot_voice, dialogue_manager với TTS giả.

const MainScene: PackedScene = preload("res://scenes/main.tscn")
const S = Config.RobotState
const TEST_DIR: String = "user://test_voices_g22"


class FakeStt:
	extends SttClient
	var sent: Array = []

	func _process(_delta: float) -> void:
		pass

	func is_server_connected() -> bool:
		return true

	func send_utterance(utt_id: int, clip_id: String, distance_m: float, snr_db: float, noise: String) -> bool:
		sent.append(SttClient.build_utterance(utt_id, clip_id, distance_m, snr_db, noise))
		return true


class FakeTts:
	extends TtsClient
	var sent: Array = []
	var online: bool = true

	func _process(_delta: float) -> void:
		pass

	func is_server_connected() -> bool:
		return online

	func send_speak(utt_id: int, text: String, voice: String) -> bool:
		if not online:
			return false
		sent.append(TtsClient.build_speak(utt_id, text, voice))
		return true


static func _pcm(seconds: float, rate: int = 24000) -> PackedByteArray:
	var b := PackedByteArray()
	b.resize(int(seconds * rate) * 2)
	return b


static func _audio_json(utt_id: int, seconds: float = 0.2, extra: Dictionary = {}) -> String:
	var m: Dictionary = {"type": "audio", "utt_id": utt_id, "sample_rate": 24000, "channels": 1,
			"pcm16_b64": Marshalls.raw_to_base64(_pcm(seconds)), "duration_s": seconds, "tts_ms": 85.3,
			"cache_hit": true}
	m.merge(extra, true)
	return JSON.stringify(m)


# --- parse_audio / pcm16_to_stream ---

func test_parse_audio_ok() -> void:
	var r: Dictionary = TtsClient.parse_audio(_audio_json(7))
	assert_true(r["ok"], r["error"])
	assert_eq(r["utt_id"], 7)
	assert_eq(r["sample_rate"], 24000)
	assert_eq((r["pcm"] as PackedByteArray).size(), 9600)
	assert_true(r["cache_hit"])
	assert_almost_eq(r["tts_ms"], 85.3, 1e-6)


func test_parse_audio_errors() -> void:
	var cases: Array = [
		["{bad", "invalid json"],
		[JSON.stringify({"utt_id": 1}), "missing field: type"],
		[JSON.stringify({"type": "transcript", "utt_id": 1}), "invalid field: type"],
		[JSON.stringify({"type": "audio", "utt_id": 1}), "missing field: sample_rate"],
		[_audio_json(1, 0.2, {"channels": 2}), "invalid field: channels"],
		[_audio_json(1, 0.2, {"sample_rate": -1}), "invalid field: sample_rate"],
		[_audio_json(1, 0.2, {"utt_id": 1.5}), "invalid field: utt_id"],
		[_audio_json(1, 0.2, {"cache_hit": "yes"}), "invalid field: cache_hit"],
		[_audio_json(1, 0.2, {"pcm16_b64": ""}), "empty audio"],
		[_audio_json(1, 0.2, {"pcm16_b64": Marshalls.raw_to_base64(PackedByteArray([1, 2, 3]))}),
				"invalid field: pcm16_b64"],
	]
	for c: Array in cases:
		var r: Dictionary = TtsClient.parse_audio(c[0])
		assert_false(r["ok"], c[1])
		assert_eq(r["error"], c[1])
	var e: Dictionary = TtsClient.parse_audio(JSON.stringify({"type": "error", "utt_id": 7, "message": "text too long"}))
	assert_eq([e["ok"], e["type"], e["utt_id"], e["error"]], [false, "error", 7, "text too long"])


func test_pcm16_to_stream_length() -> void:
	var s: AudioStreamWAV = TtsClient.pcm16_to_stream(_pcm(0.2), 24000)
	assert_eq(s.format, AudioStreamWAV.FORMAT_16_BITS)
	assert_eq(s.mix_rate, 24000)
	assert_false(s.stereo)
	assert_almost_eq(s.get_length(), 0.2, 1e-6)


func test_build_speak() -> void:
	assert_eq(TtsClient.build_speak(7, "Dạ.", "Ngọc Huyền"),
			{"type": "speak", "utt_id": 7, "text": "Dạ.", "voice": "Ngọc Huyền"})


func test_transcript_action_target_optional() -> void:
	var base := {"type": "transcript", "utt_id": 1, "clip_id": "A_07_r", "text": "x", "stt_ms": 1.0, "audio_s": 1.0}
	assert_eq(SttClient.parse_transcript(JSON.stringify(base))["action"], "", "server G14 không có action")
	base["action"] = "guide"
	base["target"] = "room_205"
	var r: Dictionary = SttClient.parse_transcript(JSON.stringify(base))
	assert_eq([r["action"], r["target"]], ["guide", "room_205"])
	base["action"] = 3
	assert_eq(SttClient.parse_transcript(JSON.stringify(base))["error"], "invalid field: action")


func test_alternate_clip() -> void:
	var clips := {"A_07_r": {"speaker": "A", "sentence_id": "07", "take": "r"},
			"A_07_n": {"speaker": "A", "sentence_id": "07", "take": "n"},
			"A_08_n": {"speaker": "A", "sentence_id": "08", "take": "n"},
			"B_07_n": {"speaker": "B", "sentence_id": "07", "take": "n"}}
	assert_eq(Npc.alternate_clip(clips, "A_07_r"), "A_07_n")
	assert_eq(Npc.alternate_clip(clips, "A_07_n"), "A_07_r")
	assert_eq(Npc.alternate_clip(clips, "A_07_r", ["A_07_n"] as Array[String]), "")
	assert_eq(Npc.alternate_clip(clips, "A_08_n"), "")
	assert_eq(Npc.alternate_clip(clips, "Z"), "")


# --- robot_voice ---

func test_robot_scene_has_voice_on_head() -> void:
	var robot := (load("res://scenes/robot.tscn") as PackedScene).instantiate()
	add_child_autofree(robot)
	var v := robot.get_node_or_null("Head/Voice") as RobotVoice
	assert_not_null(v)
	assert_gt(v.global_position.y, 1.0, "loa ở đầu robot")


func test_robot_voice_says_and_finishes() -> void:
	var v := RobotVoice.new()
	add_child_autofree(v)
	watch_signals(v)
	v.say(TtsClient.pcm16_to_stream(_pcm(0.1), 24000))
	assert_true(v.speaking)
	await wait_for_signal(v.finished_speaking, 2.0)
	assert_signal_emit_count(v, "finished_speaking", 1)
	assert_false(v.speaking)
	v.stop_speaking()
	assert_signal_emit_count(v, "finished_speaking", 1, "không phát lại khi không nói")


# --- tích hợp với main.tscn (STT, TTS giả) ---

func _write_voices() -> void:
	DirAccess.make_dir_recursive_absolute(TEST_DIR)
	var clips: Dictionary = {}
	for id: String in ["A_07_r", "A_07_n", "A_25_r"]:
		var wav := AudioStreamWAV.new()
		wav.format = AudioStreamWAV.FORMAT_16_BITS
		wav.mix_rate = 16000
		wav.data = _pcm(0.1, 16000)
		wav.save_to_wav(TEST_DIR.path_join(id + ".wav"))
		clips[id] = {"speaker": "A", "sentence_id": id.get_slice("_", 1), "take": id.get_slice("_", 2),
				"intent": "hoi_phong", "duration_s": 0.1}
	var f := FileAccess.open(TEST_DIR.path_join("clips.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(clips))
	f.close()


func _main() -> Array:
	_write_voices()
	var main := MainScene.instantiate() as Main
	main.seed = 3
	for n: String in ["RunLogger", "DialogueLogger"]:
		main.get_node(n).free()
	for pair: Array in [["SttClient", FakeStt.new()], ["TtsClient", FakeTts.new()]]:
		var old: Node = main.get_node(pair[0])
		main.remove_child(old)
		old.free()
		(pair[1] as Node).name = pair[0]
		main.add_child(pair[1])
		main.move_child(pair[1], 0)
	(main.get_node("Human/Npc") as Npc).voices_dir = TEST_DIR
	add_child_autofree(main)
	main.vision.set_process(false)
	return [main, main.get_node("DialogueManager"), main.get_node("SttClient"), main.get_node("TtsClient")]


func _transcript(utt_id: int, clip: String, action: String, response: String, slots: Dictionary = {}) -> Dictionary:
	return SttClient.parse_transcript(JSON.stringify({"type": "transcript", "utt_id": utt_id, "clip_id": clip,
			"text": "phòng khám số hai trăm linh năm", "intent": "hoi_phong", "intent_conf": 0.9, "slots": slots,
			"response": response, "stt_ms": 320.0, "audio_s": 3.8, "effective_snr_db": 17.1, "action": action,
			"target": "room_205" if action == "guide" else null}))


## NPC vừa nói xong `clip` ➔ robot THINK. Robot đứng cách NPC 1.5 m (xa hơn thì NPC tự dừng nói, G15).
func _heard(main: Main, dm: DialogueManager, clip: String) -> void:
	main.robot.global_position = main.human.global_position + Vector3(1.5, 0, 0)
	main.state = S.ARRIVED
	dm.npc.state = Npc.TALK
	dm._on_talk_started(clip)
	dm.npc.state = Npc.WAIT_REPLY
	dm._on_utterance_finished(clip)


func test_turn_with_tts_speaks_and_returns_to_arrived() -> void:
	var p: Array = _main()
	var main: Main = p[0]
	var dm: DialogueManager = p[1]
	var tts: FakeTts = p[3]
	watch_signals(dm)
	_heard(main, dm, "A_07_r")
	dm._on_transcript(_transcript(dm.utt_id, "A_07_r", "guide", "Dạ, phòng 205 ở tầng 2.", {"room": "205"}))
	assert_eq(main.state, S.RESPOND)
	assert_eq(tts.sent, [TtsClient.build_speak(dm.utt_id, "Dạ, phòng 205 ở tầng 2.", Config.ROBOT_VOICE)])
	assert_false(dm.subtitle.is_showing(), "phụ đề chờ âm thanh")
	assert_eq(main.overlay.get_status(), "Đang dẫn đến: phòng 205")
	assert_signal_emit_count(dm, "turn_completed", 0)
	dm._on_tts_audio(TtsClient.parse_audio(_audio_json(dm.utt_id - 1)))
	assert_false(dm.speaking, "audio của utt cũ bị bỏ")
	dm._on_tts_audio(TtsClient.parse_audio(_audio_json(dm.utt_id, 0.2)))
	assert_true(dm.speaking and dm.voice.speaking)
	assert_true(dm.subtitle.is_showing())
	var row: Dictionary = get_signal_parameters(dm, "turn_completed")[0]
	assert_eq([row["action"], row["target"], row["tts_error"], row["tts_cache_hit"]], ["guide", "room_205", "", "true"])
	assert_almost_eq(float(row["speak_duration_s"]), 0.2, 1e-6)
	assert_eq(row["response_len"], "Dạ, phòng 205 ở tầng 2.".length())
	await wait_for_signal(dm.voice.finished_speaking, 2.0)
	await wait_process_frames(2)
	assert_eq(main.state, S.ARRIVED)
	assert_false(dm.subtitle.is_showing(), "phụ đề ẩn khi robot nói xong")
	assert_eq(dm.npc.state, Npc.IDLE)


func test_tts_timeout_subtitle_only() -> void:
	var p: Array = _main()
	var main: Main = p[0]
	var dm: DialogueManager = p[1]
	watch_signals(dm)
	_heard(main, dm, "A_07_r")
	dm._on_transcript(_transcript(dm.utt_id, "A_07_r", "answer", "Dạ, nhà thuốc ở cuối sảnh."))
	dm.tts_deadline_ms = Time.get_ticks_msec() - 1
	await wait_process_frames(2)
	assert_eq(main.state, S.RESPOND, "phụ đề vẫn hiện")
	assert_true(dm.subtitle.is_showing())
	assert_almost_eq(dm.subtitle.time_left, Config.SUBTITLE_S, 0.2)
	assert_eq(get_signal_parameters(dm, "turn_completed")[0]["tts_error"], "timeout")
	dm._on_tts_audio(TtsClient.parse_audio(_audio_json(dm.utt_id)))
	assert_false(dm.speaking, "audio đến muộn sau timeout bị bỏ")
	dm.subtitle.time_left = 0.01
	await wait_process_frames(3)
	assert_eq(main.state, S.ARRIVED)


func test_tts_disconnected_and_error() -> void:
	var p: Array = _main()
	var main: Main = p[0]
	var dm: DialogueManager = p[1]
	var tts: FakeTts = p[3]
	watch_signals(dm)
	tts.online = false
	_heard(main, dm, "A_07_r")
	dm._on_transcript(_transcript(dm.utt_id, "A_07_r", "answer", "Dạ."))
	assert_eq(get_signal_parameters(dm, "turn_completed")[0]["tts_error"], "disconnected")
	assert_almost_eq(dm.subtitle.time_left, Config.SUBTITLE_S, 0.05, "TTS tắt ➔ phụ đề vẫn hiện 4 giây")
	dm.subtitle.time_left = 0.01
	await wait_process_frames(3)
	assert_eq(main.state, S.ARRIVED)
	tts.online = true
	dm.npc.reset()
	_heard(main, dm, "A_07_r")
	dm._on_transcript(_transcript(dm.utt_id, "A_07_r", "answer", "Dạ."))
	dm._on_tts_error(dm.utt_id, "text too long")
	assert_eq(get_signal_parameters(dm, "turn_completed")[0]["tts_error"], "server: text too long")
	assert_false(dm.waiting_tts)


func test_clarify_npc_repeats_with_other_take() -> void:
	var p: Array = _main()
	var main: Main = p[0]
	var dm: DialogueManager = p[1]
	var stt: FakeStt = p[2]
	_heard(main, dm, "A_07_r")
	dm._on_transcript(_transcript(dm.utt_id, "A_07_r", "clarify", "Dạ, anh chị nói lại giúp tôi được không ạ?"))
	dm._on_tts_audio(TtsClient.parse_audio(_audio_json(dm.utt_id, 0.1)))
	await wait_for_signal(dm.voice.finished_speaking, 2.0)
	assert_eq(main.state, S.LISTEN, "robot nói xong ➔ nghe người bệnh nói lại")
	assert_eq(dm.npc.state, Npc.TALK)
	assert_eq(dm.npc.current_clip, "A_07_n", "cùng câu, khác take")
	assert_eq(dm.clarify_count, 1)
	await wait_for_signal(dm.npc.utterance_finished, 2.0)
	assert_eq(main.state, S.THINK)
	assert_eq(stt.sent[-1]["clip_id"], "A_07_n")
	# Hỏi lại lần 2 nhưng hết clip khác ➔ kết thúc lượt.
	dm._on_transcript(_transcript(dm.utt_id, "A_07_n", "clarify", "Dạ, anh chị nói lại giúp tôi được không ạ?"))
	dm._on_tts_audio(TtsClient.parse_audio(_audio_json(dm.utt_id, 0.1)))
	await wait_for_signal(dm.voice.finished_speaking, 2.0)
	await wait_process_frames(2)
	assert_eq(main.state, S.ARRIVED)
	assert_eq(dm.npc.state, Npc.IDLE)


func test_clarify_without_other_take_ends_turn() -> void:
	var p: Array = _main()
	var main: Main = p[0]
	var dm: DialogueManager = p[1]
	_heard(main, dm, "A_25_r")
	dm._on_transcript(_transcript(dm.utt_id, "A_25_r", "clarify", "Dạ, anh chị nói lại giúp tôi được không ạ?"))
	dm._on_tts_audio(TtsClient.parse_audio(_audio_json(dm.utt_id, 0.1)))
	await wait_for_signal(dm.voice.finished_speaking, 2.0)
	await wait_process_frames(2)
	assert_eq(main.state, S.ARRIVED)


func test_emergency_shows_red_alert_and_logs() -> void:
	var p: Array = _main()
	var main: Main = p[0]
	var dm: DialogueManager = p[1]
	watch_signals(dm)
	_heard(main, dm, "A_25_r")
	dm._on_transcript(_transcript(dm.utt_id, "A_25_r", "emergency",
			"Tôi đang gọi nhân viên y tế ngay. Anh chị giữ bình tĩnh nhé."))
	assert_eq(main.overlay.get_alert(), ViewOverlay.EMERGENCY_TEXT)
	dm._on_tts_audio(TtsClient.parse_audio(_audio_json(dm.utt_id, 0.1)))
	assert_eq(get_signal_parameters(dm, "turn_completed")[0]["action"], "emergency")
	main.reset_positions()
	assert_eq(main.overlay.get_alert(), "", "R xóa cảnh báo")
	assert_false(dm.speaking)


func test_guide_text() -> void:
	assert_eq(ViewOverlay.guide_text({"department": "tim mạch"}), "Đang dẫn đến: khoa tim mạch")
	assert_eq(ViewOverlay.guide_text({"room": "205"}), "Đang dẫn đến: phòng 205")
	assert_eq(ViewOverlay.guide_text({}), "")
	assert_eq(ViewOverlay.tts_connection_text(false), "TTS: mất kết nối")
