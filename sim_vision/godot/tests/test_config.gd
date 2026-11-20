extends GutTest


func test_constants_match_contract() -> void:
	assert_eq(Config.WS_URL, "ws://127.0.0.1:8765")
	assert_eq(Config.CAPTURE_HZ, 5)
	assert_eq(Config.IMG_W, 640)
	assert_eq(Config.IMG_H, 480)
	assert_almost_eq(Config.JPEG_QUALITY, 0.8, 1e-6)
	assert_almost_eq(Config.YOLO_CONF, 0.4, 1e-6)
	assert_almost_eq(Config.V_MAX, 0.8, 1e-6)
	assert_almost_eq(Config.OMEGA_MAX, 1.5, 1e-6)
	assert_almost_eq(Config.K_ANG, 2.0, 1e-6)
	assert_almost_eq(Config.K_LIN, 1.5, 1e-6)
	assert_almost_eq(Config.H_TARGET, 0.85, 1e-6)
	assert_almost_eq(Config.H_HYST, 0.10, 1e-6)
	assert_almost_eq(Config.ALIGN_TOL, 0.25, 1e-6)
	assert_almost_eq(Config.LOST_TIMEOUT_S, 1.5, 1e-6)
	assert_almost_eq(Config.SEARCH_OMEGA, 0.5, 1e-6)
	assert_eq(Config.STALE_MS, 500)
	assert_almost_eq(Config.SAFE_DIST_HUMAN, 0.8, 1e-6)
	assert_almost_eq(Config.SAFE_DIST_OBSTACLE, 0.5, 1e-6)
	assert_almost_eq(Config.RECONNECT_S, 2.0, 1e-6)


func test_state_name() -> void:
	assert_eq(Config.state_name(Config.RobotState.SEARCH), "SEARCH")
	assert_eq(Config.state_name(Config.RobotState.APPROACH), "APPROACH")
	assert_eq(Config.state_name(Config.RobotState.ARRIVED), "ARRIVED")


func test_initial_state_is_search() -> void:
	# Mục 2.3: trạng thái ban đầu là SEARCH (giá trị enum đầu tiên).
	assert_eq(Config.RobotState.SEARCH, 0)
