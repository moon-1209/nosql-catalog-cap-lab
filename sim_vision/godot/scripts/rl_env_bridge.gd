class_name RLEnvBridge
extends Node
## Cầu nối môi trường RL cho Robot bệnh viện (Phase 1 Single-Agent, sẵn sàng mở rộng Multi-Agent).
## Quản lý ca trực liên tục 180s, định tuyến thông minh Tầng 1 / Thang máy / Nhân viên y tế,
## cơ chế dẫn đường bệnh nhân cao tuổi (tether <= 2.5m), vector quan sát 31 chiều và hàm thưởng R_team.

enum TaskPhase {
	SEARCH_PATIENT = 0,
	APPROACH_PATIENT = 1,
	GUIDE_ESCORT = 2,
	CALL_STAFF = 3,
}

const OBS_DIM: int = 31
const SHIFT_DURATION_S: float = 180.0
const ESCORT_WALK_SPEED: float = 0.48
const TETHER_IDEAL_MIN_M: float = 0.9
const TETHER_IDEAL_MAX_M: float = 2.2
const TETHER_MAX_M: float = 2.5
# Bệnh nhân đi theo dấu robot (khớp ESCORT_* trong src/training/hospital_env.py)
const ESCORT_STOP_DIST_M: float = 0.9
const ESCORT_CRUMB_SPACING_M: float = 0.25
const ESCORT_CRUMB_REACH_M: float = 0.45
const ESCORT_TRAIL_JUMP_M: float = 5.0
const ESCORT_TRAIL_MAX: int = 400
const GOAL_ARRIVE_ROBOT_M: float = 1.4     # = hospital_env.GOAL_ARRIVE_ROBOT_M
const GOAL_ARRIVE_PATIENT_M: float = 2.5   # = hospital_env.GOAL_ARRIVE_PATIENT_M
const STAFF_ARRIVE_M: float = 1.5

const REWARD_ANSWER: float = 10.0
const REWARD_CALL_STAFF: float = 20.0
const REWARD_GUIDE_ARRIVED: float = 30.0
const K_PROGRESS: float = 1.2
const PENALTY_STEP: float = -0.005
const PENALTY_TETHER_STRETCH: float = -0.08
const BONUS_TETHER_GOOD: float = 0.02
const PENALTY_COLLISION: float = -5.0
const SAFE_LIDAR_MARGIN_M: float = 0.45
const COLLISION_LIDAR_M: float = 0.40       # = hospital_env.COLLISION_LIDAR_M

const FLOOR1_DIRECT_KEYS: Array[String] = [
	"101", "cap_cuu", "110", "112", "nha_thuoc", "tiep_don", "ghe_cho", "thang_may", "nha_ve_sinh", "hanh_lang"
]
const FLOOR1_LOBBY_ALIASES: Array[String] = [
	"uu_tien", "bhyt", "thu_ngan", "xe_lan", "105", "115", "can_tin", "gui_xe"
]
const FLOOR1_CLINIC_ALIASES: Array[String] = [
	"120", "125", "130", "135", "140"
]
const FLOOR2_DIRECT_KEYS: Array[String] = [
	"201", "204", "205", "210", "220", "sanh_t2", "wc_t2", "thang_may_t2", "hanh_lang_t2"
]
const FLOOR3_DIRECT_KEYS: Array[String] = [
	"301", "302", "303", "315", "sanh_t3", "wc_t3", "thang_may_t3", "hanh_lang_t3"
]
## Khoa của NLU (dept_<slug>, sim_vision/python/voice/hospital_map.json) ➔ số phòng
const NLU_DEPARTMENT_ROOMS: Dictionary = {
	"dept_tim_mach": "301", "dept_tieu_hoa": "205", "dept_tai_mui_hong": "210", "dept_co_xuong_khop": "315",
	"dept_nhi": "401", "dept_san": "410", "dept_cap_cuu": "101", "dept_noi_tong_quat": "120",
	"dept_ho_hap": "320", "dept_than_kinh": "330", "dept_da_lieu": "220", "dept_mat": "230", "dept_rang_ham_mat": "240",
}

