class_name DialogueManager
extends Node
## Điều phối một lượt hội thoại (G16, G22), con trực tiếp của Main:
## NPC TALK ➔ robot LISTEN; NPC nói xong ➔ gửi utterance, robot THINK; nhận transcript ➔ RESPOND, gửi `speak`
## sang TTS; nhận audio ➔ robot nói qua loa trên đầu + phụ đề đến khi nói xong ➔ ARRIVED, npc.on_reply_shown().
## TTS lỗi / mất kết nối / quá TTS_TIMEOUT_S ➔ chỉ phụ đề SUBTITLE_S giây (log tts_error).
## STT timeout / lỗi / mất kết nối ➔ câu xin lỗi, về ARRIVED ngay.
## action (G20): clarify ➔ nói xong thì NPC nói lại bằng clip cùng câu khác take (nếu có); emergency ➔ cảnh báo đỏ;
## guide ➔ hiện "Đang dẫn đến: …" (dẫn đường thật làm ở giai đoạn RL).

## Phát sau mỗi lượt (kể cả lỗi), cùng nội dung dòng log; G17 dùng. Có TTS ➔ phát khi biết kết quả TTS.
signal turn_completed(row: Dictionary)

## Phụ đề giữ thêm sau khi âm thanh hết (ẩn ngay khi robot nói xong); quá thời lượng + SPEAK_GRACE_S mà player
## chưa báo xong ➔ coi như xong (tránh treo).
const SPEAK_GRACE_S: float = 2.0

@export var snr_db: float = Config.DEFAULT_SNR_DB
@export var noise: String = "babble"
@export var npc_path: NodePath = ^"../Human/Npc"
@export var stt_path: NodePath = ^"../SttClient"
@export var tts_path: NodePath = ^"../TtsClient"
@export var voice_path: NodePath = ^"../Robot/Head/Voice"
@export var subtitle_path: NodePath = ^"../UI/Subtitle"

var utt_id: int = 0                 # utt_id đang chờ (tăng mỗi lượt, không reset)
var deadline_ms: int = -1           # −1 = không chờ STT
var pending_clip: String = ""
var sent_distance_m: float = 0.0
var waiting_tts: bool = false
var tts_deadline_ms: int = -1
var speaking: bool = false
var speak_deadline_ms: int = -1
var action: String = ""
var clarify_count: int = 0
var used_clips: Array[String] = []

var _start_ms: int = 0
var active_npc: Npc = null
var _registered_npcs: Array[Npc] = []
var _reply: Dictionary = {}         # transcript đang trả lời
var _row: Dictionary = {}           # dòng log chờ kết quả TTS

@onready var main: Main = get_parent() as Main
@onready var npc: Npc = get_node(npc_path)
@onready var stt: SttClient = get_node(stt_path)
@onready var tts: TtsClient = get_node_or_null(tts_path)          # không có ➔ chỉ phụ đề (như G16)
@onready var voice: RobotVoice = get_node_or_null(voice_path)
@onready var subtitle: Subtitle = get_node(subtitle_path)
@onready var logger: DialogueLogger = get_node_or_null(^"../DialogueLogger")


func _ready() -> void:
	_start_ms = Time.get_ticks_msec()
	# Main chưa _ready (con _ready trước cha) ➔ lấy Robot bằng get_node, đọc main.state lúc gọi.
	active_npc = npc
	npc.setup(main.get_node(^"Robot"), func() -> int: return main.state)
	register_npc(npc)
	stt.transcript_received.connect(_on_transcript)
	stt.error_received.connect(_on_stt_error)
	stt.connection_changed.connect(_on_stt_connection_changed)
	subtitle.finished.connect(_on_subtitle_finished)
	var overlay := main.get_node(^"UI/ViewOverlay") as ViewOverlay
	# Hiện dòng STT ngay từ đầu (chưa nối được lần nào thì cũng không có sự kiện connection_changed).
	overlay.set_stt_connected(stt.is_server_connected())
	if tts != null:
		tts.audio_received.connect(_on_tts_audio)
		tts.error_received.connect(_on_tts_error)
		tts.connection_changed.connect(_on_tts_connection_changed)
		overlay.set_tts_connected(tts.is_server_connected())
	if voice != null:
		voice.finished_speaking.connect(_on_finished_speaking)
	if logger != null:
		logger.open()


func _process(_delta: float) -> void:
	var now: int = Time.get_ticks_msec()
	if main.state == Config.RobotState.THINK and DialogueManager.is_timed_out(deadline_ms, now):
		_fail("timeout")
	elif main.state == Config.RobotState.RESPOND and waiting_tts \
			and DialogueManager.is_timed_out(tts_deadline_ms, now):
		_speak_failed("timeout")
	elif speaking and DialogueManager.is_timed_out(speak_deadline_ms, now) and voice != null:
		voice.stop_speaking()


