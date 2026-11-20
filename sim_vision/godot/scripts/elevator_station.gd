class_name ElevatorStation
extends StaticBody3D
## Trạm thang máy bệnh viện tương tác 2 chiều (Floor 1 <-> Floor 2).
## Điều khiển cửa trượt 2 cánh (DoorLeft, DoorRight), đèn LED hiển thị tầng,
## chuông báo tầng (Ding-Dong) và buồng thang máy có ánh sáng nội thất.

signal doors_opened
signal doors_closed

@export var current_floor: int = 1
@export var door_open_distance: float = 0.72
@export var door_speed: float = 1.6

var is_open: bool = false
var _left_closed_x: float = -0.43
var _right_closed_x: float = 0.43

@onready var door_left: MeshInstance3D = $DoorLeft
@onready var door_right: MeshInstance3D = $DoorRight
@onready var floor_led_text: Label3D = $FloorIndicator/FloorLedText
@onready var header_text: Label3D = $HeaderSign/HeaderText
@onready var collision_shape: CollisionShape3D = $Collision
@onready var audio_chime: AudioStreamPlayer3D = $AudioChime
@onready var audio_hum: AudioStreamPlayer3D = $AudioHum
@onready var cabin_light: OmniLight3D = get_node_or_null(^"Cabin/CabinLight")


func _ready() -> void:
	if door_left != null:
		_left_closed_x = door_left.position.x
	if door_right != null:
		_right_closed_x = door_right.position.x
	set_floor_indicator(current_floor, "")


func _process(delta: float) -> void:
	if door_left == null or door_right == null:
		return
	var target_left_x: float = (_left_closed_x - door_open_distance) if is_open else _left_closed_x
	var target_right_x: float = (_right_closed_x + door_open_distance) if is_open else _right_closed_x
	door_left.position.x = move_toward(door_left.position.x, target_left_x, door_speed * delta)
	door_right.position.x = move_toward(door_right.position.x, target_right_x, door_speed * delta)


## Mở cửa thang máy, tắt va chạm chắn cửa để robot/bệnh nhân bước vào
func open_doors() -> void:
	is_open = true
	if collision_shape != null:
		collision_shape.set_deferred(&"disabled", true)
	play_chime()
	var tween := create_tween()
	tween.tween_interval(0.6)
	tween.finished.connect(func(): doors_opened.emit())


## Đóng cửa thang máy, bật lại va chạm chắn cửa
func close_doors() -> void:
	is_open = false
	if collision_shape != null:
		collision_shape.set_deferred(&"disabled", false)
	var tween := create_tween()
	tween.tween_interval(0.6)
	tween.finished.connect(func(): doors_closed.emit())


## Cập nhật bảng đèn LED hiển thị tầng
func set_floor_indicator(floor_num: int, arrow: String = "") -> void:
	if floor_led_text == null:
		return
	var arrow_str: String = (" " + arrow) if not arrow.is_empty() else ""
	floor_led_text.text = "TẦNG %d%s" % [floor_num, arrow_str]


## Điểm đón/chờ ngay trước cửa thang máy (ngoài hành lang)
func get_entrance_position() -> Vector3:
	return global_transform * Vector3(0.0, 0.0, 1.4)


## Điểm bên trong buồng thang máy
func get_cabin_position() -> Vector3:
	return global_transform * Vector3(0.0, 0.0, -1.0)


func play_chime() -> void:
	if audio_chime != null:
		audio_chime.play()


func start_hum() -> void:
	if audio_hum != null and not audio_hum.playing:
		audio_hum.play()


func stop_hum() -> void:
	if audio_hum != null and audio_hum.playing:
		audio_hum.stop()