var task_phase: int = TaskPhase.SEARCH_PATIENT
var active_action: String = ""
var active_target_key: String = ""
var active_goal_pos: Vector3 = Vector3.ZERO
var goal_position: Vector3 = Vector3.ZERO
var goal_key: String = ""
var final_target_key: String = ""
var patients_helped: int = 0
var cumulative_team_reward: float = 0.0
var prev_goal_dist: float = -1.0
var escort_trail: Array[Vector3] = []  # dấu robot cho bệnh nhân đi theo khi GUIDE_ESCORT

var robot_ref: Robot = null
var room_ref: Room = null


func setup(p_robot: Robot, p_room: Room) -> void:
	robot_ref = p_robot
	room_ref = p_room


func begin_post_dialogue_task(act: String, target_str: String, floor_num: int, _patient: CharacterBody3D = null) -> void:
	final_target_key = resolve_final_target(act, target_str, floor_num)
	var current_floor: int = Room.get_floor(robot_ref.global_position) if robot_ref != null else 1
	goal_key = resolve_destination_key(act, target_str, floor_num, current_floor)
	if act == "guide":
		task_phase = TaskPhase.GUIDE_ESCORT
		escort_trail.clear()
		if robot_ref != null:
			escort_trail.append(robot_ref.global_position)
		if room_ref != null:
			goal_position = room_ref.get_room_waypoint(goal_key)
	elif act in ["call_staff", "emergency"]:
		task_phase = TaskPhase.CALL_STAFF
		var from_pos: Vector3 = robot_ref.global_position if robot_ref != null else Vector3.ZERO
		goal_position = find_nearest_staff_position(room_ref, from_pos)


## Phân giải phòng đích cuối cùng của bệnh nhân
## Đích từ NLU ("room_205", "dept_tim_mach") ➔ {"key": số phòng, "floor": tầng = chữ số đầu của số phòng}.
static func normalize_nlu_target(target_id: String, dest_floor: int = 1) -> Dictionary:
	var t: String = target_id.strip_edges().to_lower()
	if NLU_DEPARTMENT_ROOMS.has(t):
		t = NLU_DEPARTMENT_ROOMS[t]
	elif t.begins_with("room_"):
		t = t.substr(5)
	elif t.begins_with("dept_"):
		var stripped: String = t.substr(5)
		if NLU_DEPARTMENT_ROOMS.has(stripped):
			t = NLU_DEPARTMENT_ROOMS[stripped]
		else:
			t = stripped
	elif t.begins_with("facility_"):
		t = t.substr(9)
	if NLU_DEPARTMENT_ROOMS.has(t):
		t = NLU_DEPARTMENT_ROOMS[t]
	var fl: int = dest_floor
	if t.length() == 3 and t.is_valid_int():
		fl = maxi(dest_floor, int(t.substr(0, 1)))
	return {"key": t, "floor": fl}


static func resolve_final_target(action_name: String, target_id: String, dest_floor: int = 1) -> String:
	if action_name in ["call_staff", "emergency"]:
		return "staff"
	if action_name != "guide":
		return ""
	var nlu: Dictionary = RLEnvBridge.normalize_nlu_target(target_id, dest_floor)
	var t: String = nlu["key"]
	dest_floor = nlu["floor"]
	if t in FLOOR1_LOBBY_ALIASES:
		return "tiep_don"
	if t in FLOOR3_DIRECT_KEYS:
		return t
	if t.begins_with("3"):
		return t if t in ["301", "302", "303", "315"] else "301"
	if t in FLOOR2_DIRECT_KEYS:
		return t
	if t.begins_with("2"):
		return "205"
	if t in FLOOR1_DIRECT_KEYS:
		return t
	if t in FLOOR1_CLINIC_ALIASES:
		return "112"
	if dest_floor >= 3:
		return "301"
	if dest_floor >= 2:
		return "sanh_t2"
	if t != "":
		return "tiep_don"
	return "tiep_don"


