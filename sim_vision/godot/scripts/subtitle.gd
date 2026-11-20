class_name Subtitle
extends Control
## Phụ đề hội thoại (G16): dòng 1 "Nghe được: <text>" (nhỏ, nhạt), dòng 2 "Robot: <response>" (≥ 22 px).
## Hiện trong `duration` giây rồi tự ẩn và phát `finished`.

signal finished

const HEARD_PREFIX: String = "Nghe được: "
const ROBOT_PREFIX: String = "Robot: "
const SORRY: String = "Xin lỗi, tôi chưa nghe rõ. Anh chị nói lại được không ạ?"

var time_left: float = 0.0

@onready var _heard: Label = $Panel/Box/Heard
@onready var _reply: Label = $Panel/Box/Reply


func _ready() -> void:
	visible = false


## Hiện phụ đề; `heard` rỗng ➔ ẩn dòng 1.
func show_reply(heard: String, response: String, duration: float = Config.SUBTITLE_S) -> void:
	var lines: PackedStringArray = Subtitle.format_lines(heard, response)
	_heard.text = lines[0]
	_heard.visible = lines[0] != ""
	_reply.text = lines[1]
	time_left = duration
	visible = true


func show_sorry(duration: float = Config.SUBTITLE_S) -> void:
	show_reply("", SORRY, duration)


func is_showing() -> bool:
	return visible


func hide_now() -> void:
	time_left = 0.0
	visible = false


func _process(delta: float) -> void:
	if not visible:
		return
	time_left -= delta
	if time_left <= 0.0:
		hide_now()
		finished.emit()


static func format_lines(heard: String, response: String) -> PackedStringArray:
	return [HEARD_PREFIX + heard if heard != "" else "", ROBOT_PREFIX + response]
