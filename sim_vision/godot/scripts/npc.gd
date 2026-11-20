class_name Npc
extends Node
## NPC (G15): node con của Human. Robot ở ARRIVED và đủ gần ➔ quay mặt về robot ➔ phát clip thu âm thật.
## Trạng thái (Mục 2.3): "IDLE" | "NOTICE" | "TALK" | "WAIT_REPLY". Không đổi API của human.gd.

signal talk_started(clip_id: String)
signal talk_aborted(clip_id: String)
signal utterance_finished(clip_id: String)

const IDLE: String = "IDLE"
const NOTICE: String = "NOTICE"
const TALK: String = "TALK"
const WAIT_REPLY: String = "WAIT_REPLY"
const LEAVE_MARGIN_M: float = 1.0    # robot rời xa hơn TALK_TRIGGER_DIST + 1.0 khi đang TALK ➔ dừng nói
const VOICES_DIR: String = "res://assets/voices"
const TALK_ANIM: StringName = &"human/talk"
const IDLE_ANIM: StringName = &"human/idle"

@export var speaker: String = "A"    # A nam, B nữ
@export var clip_id: String = ""     # rỗng = chọn ngẫu nhiên trong các clip của speaker
@warning_ignore("shadowed_global_identifier")
@export var seed: int = -1
@export var escort_only: bool = false  # true = chỉ chọn clip hỏi đường / dẫn đường (hoi_phong, hoi_khoa, dan_duong)

const ESCORT_INTENTS: Array[String] = ["hoi_phong", "hoi_khoa", "dan_duong"]

var state: String = IDLE
var cooldown_left: float = 0.0
var turns_done: int = 0
var current_clip: String = ""
var robot: Node3D = null
## Hàm không tham số trả trạng thái robot (Config.RobotState); main/dialogue_manager gán.
var robot_state_fn: Callable = Callable()
var voices_dir: String = VOICES_DIR

var _clips: Dictionary = {}
var _used_intents: Array[String] = []
var _rng := RandomNumberGenerator.new()
var _was_walking: bool = false
var _tween: Tween = null

@onready var human: Node3D = get_parent() as Node3D
var player: AudioStreamPlayer3D = null


func _ready() -> void:
	if seed >= 0:
		_rng.seed = seed
	else:
		_rng.randomize()
	if player == null:
		player = get_node_or_null(^"../Head/Voice") as AudioStreamPlayer3D
	if player == null and human != null:
		player = human.get_node_or_null(^"Head/Voice") as AudioStreamPlayer3D
	if player == null and human != null:
		player = human.get_node_or_null(^"Voice") as AudioStreamPlayer3D
	if player != null and not player.finished.is_connected(_on_audio_finished):
		player.finished.connect(_on_audio_finished)


func setup(robot_node: Node3D, state_fn: Callable) -> void:
	robot = robot_node
	robot_state_fn = state_fn


func _process(delta: float) -> void:
	cooldown_left = maxf(cooldown_left - delta, 0.0)
	if robot == null or not robot_state_fn.is_valid():
		return
	var h_pos: Vector3 = human.get_interaction_position() if (human != null and human.has_method("get_interaction_position")) else (human.global_position if human != null else Vector3.ZERO)
	var dist: float = Human.flat_distance(h_pos, robot.global_position)
	var r_state: int = robot_state_fn.call()
	if r_state == Config.RobotState.APPROACH and dist <= Config.SAFE_DIST_HUMAN + 0.35 and robot.get("v") != null and absf(robot.v) < 0.05:
		r_state = Config.RobotState.ARRIVED
	var next: String = Npc.next_state(state, r_state, dist, cooldown_left, turns_done)
	if state == IDLE and next == NOTICE:
		_notice()
	elif state == TALK and next == IDLE:
		_abort_talk()


