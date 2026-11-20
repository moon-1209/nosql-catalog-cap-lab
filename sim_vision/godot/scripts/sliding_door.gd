@tool
class_name SlidingDoor
extends Node3D
## Cửa trượt tự động kiểu RimWorld âm tường (pocket sliding door) cho môi trường bệnh viện.
## Khi Robot hoặc Human (CharacterBody3D) tiến vào vùng cảm biến TriggerArea (1.8 m mỗi bên),
## cửa mở ngay lập tức: tắt collision_layer và CollisionShape3D để RayCast3D/dẫn đường RL không bị kẹt,
## đồng thời trượt cánh cửa vào hốc tường trong `slide_duration_s` (0.25 s).
## Tự động đóng lại sau `close_delay_s` (1.5 s) kể từ khi vùng cảm biến trống.
## `robot_can_open = false` (cửa chính ra ngoài): chỉ người mở được, robot coi như tường ➔ không rời tòa nhà.

signal door_state_changed(opened: bool)

@export var open_offset: Vector3 = Vector3(1.75, 0.0, 0.0)
@export var slide_duration_s: float = 0.25
@export var close_delay_s: float = 1.5
@export var door_label: String = "":
	set(v):
		door_label = v
		_update_labels()
@export var robot_can_open: bool = true

var is_open: bool = false
var _collision_disabled: bool = false
var _close_timer: float = 0.0
var _occupants: Dictionary = {}

@onready var _door_panel: Node3D = $DoorPanel
@onready var _door_body: StaticBody3D = $DoorBody
@onready var _collision: CollisionShape3D = $DoorBody/CollisionShape3D
@onready var _trigger_area: Area3D = $TriggerArea
@onready var _status_mat: StandardMaterial3D = null
@onready var _header_label: Label3D = get_node_or_null(^"Frame/HeaderSign/Label")
@onready var _header_label_back: Label3D = get_node_or_null(^"Frame/HeaderSign/LabelBack")


func _update_labels() -> void:
	var front: Label3D = _header_label if _header_label != null else get_node_or_null(^"Frame/HeaderSign/Label") as Label3D
	var back: Label3D = _header_label_back if _header_label_back != null else get_node_or_null(^"Frame/HeaderSign/LabelBack") as Label3D
	var text_to_set: String = door_label if not door_label.is_empty() else "PHÒNG KHÁM"
	for lbl: Label3D in [front, back]:
		if lbl != null:
			lbl.text = text_to_set


func _ready() -> void:
	add_to_group(&"sliding_doors")
	_update_labels()
	if Engine.is_editor_hint():
		return
	if _trigger_area != null:
		_trigger_area.body_entered.connect(_on_body_entered)
		_trigger_area.body_exited.connect(_on_body_exited)
	var indicator := get_node_or_null(^"Frame/StatusLight") as MeshInstance3D
	if indicator != null and indicator.mesh != null:
		_status_mat = indicator.get_active_material(0) as StandardMaterial3D
		if _status_mat != null:
			_status_mat = _status_mat.duplicate() as StandardMaterial3D
			indicator.set_surface_override_material(0, _status_mat)
	_update_visual_indicator()


func _physics_process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	step(delta)


## Hàm bước vật lý tách riêng để unit test gọi trực tiếp không cần chờ thời gian thực.
func step(delta: float) -> void:
	if is_open and _occupants.is_empty() and _close_timer > 0.0:
		_close_timer -= delta
		if _close_timer <= 0.0:
			_close_timer = 0.0
			force_close()
	if _door_panel != null:
		var target_pos: Vector3 = open_offset if is_open else Vector3.ZERO
		var speed: float = open_offset.length() / maxf(slide_duration_s, 0.01)
		_door_panel.position = _door_panel.position.move_toward(target_pos, speed * delta)


static func is_valid_opener(body: Node) -> bool:
	if body == null:
		return false
	return body is CharacterBody3D or body.is_in_group(&"door_opener")


func _on_body_entered(body: Node3D) -> void:
	if not SlidingDoor.is_valid_opener(body) or (not robot_can_open and body is Robot):
		return
	_occupants[body.get_instance_id()] = true
	_close_timer = 0.0
	if not is_open:
		force_open()


func _on_body_exited(body: Node3D) -> void:
	if body == null:
		return
	_occupants.erase(body.get_instance_id())
	if _occupants.is_empty() and is_open:
		_close_timer = close_delay_s


## Mở cửa ngay lập tức và tắt va chạm vật lý để RayCast3D nhìn xuyên qua ngay.
func force_open() -> void:
	var changed: bool = not is_open
	is_open = true
	_collision_disabled = true
	_close_timer = 0.0
	if _door_body != null:
		_door_body.collision_layer = 0
	if _collision != null:
		_collision.set_deferred("disabled", true)
	_update_visual_indicator()
	if changed:
		door_state_changed.emit(true)


## Đóng cửa và bật lại va chạm vật lý.
func force_close() -> void:
	var changed: bool = is_open
	is_open = false
	_collision_disabled = false
	_close_timer = 0.0
	if _door_body != null:
		_door_body.collision_layer = 1
	if _collision != null:
		_collision.set_deferred("disabled", false)
	_update_visual_indicator()
	if changed:
		door_state_changed.emit(false)


func is_collision_disabled() -> bool:
	return _collision_disabled


func get_slide_progress() -> float:
	if _door_panel == null or open_offset.length() <= 1e-6:
		return 1.0 if is_open else 0.0
	return clampf(_door_panel.position.length() / open_offset.length(), 0.0, 1.0)


func get_panel_position() -> Vector3:
	return _door_panel.position if _door_panel != null else Vector3.ZERO


func occupant_count() -> int:
	return _occupants.size()


func _update_visual_indicator() -> void:
	if _status_mat == null:
		return
	var col := Color(0.15, 0.85, 0.35) if is_open else Color(0.1, 0.55, 0.78)
	_status_mat.albedo_color = col
	_status_mat.emission = col
