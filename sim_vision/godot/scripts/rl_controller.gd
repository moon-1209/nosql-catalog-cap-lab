class_name RLController
extends Controller
## Bộ điều khiển RL (kế thừa Controller để giữ nguyên giao diện `step` tương thích với Main).
## Hỗ trợ:
## 1) Nhận lệnh trực tiếp từ mạng chính sách PPO qua `set_rl_action(a_v, a_omega)`
## 2) Hoạt động độc lập với bộ điều hướng pha nhiệm vụ (`SEARCH`, `APPROACH`, `GUIDE_ESCORT`, `CALL_STAFF`)
##    kết hợp tránh vật cản bằng LiDAR 17 tia khi chạy suy luận nội bộ.

const RLEnvBridgeRef = preload("res://scripts/rl_env_bridge.gd")

var has_external_action: bool = false
var external_v: float = 0.0
var external_omega: float = 0.0
var external_state: int = Config.RobotState.SEARCH


## Nạp hành động đã chuẩn hóa [-1, 1]^2 từ mô hình PPO (a_v, a_omega) sang (v, omega) thực tế.
static func decode_action(a_v: float, a_omega: float) -> Vector2:
	var v: float = clampf((a_v + 1.0) * 0.5 * Config.V_MAX, 0.0, Config.V_MAX)
	var omega: float = clampf(a_omega * Config.OMEGA_MAX, -Config.OMEGA_MAX, Config.OMEGA_MAX)
	return Vector2(v, omega)


func set_rl_action(a_v: float, a_omega: float, next_state: int = Config.RobotState.APPROACH) -> void:
	var cmd: Vector2 = RLController.decode_action(a_v, a_omega)
	external_v = cmd.x
	external_omega = cmd.y
	external_state = next_state
	has_external_action = true


func clear_rl_action() -> void:
	has_external_action = false


## Tính lệnh điều hướng tới điểm đích `goal_pos` kết hợp phản xạ tránh vật cản từ 17 tia LiDAR
## (dùng cho dẫn đường GUIDE_ESCORT / CALL_STAFF hoặc khi chạy chính sách lai).
## Tính điểm trung gian (doorway / corridor sub-goal) khi robot và đích ở khác phòng.
# Cửa & vách ngăn từng tầng (khớp _derive_doors() đọc src/training/hospital_layout.json; tầng 2 ở X + 50 m, tầng 3 ở X + 100 m)
const DOORS: Dictionary = {
	"1_north": [[-8.0, 0.0, 8.0], [-4.0, 4.0]],
	"1_south": [[-9.0, 0.0, 9.0], [-6.0, 6.0]],
	"2_north": [[41.65, 50.0, 58.35], [46.0, 54.0]],
	"2_south": [[41.925, 50.0, 57.5], [45.0, 55.0]],
	"3_north": [[91.65, 100.0, 108.35], [96.0, 104.0]],
	"3_south": [[91.925, 100.0, 107.5], [95.0, 105.0]],
}
const ELEVATOR_POSITIONS: Dictionary = {1: Vector3(9.0, 0.0, 5.2), 2: Vector3(59.0, 0.0, 4.6), 3: Vector3(109.0, 0.0, 4.6)}


static func floor_of(x: float) -> int:
	if x >= 75.0:
		return 3
	elif x >= 25.0:
		return 2
	return 1


## Cửa của cột phòng chứa x (side: "north" = phòng z < -2, "south" = phòng z > +2).
static func door_x(x: float, side: String) -> float:
	var entry: Array = DOORS["%d_%s" % [floor_of(x), side]]
	var idx: int = 0
	for d: float in entry[1]:
		if d < x:
			idx += 1
	return float(entry[0][idx])


