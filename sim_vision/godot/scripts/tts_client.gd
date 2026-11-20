class_name TtsClient
extends Node
## Kết nối TTS server (G22, hợp đồng Mục 2.5): gửi `speak`, nhận `audio` / `error`.
## Giống SttClient: tự nối lại mỗi RECONNECT_S, kiểm tra message trước khi phát signal; bỏ utt_id cũ là việc
## của dialogue_manager.

signal audio_received(r: Dictionary)
signal error_received(utt_id: int, message: String)
signal connection_changed(connected: bool)

## Câu trả lời ~3–6 s PCM 24 kHz ➔ ~300 KB base64; bộ đệm nhận mặc định của WebSocketPeer chỉ 64 KiB.
const INBOUND_BUFFER: int = 8 * 1024 * 1024

var url: String = Config.TTS_WS_URL

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
	_ws.inbound_buffer_size = INBOUND_BUFFER
	var err: Error = _ws.connect_to_url(url)
	if err != OK:
		push_warning("TtsClient: connect_to_url failed: %s" % error_string(err))


## Gửi `speak`; chưa kết nối hoặc gửi lỗi ➔ false.
func send_speak(utt_id: int, text: String, voice: String) -> bool:
	if not _connected:
		return false
	var err: Error = _ws.send_text(JSON.stringify(TtsClient.build_speak(utt_id, text, voice)))
	if err != OK:
		push_warning("TtsClient: send failed: %s" % error_string(err))
		return false
	return true


func handle_message(text: String) -> void:
	var r: Dictionary = TtsClient.parse_audio(text)
	if r["ok"]:
		audio_received.emit(r)
	elif r["type"] == "error":
		error_received.emit(r["utt_id"], r["error"])
	else:
		push_warning("TtsClient: %s" % r["error"])


static func build_speak(utt_id: int, text: String, voice: String) -> Dictionary:
	return {"type": "speak", "utt_id": utt_id, "text": text, "voice": voice}


## Parse message server. Trả {ok, type, utt_id, sample_rate, channels, pcm (PackedByteArray), duration_s, tts_ms,
## cache_hit, error}. `type == "error"` ➔ ok = false, `error` = message của server. Âm thanh rỗng / lẻ byte ➔ lỗi.
static func parse_audio(text: String) -> Dictionary:
	var out: Dictionary = {"ok": false, "type": "", "utt_id": -1, "sample_rate": 0, "channels": 0,
			"pcm": PackedByteArray(), "duration_s": 0.0, "tts_ms": 0.0, "cache_hit": false, "error": ""}
	var json := JSON.new()
	var msg: Variant = json.data if json.parse(text) == OK else null
	if not msg is Dictionary:
		out["error"] = "invalid json"
		return out
	var m := msg as Dictionary
	if SttClient._is_index(m.get("utt_id")):
		out["utt_id"] = int(m["utt_id"])
	if not m.get("type") is String:
		out["error"] = "missing field: type"
		return out
	out["type"] = m["type"]
	if m["type"] == "error":
		out["error"] = str(m.get("message", ""))
		return out
	if m["type"] != "audio":
		return _invalid(out, "type")
	for field: String in ["utt_id", "sample_rate", "channels", "pcm16_b64", "duration_s", "tts_ms", "cache_hit"]:
		if not m.has(field):
			out["error"] = "missing field: %s" % field
			return out
	if not SttClient._is_index(m["utt_id"]):
		return _invalid(out, "utt_id")
	if not SttClient._is_index(m["sample_rate"]) or float(m["sample_rate"]) < 8000.0:
		return _invalid(out, "sample_rate")
	if not SttClient._is_number(m["channels"]) or float(m["channels"]) != 1.0:
		return _invalid(out, "channels")
	for f: String in ["duration_s", "tts_ms"]:
		if not SttClient._is_number(m[f]) or float(m[f]) < 0.0:
			return _invalid(out, f)
	if not m["cache_hit"] is bool:
		return _invalid(out, "cache_hit")
	if not m["pcm16_b64"] is String:
		return _invalid(out, "pcm16_b64")
	var pcm: PackedByteArray = Marshalls.base64_to_raw(m["pcm16_b64"])
	if pcm.is_empty():
		out["error"] = "empty audio"
		return out
	if pcm.size() % 2 != 0:
		return _invalid(out, "pcm16_b64")
	out["ok"] = true
	out["utt_id"] = int(m["utt_id"])
	out["sample_rate"] = int(m["sample_rate"])
	out["channels"] = 1
	out["pcm"] = pcm
	out["duration_s"] = float(m["duration_s"])
	out["tts_ms"] = float(m["tts_ms"])
	out["cache_hit"] = m["cache_hit"]
	return out


## PCM 16-bit little-endian mono ➔ AudioStreamWAV.
static func pcm16_to_stream(pcm: PackedByteArray, sample_rate: int) -> AudioStreamWAV:
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = sample_rate
	s.stereo = false
	s.data = pcm
	return s


static func _invalid(out: Dictionary, field: String) -> Dictionary:
	out["error"] = "invalid field: %s" % field
	return out
