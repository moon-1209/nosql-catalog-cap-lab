extends GutTest

const DET: String = '{"x1":0.41,"y1":0.2,"x2":0.58,"y2":0.86,"conf":0.87}'

var client: VisionClient


func before_each() -> void:
	client = VisionClient.new()
	client.set_process(false)  # không kết nối thật trong unit test
	add_child_autofree(client)
	watch_signals(client)


func _msg(frame_id: int, dets: String = "[]") -> String:
	return '{"type":"detections","frame_id":%d,"infer_ms":20,"detections":%s}' % [frame_id, dets]


# --- parse_message ---

func test_parse_valid_empty() -> void:
	var r: Dictionary = VisionClient.parse_message(_msg(5))
	assert_true(r["ok"])
	assert_eq(r["frame_id"], 5)
	assert_eq(r["dets"], [])
	assert_almost_eq(r["infer_ms"], 20.0, 1e-6)


func test_parse_valid_with_detection() -> void:
	var r: Dictionary = VisionClient.parse_message(_msg(3, "[" + DET + "]"))
	assert_true(r["ok"])
	assert_eq(r["dets"].size(), 1)
	assert_almost_eq(r["dets"][0]["conf"], 0.87, 1e-6)
	assert_almost_eq(r["dets"][0]["x2"], 0.58, 1e-6)


func test_parse_example_detections_string() -> void:
	var r: Dictionary = VisionClient.parse_message('{"detections":"abc"}')
	assert_false(r["ok"])
	assert_ne(r["error"], "")


func test_parse_invalid_json() -> void:
	for text: String in ["abc", "", "[1,2]", "42"]:
		var r: Dictionary = VisionClient.parse_message(text)
		assert_false(r["ok"], text)
		assert_eq(r["error"], "invalid json")


func test_parse_missing_fields() -> void:
	assert_eq(VisionClient.parse_message('{"type":"detections","infer_ms":1,"detections":[]}')["error"], "missing field: frame_id")
	assert_eq(VisionClient.parse_message('{"type":"detections","frame_id":1,"detections":[]}')["error"], "missing field: infer_ms")
	assert_eq(VisionClient.parse_message('{"type":"detections","frame_id":1,"infer_ms":1}')["error"], "missing field: detections")


func test_parse_wrong_types() -> void:
	assert_false(VisionClient.parse_message('{"type":"detections","frame_id":"1","infer_ms":1,"detections":[]}')["ok"])
	assert_false(VisionClient.parse_message('{"type":"detections","frame_id":1.5,"infer_ms":1,"detections":[]}')["ok"])
	assert_false(VisionClient.parse_message('{"type":"detections","frame_id":-1,"infer_ms":1,"detections":[]}')["ok"])
	assert_false(VisionClient.parse_message('{"type":"detections","frame_id":1,"infer_ms":"x","detections":[]}')["ok"])
	assert_false(VisionClient.parse_message('{"type":"detections","frame_id":1,"infer_ms":1,"detections":{}}')["ok"])
	assert_false(VisionClient.parse_message('{"type":"frame","frame_id":1}')["ok"])


func test_parse_error_type() -> void:
	var r: Dictionary = VisionClient.parse_message('{"type":"error","frame_id":12,"message":"invalid jpeg"}')
	assert_false(r["ok"])
	assert_string_contains(r["error"], "invalid jpeg")


func test_parse_drops_bad_detections_individually() -> void:
	var bad: Array[String] = [
		'{"x1":0.1,"y1":0.2,"x2":0.5,"y2":0.9}',                  # thiếu conf
		'{"x1":"0.1","y1":0.2,"x2":0.5,"y2":0.9,"conf":0.8}',     # sai kiểu
		'{"x1":-0.1,"y1":0.2,"x2":0.5,"y2":0.9,"conf":0.8}',      # ngoài [0,1]
		'{"x1":0.1,"y1":0.2,"x2":1.2,"y2":0.9,"conf":0.8}',       # ngoài [0,1]
		'{"x1":0.6,"y1":0.2,"x2":0.5,"y2":0.9,"conf":0.8}',       # x1 > x2
		'{"x1":0.1,"y1":0.9,"x2":0.5,"y2":0.9,"conf":0.8}',       # y1 == y2
		'{"x1":0.1,"y1":0.2,"x2":0.5,"y2":0.9,"conf":1.5}',       # conf ngoài [0,1]
		'"abc"',
	]
	var r: Dictionary = VisionClient.parse_message(_msg(1, "[" + ",".join(bad) + "," + DET + "]"))
	assert_true(r["ok"])
	assert_eq(r["dets"].size(), 1, "chỉ giữ detection hợp lệ")


# --- bỏ frame cũ / trễ ---

func test_is_fresh() -> void:
	assert_true(VisionClient.is_fresh(5, 4, 1000, 1200))
	assert_false(VisionClient.is_fresh(4, 4, 1000, 1200), "bằng frame gần nhất")
	assert_false(VisionClient.is_fresh(3, 4, 1000, 1200), "cũ hơn")
	assert_false(VisionClient.is_fresh(5, 4, 1000, 1000 + Config.STALE_MS + 1), "trễ")
	assert_true(VisionClient.is_fresh(5, 4, 1000, 1000 + Config.STALE_MS), "đúng ngưỡng")
	assert_false(VisionClient.is_fresh(5, 4, -1, 1200), "chưa từng gửi")


func test_out_of_order_frame_dropped() -> void:
	client.record_sent(6, 1000)
	client.record_sent(7, 1100)
	client.handle_message(_msg(7), 1200)
	client.handle_message(_msg(6), 1210)
	assert_signal_emit_count(client, "detections_received", 1)
	assert_signal_emitted_with_parameters(client, "detections_received", [7, [], 20.0])


func test_stale_result_dropped() -> void:
	client.record_sent(1, 1000)
	client.handle_message(_msg(1), 1000 + Config.STALE_MS + 50)
	assert_signal_not_emitted(client, "detections_received")


func test_unknown_frame_dropped() -> void:
	client.handle_message(_msg(99), 1000)
	assert_signal_not_emitted(client, "detections_received")


func test_invalid_and_error_messages_do_not_crash() -> void:
	client.handle_message('{"detections":"abc"}', 1000)
	client.handle_message('{"type":"error","frame_id":1,"message":"invalid jpeg"}', 1000)
	client.handle_message("not json", 1000)
	assert_signal_not_emitted(client, "detections_received")


func test_sent_at_cleaned_up() -> void:
	for i: int in 10:
		client.record_sent(i, 1000 + i * 200)
	client.handle_message(_msg(9), 2850)
	assert_eq(client.pending_count(), 0, "đã dọn các frame ≤ 9")
	client.record_sent(10, 3000)
	client.record_sent(11, 3100)
	client._drop_expired(3000 + Config.STALE_MS + 1)
	assert_eq(client.pending_count(), 1, "frame 10 quá hạn bị dọn, frame 11 còn")
