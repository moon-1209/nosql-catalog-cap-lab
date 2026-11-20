class_name DialogueBatch
extends Node
## Batch hội thoại (G17): N episode (mặc định 40), seed = chỉ số episode. Mỗi episode: vị trí ngẫu nhiên theo seed,
## clip chọn theo vòng để phủ đều intent, SNR/noise và H_TARGET xoay vòng theo danh sách cấu hình; chạy đến khi
## xong 1 lượt hội thoại hoặc quá MAX_EPISODE_S giây mô phỏng.
## Ghi logs/dialogue_batch_<YYYYMMDD_HHMMSS>.csv. Cần YOLO (8765) và STT (8766) server, cửa sổ có render.
## Chạy: godot --path . res://tools/dialogue_batch.tscn [-- --episodes=40 --max-time=60]

const MainScene: PackedScene = preload("res://scenes/main.tscn")
const CONNECT_TIMEOUT_S: float = 15.0
const MAX_EPISODE_S: float = 60.0
const SPEAK_WAIT_S: float = 15.0
## Chiều cao box lúc dừng (người dùng chọn cách 1, 2026-10-22): ~1.9 / 1.65 / 1.5 m, đều ≤ TALK_TRIGGER_DIST.
const H_TARGETS: Array[float] = [0.75, 0.80, 0.85]
## (snr_db, noise); noise "none" thì snr_db không dùng.
const CONDITIONS: Array = [[20.0, "babble"], [10.0, "babble"], [20.0, "white"], [30.0, "none"]]
const COLUMNS: PackedStringArray = ["episode", "seed", "h_target", "speaker", "clip_id", "snr_db", "noise",
		"completed", "error", "distance_m", "effective_snr_db", "hyp_text", "intent_pred", "intent_conf",
		"stt_ms", "latency_ms", "sim_time_s",
		# G22/G23 (thêm cuối, cột G17 giữ nguyên): có TTS thì latency_ms tính đến lúc robot bắt đầu nói.
		"action", "target", "response_len", "tts_ms", "tts_cache_hit", "tts_error", "speak_duration_s"]

var episodes: int = 40
var max_sim_s: float = MAX_EPISODE_S


func _ready() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--episodes="):
			episodes = int(arg.get_slice("=", 1))
		elif arg.begins_with("--max-time="):
			max_sim_s = float(arg.get_slice("=", 1))
	if DisplayServer.get_name() == "headless":
		push_error("dialogue_batch: cần cửa sổ có render (camera robot không có ảnh khi --headless)")
		get_tree().quit(2)
		return
	_run_all()


## Thứ tự clip phủ đều intent: episode e lấy intent thứ e % số intent, clip thứ (e / số intent) của intent đó.
static func clip_schedule(clips: Dictionary, speaker: String, n: int) -> Array[String]:
	var by_intent: Dictionary = {}
	var ids: Array = clips.keys()
	ids.sort()
	for id: String in ids:
		if str(clips[id].get("speaker", "")) == speaker:
			var it: String = str(clips[id].get("intent", ""))
			if not by_intent.has(it):
				by_intent[it] = []
			by_intent[it].append(id)
	var intents: Array = by_intent.keys()
	intents.sort()
	var out: Array[String] = []
	if intents.is_empty():
		return out
	for e: int in n:
		var group: Array = by_intent[intents[e % intents.size()]]
		out.append(group[(e / intents.size()) % group.size()])
	return out


static func h_target_for(episode: int) -> float:
	return H_TARGETS[episode % H_TARGETS.size()]


static func condition_for(episode: int) -> Array:
	return CONDITIONS[episode % CONDITIONS.size()]


static func format_row(r: Dictionary) -> String:
	var cells: PackedStringArray = []
	for col: String in COLUMNS:
		var v: Variant = r.get(col)
		if v == null:
			cells.append("")
		elif v is float:
			cells.append("%.4f" % v)
		elif v is bool:
			cells.append("true" if v else "false")
		else:
			cells.append(DialogueLogger.csv_escape(str(v)))
	return ",".join(cells)


