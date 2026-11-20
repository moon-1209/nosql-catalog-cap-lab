class_name RLPolicyClient
extends Node
## Client WebSocket tới rl_policy_server.py (PPO đã train). Gửi trạng thái thô 5 Hz (khớp dt = 0.2 s
## lúc train), nhận lệnh (v, omega) thực tế. Mất kết nối thì thử lại mỗi RECONNECT_S;
## Main quay về controller cũ khi chưa kết nối.

signal action_received(v: float, omega: float, phase: int)
signal connection_changed(connected: bool)

const URL: String = "ws://127.0.0.1:8768"
const STEP_DT_S: float = 0.2

var _ws: WebSocketPeer = null
var _connected: bool = false
var _last_attempt_ms: int = -1
var _next_id: int = 0
var _waiting: bool = false


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
		_last_attempt_ms = now
		_ws = WebSocketPeer.new()
		_ws.connect_to_url(URL)
	while _ws != null and _ws.get_available_packet_count() > 0:
		_handle_message(_ws.get_packet().get_string_from_utf8())


func _set_connected(value: bool) -> void:
	if value != _connected:
		_connected = value
		_waiting = false
		connection_changed.emit(value)


## Gửi một bước quan sát; bỏ qua nếu bước trước chưa có trả lời (không dồn hàng đợi).
func send_state(robot_pos: Vector3, robot_yaw: float, v: float, omega: float, lidar: PackedFloat32Array,
		patient_pos: Vector3, phase: int, goal_pos: Vector3, task_id: int) -> void:
	if not _connected or _waiting:
		return
	var msg: Dictionary = {
		"type": "rl_state", "id": _next_id,
		"robot": [robot_pos.x, robot_pos.z, robot_yaw, v, omega],
		"lidar": Array(lidar),
		"patient": [patient_pos.x, patient_pos.z],
		"phase": phase, "goal": [goal_pos.x, goal_pos.z], "task_id": task_id,
	}
	if _ws.send_text(JSON.stringify(msg)) == OK:
		_waiting = true
		_next_id += 1


func _handle_message(text: String) -> void:
	_waiting = false
	var data: Variant = JSON.parse_string(text)
	if not (data is Dictionary) or str(data.get("type", "")) != "rl_action":
		push_warning("RLPolicyClient: bad reply %s" % text.left(200))
		return
	action_received.emit(float(data["v"]), float(data["omega"]), int(data.get("phase", 0)))
