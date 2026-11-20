class_name InspectionPanel
extends Control
## Bảng điều khiển kiểm tra thông số Robot (Inspection Telemetry) ở góc trên bên trái.
## Hỗ trợ đóng/mở bằng nút bấm chuột và phím tắt 'I' hoặc 'Tab'.
## Hiển thị trực quan dữ liệu đầu vào theo 4 Tab: LiDAR, YOLO Vision, RL Navigation, Voice & NLU.

var is_open: bool = false

var _lidar_bars: Array[ProgressBar] = []
var _lidar_vals: Array[Label] = []

# YOLO elements
var _vis_det_bar: ProgressBar
var _vis_det_val: Label
var _vis_cx_bar: ProgressBar
var _vis_cx_val: Label
var _vis_h_bar: ProgressBar
var _vis_h_val: Label
var _vis_conf_bar: ProgressBar
var _vis_conf_val: Label
var _vis_summary: Label

# RL Navigation elements
var _rl_phase_badge: Label
var _rl_goal_bar: ProgressBar
var _rl_goal_val: Label
var _rl_sin_bar: ProgressBar
var _rl_sin_val: Label
var _rl_cos_bar: ProgressBar
var _rl_cos_val: Label
var _rl_tether_bar: ProgressBar
var _rl_tether_val: Label
var _rl_v_bar: ProgressBar
var _rl_v_val: Label
var _rl_w_bar: ProgressBar
var _rl_w_val: Label

# Voice elements
var _stt_status_lbl: Label
var _tts_status_lbl: Label
var _hyp_text_lbl: Label
var _intent_lbl: Label
var _target_room_lbl: Label

@onready var _toggle_btn: Button = $ToggleBtn
@onready var _content: PanelContainer = $ContentPanel


func _ready() -> void:
	_toggle_btn.pressed.connect(toggle)
	_build_ui_tabs()
	set_open(false)


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	if key.keycode == KEY_I or key.keycode == KEY_TAB:
		toggle()
		get_viewport().set_input_as_handled()


func toggle() -> void:
	set_open(not is_open)


func set_open(open: bool) -> void:
	is_open = open
	if _content != null:
		_content.visible = is_open
	if _toggle_btn != null:
		_toggle_btn.text = "[▲] Thu gọn thông số (I/Tab)" if is_open else "[▼] Thông số Robot (I/Tab)"