func _run_all() -> void:
	var logs_dir: String = ProjectSettings.globalize_path("res://").path_join("../logs").simplify_path()
	DirAccess.make_dir_recursive_absolute(logs_dir)
	var clips: Dictionary = Npc.load_clips(Npc.VOICES_DIR.path_join("clips.json"))
	var schedule: Array[String] = DialogueBatch.clip_schedule(clips, "A", episodes)
	if schedule.is_empty():
		push_error("dialogue_batch: no clips for speaker A (chạy `python -m voice.sync_voices` trước)")
		get_tree().quit(1)
		return
	var stamp: String = Time.get_datetime_string_from_system(false, true).replace("-", "").replace(":", "").replace(" ", "_")
	var path: String = logs_dir.path_join("dialogue_batch_%s.csv" % stamp)
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("dialogue_batch: cannot write %s" % path)
		get_tree().quit(1)
		return
	f.store_line(",".join(COLUMNS))
	var completed: int = 0
	for e: int in episodes:
		var r: Dictionary = await _run_episode(e, schedule[e])
		if r.is_empty():
			push_error("dialogue_batch: cannot connect to YOLO/STT servers")
			f.close()
			get_tree().quit(1)
			return
		f.store_line(DialogueBatch.format_row(r))
		f.flush()
		completed += 1 if r["completed"] else 0
		print("ep=%d h=%.2f clip=%s %s/%s completed=%s err=%s dist=%.2f intent=%s latency=%s ms" % [
				e, r["h_target"], r["clip_id"], r["noise"], r["snr_db"], r["completed"], r["error"],
				r["distance_m"] if r["distance_m"] != null else -1.0, r["intent_pred"], r["latency_ms"]])
	f.close()
	print("completed %d/%d ➔ %s" % [completed, episodes, path])
	get_tree().quit(0)


func _run_episode(e: int, clip: String) -> Dictionary:
	var main: Main = MainScene.instantiate()
	main.seed = e
	# Batch tự ghi CSV ➔ bỏ log từng lượt (G9, G16) để không sinh 2 file mỗi episode.
	for log_node: String in ["RunLogger", "DialogueLogger"]:
		var n: Node = main.get_node_or_null(log_node)
		if n != null:
			main.remove_child(n)
			n.free()
	var ctrl := HTargetController.new()
	ctrl.name = "HTargetController"
	ctrl.h_target = DialogueBatch.h_target_for(e)
	main.add_child(ctrl)
	main.controller_path = ^"HTargetController"
	var cond: Array = DialogueBatch.condition_for(e)
	var dm: DialogueManager = main.get_node("DialogueManager")
	dm.snr_db = cond[0]
	dm.noise = cond[1]
	var npc: Npc = main.get_node("Human/Npc")
	npc.speaker = "A"
	npc.clip_id = clip
	npc.seed = e
	add_child(main)
	var stt: SttClient = main.get_node("SttClient")
	var waited: float = 0.0
	while not (main.vision.is_server_connected() and stt.is_server_connected()):
		waited += await _physics_step()
		if waited > CONNECT_TIMEOUT_S:
			main.queue_free()
			return {}
	var ev := {"finished_ms": -1, "row": {}}
	# Chỉ lần nói đầu tiên (nhánh clarify làm NPC nói lại sau khi lượt đã được ghi).
	npc.utterance_finished.connect(func(_c: String) -> void:
		if int(ev["finished_ms"]) < 0:
			ev["finished_ms"] = Time.get_ticks_msec())
	dm.turn_completed.connect(func(row: Dictionary) -> void:
		if (ev["row"] as Dictionary).is_empty():
			ev["row"] = row
			ev["done_ms"] = Time.get_ticks_msec())
	var t: float = 0.0
	while t < max_sim_s and (ev["row"] as Dictionary).is_empty():
		t += await _physics_step()
	# Có phụ đề / robot bắt đầu nói ➔ chờ robot nói xong (về ARRIVED) để nghe được câu trả lời, tối đa SPEAK_WAIT_S.
	var waited_speak: float = 0.0
	while not (ev["row"] as Dictionary).is_empty() and main.state != Config.RobotState.ARRIVED \
			and waited_speak < SPEAK_WAIT_S:
		waited_speak += await _physics_step()
	var row: Dictionary = ev["row"]
	var done: bool = not row.is_empty()
	var result := {
		"episode": e, "seed": e, "h_target": DialogueBatch.h_target_for(e), "speaker": "A", "clip_id": clip,
		"snr_db": float(cond[0]), "noise": cond[1], "completed": done and str(row.get("error", "")) == "",
		"error": str(row.get("error", "")) if done else "episode timeout", "distance_m": row.get("distance_m"),
		"effective_snr_db": row.get("effective_snr_db"), "hyp_text": row.get("hyp_text"),
		"intent_pred": row.get("intent_pred"), "intent_conf": row.get("intent_conf"), "stt_ms": row.get("stt_ms"),
		"latency_ms": float(ev["done_ms"] - ev["finished_ms"]) if done and ev["finished_ms"] >= 0 else null,
		"sim_time_s": t,
	}
	for k: String in ["action", "target", "response_len", "tts_ms", "tts_cache_hit", "tts_error", "speak_duration_s"]:
		result[k] = row.get(k)
	main.queue_free()
	await get_tree().process_frame
	return result


func _physics_step() -> float:
	await get_tree().physics_frame
	return get_physics_process_delta_time()