## Hàm thuần theo pseudocode G15.2.
static func next_state(s: String, robot_state: int, dist: float, cooldown: float, turns: int) -> String:
	if s == IDLE and robot_state == Config.RobotState.ARRIVED and dist <= Config.TALK_TRIGGER_DIST \
			and cooldown <= 0.0 and turns < Config.MAX_TURNS:
		return NOTICE
	if s == TALK and dist > Config.TALK_TRIGGER_DIST + LEAVE_MARGIN_M:
		return IDLE
	return s


## Góc quay (rad) ngắn nhất từ `from_yaw` tới `to_yaw`, trong [−PI, PI].
static func shortest_turn(from_yaw: float, to_yaw: float) -> float:
	return wrapf(to_yaw - from_yaw, -PI, PI)


## Yaw để mặt (+Z cục bộ) hướng từ `from` về `to` trên mặt phẳng XZ.
static func yaw_towards(from: Vector3, to: Vector3) -> float:
	return atan2(to.x - from.x, to.z - from.z)


## Chọn clip của `speaker`, ưu tiên intent chưa dùng; dùng hết thì dùng lại từ đầu. Không có clip ➔ "".
static func pick_clip(clips: Dictionary, spk: String, used_intents: Array[String],
		rng: RandomNumberGenerator, escort_filter: bool = false) -> String:
	var mine: Array[String] = []
	for id: String in clips:
		if str(clips[id].get("speaker", "")) == spk:
			if escort_filter:
				var it: String = str(clips[id].get("intent", ""))
				var sid: String = str(clips[id].get("sentence_id", ""))
				if not ESCORT_INTENTS.has(it) or sid == "05":
					continue
			mine.append(id)
	if mine.is_empty():
		return ""
	mine.sort()
	var fresh: Array[String] = mine.filter(func(id: String) -> bool:
		return not used_intents.has(str(clips[id].get("intent", ""))))
	var pool: Array[String] = fresh if not fresh.is_empty() else mine
	return pool[rng.randi_range(0, pool.size() - 1)]


## Clip để người bệnh nói lại (G22, nhánh clarify): cùng speaker và sentence_id, khác take, chưa dùng
## (`used`); nhiều clip ➔ theo tên. Không có ➔ "".
static func alternate_clip(clips: Dictionary, id: String, used: Array[String] = []) -> String:
	if not clips.has(id):
		return ""
	var me: Dictionary = clips[id]
	var ids: Array = clips.keys()
	ids.sort()
	for other: String in ids:
		var c: Dictionary = clips[other]
		if other != id and not used.has(other) and str(c.get("speaker", "")) == str(me.get("speaker", "")) \
				and str(c.get("sentence_id", "")) == str(me.get("sentence_id", "")) \
				and str(c.get("take", "")) != str(me.get("take", "")):
			return other
	return ""


## Đọc clips.json; lỗi ➔ push_error và trả {}.
static func load_clips(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Npc: %s not found (run `python -m voice.sync_voices`)" % path)
		return {}
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path)) != OK or not parser.data is Dictionary:
		push_error("Npc: invalid %s" % path)
		return {}
	return parser.data


## Nạp wav: dùng bản đã import nếu có, không thì đọc thẳng file (voices không commit nên có thể chưa import).
static func load_voice(id: String, dir: String = VOICES_DIR) -> AudioStream:
	var path: String = dir.path_join(id + ".wav")
	if ResourceLoader.exists(path):
		return load(path) as AudioStream
	if FileAccess.file_exists(path):
		return AudioStreamWAV.load_from_file(path)
	return null


func reset() -> void:
	if _tween != null:
		_tween.kill()
	if player != null:
		player.stop()
	if state != IDLE:
		_resume_walking()
	state = IDLE
	cooldown_left = 0.0
	turns_done = 0
	current_clip = ""


## Gọi bởi dialogue_manager sau khi robot trả lời xong.
## Danh sách clip (nạp khi cần lần đầu).
func get_clips() -> Dictionary:
	if _clips.is_empty():
		_clips = Npc.load_clips(voices_dir.path_join("clips.json"))
	return _clips