## Ánh xạ đích trung gian theo tầng:
## - Cùng tầng: dẫn trực tiếp tới phòng đích
## - Khác tầng: dẫn tới trạm Thang máy của tầng hiện tại
static func resolve_destination_key(action_name: String, target_id: String, dest_floor: int = 1, current_floor: int = 1) -> String:
	if action_name in ["call_staff", "emergency"]:
		return "staff"
	if action_name != "guide":
		return ""
	var final_key: String = resolve_final_target(action_name, target_id, dest_floor)
	var nlu: Dictionary = RLEnvBridge.normalize_nlu_target(target_id, dest_floor)
	var target_floor: int = 1
	if final_key in FLOOR3_DIRECT_KEYS or nlu["floor"] >= 3 or final_key.begins_with("3"):
		target_floor = 3
	elif final_key in FLOOR2_DIRECT_KEYS or nlu["floor"] == 2 or final_key.begins_with("2"):
		target_floor = 2

	if current_floor == target_floor:
		return final_key
	else:
		return "thang_may" if current_floor == 1 else ("thang_may_t2" if current_floor == 2 else "thang_may_t3")


## Tìm vị trí Nhân viên y tế (MedicalStaffNurse hoặc MedicalStaffDoctor) gần robot nhất.
static func find_nearest_staff_position(room: Room, from_pos: Vector3) -> Vector3:
	if room == null:
		return Vector3(-1.9, 0.0, 7.45)
	var furn: Node = room.get_node_or_null(^"Furniture")
	var best_pos := Vector3(-1.9, 0.0, 7.45)
	var best_dist: float = INF
	if furn != null:
		for child: Node in furn.get_children():
			if child is HospitalNpc:
				var npc := child as HospitalNpc
				if npc.staff_role in ["nurse", "doctor"]:
					var d: float = Human.flat_distance(from_pos, npc.global_position)
					if d < best_dist:
						best_dist = d
						best_pos = npc.global_position
	return best_pos


## Tạo vector quan sát chuẩn hóa 31 chiều cho tác tử RL.
static func build_observation(
	robot_pos: Vector3,
	robot_yaw: float,
	robot_cmd: Vector2,
	lidar_readings: PackedFloat32Array,
	det: Dictionary,
	phase: int,
	goal_pos: Vector3,
	patient_pos: Vector3
) -> PackedFloat32Array:
	var obs := PackedFloat32Array()
	obs.resize(OBS_DIM)

	# 0..16: 17 tia LiDAR [0, 1]
	for i: int in Robot.LIDAR_NUM_RAYS:
		obs[i] = lidar_readings[i] if i < lidar_readings.size() else 1.0

	# 17..20: Đặc trưng nhận diện người từ YOLO [has_det, cx - 0.5, h, conf]
	if det.is_empty():
		obs[17] = 0.0
		obs[18] = 0.0
		obs[19] = 0.0
		obs[20] = 0.0
	else:
		var cx: float = (float(det.get("x1", 0.5)) + float(det.get("x2", 0.5))) * 0.5
		var h: float = float(det.get("y2", 0.0)) - float(det.get("y1", 0.0))
		var conf: float = float(det.get("conf", 0.0))
		obs[17] = 1.0
		obs[18] = clampf(cx - 0.5, -0.5, 0.5)
		obs[19] = clampf(h, 0.0, 1.0)
		obs[20] = clampf(conf, 0.0, 1.0)

	# 21..24: One-hot pha nhiệm vụ
	obs[21] = 1.0 if phase == TaskPhase.SEARCH_PATIENT else 0.0
	obs[22] = 1.0 if phase == TaskPhase.APPROACH_PATIENT else 0.0
	obs[23] = 1.0 if phase == TaskPhase.GUIDE_ESCORT else 0.0
	obs[24] = 1.0 if phase == TaskPhase.CALL_STAFF else 0.0

	# 25..27: Tọa độ cực tương đối tới đích (d_goal / 25, sin(theta), cos(theta)) trong hệ quy chiếu robot (-Z là phía trước)
	var d_goal: float = Human.flat_distance(robot_pos, goal_pos)
	var fwd := Vector3(-sin(robot_yaw), 0.0, -cos(robot_yaw))
	var to_goal := Vector3(goal_pos.x - robot_pos.x, 0.0, goal_pos.z - robot_pos.z)
	var angle_rad: float = 0.0
	if to_goal.length() > 1e-4:
		angle_rad = deg_to_rad(RunLogger.signed_angle_deg(fwd, to_goal))
	obs[25] = clampf(d_goal / 25.0, 0.0, 1.0)
	obs[26] = sin(angle_rad)
	obs[27] = cos(angle_rad)

	# 28..30: Khoảng cách dây dẫn bệnh nhân cao tuổi (tether) & vận tốc bản thân
	var d_tether: float = Human.flat_distance(robot_pos, patient_pos) if phase == TaskPhase.GUIDE_ESCORT else 0.0
	obs[28] = clampf(d_tether / 5.0, 0.0, 1.0)
	obs[29] = clampf(robot_cmd.x / Config.V_MAX, 0.0, 1.0)
	obs[30] = clampf(robot_cmd.y / Config.OMEGA_MAX, -1.0, 1.0)
	return obs


