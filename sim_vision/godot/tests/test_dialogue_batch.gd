extends GutTest


func _clips() -> Dictionary:
	return {
		"A_01_r": {"speaker": "A", "intent": "dang_ky_kham"}, "A_01_n": {"speaker": "A", "intent": "dang_ky_kham"},
		"A_25_r": {"speaker": "A", "intent": "cap_cuu"}, "A_06_r": {"speaker": "A", "intent": "hoi_khoa"},
		"B_06_r": {"speaker": "B", "intent": "hoi_phong"},
	}


func test_clip_schedule_covers_intents_round_robin() -> void:
	var s: Array[String] = DialogueBatch.clip_schedule(_clips(), "A", 6)
	# intent sắp xếp: cap_cuu, dang_ky_kham, hoi_khoa; clip trong intent sắp theo tên.
	assert_eq(s, ["A_25_r", "A_01_n", "A_06_r", "A_25_r", "A_01_r", "A_06_r"] as Array[String])


func test_clip_schedule_filters_speaker_and_handles_empty() -> void:
	assert_eq(DialogueBatch.clip_schedule(_clips(), "B", 2), ["B_06_r", "B_06_r"] as Array[String])
	assert_eq(DialogueBatch.clip_schedule(_clips(), "C", 3), [] as Array[String])


func test_h_target_and_condition_cycle() -> void:
	assert_eq([DialogueBatch.h_target_for(0), DialogueBatch.h_target_for(1), DialogueBatch.h_target_for(2),
			DialogueBatch.h_target_for(3)], [0.75, 0.80, 0.85, 0.75])
	assert_eq(DialogueBatch.condition_for(1), [10.0, "babble"])
	assert_eq(DialogueBatch.condition_for(4), DialogueBatch.condition_for(0))


func test_format_row_escapes_text_and_empty_cells() -> void:
	var r := {"episode": 2, "seed": 2, "h_target": 0.8, "speaker": "A", "clip_id": "A_06_r", "snr_db": 20.0,
			"noise": "babble", "completed": true, "error": "", "distance_m": 1.62, "hyp_text": "Khoa nào, ở đâu?",
			"intent_pred": "hoi_khoa", "intent_conf": 1.0, "stt_ms": 812.0, "latency_ms": 930.0, "sim_time_s": 21.5}
	var line: String = DialogueBatch.format_row(r)
	assert_eq(line.split(",")[0], "2")
	assert_string_contains(line, ",true,,1.6200,,\"Khoa nào, ở đâu?\",hoi_khoa,")
	assert_eq(line.count(","), DialogueBatch.COLUMNS.size() - 1 + 1, "dấu phẩy trong hyp nằm trong ngoặc kép")


func test_h_target_controller_scales_box_height() -> void:
	var dets: Array = [{"x1": 0.4, "y1": 0.1, "x2": 0.6, "y2": 0.85, "conf": 0.9}]
	var scaled: Array = HTargetController.scale_dets(dets, 0.85 / 0.75)
	assert_almost_eq(float(scaled[0]["y2"]) - float(scaled[0]["y1"]), 0.75 * 0.85 / 0.75, 1e-6)
	assert_eq(float(dets[0]["y2"]), 0.85, "không sửa mảng gốc")
	var c := HTargetController.new()
	c.h_target = 0.75
	var box := {"x1": 0.45, "y1": 0.1, "x2": 0.55, "y2": 0.86, "conf": 0.9}         # h = 0.76 ≥ 0.75
	assert_eq(int(c.step(Config.RobotState.APPROACH, [box], 0.0)["state"]), Config.RobotState.ARRIVED)
	box["y2"] = 0.80                                                                 # h = 0.70 < 0.75
	assert_eq(int(c.step(Config.RobotState.APPROACH, [box], 0.0)["state"]), Config.RobotState.APPROACH)
	c.free()
