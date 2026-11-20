class_name DialogueLogger
extends Node
## Log hội thoại (G16): logs/dialogue_<YYYYMMDD_HHMMSS>.csv, mỗi lượt một dòng, ghi và flush ngay.
## Khác RunLogger (G9): ô chứa dấu phẩy / ngoặc kép / xuống dòng được đặt trong ngoặc kép (hyp_text).

const COLUMNS: PackedStringArray = ["time_s", "utt_id", "clip_id", "speaker", "take", "distance_m", "snr_db",
		"noise", "effective_snr_db", "hyp_text", "intent_pred", "intent_conf", "stt_ms", "error",
		# G22
		"action", "target", "response_len", "tts_ms", "tts_cache_hit", "tts_error", "speak_duration_s"]
const FLOAT_COLUMNS: PackedStringArray = ["time_s", "distance_m", "snr_db", "effective_snr_db", "intent_conf",
		"stt_ms", "tts_ms", "speak_duration_s"]

var path: String = ""

var _file: FileAccess = null
var _error_reported: bool = false


func open(dir: String = "", prefix: String = "dialogue") -> bool:
	if dir == "":
		dir = ProjectSettings.globalize_path("res://").path_join("../logs").simplify_path()
	if not DirAccess.dir_exists_absolute(dir) and DirAccess.make_dir_recursive_absolute(dir) != OK:
		_report_error("cannot create directory %s" % dir)
		return false
	var stamp: String = Time.get_datetime_string_from_system(false, true).replace("-", "").replace(":", "").replace(" ", "_")
	path = dir.path_join("%s_%s.csv" % [prefix, stamp])
	_file = FileAccess.open(path, FileAccess.WRITE)
	if _file == null:
		_report_error("cannot open %s (%s)" % [path, error_string(FileAccess.get_open_error())])
		return false
	_file.store_line(",".join(COLUMNS))
	_file.flush()
	return true


func log_row(row: Dictionary) -> void:
	if _file == null:
		return
	_file.store_line(DialogueLogger.format_row(row))
	_file.flush()


func close() -> void:
	if _file != null:
		_file.close()
		_file = null


func is_open() -> bool:
	return _file != null


func _exit_tree() -> void:
	close()


func _report_error(msg: String) -> void:
	if not _error_reported:
		_error_reported = true
		push_error("DialogueLogger: " + msg)


static func format_row(row: Dictionary) -> String:
	var cells: PackedStringArray = []
	for col: String in COLUMNS:
		var v: Variant = row.get(col)
		if v == null:
			cells.append("")
		elif col in FLOAT_COLUMNS:
			cells.append("%.4f" % float(v))
		else:
			cells.append(DialogueLogger.csv_escape(str(v)))
	return ",".join(cells)


static func csv_escape(s: String) -> String:
	if s.contains(",") or s.contains("\"") or s.contains("\n") or s.contains("\r"):
		return "\"" + s.replace("\"", "\"\"") + "\""
	return s
