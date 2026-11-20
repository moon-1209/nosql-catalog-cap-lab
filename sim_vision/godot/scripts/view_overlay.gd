class_name ViewOverlay
extends Control
## Ô góc nhìn robot ở góc trên bên phải (G5): ảnh camera + box người + trạng thái.
## Box vẽ bằng `_draw` của node `Boxes` đặt trên `View`; ảnh gốc không bị sửa.

const BOX_COLOR := Color(0.1, 1.0, 0.2)
const TEXT_COLOR := Color(1, 1, 1)
const SHADOW_COLOR := Color(0, 0, 0, 0.8)
const FONT_SIZE: int = 13

var _dets: Array = []
var _state: String = ""
var _connected: bool = false
var _stt_shown: bool = false        # dòng STT chỉ hiện khi scene có hội thoại (G16)
var _stt_connected: bool = false
var _tts_shown: bool = false        # dòng TTS (G22)
var _tts_connected: bool = false
var _alert: String = ""             # cảnh báo đỏ (G22, cap_cuu)
var _status: String = ""            # vd "Đang dẫn đến: khoa tim mạch" (G22, guide)

const ALERT_COLOR := Color(1, 0.15, 0.1)
const ALERT_FONT_SIZE: int = 22
const EMERGENCY_TEXT: String = "GỌI NHÂN VIÊN Y TẾ"

@onready var _view: TextureRect = $View
@onready var _boxes: Control = $Boxes


func _ready() -> void:
	_boxes.draw.connect(_on_boxes_draw)


func set_viewport(viewport: SubViewport) -> void:
	_view.texture = viewport.get_texture()


func show_detections(dets: Array, state: String, connected: bool) -> void:
	_dets = dets
	_state = state
	_connected = connected
	_boxes.queue_redraw()


## Box chuẩn hóa [0, 1] ➔ hình chữ nhật pixel trong ô kích thước `size`.
static func norm_to_pixel(det: Dictionary, size: Vector2) -> Rect2:
	var p1 := Vector2(float(det["x1"]) * size.x, float(det["y1"]) * size.y)
	var p2 := Vector2(float(det["x2"]) * size.x, float(det["y2"]) * size.y)
	return Rect2(p1, p2 - p1)


func set_stt_connected(connected: bool) -> void:
	_stt_shown = true
	_stt_connected = connected
	_boxes.queue_redraw()


func set_tts_connected(connected: bool) -> void:
	_tts_shown = true
	_tts_connected = connected
	_boxes.queue_redraw()


func set_alert(text: String) -> void:
	_alert = text
	_boxes.queue_redraw()


func set_status(text: String) -> void:
	if text != _status and not text.is_empty():
		print("[status %.1fs] %s" % [Time.get_ticks_msec() / 1000.0, text])  # sự kiện nhiệm vụ vào log để soát sau
	_status = text
	_boxes.queue_redraw()


func get_alert() -> String:
	return _alert


func get_status() -> String:
	return _status


static func tts_connection_text(connected: bool) -> String:
	return "TTS: đã kết nối" if connected else "TTS: mất kết nối"


static func guide_text(slots: Dictionary) -> String:
	if slots.has("department"):
		return "Đang dẫn đến: khoa %s" % str(slots["department"])
	if slots.has("room"):
		return "Đang dẫn đến: phòng %s" % str(slots["room"])
	return ""


static func stt_connection_text(connected: bool) -> String:
	return "STT: đã kết nối" if connected else "STT: mất kết nối"


static func label_text(det: Dictionary) -> String:
	return "person %.2f" % float(det["conf"])


static func connection_text(connected: bool) -> String:
	return "YOLO: đã kết nối" if connected else "YOLO: mất kết nối"


func _on_boxes_draw() -> void:
	var font: Font = ThemeDB.fallback_font
	var size: Vector2 = _boxes.size
	for det: Variant in _dets:
		var r: Rect2 = ViewOverlay.norm_to_pixel(det as Dictionary, size)
		_boxes.draw_rect(r, BOX_COLOR, false, 2.0)
		_text(font, r.position + Vector2(2, -4) if r.position.y > FONT_SIZE + 2 else r.position + Vector2(2, FONT_SIZE + 2),
				ViewOverlay.label_text(det as Dictionary), BOX_COLOR)
	_text(font, Vector2(6, FONT_SIZE + 4), _state, TEXT_COLOR)
	_text(font, Vector2(6, size.y - 6), ViewOverlay.connection_text(_connected),
			TEXT_COLOR if _connected else Color(1, 0.35, 0.3))
	var line: int = 1
	if _stt_shown:
		_text(font, Vector2(6, size.y - 6 - (FONT_SIZE + 2) * line), ViewOverlay.stt_connection_text(_stt_connected),
				TEXT_COLOR if _stt_connected else Color(1, 0.35, 0.3))
		line += 1
	if _tts_shown:
		_text(font, Vector2(6, size.y - 6 - (FONT_SIZE + 2) * line), ViewOverlay.tts_connection_text(_tts_connected),
				TEXT_COLOR if _tts_connected else Color(1, 0.35, 0.3))
	if _status != "":
		_text(font, Vector2(6, 2 * FONT_SIZE + 8), _status, Color(1, 0.85, 0.3))
	if _alert != "":
		var w: float = font.get_string_size(_alert, HORIZONTAL_ALIGNMENT_LEFT, -1, ALERT_FONT_SIZE).x
		var pos := Vector2((size.x - w) / 2.0, size.y / 2.0)
		_boxes.draw_rect(Rect2(pos - Vector2(8, ALERT_FONT_SIZE + 4), Vector2(w + 16, ALERT_FONT_SIZE + 14)),
				Color(0, 0, 0, 0.7))
		_boxes.draw_string(font, pos, _alert, HORIZONTAL_ALIGNMENT_LEFT, -1, ALERT_FONT_SIZE, ALERT_COLOR)


func _text(font: Font, pos: Vector2, text: String, color: Color) -> void:
	_boxes.draw_string(font, pos + Vector2(1, 1), text, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT_SIZE, SHADOW_COLOR)
	_boxes.draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT_SIZE, color)