## Đặt lại khi Main đặt lại vị trí (phím R). utt_id giữ nguyên để transcript / audio muộn của lượt cũ bị bỏ.
func reset() -> void:
	deadline_ms = -1
	pending_clip = ""
	waiting_tts = false
	tts_deadline_ms = -1
	speaking = false
	speak_deadline_ms = -1
	action = ""
	clarify_count = 0
	used_clips.clear()
	for n: Npc in _registered_npcs:
		if is_instance_valid(n):
			n.reset()
	active_npc = npc
	if voice != null and voice.speaking:
		voice.speaking = false            # không phát finished_speaking cho lượt đã hủy
		voice.stop()
	if subtitle != null:
		subtitle.hide_now()
	if main != null and main.overlay != null:
		main.overlay.set_alert("")
		main.overlay.set_status("")


static func is_timed_out(deadline: int, now_ms: int) -> bool:
	return deadline >= 0 and now_ms > deadline


## Nhận transcript khi đúng utt_id đang chờ và robot đang THINK.
static func accepts(r: Dictionary, waiting_utt_id: int, robot_state: int) -> bool:
	return robot_state == Config.RobotState.THINK and int(r["utt_id"]) == waiting_utt_id


## Nhận audio khi đúng utt_id, robot đang RESPOND và đang chờ TTS.
static func accepts_audio(a: Dictionary, waiting_utt_id: int, robot_state: int, waiting: bool) -> bool:
	return waiting and robot_state == Config.RobotState.RESPOND and int(a["utt_id"]) == waiting_utt_id


static func clip_speaker(clip_id: String) -> String:
	return clip_id.get_slice("_", 0)


static func clip_take(clip_id: String) -> String:
	var parts: PackedStringArray = clip_id.split("_")
	return parts[parts.size() - 1] if parts.size() >= 3 else ""


func build_log_row(r: Dictionary, error: String) -> Dictionary:
	var row: Dictionary = {
		"time_s": (Time.get_ticks_msec() - _start_ms) / 1000.0, "utt_id": utt_id, "clip_id": pending_clip,
		"speaker": DialogueManager.clip_speaker(pending_clip), "take": DialogueManager.clip_take(pending_clip),
		"distance_m": sent_distance_m, "snr_db": snr_db, "noise": noise, "error": error,
	}
	if not r.is_empty():
		row["effective_snr_db"] = r["effective_snr_db"]
		row["hyp_text"] = r["text"]
		row["intent_pred"] = r["intent"]
		row["intent_conf"] = r["intent_conf"]
		row["stt_ms"] = r["stt_ms"]
		row["action"] = r.get("action", "")
		row["target"] = r.get("target", "")
		row["response_len"] = str(r["response"]).length()
	return row


func _on_talk_started(clip_id: String) -> void:
	if main != null and main.has_method("is_task_busy") and main.is_task_busy():
		return
	print("[ESCORT_DEBUG] >>> NPC talk started: clip_id='%s', robot_state=%s" % [clip_id, Config.state_name(main.state)])
	if main.state == Config.RobotState.ARRIVED:
		clarify_count = 0
		used_clips = [clip_id]
		main.overlay.set_alert("")
		main.overlay.set_status("")
		main.set_dialogue_state(Config.RobotState.LISTEN)


func _on_talk_aborted(_clip_id: String) -> void:
	if main.state == Config.RobotState.LISTEN:
		main.set_dialogue_state(Config.RobotState.ARRIVED)


func _on_utterance_finished(clip_id: String) -> void:
	utt_id += 1
	pending_clip = clip_id
	var speaker_node: Node3D = active_npc.human if (active_npc != null and active_npc.human != null) else npc.human
	sent_distance_m = Human.flat_distance(main.get_node(^"Robot").global_position, speaker_node.global_position)
	main.set_dialogue_state(Config.RobotState.THINK)
	deadline_ms = Time.get_ticks_msec() + int(Config.STT_TIMEOUT_S * 1000.0)
	if not stt.send_utterance(utt_id, clip_id, sent_distance_m, snr_db, noise):
		_fail("stt disconnected")


func _on_transcript(r: Dictionary) -> void:
	if not DialogueManager.accepts(r, utt_id, main.state):
		return
	deadline_ms = -1
	main.set_dialogue_state(Config.RobotState.RESPOND)
	_reply = r.duplicate()
	if _reply["response"] == "":
		_reply["response"] = Subtitle.SORRY
	action = str(r.get("action", ""))
	_row = build_log_row(r, "")
	if action == "emergency":
		main.overlay.set_alert(ViewOverlay.EMERGENCY_TEXT)
	elif action == "guide":
		main.overlay.set_status(ViewOverlay.guide_text(r.get("slots", {})))
	if tts == null or voice == null or not tts.is_server_connected():
		_speak_failed("disconnected")
		return
	if not tts.send_speak(utt_id, _reply["response"], Config.ROBOT_VOICE):
		_speak_failed("disconnected")
		return
	waiting_tts = true
	tts_deadline_ms = Time.get_ticks_msec() + int(Config.TTS_TIMEOUT_S * 1000.0)