func _build_ui_tabs() -> void:
	var tab_container := $ContentPanel/Tabs as TabContainer
	if tab_container == null:
		return

	# --- Tab 1: LiDAR ---
	var lidar_scroll := ScrollContainer.new()
	lidar_scroll.name = "LiDAR (17 tia)"
	var lidar_vbox := VBoxContainer.new()
	lidar_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lidar_scroll.add_child(lidar_vbox)
	tab_container.add_child(lidar_scroll)

	_lidar_bars.clear()
	_lidar_vals.clear()
	for i: int in 17:
		var row := HBoxContainer.new()
		var angle_deg: float = -120.0 + (240.0 / 16.0) * float(i)
		var lbl_name := Label.new()
		lbl_name.text = "Tia %02d (%+4.0f°):" % [i + 1, angle_deg]
		lbl_name.custom_minimum_size = Vector2(105, 0)
		row.add_child(lbl_name)

		var bar := ProgressBar.new()
		bar.min_value = 0.0
		bar.max_value = 8.0
		bar.step = 0.01
		bar.value = 8.0
		bar.show_percentage = false
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bar.custom_minimum_size = Vector2(130, 16)
		row.add_child(bar)
		_lidar_bars.append(bar)

		var lbl_val := Label.new()
		lbl_val.text = "8.00m"
		lbl_val.custom_minimum_size = Vector2(50, 0)
		lbl_val.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		row.add_child(lbl_val)
		_lidar_vals.append(lbl_val)

		lidar_vbox.add_child(row)

	# --- Tab 2: YOLO Vision ---
	var yolo_vbox := VBoxContainer.new()
	yolo_vbox.name = "YOLO Vision"
	yolo_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tab_container.add_child(yolo_vbox)

	_vis_summary = Label.new()
	_vis_summary.text = "Trạng thái nhận diện: Chờ tín hiệu..."
	yolo_vbox.add_child(_vis_summary)

	var det_row := _create_stat_row("Người phát hiện (has_det):", 0.0, 1.0, 0.0, "%0.0f")
	_vis_det_bar = det_row["bar"]
	_vis_det_val = det_row["val"]
	yolo_vbox.add_child(det_row["row"])

	var cx_row := _create_stat_row("Lệch tâm ngang (cx_offset):", -0.5, 0.5, 0.0, "%+0.2f")
	_vis_cx_bar = cx_row["bar"]
	_vis_cx_val = cx_row["val"]
	yolo_vbox.add_child(cx_row["row"])

	var h_row := _create_stat_row("Chiều cao box (box_height):", 0.0, 1.0, 0.0, "%0.2f")
	_vis_h_bar = h_row["bar"]
	_vis_h_val = h_row["val"]
	yolo_vbox.add_child(h_row["row"])

	var conf_row := _create_stat_row("Độ tin cậy (confidence):", 0.0, 1.0, 0.0, "%0.1f%%", 100.0)
	_vis_conf_bar = conf_row["bar"]
	_vis_conf_val = conf_row["val"]
	yolo_vbox.add_child(conf_row["row"])

	# --- Tab 3: RL Navigation ---
	var rl_vbox := VBoxContainer.new()
	rl_vbox.name = "RL Navigation"
	rl_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tab_container.add_child(rl_vbox)

	_rl_phase_badge = Label.new()
	_rl_phase_badge.text = "Pha nhiệm vụ: SEARCH_PATIENT"
	rl_vbox.add_child(_rl_phase_badge)

	var goal_row := _create_stat_row("Khoảng cách tới đích (d_goal):", 0.0, 25.0, 0.0, "%.2f m")
	_rl_goal_bar = goal_row["bar"]
	_rl_goal_val = goal_row["val"]
	rl_vbox.add_child(goal_row["row"])

	var sin_row := _create_stat_row("Lệch góc sin(theta):", -1.0, 1.0, 0.0, "%+0.2f")
	_rl_sin_bar = sin_row["bar"]
	_rl_sin_val = sin_row["val"]
	rl_vbox.add_child(sin_row["row"])

	var cos_row := _create_stat_row("Hướng nhìn cos(theta):", -1.0, 1.0, 1.0, "%+0.2f")
	_rl_cos_bar = cos_row["bar"]
	_rl_cos_val = cos_row["val"]
	rl_vbox.add_child(cos_row["row"])

	var tether_row := _create_stat_row("Khoảng cách dắt người (d_tether):", 0.0, 5.0, 0.0, "%.2f m")
	_rl_tether_bar = tether_row["bar"]
	_rl_tether_val = tether_row["val"]
	rl_vbox.add_child(tether_row["row"])

	var v_row := _create_stat_row("Vận tốc tiến (v):", 0.0, 0.8, 0.0, "%.2f m/s")
	_rl_v_bar = v_row["bar"]
	_rl_v_val = v_row["val"]
	rl_vbox.add_child(v_row["row"])

	var w_row := _create_stat_row("Vận tốc quay (omega):", -1.2, 1.2, 0.0, "%+.2f rad/s")
	_rl_w_bar = w_row["bar"]
	_rl_w_val = w_row["val"]
	rl_vbox.add_child(w_row["row"])

	# --- Tab 4: Voice & NLU ---
	var voice_vbox := VBoxContainer.new()
	voice_vbox.name = "Hội Thoại / Voice"
	voice_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tab_container.add_child(voice_vbox)

	var conn_row := HBoxContainer.new()
	_stt_status_lbl = Label.new()
	_stt_status_lbl.text = "STT: Đã kết nối"
	_stt_status_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	conn_row.add_child(_stt_status_lbl)

	_tts_status_lbl = Label.new()
	_tts_status_lbl.text = "TTS: Sẵn sàng"
	_tts_status_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	conn_row.add_child(_tts_status_lbl)
	voice_vbox.add_child(conn_row)

	voice_vbox.add_child(HSeparator.new())

	_hyp_text_lbl = Label.new()
	_hyp_text_lbl.text = "Nghe được: (Chưa có hội thoại)"
	_hyp_text_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	voice_vbox.add_child(_hyp_text_lbl)

	_intent_lbl = Label.new()
	_intent_lbl.text = "Ý định (Intent): (trống)"
	voice_vbox.add_child(_intent_lbl)

	_target_room_lbl = Label.new()
	_target_room_lbl.text = "Đích điều hướng: (trống)"
	voice_vbox.add_child(_target_room_lbl)


func _create_stat_row(label_text: String, min_v: float, max_v: float, init_v: float, format_str: String, mult: float = 1.0) -> Dictionary:
	var row := HBoxContainer.new()
	var lbl := Label.new()
	lbl.text = label_text
	lbl.custom_minimum_size = Vector2(170, 0)
	row.add_child(lbl)

	var bar := ProgressBar.new()
	bar.min_value = min_v
	bar.max_value = max_v
	bar.step = 0.01
	bar.value = init_v
	bar.show_percentage = false
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar.custom_minimum_size = Vector2(100, 16)
	row.add_child(bar)

	var vlbl := Label.new()
	vlbl.text = format_str % (init_v * mult)
	vlbl.custom_minimum_size = Vector2(65, 0)
	vlbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(vlbl)

	return {"row": row, "bar": bar, "val": vlbl}


