class_name BatchRun
extends Node
## Chạy nhiều lượt tự động (G10): seed 0..N−1, mỗi lượt tối đa MAX_SIM_S giây mô phỏng.
## Ghi logs/batch_summary.csv: seed, success, time_to_arrive_s, final_distance_m, collisions, frames, mean_infer_ms.
## Cần YOLO server (G2) đang chạy và cửa sổ có render (không chạy được với --headless: camera không có ảnh).
## Chạy: godot --path . res://tools/batch_run.tscn [-- --runs=10 --max-time=30]

const MainScene: PackedScene = preload("res://scenes/main.tscn")
const SUCCESS_MIN_M: float = 0.8
const SUCCESS_MAX_M: float = 1.5
const CONNECT_TIMEOUT_S: float = 15.0
const TOUCH_EPS: float = 0.02         # m, khe hở coi như chạm
const HEADER: String = "seed,success,time_to_arrive_s,final_distance_m,collisions,frames,mean_infer_ms"

var runs: int = 10
var max_sim_s: float = 30.0


func _ready() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--runs="):
			runs = int(arg.get_slice("=", 1))
		elif arg.begins_with("--max-time="):
			max_sim_s = float(arg.get_slice("=", 1))
	if DisplayServer.get_name() == "headless":
		push_error("batch_run: cần cửa sổ có render (camera robot không có ảnh khi --headless)")
		get_tree().quit(2)
		return
	_run_all()


func _run_all() -> void:
	var logs_dir: String = ProjectSettings.globalize_path("res://").path_join("../logs").simplify_path()
	DirAccess.make_dir_recursive_absolute(logs_dir)
	var lines: PackedStringArray = [HEADER]
	var successes: int = 0
	for s: int in runs:
		var r: Dictionary = await _run_episode(s)
		if r.is_empty():
			push_error("batch_run: cannot connect to YOLO server at %s" % Config.WS_URL)
			get_tree().quit(1)
			return
		lines.append(BatchRun.format_summary_row(r))
		successes += 1 if r["success"] else 0
		print("seed=%d success=%s t=%s final=%.2f m collisions=%d frames=%d infer=%.1f ms" % [
				s, r["success"], r["time_to_arrive_s"], r["final_distance_m"], r["collisions"], r["frames"], r["mean_infer_ms"]])
	var path: String = logs_dir.path_join("batch_summary.csv")
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("batch_run: cannot write %s" % path)
	else:
		f.store_string("\n".join(lines) + "\n")
		f.close()
	print("success %d/%d ➔ %s" % [successes, runs, path])
	get_tree().quit(0)


## Một lượt; trả {} nếu không kết nối được server.
func _run_episode(episode_seed: int) -> Dictionary:
	var main: Main = MainScene.instantiate()
	main.seed = episode_seed
	add_child(main)
	var waited: float = 0.0
	while not main.vision.is_server_connected():
		waited += await _physics_step()
		if waited > CONNECT_TIMEOUT_S:
			main.queue_free()
			return {}
	# Robot đứng yên khi chưa kết nối ➔ tính giờ từ lúc kết nối; vị trí giống main.tscn cùng seed.
	var stats := {"frames": 0, "infer_sum": 0.0}
	main.cycle_completed.connect(func(info: Dictionary) -> void:
		stats["frames"] += 1
		stats["infer_sum"] += float(info["infer_ms"]))
	var t: float = 0.0
	var collisions: int = 0
	var touching: bool = false
	var arrive_t: Variant = null
	while t < max_sim_s:
		t += await _physics_step()
		var hit: bool = BatchRun.touches(main.robot, main.human)
		if hit and not touching:
			collisions += 1
		touching = hit
		if BatchRun.is_success(main.state, main.human_distance()):
			arrive_t = t
			break
	var result := {
		"seed": episode_seed, "success": arrive_t != null, "time_to_arrive_s": arrive_t,
		"final_distance_m": main.human_distance(), "collisions": collisions, "frames": stats["frames"],
		"mean_infer_ms": stats["infer_sum"] / stats["frames"] if stats["frames"] > 0 else 0.0,
	}
	main.queue_free()
	await get_tree().process_frame
	return result


func _physics_step() -> float:
	await get_tree().physics_frame
	return get_physics_process_delta_time()


## Thành công: ARRIVED và khoảng cách thật trong [SUCCESS_MIN_M, SUCCESS_MAX_M].
static func is_success(state: int, distance_m: float) -> bool:
	return state == Config.RobotState.ARRIVED and distance_m >= SUCCESS_MIN_M and distance_m <= SUCCESS_MAX_M


## Robot chạm người: có va chạm trượt với người, hoặc hai capsule/trụ cách nhau ≤ TOUCH_EPS.
static func touches(robot: Robot, human: Human) -> bool:
	for i: int in robot.get_slide_collision_count():
		if robot.get_slide_collision(i).get_collider() == human:
			return true
	var r_robot: float = ((robot.get_node("Collision") as CollisionShape3D).shape as CylinderShape3D).radius
	var r_human: float = ((human.get_node("Collision") as CollisionShape3D).shape as CapsuleShape3D).radius
	return Human.flat_distance(robot.global_position, human.global_position) <= r_robot + r_human + TOUCH_EPS


static func format_summary_row(r: Dictionary) -> String:
	var t: Variant = r["time_to_arrive_s"]
	return "%d,%s,%s,%.4f,%d,%d,%.4f" % [r["seed"], "true" if r["success"] else "false",
			"" if t == null else "%.4f" % float(t), r["final_distance_m"], r["collisions"], r["frames"], r["mean_infer_ms"]]
