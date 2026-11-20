extends GutTest

const PanelScene: PackedScene = preload("res://scenes/inspection_panel.tscn")
const InspectionPanelScript = preload("res://scripts/inspection_panel.gd")

var _panel: Node


func before_each() -> void:
	_panel = PanelScene.instantiate()
	add_child_autofree(_panel)


func test_initial_state_closed_and_toggleable() -> void:
	assert_false(_panel.is_open, "starts collapsed")
	var content: Control = _panel.get_node(^"ContentPanel") as Control
	assert_false(content.visible)

	_panel.toggle()
	assert_true(_panel.is_open, "expanded after toggle")
	assert_true(content.visible)

	_panel.toggle()
	assert_false(_panel.is_open, "collapsed after second toggle")
	assert_false(content.visible)


func test_update_lidar_values_and_colors() -> void:
	_panel.set_open(true)
	var readings := PackedFloat32Array()
	readings.resize(17)
	readings[0] = 0.05   # 0.40m (< 0.8m -> red)
	readings[1] = 0.15   # 1.20m (< 1.5m -> yellow)
	readings[2] = 0.50   # 4.00m (>= 1.5m -> green)
	for i: int in range(3, 17):
		readings[i] = 1.0 # 8.00m

	_panel.update_lidar(readings)

	assert_almost_eq(_panel._lidar_bars[0].value, 0.40, 0.05)
	assert_eq(_panel._lidar_vals[0].text, "0.40m")
	assert_eq(_panel._lidar_bars[0].modulate, Color(1.0, 0.2, 0.2))

	assert_almost_eq(_panel._lidar_bars[1].value, 1.20, 0.05)
	assert_eq(_panel._lidar_vals[1].text, "1.20m")
	assert_eq(_panel._lidar_bars[1].modulate, Color(1.0, 0.85, 0.2))

	assert_almost_eq(_panel._lidar_bars[2].value, 4.00, 0.05)
	assert_eq(_panel._lidar_vals[2].text, "4.00m")
	assert_eq(_panel._lidar_bars[2].modulate, Color(0.2, 0.9, 0.3))


func test_update_vision_and_navigation() -> void:
	_panel.set_open(true)

	# Test YOLO vision
	var det: Dictionary = {"x1": 0.3, "y1": 0.1, "x2": 0.7, "y2": 0.9, "conf": 0.85}
	_panel.update_vision([det])
	assert_eq(_panel._vis_det_bar.value, 1.0)
	assert_almost_eq(_panel._vis_conf_bar.value, 0.85, 0.01)
	assert_eq(_panel._vis_conf_val.text, "85.0%")

	# Test empty dets
	_panel.update_vision([])
	assert_eq(_panel._vis_det_bar.value, 0.0)
	assert_eq(_panel._vis_conf_val.text, "0.0%")

	# Test RL navigation
	_panel.update_rl_navigation("GUIDE_ESCORT", 12.5, 0.707, 0.707, 1.8, 0.6, -0.4)
	assert_almost_eq(_panel._rl_goal_bar.value, 12.5, 0.01)
	assert_eq(_panel._rl_goal_val.text, "12.50 m")
	assert_almost_eq(_panel._rl_tether_bar.value, 1.8, 0.01)
	assert_almost_eq(_panel._rl_v_bar.value, 0.6, 0.01)
	assert_almost_eq(_panel._rl_w_bar.value, -0.4, 0.01)


func test_unhandled_input_shortcuts() -> void:
	assert_false(_panel.is_open)

	var ev_i := InputEventKey.new()
	ev_i.keycode = KEY_I
	ev_i.pressed = true
	_panel._unhandled_input(ev_i)
	assert_true(_panel.is_open, "toggled open with key I")

	var ev_tab := InputEventKey.new()
	ev_tab.keycode = KEY_TAB
	ev_tab.pressed = true
	_panel._unhandled_input(ev_tab)
	assert_false(_panel.is_open, "toggled closed with key Tab")
