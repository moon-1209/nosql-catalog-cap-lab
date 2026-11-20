class_name RunLogger
extends Node
## Ghi CSV mỗi chu kỳ nhận diện (G9): logs/run_<YYYYMMDD_HHMMSS>.csv.
## Ghi đệm, flush mỗi 1 giây và khi thoát. Không ghi được file ➔ push_error một lần, scene vẫn chạy.

const COLUMNS: PackedStringArray = ["time_s", "frame_id", "state", "n_det", "conf", "cx", "h",
		"true_distance_m", "true_angle_deg", "v", "omega", "infer_ms", "connected"]
const FLOAT_COLUMNS: PackedStringArray = ["time_s", "conf", "cx", "h", "true_distance_m",
		"true_angle_deg", "v", "omega", "infer_ms"]
const FLUSH_MS: int = 1000

var path: String = ""

var _file: FileAccess = null
var _buffer: PackedStringArray = []
var _last_flush_ms: int = 0
var _error_reported: bool = false


## Mở file mới trong `dir` (mặc định thư mục logs/ cạnh project Godot). Trả true nếu mở được.
func open(dir: String = "") -> bool:
	if dir == "":
		dir = ProjectSettings.globalize_path("res://").path_join("../logs").simplify_path()
	if not DirAccess.dir_exists_absolute(dir) and DirAccess.make_dir_recursive_absolute(dir) != OK:
		_report_error("cannot create directory %s" % dir)
		return false
	var stamp: String = Time.get_datetime_string_from_system(false, true).replace("-", "").replace(":", "").replace(" ", "_")
	path = dir.path_join("run_%s.csv" % stamp)
	_file = FileAccess.open(path, FileAccess.WRITE)
	if _file == null:
		_report_error("cannot open %s (%s)" % [path, error_string(FileAccess.get_open_error())])
		return false
	_file.store_line(",".join(COLUMNS))
	_last_flush_ms = Time.get_ticks_msec()
	return true


func log_row(row: Dictionary) -> void:
	if _file == null:
		return
	_buffer.append(RunLogger.format_row(row))


func flush() -> void:
	if _file == null:
		return
	for line: String in _buffer:
		_file.store_line(line)
	_buffer.clear()
	_file.flush()
	if _file.get_error() != OK:
		_report_error("write failed: %s" % error_string(_file.get_error()))
	_last_flush_ms = Time.get_ticks_msec()


func close() -> void:
	if _file == null:
		return
	flush()
	_file.close()
	_file = null


func is_open() -> bool:
	return _file != null


func _process(_delta: float) -> void:
	if _file != null and Time.get_ticks_msec() - _last_flush_ms >= FLUSH_MS:
		flush()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		close()


func _exit_tree() -> void:
	close()  # thoát bằng get_tree().quit() không có WM_CLOSE_REQUEST


func _report_error(msg: String) -> void:
	if not _error_reported:
		_error_reported = true
		push_error("RunLogger: " + msg)


## Một dòng CSV theo COLUMNS; số thực 4 chữ số thập phân; thiếu giá trị (vd không có detection) ➔ ô trống.
static func format_row(row: Dictionary) -> String:
	var cells: PackedStringArray = []
	for col: String in COLUMNS:
		var v: Variant = row.get(col)
		if v == null:
			cells.append("")
		elif col in FLOAT_COLUMNS:
			cells.append("%.4f" % float(v))
		elif v is bool:
			cells.append("true" if v else "false")
		else:
			cells.append(str(v))
	return ",".join(cells)


## Góc có dấu (độ) từ hướng trước của robot tới mục tiêu, trên mặt phẳng XZ.
## Dương khi mục tiêu bên trái; nằm trong (−180, 180].
static func signed_angle_deg(forward: Vector3, to_target: Vector3) -> float:
	var f := Vector3(forward.x, 0.0, forward.z)
	var t := Vector3(to_target.x, 0.0, to_target.z)
	if f.length_squared() == 0.0 or t.length_squared() == 0.0:
		return 0.0
	var deg: float = rad_to_deg(f.signed_angle_to(t, Vector3.UP))
	return 180.0 if deg <= -180.0 + 1e-9 else deg