## Hàm thuần tính phần thưởng mỗi bước (Shared Team Reward R_team + Potential Shaping + Tether + Safety).
static func compute_step_reward(
	prev_dist: float,
	curr_dist: float,
	phase: int,
	d_tether: float,
	min_lidar_m: float,
	task_event: String = ""
) -> Dictionary:
	var r_team: float = 0.0
	if task_event == "answer":
		r_team = REWARD_ANSWER
	elif task_event in ["call_staff", "emergency"]:
		r_team = REWARD_CALL_STAFF
	elif task_event == "guide_completed":
		r_team = REWARD_GUIDE_ARRIVED

	var r_progress: float = 0.0
	if prev_dist >= 0.0 and curr_dist >= 0.0:
		var allow_progress: bool = not (phase == TaskPhase.GUIDE_ESCORT and d_tether > TETHER_MAX_M)
		if allow_progress:
			r_progress = clampf(K_PROGRESS * (prev_dist - curr_dist), -0.5, 0.5)

	var r_tether: float = 0.0
	if phase == TaskPhase.GUIDE_ESCORT:
		if d_tether >= TETHER_IDEAL_MIN_M and d_tether <= TETHER_IDEAL_MAX_M:
			r_tether = BONUS_TETHER_GOOD
		elif d_tether > TETHER_MAX_M:
			r_tether = PENALTY_TETHER_STRETCH

	var r_safety: float = PENALTY_STEP
	var collided: bool = false
	if min_lidar_m < COLLISION_LIDAR_M:
		r_safety += PENALTY_COLLISION
		collided = true
	elif min_lidar_m < SAFE_LIDAR_MARGIN_M:
		r_safety -= 0.25 * (1.0 - min_lidar_m / SAFE_LIDAR_MARGIN_M)

	var total: float = r_team + r_progress + r_tether + r_safety
	return {
		"total": total,
		"r_team": r_team,
		"r_progress": r_progress,
		"r_tether": r_tether,
		"r_safety": r_safety,
		"collided": collided,
	}


## Bệnh nhân đi theo sau robot trong pha GUIDE_ESCORT: lần lượt qua các dấu robot đã đi (cách nhau
## ESCORT_CRUMB_SPACING_M), không cắt góc xuyên khung cửa; dừng khi cách robot ESCORT_STOP_DIST_M.
## Di chuyển bằng move_and_slide nên va chạm tường / đồ đạc như người thật.
static func step_escorted_patient(patient: CharacterBody3D, robot_pos: Vector3, delta: float, trail: Array[Vector3] = []) -> void:
	if patient == null:
		return
	if not trail.is_empty() and Human.flat_distance(robot_pos, trail[-1]) > ESCORT_TRAIL_JUMP_M:
		trail.clear()  # robot vừa đi thang máy
	if trail.is_empty() or Human.flat_distance(robot_pos, trail[-1]) >= ESCORT_CRUMB_SPACING_M:
		trail.append(robot_pos)
		if trail.size() > ESCORT_TRAIL_MAX:
			trail.pop_front()

	var d_robot: float = Human.flat_distance(patient.global_position, robot_pos)
	if d_robot <= ESCORT_STOP_DIST_M:
		patient.escort_stop()
		return
	while trail.size() > 1:
		var d0: float = Human.flat_distance(patient.global_position, trail[0])
		var d1: float = Human.flat_distance(patient.global_position, trail[1])
		if d0 <= ESCORT_CRUMB_REACH_M or d1 <= d0:
			trail.pop_front()
		else:
			break
	var step: float = minf(ESCORT_WALK_SPEED * delta, d_robot - ESCORT_STOP_DIST_M)
	patient.escort_step_towards(trail[0], step, delta)