## Tính điểm trung gian (cửa phòng / tim hành lang / thang máy) khi robot và đích ở khác phòng hoặc khác tầng.
## Khớp HospitalShiftEnv._route_through_corridor_goal (src/training/hospital_env.py).
static func route_through_corridor_goal(robot_pos: Vector3, final_goal: Vector3) -> Vector3:
	var rx: float = robot_pos.x
	var rz: float = robot_pos.z
	var gx: float = final_goal.x
	var gz: float = final_goal.z
	if floor_of(gx) != floor_of(rx):
		var elev: Vector3 = ELEVATOR_POSITIONS[floor_of(rx)]
		gx = elev.x
		gz = elev.z

	# Robot đang trong phòng phía Bắc (Z < -2.1) và đích ở ngoài phòng đó
	if rz < -2.1 and (gz > -1.8 or door_x(gx, "north") != door_x(rx, "north")):
		var dx: float = door_x(rx, "north")
		if absf(rx - dx) > 0.6 or rz < -1.8:
			return Vector3(dx, final_goal.y, -1.2)

	# Robot đang trong phòng phía Nam (Z > 2.1) và đích ở ngoài phòng đó
	if rz > 2.1 and (gz < 1.8 or door_x(gx, "south") != door_x(rx, "south")):
		var dx: float = door_x(rx, "south")
		if absf(rx - dx) > 0.6 or rz > 1.8:
			return Vector3(dx, final_goal.y, 1.2)

	# Robot đang trong hành lang và đích ở phòng phía Bắc: đi theo tim hành lang (z = 0) tới cửa
	if rz >= -2.1 and rz <= 2.1 and gz < -2.2:
		var dx: float = door_x(gx, "north")
		if absf(rx - dx) > 0.8:
			return Vector3(dx, final_goal.y, 0.0)
		if rz > -2.1:
			return Vector3(dx, final_goal.y, -2.6)

	# Robot đang trong hành lang và đích ở phòng phía Nam
	if rz >= -2.1 and rz <= 2.1 and gz > 2.2:
		var dx: float = door_x(gx, "south")
		if absf(rx - dx) > 0.8:
			return Vector3(dx, final_goal.y, 0.0)
		if rz < 2.1:
			return Vector3(dx, final_goal.y, 2.6)

	return Vector3(gx, final_goal.y, gz)


static func step_towards_goal_with_lidar(
	robot_pos: Vector3,
	robot_yaw: float,
	goal_pos: Vector3,
	lidar: PackedFloat32Array,
	d_tether: float = 0.0,
	is_escorting: bool = false
) -> Vector2:
	var active_goal: Vector3 = route_through_corridor_goal(robot_pos, goal_pos)
	var dist: float = Human.flat_distance(robot_pos, active_goal)
	var final_dist: float = Human.flat_distance(robot_pos, goal_pos)
	if final_dist <= RLEnvBridge.GOAL_ARRIVE_ROBOT_M:
		return Vector2.ZERO
	if is_escorting and d_tether > RLEnvBridge.TETHER_MAX_M:
		# Đợi bệnh nhân cao tuổi theo kịp
		return Vector2.ZERO

	var fwd := Vector3(-sin(robot_yaw), 0.0, -cos(robot_yaw))
	var to_goal := Vector3(active_goal.x - robot_pos.x, 0.0, active_goal.z - robot_pos.z)
	var angle_rad: float = deg_to_rad(RunLogger.signed_angle_deg(fwd, to_goal))

	# Đẩy góc lái tránh tường/vật cản từ nửa trái và nửa phải của LiDAR 17 tia
	var repel_turn: float = 0.0
	var speed_factor: float = 1.0
	if lidar.size() >= Robot.LIDAR_NUM_RAYS:
		var mid: int = Robot.LIDAR_NUM_RAYS / 2
		var left_clear: float = 0.0
		var right_clear: float = 0.0
		for i: int in range(0, mid):
			left_clear += lidar[i]
		for i: int in range(mid + 1, Robot.LIDAR_NUM_RAYS):
			right_clear += lidar[i]
		var center_min: float = minf(lidar[mid], minf(lidar[mid - 1], lidar[mid + 1]))
		if center_min < 0.65:
			var turn_strength: float = clampf((0.65 - center_min) / 0.5, 0.4, 1.2)
			repel_turn = turn_strength if left_clear >= right_clear else -turn_strength
			speed_factor = clampf(center_min / 0.65, 0.35, 1.0)

	var omega: float = clampf(1.8 * angle_rad + repel_turn, -Config.OMEGA_MAX, Config.OMEGA_MAX)
	var max_v: float = (RLEnvBridge.ESCORT_WALK_SPEED if is_escorting else Config.V_MAX) * speed_factor
	var v: float = clampf(0.55 * dist, 0.0, max_v)
	if absf(angle_rad) > 0.65:
		v *= 0.25
	return Vector2(v, omega)


func step(state: int, dets: Array, time_since_seen_s: float) -> Dictionary:
	if has_external_action:
		var target_det: Dictionary = Controller.pick_target(dets) if not dets.is_empty() else {}
		return _cmd(external_state, external_v, external_omega, target_det)
	return super.step(state, dets, time_since_seen_s)