## Người bệnh nói lại bằng clip `id` khi robot vừa hỏi lại (G22). Chỉ khi đang WAIT_REPLY; lỗi ➔ false.
func say_again(id: String) -> bool:
	if state != WAIT_REPLY:
		return false
	var stream: AudioStream = Npc.load_voice(id, voices_dir)
	if stream == null:
		push_error("Npc: cannot load voice clip '%s'" % id)
		return false
	current_clip = id
	state = TALK
	player.stream = stream
	player.play()
	talk_started.emit(id)
	return true


func on_reply_shown() -> void:
	if state == IDLE:
		return
	state = IDLE
	cooldown_left = Config.NPC_COOLDOWN_S
	turns_done += 1
	_resume_walking()


func _notice() -> void:
	state = NOTICE
	_was_walking = bool(human.get("walks")) if human != null and human.get("walks") != null else false
	if human != null:
		human.set("walks", false)
		if human.get("velocity") != null:
			human.set("velocity", Vector3.ZERO)
	var is_seated_val: bool = bool(human.get("is_seated")) if human != null and human.get("is_seated") != null else false
	if is_seated_val:
		_start_talk()
	else:
		var target: float = Npc.yaw_towards(human.global_position, robot.global_position)
		var end_yaw: float = human.rotation.y + Npc.shortest_turn(human.rotation.y, target)
		_tween = create_tween()
		_tween.tween_property(human, ^"rotation:y", end_yaw, Config.TURN_DURATION_S) \
				.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		_tween.finished.connect(_start_talk)


func _start_talk() -> void:
	if state != NOTICE:
		return
	if _clips.is_empty() and clip_id == "":
		_clips = Npc.load_clips(voices_dir.path_join("clips.json"))
	var id: String = clip_id if clip_id != "" else Npc.pick_clip(_clips, speaker, _used_intents, _rng, escort_only)
	if id == "" and speaker != "A":
		id = Npc.pick_clip(_clips, "A", _used_intents, _rng, escort_only)
	var stream: AudioStream = Npc.load_voice(id, voices_dir) if id != "" else null
	if stream == null:
		push_error("Npc: cannot load voice clip '%s' (speaker %s)" % [id, speaker])
		state = IDLE
		cooldown_left = Config.NPC_COOLDOWN_S  # tránh báo lỗi mỗi khung hình
		_resume_walking()
		return
	current_clip = id
	var intent: String = str(_clips.get(id, {}).get("intent", ""))
	if intent != "" and not _used_intents.has(intent):
		_used_intents.append(intent)
	if _used_intents.size() >= _distinct_intents():
		_used_intents.clear()
	state = TALK
	var anim: AnimationPlayer = human.get_node_or_null(^"AnimationPlayer") as AnimationPlayer if human != null else null
	if anim == null and human != null:
		var model_node: Node3D = human.get_node_or_null(^"Model") as Node3D
		if model_node != null:
			anim = model_node.get_node_or_null(^"AnimationPlayer") as AnimationPlayer
	if anim != null and anim.has_animation(TALK_ANIM):
		anim.play(TALK_ANIM, 0.3)
	if player != null:
		player.stream = stream
		player.play()
	talk_started.emit(id)


func _abort_talk() -> void:
	player.stop()
	state = IDLE
	_resume_walking()
	talk_aborted.emit(current_clip)


func _on_audio_finished() -> void:
	if state != TALK:
		return
	state = WAIT_REPLY
	utterance_finished.emit(current_clip)


func _resume_walking() -> void:
	if human != null and human.get("walks") != null:
		human.set("walks", _was_walking)


func _distinct_intents() -> int:
	if escort_only:
		return ESCORT_INTENTS.size()
	var seen: Dictionary = {}
	for id: String in _clips:
		if str(_clips[id].get("speaker", "")) == speaker:
			seen[str(_clips[id].get("intent", ""))] = true
	if seen.is_empty():
		for id: String in _clips:
			seen[str(_clips[id].get("intent", ""))] = true
	return seen.size()
