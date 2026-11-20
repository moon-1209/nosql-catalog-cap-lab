extends GutTest

const HEADER: String = "time_s,frame_id,state,n_det,conf,cx,h,true_distance_m,true_angle_deg,v,omega,infer_ms,connected"


func test_columns_order() -> void:
	assert_eq(",".join(RunLogger.COLUMNS), HEADER)


func test_format_row_with_detection() -> void:
	var row := {"time_s": 1.23456, "frame_id": 12, "state": "APPROACH", "n_det": 1, "conf": 0.87,
			"cx": 0.495, "h": 0.66, "true_distance_m": 2.1, "true_angle_deg": -3.5, "v": 0.525,
			"omega": -0.1, "infer_ms": 23.5, "connected": true}
	assert_eq(RunLogger.format_row(row),
			"1.2346,12,APPROACH,1,0.8700,0.4950,0.6600,2.1000,-3.5000,0.5250,-0.1000,23.5000,true")


func test_format_row_without_detection() -> void:
	var row := {"time_s": 0.2, "frame_id": 0, "state": "SEARCH", "n_det": 0, "true_distance_m": 4.32,
			"true_angle_deg": 120.0, "v": 0.0, "omega": 0.5, "infer_ms": 30.0, "connected": true}
	assert_eq(RunLogger.format_row(row),
			"0.2000,0,SEARCH,0,,,,4.3200,120.0000,0.0000,0.5000,30.0000,true")


func test_signed_angle_examples() -> void:
	assert_almost_eq(RunLogger.signed_angle_deg(Vector3(0, 0, -1), Vector3(-1, 0, 0)), 90.0, 1e-4, "người bên trái")
	assert_almost_eq(RunLogger.signed_angle_deg(Vector3(0, 0, -1), Vector3(1, 0, 0)), -90.0, 1e-4)


func test_signed_angle_zero_and_behind() -> void:
	assert_almost_eq(RunLogger.signed_angle_deg(Vector3(0, 0, -1), Vector3(0, 0, -5)), 0.0, 1e-4)
	assert_almost_eq(RunLogger.signed_angle_deg(Vector3(0, 0, -1), Vector3(0, 0, 3)), 180.0, 1e-4, "(−180, 180]")


func test_signed_angle_ignores_height_and_rotated_forward() -> void:
	assert_almost_eq(RunLogger.signed_angle_deg(Vector3(1, 0, 0), Vector3(1, 5, -1)), 45.0, 1e-4)
	assert_almost_eq(RunLogger.signed_angle_deg(Vector3(1, 0, 0), Vector3(0, 1, 0)), 0.0, 1e-4, "không có thành phần XZ")


func test_open_log_close_writes_file() -> void:
	var dir: String = ProjectSettings.globalize_path("user://test_logs")
	var logger := RunLogger.new()
	add_child_autofree(logger)
	assert_true(logger.open(dir))
	assert_string_contains(logger.path.get_file(), "run_")
	logger.log_row({"time_s": 0.1, "frame_id": 0, "state": "SEARCH", "n_det": 0, "connected": false})
	logger.log_row({"time_s": 0.3, "frame_id": 1, "state": "SEARCH", "n_det": 0, "connected": true})
	logger.close()
	var lines: PackedStringArray = FileAccess.get_file_as_string(logger.path).strip_edges().split("\n")
	assert_eq(lines.size(), 3)
	assert_eq(lines[0], HEADER)
	assert_true(lines[2].begins_with("0.3000,1,SEARCH,0,"))
	DirAccess.remove_absolute(logger.path)


func test_flush_after_one_second() -> void:
	var logger := RunLogger.new()
	add_child_autofree(logger)
	logger.open(ProjectSettings.globalize_path("user://test_logs"))
	logger.log_row({"frame_id": 0, "state": "SEARCH"})
	assert_eq(FileAccess.get_file_as_string(logger.path).strip_edges().split("\n").size(), 1, "chưa flush")
	await wait_seconds(1.2)
	assert_eq(FileAccess.get_file_as_string(logger.path).strip_edges().split("\n").size(), 2, "đã flush sau 1 s")
	logger.close()
	DirAccess.remove_absolute(logger.path)


func test_unwritable_path_reports_once_and_keeps_running() -> void:
	var logger := RunLogger.new()
	add_child_autofree(logger)
	var unwritable: String = "C:/" if OS.get_name() == "Windows" else "/"
	assert_false(logger.open(unwritable))  # thư mục có sẵn nhưng chỉ đọc
	assert_push_error("RunLogger")
	logger.log_row({"frame_id": 0})
	logger.flush()
	logger.close()
	assert_false(logger.is_open())
