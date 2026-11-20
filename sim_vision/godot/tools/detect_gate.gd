extends Node3D
## Cổng kiểm tra G4: YOLO có nhận ra người tả thực không.
## Camera cao 1.2 m nhìn ngang vào người ở 1, 2, 4, 6 m, người quay 0/45/90/180°;
## mỗi mốc 20 ảnh (ánh sáng ±10%, camera lệch ±5°), gửi YOLO server, đếm ảnh có conf ≥ 0.5.
## Chạy (cần YOLO server ở G2 đang chạy): godot --path . res://tools/detect_gate.tscn

const DISTANCES: Array[float] = [1.0, 2.0, 4.0, 6.0]
const YAWS: Array[float] = [0.0, 45.0, 90.0, 180.0]
const SHOTS: int = 20
const HIT_CONF: float = 0.5
const CAM_HEIGHT: float = 1.2
const CAM_X: float = -3.6          # camera sát tường tây, nhìn về +X để đủ chỗ cho 6 m
const LIGHT_JITTER: float = 0.10
const CAM_JITTER_DEG: float = 5.0
const REPLY_TIMEOUT_MS: int = 5000

@onready var _room: Room = $Room
@onready var _human: Human = $Human
@onready var _viewport: SubViewport = $SubViewport
@onready var _camera: Camera3D = $SubViewport/Camera3D

var _ws := WebSocketPeer.new()
var _rng := RandomNumberGenerator.new()
var _lights: Array[Light3D] = []
var _base_energy: Array[float] = []


func _ready() -> void:
	_rng.seed = 0
	for n: Node in _room.find_children("*", "Light3D", true, false):
		_lights.append(n as Light3D)
		_base_energy.append((n as Light3D).light_energy)
	_run()


func _run() -> void:
	if not await _connect():
		push_error("detect_gate: cannot connect to %s — start python/yolo_server.py first" % Config.WS_URL)
		get_tree().quit(1)
		return
	var logs_dir: String = ProjectSettings.globalize_path("res://").path_join("../logs").simplify_path()
	DirAccess.make_dir_recursive_absolute(logs_dir.path_join("detect_gate"))
	var lines: PackedStringArray = ["distance_m,yaw_deg,hits,n,rate,mean_top_conf"]
	var frame_id: int = 0
	print("d(m)  yaw  hits/20  mean_top_conf")
	for d: float in DISTANCES:
		for yaw: float in YAWS:
			_place(d, yaw)
			var hits: int = 0
			var conf_sum: float = 0.0
			for i: int in SHOTS:
				_jitter(d)
				var img: Image = await _capture()
				if i == 0:
					img.save_jpg(logs_dir.path_join("detect_gate/d%d_yaw%d.jpg" % [int(d), int(yaw)]))
				var top: float = await _detect(img, frame_id)
				frame_id += 1
				conf_sum += top
				if top >= HIT_CONF:
					hits += 1
			print("%-5.0f %-4.0f %2d/%d    %.3f" % [d, yaw, hits, SHOTS, conf_sum / SHOTS])
			lines.append("%.1f,%.0f,%d,%d,%.4f,%.4f" % [d, yaw, hits, SHOTS, float(hits) / SHOTS, conf_sum / SHOTS])
	var path: String = logs_dir.path_join("detect_gate.csv")
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("detect_gate: cannot write %s" % path)
	else:
		f.store_string("\n".join(lines) + "\n")
		f.close()
		print("saved ", path)
	_ws.close()
	get_tree().quit(0)


## Người ở x = CAM_X + d trên trục z = 0; yaw 0° = mặt người (+Z cục bộ) nhìn về camera (−X).
func _place(d: float, yaw_deg: float) -> void:
	_human.global_position = Vector3(CAM_X + d, 0.0, 0.0)
	_human.rotation.y = deg_to_rad(-90.0 + yaw_deg)


func _jitter(d: float) -> void:
	for i: int in _lights.size():
		_lights[i].light_energy = _base_energy[i] * _rng.randf_range(1.0 - LIGHT_JITTER, 1.0 + LIGHT_JITTER)
	var eye := Vector3(CAM_X, CAM_HEIGHT, 0.0)
	_camera.look_at_from_position(eye, Vector3(CAM_X + d, CAM_HEIGHT, 0.0))
	_camera.rotate_object_local(Vector3.UP, deg_to_rad(_rng.randf_range(-CAM_JITTER_DEG, CAM_JITTER_DEG)))
	_camera.rotate_object_local(Vector3.RIGHT, deg_to_rad(_rng.randf_range(-CAM_JITTER_DEG, CAM_JITTER_DEG)))


func _capture() -> Image:
	for i: int in 3:
		await RenderingServer.frame_post_draw
	return _viewport.get_texture().get_image()


func _connect() -> bool:
	_ws.outbound_buffer_size = 1 << 22
	if _ws.connect_to_url(Config.WS_URL) != OK:
		return false
	var deadline: int = Time.get_ticks_msec() + REPLY_TIMEOUT_MS
	while Time.get_ticks_msec() < deadline:
		_ws.poll()
		match _ws.get_ready_state():
			WebSocketPeer.STATE_OPEN:
				return true
			WebSocketPeer.STATE_CLOSED:
				return false
		await get_tree().process_frame
	return false


## Gửi ảnh, chờ đúng frame_id, trả conf cao nhất (0 nếu không có người hoặc lỗi).
func _detect(img: Image, frame_id: int) -> float:
	var msg: Dictionary = {
		"type": "frame", "frame_id": frame_id, "width": img.get_width(), "height": img.get_height(),
		"jpeg_b64": Marshalls.raw_to_base64(img.save_jpg_to_buffer(Config.JPEG_QUALITY)),
	}
	_ws.send_text(JSON.stringify(msg))
	var deadline: int = Time.get_ticks_msec() + REPLY_TIMEOUT_MS
	while Time.get_ticks_msec() < deadline:
		_ws.poll()
		while _ws.get_available_packet_count() > 0:
			var reply: Variant = JSON.parse_string(_ws.get_packet().get_string_from_utf8())
			if reply is Dictionary and int((reply as Dictionary).get("frame_id", -1)) == frame_id:
				var r := reply as Dictionary
				if r.get("type") != "detections":
					push_warning("detect_gate: server error: %s" % r.get("message"))
					return 0.0
				var dets: Array = r.get("detections", [])
				return float((dets[0] as Dictionary).get("conf", 0.0)) if dets.size() > 0 else 0.0
		await get_tree().process_frame
	push_warning("detect_gate: timeout waiting frame %d" % frame_id)
	return 0.0