func _on_tts_audio(a: Dictionary) -> void:
	if not DialogueManager.accepts_audio(a, utt_id, main.state, waiting_tts):
		return
	waiting_tts = false
	tts_deadline_ms = -1
	var stream: AudioStreamWAV = TtsClient.pcm16_to_stream(a["pcm"], a["sample_rate"])
	var duration: float = float(a["duration_s"])
	speaking = true
	speak_deadline_ms = Time.get_ticks_msec() + int((duration + SPEAK_GRACE_S) * 1000.0)
	voice.say(stream)
	subtitle.show_reply(_reply["text"], _reply["response"], duration + SPEAK_GRACE_S)
	_row["tts_ms"] = a["tts_ms"]
	_row["tts_cache_hit"] = "true" if a["cache_hit"] else "false"
	_row["tts_error"] = ""
	_row["speak_duration_s"] = duration
	_log(_row)


func _on_tts_error(err_utt_id: int, message: String) -> void:
	if waiting_tts and err_utt_id == utt_id:
		_speak_failed("server: " + message)


func _on_tts_connection_changed(connected: bool) -> void:
	main.overlay.set_tts_connected(connected)
	if not connected and waiting_tts:
		_speak_failed("disconnected")


## Không có âm thanh ➔ chỉ hiện phụ đề SUBTITLE_S giây; kết thúc khi phụ đề hết.
func _speak_failed(tts_error: String) -> void:
	waiting_tts = false
	tts_deadline_ms = -1
	subtitle.show_reply(_reply["text"], _reply["response"], Config.SUBTITLE_S)
	_row["tts_error"] = tts_error
	_log(_row)


func _on_finished_speaking() -> void:
	if not speaking:
		return
	speaking = false
	speak_deadline_ms = -1
	subtitle.hide_now()
	if main.state == Config.RobotState.RESPOND:
		_after_response()


func _on_stt_error(err_utt_id: int, message: String) -> void:
	if err_utt_id == utt_id and main.state == Config.RobotState.THINK:
		_fail("server: " + message)


func _on_stt_connection_changed(connected: bool) -> void:
	main.overlay.set_stt_connected(connected)
	if not connected and main.state == Config.RobotState.THINK:
		_fail("stt disconnected")


func _on_subtitle_finished() -> void:
	if main.state == Config.RobotState.RESPOND and not waiting_tts and not speaking:
		_after_response()


## Robot nói xong. clarify ➔ người bệnh nói lại bằng clip khác take (tối đa MAX_CLARIFY lần), không thì kết thúc.
func _after_response() -> void:
	var target_npc: Npc = active_npc if active_npc != null else npc
	var is_escort_only: bool = bool(main.get("escort_only_mode")) if main != null and "escort_only_mode" in main else false
	if action == "clarify" and clarify_count < Config.MAX_CLARIFY and not is_escort_only:
		var alt: String = Npc.alternate_clip(target_npc.get_clips(), pending_clip, used_clips)
		if alt != "":
			main.set_dialogue_state(Config.RobotState.LISTEN)
			if target_npc.say_again(alt):
				clarify_count += 1
				used_clips.append(alt)
				return
	_finish()


## Câu xin lỗi, ghi lỗi, về ARRIVED ngay (phụ đề vẫn hiện hết SUBTITLE_S).
func _fail(error: String) -> void:
	deadline_ms = -1
	subtitle.show_sorry(Config.SUBTITLE_S)
	_log(build_log_row({}, error))
	_finish()


func _finish() -> void:
	action = ""
	main.set_dialogue_state(Config.RobotState.ARRIVED)
	if active_npc != null:
		active_npc.on_reply_shown()
	else:
		npc.on_reply_shown()


func _log(row: Dictionary) -> void:
	if logger != null:
		logger.log_row(row)
	turn_completed.emit(row)

func register_npc(other_npc: Npc) -> void:
	if other_npc == null or _registered_npcs.has(other_npc):
		return
	_registered_npcs.append(other_npc)
	other_npc.talk_started.connect(func(clip_id: String) -> void:
		if main != null and main.has_method("is_task_busy") and main.is_task_busy():
			return
		active_npc = other_npc
		_on_talk_started(clip_id)
	)
	other_npc.talk_aborted.connect(func(clip_id: String) -> void:
		_on_talk_aborted(clip_id)
	)
	other_npc.utterance_finished.connect(func(clip_id: String) -> void:
		active_npc = other_npc
		_on_utterance_finished(clip_id)
	)
