extends GutTest

const EPS: float = 1e-6
const S := Config.RobotState

var ctrl: Controller


func before_each() -> void:
	ctrl = Controller.new()
	autofree(ctrl)


## Detection có tâm x = cx, chiều cao h (tọa độ chuẩn hóa).
func _det(cx: float, h: float, conf: float = 0.9) -> Dictionary:
	return {"x1": cx - 0.05, "y1": 0.2, "x2": cx + 0.05, "y2": 0.2 + h, "conf": conf}


func _check(out: Dictionary, state: int, v: float, omega: float) -> void:
	assert_eq(out["state"], state, "state %s" % Config.state_name(out["state"]))
	assert_almost_eq(out["v"], v, EPS, "v")
	assert_almost_eq(out["omega"], omega, EPS, "omega")


# --- Bảng ví dụ G7.3 ---

func test_search_no_dets() -> void:
	_check(ctrl.step(S.SEARCH, [], 0.0), S.SEARCH, 0.0, 0.5)


func test_approach_just_lost_waits() -> void:
	var out: Dictionary = ctrl.step(S.APPROACH, [], 0.5)
	_check(out, S.APPROACH, 0.0, 0.0)
	assert_eq(out["target"], {})


func test_approach_lost_too_long_searches() -> void:
	_check(ctrl.step(S.APPROACH, [], 2.0), S.SEARCH, 0.0, 0.5)


func test_search_person_right_turns_right_only() -> void:
	_check(ctrl.step(S.SEARCH, [_det(0.80, 0.30, 0.9)], 0.0), S.APPROACH, 0.0, -0.6)


func test_approach_small_offset() -> void:
	# Dò vết: e = 0.05 ➔ omega = -2.0·0.05 = -0.1; v = 1.5·(0.85-0.40) = 0.675.
	_check(ctrl.step(S.APPROACH, [_det(0.55, 0.40)], 0.0), S.APPROACH, 0.675, -0.1)


func test_approach_close_arrives() -> void:
	_check(ctrl.step(S.APPROACH, [_det(0.50, 0.90)], 0.0), S.ARRIVED, 0.0, 0.0)


func test_arrived_within_hysteresis_stays() -> void:
	_check(ctrl.step(S.ARRIVED, [_det(0.50, 0.78)], 0.0), S.ARRIVED, 0.0, 0.0)


func test_arrived_below_hysteresis_approaches() -> void:
	_check(ctrl.step(S.ARRIVED, [_det(0.50, 0.50)], 0.0), S.APPROACH, 0.525, 0.0)


func test_picks_highest_conf() -> void:
	var low: Dictionary = _det(0.2, 0.3, 0.6)
	var high: Dictionary = _det(0.7, 0.3, 0.9)
	var out: Dictionary = ctrl.step(S.SEARCH, [low, high], 0.0)
	assert_eq(out["target"], high)
	out = ctrl.step(S.SEARCH, [high, low], 0.0)
	assert_eq(out["target"], high, "không phụ thuộc thứ tự")


# --- Test biên ---

func test_cx_zero_turns_left_max_without_moving() -> void:
	# e = -0.5 ➔ omega = +1.0 (quay trái, Mục 2.4), |e| > ALIGN_TOL ➔ v = 0.
	var d := {"x1": 0.0, "y1": 0.2, "x2": 0.0001, "y2": 0.5, "conf": 0.9}
	var out: Dictionary = ctrl.step(S.SEARCH, [d], 0.0)
	assert_eq(out["state"], S.APPROACH)
	assert_almost_eq(out["omega"], 2.0 * 0.49995, EPS)
	assert_eq(out["v"], 0.0)


func test_cx_one_turns_right() -> void:
	var d := {"x1": 0.9999, "y1": 0.2, "x2": 1.0, "y2": 0.5, "conf": 0.9}
	var out: Dictionary = ctrl.step(S.APPROACH, [d], 0.0)
	assert_lt(out["omega"], 0.0)
	assert_eq(out["v"], 0.0)


func test_tiny_box_speed_clamped_to_vmax() -> void:
	# h ≈ 0 ➔ K_LIN·0.85 = 1.275 > V_MAX ➔ v = 0.8.
	var d := {"x1": 0.49, "y1": 0.5, "x2": 0.51, "y2": 0.5001, "conf": 0.9}
	_check(ctrl.step(S.SEARCH, [d], 0.0), S.APPROACH, Config.V_MAX, 0.0)


func test_omega_never_exceeds_limit() -> void:
	for i: int in 21:
		var cx: float = i / 20.0
		var d := {"x1": maxf(cx - 0.01, 0.0), "y1": 0.2, "x2": minf(cx + 0.01, 1.0), "y2": 0.4, "conf": 0.9}
		var out: Dictionary = ctrl.step(S.APPROACH, [d], 0.0)
		assert_true(absf(out["omega"]) <= Config.OMEGA_MAX + EPS)
		assert_true(out["v"] >= 0.0 and out["v"] <= Config.V_MAX + EPS)


func test_h_exactly_target_arrives() -> void:
	var d := {"x1": 0.45, "y1": 0.10, "x2": 0.55, "y2": 0.95, "conf": 0.9}  # h = 0.85
	assert_eq(ctrl.step(S.APPROACH, [d], 0.0)["state"], S.ARRIVED)


func test_hysteresis_lower_bound_inclusive() -> void:
	var d := {"x1": 0.45, "y1": 0.15, "x2": 0.55, "y2": 0.90, "conf": 0.9}  # h = 0.75
	assert_eq(ctrl.step(S.ARRIVED, [d], 0.0)["state"], S.ARRIVED)
	assert_eq(ctrl.step(S.APPROACH, [d], 0.0)["state"], S.APPROACH, "trễ chỉ áp dụng khi đang ARRIVED")


func test_lost_timeout_boundary_not_exceeded() -> void:
	_check(ctrl.step(S.APPROACH, [], Config.LOST_TIMEOUT_S), S.APPROACH, 0.0, 0.0)


func test_arrived_lost_briefly_stays_arrived() -> void:
	_check(ctrl.step(S.ARRIVED, [], 0.3), S.ARRIVED, 0.0, 0.0)


func test_align_tol_boundary_still_moves() -> void:
	var d := {"x1": 0.70, "y1": 0.2, "x2": 0.80, "y2": 0.5, "conf": 0.9}  # cx = 0.75, e = 0.25
	assert_gt(ctrl.step(S.APPROACH, [d], 0.0)["v"], 0.0, "|e| = ALIGN_TOL không bị chặn (điều kiện là >)")


func test_equal_conf_picks_taller_box() -> void:
	var short: Dictionary = _det(0.3, 0.2, 0.8)
	var tall: Dictionary = _det(0.6, 0.4, 0.8)
	assert_eq(Controller.pick_target([short, tall]), tall)
	assert_eq(Controller.pick_target([tall, short]), tall)


func test_pure_function() -> void:
	var dets: Array = [_det(0.55, 0.30)]
	var copy: Array = dets.duplicate(true)
	var a: Dictionary = ctrl.step(S.APPROACH, dets, 0.0)
	var b: Dictionary = ctrl.step(S.APPROACH, dets, 0.0)
	assert_eq(a, b, "cùng input ➔ cùng output")
	assert_eq(dets, copy, "không sửa input")