## Cập nhật toàn bộ 17 tia LiDAR
func update_lidar(readings: PackedFloat32Array) -> void:
	if not is_open:
		return
	for i: int in mini(readings.size(), _lidar_bars.size()):
		var norm_d: float = readings[i]
		var meters: float = norm_d * 8.0
		_lidar_bars[i].value = meters
		_lidar_vals[i].text = "%.2fm" % meters
		if meters < 0.8:
			_lidar_bars[i].modulate = Color(1.0, 0.2, 0.2)
		elif meters < 1.5:
			_lidar_bars[i].modulate = Color(1.0, 0.85, 0.2)
		else:
			_lidar_bars[i].modulate = Color(0.2, 0.9, 0.3)


## Cập nhật kết quả nhận diện YOLO
func update_vision(dets: Array) -> void:
	if not is_open:
		return
	if dets.is_empty():
		_vis_summary.text = "Số người phát hiện: 0"
		_vis_det_bar.value = 0.0
		_vis_det_val.text = "0"
		_vis_cx_bar.value = 0.0
		_vis_cx_val.text = "+0.00"
		_vis_h_bar.value = 0.0
		_vis_h_val.text = "0.00"
		_vis_conf_bar.value = 0.0
		_vis_conf_val.text = "0.0%"
		return
	var d: Dictionary = dets[0] as Dictionary
	var cx: float = (float(d.get("x1", 0.5)) + float(d.get("x2", 0.5))) * 0.5
	var h: float = float(d.get("y2", 0.0)) - float(d.get("y1", 0.0))
	var conf: float = float(d.get("conf", 0.0))
	_vis_summary.text = "Số người phát hiện: %d (người gần nhất: conf %.2f)" % [dets.size(), conf]
	_vis_det_bar.value = 1.0
	_vis_det_val.text = "1"
	_vis_cx_bar.value = cx - 0.5
	_vis_cx_val.text = "%+0.2f" % (cx - 0.5)
	_vis_h_bar.value = h
	_vis_h_val.text = "%.2f" % h
	_vis_conf_bar.value = conf
	_vis_conf_val.text = "%.1f%%" % (conf * 100.0)


## Cập nhật trạng thái RL và định vị
func update_rl_navigation(phase_name: String, d_goal: float, sin_th: float, cos_th: float, d_tether: float, v: float, w: float) -> void:
	if not is_open:
		return
	_rl_phase_badge.text = "Pha nhiệm vụ: [ %s ]" % phase_name
	_rl_goal_bar.value = clampf(d_goal, 0.0, 25.0)
	_rl_goal_val.text = "%.2f m" % d_goal
	_rl_sin_bar.value = clampf(sin_th, -1.0, 1.0)
	_rl_sin_val.text = "%+0.2f" % sin_th
	_rl_cos_bar.value = clampf(cos_th, -1.0, 1.0)
	_rl_cos_val.text = "%+0.2f" % cos_th
	_rl_tether_bar.value = clampf(d_tether, 0.0, 5.0)
	_rl_tether_val.text = "%.2f m" % d_tether
	_rl_v_bar.value = clampf(v, 0.0, 0.8)
	_rl_v_val.text = "%.2f m/s" % v
	_rl_w_bar.value = clampf(w, -1.2, 1.2)
	_rl_w_val.text = "%+.2f rad/s" % w


## Cập nhật thông tin hội thoại
func update_dialogue(stt_ok: bool, tts_ok: bool, transcript: String, intent: String, target: String, floor_num: int) -> void:
	if not is_open:
		return
	_stt_status_lbl.text = "STT: Đã kết nối" if stt_ok else "STT: Mất kết nối"
	_stt_status_lbl.modulate = Color(0.2, 0.9, 0.3) if stt_ok else Color(1.0, 0.3, 0.3)
	_tts_status_lbl.text = "TTS: Sẵn sàng" if tts_ok else "TTS: Mất kết nối"
	_tts_status_lbl.modulate = Color(0.2, 0.9, 0.3) if tts_ok else Color(1.0, 0.3, 0.3)
	if not transcript.is_empty():
		_hyp_text_lbl.text = "Nghe được: \"%s\"" % transcript
	if not intent.is_empty():
		_intent_lbl.text = "Ý định: %s" % intent
	if not target.is_empty():
		_target_room_lbl.text = "Đích: %s (Tầng %d)" % [target, floor_num]
