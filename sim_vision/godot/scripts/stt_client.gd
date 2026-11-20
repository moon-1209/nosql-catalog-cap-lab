class_name SttClient
extends Node
## Kết nối STT server (G16, hợp đồng Mục 2.2 Sim_Voice): gửi `utterance`, nhận `transcript` / `error`.
## Giống VisionClient: tự nối lại mỗi RECONNECT_S, kiểm tra message trước khi phát signal.
## Bỏ message cũ theo utt_id là việc của dialogue_manager (chỉ nó biết utt_id đang chờ).

signal transcript_received(r: Dictionary)
signal error_received(utt_id: int, message: String)
signal connection_changed(connected: bool)

var url: String = Config.STT_WS_URL

var _ws: WebSocketPeer = null
var _connected: bool = false
var _last_attempt_ms: int = -1


func is_server_connected() -> bool:
	return _connected


func _process(_delta: float) -> void:
	var now: int = Time.get_ticks_msec()
	var state: int = WebSocketPeer.STATE_CLOSED
	if _ws != null:
		_ws.poll()
		state = _ws.get_ready_state()
	_set_connected(state == WebSocketPeer.STATE_OPEN)
	if state == WebSocketPeer.STATE_CLOSED \
			and (_last_attempt_ms < 0 or now - _last_attempt_ms >= int(Config.RECONNECT_S * 1000.0)):
		_try_connect(now)
	while _ws != null and _ws.get_available_packet_count() > 0:
		handle_message(_ws.get_packet().get_string_from_utf8())


func _set_connected(value: bool) -> void:
	if value != _connected:
		_connected = value
		connection_changed.emit(value)


func _try_connect(now: int) -> void:
	_last_attempt_ms = now
	_ws = WebSocketPeer.new()
	var err: Error = _ws.connect_to_url(url)
	if err != OK:
		push_warning("SttClient: connect_to_url failed: %s" % error_string(err))


## Gửi `utterance`; chưa kết nối hoặc gửi lỗi ➔ false.
func send_utterance(utt_id: int, clip_id: String, distance_m: float, snr_db: float, noise: String) -> bool:
	if not _connected:
		return false
	var msg: Dictionary = SttClient.build_utterance(utt_id, clip_id, distance_m, snr_db, noise)
	var err: Error = _ws.send_text(JSON.stringify(msg))
	if err != OK:
		push_warning("SttClient: send failed: %s" % error_string(err))
		return false
	return true


func handle_message(text: String) -> void:
	var r: Dictionary = SttClient.parse_transcript(text)
	if r["ok"]:
		transcript_received.emit(r)
	elif r["type"] == "error":
		error_received.emit(r["utt_id"], r["error"])
	else:
		push_warning("SttClient: %s" % r["error"])


static func build_utterance(utt_id: int, clip_id: String, distance_m: float, snr_db: float,
		noise: String) -> Dictionary:
	return {"type": "utterance", "utt_id": utt_id, "clip_id": clip_id, "distance_m": distance_m,
			"snr_db": snr_db, "noise": noise}


## Parse message server. Trả {ok, type, utt_id, clip_id, text, intent, intent_conf, slots, response,
## stt_ms, audio_s, effective_snr_db, action, target, error}. `type == "error"` ➔ ok = false, `error` = message của server.
## intent / intent_conf / response / effective_snr_db có thể là null (server chưa có G14, hoặc không ồn).
## action / target (G20) có thể thiếu hoặc null ➔ "".
static func parse_transcript(text: String) -> Dictionary:
	var out: Dictionary = {"ok": false, "type": "", "utt_id": -1, "clip_id": "", "text": "", "intent": "",
			"intent_conf": 0.0, "slots": {}, "response": "", "stt_ms": 0.0, "audio_s": 0.0,
			"effective_snr_db": null, "action": "", "target": "", "error": ""}
	var json := JSON.new()
	var msg: Variant = json.data if json.parse(text) == OK else null
	if not msg is Dictionary:
		out["error"] = "invalid json"
		return out
	var m := msg as Dictionary
	if _is_index(m.get("utt_id")):
		out["utt_id"] = int(m["utt_id"])
	if not m.get("type") is String:
		out["error"] = "missing field: type"
		return out
	out["type"] = m["type"]
	if m["type"] == "error":
		out["error"] = str(m.get("message", ""))
		return out
	if m["type"] != "transcript":
		out["error"] = "invalid field: type"
		return out
	for field: String in ["utt_id", "clip_id", "text", "stt_ms", "audio_s"]:
		if not m.has(field):
			out["error"] = "missing field: %s" % field
			return out
	if not _is_index(m["utt_id"]):
		return _invalid(out, "utt_id")
	if not m["clip_id"] is String or m["clip_id"] == "":
		return _invalid(out, "clip_id")
	if not m["text"] is String:
		return _invalid(out, "text")
	for f: String in ["stt_ms", "audio_s"]:
		if not _is_number(m[f]) or float(m[f]) < 0.0:
			return _invalid(out, f)
	for f: String in ["intent", "response", "action", "target"]:
		if m.get(f) != null and not m[f] is String:
			return _invalid(out, f)
	if m.get("intent_conf") != null and not _is_number(m["intent_conf"]):
		return _invalid(out, "intent_conf")
	if m.get("slots") != null and not m["slots"] is Dictionary:
		return _invalid(out, "slots")
	if m.get("effective_snr_db") != null and not _is_number(m["effective_snr_db"]):
		return _invalid(out, "effective_snr_db")
	out["ok"] = true
	out["clip_id"] = m["clip_id"]
	out["text"] = m["text"]
	out["intent"] = m.get("intent") if m.get("intent") != null else ""
	out["intent_conf"] = float(m["intent_conf"]) if m.get("intent_conf") != null else 0.0
	out["slots"] = m.get("slots") if m.get("slots") != null else {}
	out["response"] = m.get("response") if m.get("response") != null else ""
	out["stt_ms"] = float(m["stt_ms"])
	out["audio_s"] = float(m["audio_s"])
	out["effective_snr_db"] = float(m["effective_snr_db"]) if m.get("effective_snr_db") != null else null
	out["action"] = m.get("action") if m.get("action") != null else ""
	out["target"] = m.get("target") if m.get("target") != null else ""
	return out


static func _invalid(out: Dictionary, field: String) -> Dictionary:
	out["error"] = "invalid field: %s" % field
	return out


static func _is_number(v: Variant) -> bool:
	return (v is float or v is int) and is_finite(float(v))


## JSON của Godot đọc mọi số thành float ➔ số nguyên hợp lệ là số không có phần lẻ và ≥ 0.
static func _is_index(v: Variant) -> bool:
	return _is_number(v) and float(v) >= 0.0 and float(v) == floorf(float(v))
