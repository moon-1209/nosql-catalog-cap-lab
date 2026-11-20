class_name Room
extends Node3D
## Bệnh viện tầng 1 kích thước 24 m × 18 m, trần 3.2 m, gốc tọa độ ở tâm sàn (0, 0, 0).
## Gồm 6 khu vực nối với Hành lang chính qua cửa trượt tự động (SlidingDoor):
##   - 101 / cap_cuu : Khoa Cấp Cứu (Tây Bắc)
##   - 110           : Phòng Xét Nghiệm Máu (Bắc)
##   - 112           : Phòng Khám Nội (Đông Bắc)
##   - nha_thuoc     : Nhà Thuốc (Tây Nam)
##   - tiep_don      : Sảnh Chính - Quầy Tiếp Đón & Khu Ghế Chờ (Nam)
##   - thang_may     : Khu Thang Máy & Nhà Vệ Sinh (Đông Nam)
##   - hanh_lang     : Hành Lang Chính Đông - Tây (Giữa)
## Tầng 2: Khoa Tiêu Hóa (205), Tai Mũi Họng (210), X-Quang (201/204), Da Liễu (220), Thang máy (offset X = +50.0m).
## Tầng 3: Khoa Tim Mạch (301), Siêu Âm Tim (302), Điện Tâm Đồ (303), Cơ Xương Khớp (315), Thang máy (offset X = +100.0m).

const SIZE_X: float = 24.0
const SIZE_Z: float = 18.0
const HEIGHT: float = 3.2
const MAX_TRIES: int = 100

## Vùng mặc định cho get_free_position() (Hành lang trung tâm + Sảnh chính thông nhau).
const DEFAULT_SPAWN_RECT := Rect2(Vector2(-5.6, -1.8), Vector2(11.2, 10.2))

const ROOMS: Dictionary = {
	"101": {
		"name": "Khoa cấp cứu",
		"rect": Rect2(Vector2(-12.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(-8.0, 0.0, -2.0),
		"waypoint": Vector3(-8.0, 0.0, -5.2),
	},
	"cap_cuu": {
		"name": "Khoa cấp cứu",
		"rect": Rect2(Vector2(-12.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(-8.0, 0.0, -2.0),
		"waypoint": Vector3(-8.0, 0.0, -5.2),
	},
	"110": {
		"name": "Phòng xét nghiệm máu",
		"rect": Rect2(Vector2(-4.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(0.0, 0.0, -2.0),
		"waypoint": Vector3(0.0, 0.0, -5.2),
	},
	"112": {
		"name": "Phòng khám nội",
		"rect": Rect2(Vector2(4.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(8.0, 0.0, -2.0),
		"waypoint": Vector3(8.0, 0.0, -5.2),
	},
	"nha_thuoc": {
		"name": "Nhà thuốc",
		"rect": Rect2(Vector2(-12.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(-9.0, 0.0, 2.0),
		"waypoint": Vector3(-9.0, 0.0, 5.2),
	},
	"tiep_don": {
		"name": "Sảnh chính - Quầy tiếp đón",
		"rect": Rect2(Vector2(-6.0, 2.0), Vector2(12.0, 7.0)),
		"door": Vector3(0.0, 0.0, 2.0),
		"waypoint": Vector3(0.0, 0.0, 5.2),
	},
	"ghe_cho": {
		"name": "Khu ghế chờ",
		"rect": Rect2(Vector2(-6.0, 2.0), Vector2(12.0, 7.0)),
		"door": Vector3(0.0, 0.0, 2.0),
		"waypoint": Vector3(-2.5, 0.0, 4.5),
	},
	"thu_ngan": {
		"name": "Quầy thu ngân",
		"rect": Rect2(Vector2(-6.0, 2.0), Vector2(12.0, 7.0)),
		"door": Vector3(0.0, 0.0, 2.0),
		"waypoint": Vector3(1.5, 0.0, 6.2),
	},
	"bhyt": {
		"name": "Quầy bảo hiểm y tế",
		"rect": Rect2(Vector2(-6.0, 2.0), Vector2(12.0, 7.0)),
		"door": Vector3(0.0, 0.0, 2.0),
		"waypoint": Vector3(-1.5, 0.0, 6.2),
	},
	"thang_may": {
		"name": "Thang máy & Nhà vệ sinh",
		"rect": Rect2(Vector2(6.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(9.0, 0.0, 2.0),
		"waypoint": Vector3(9.0, 0.0, 5.2),
	},
	"nha_ve_sinh": {
		"name": "Nhà vệ sinh",
		"rect": Rect2(Vector2(6.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(9.0, 0.0, 2.0),
		"waypoint": Vector3(9.5, 0.0, 6.5),
	},
	"hanh_lang": {
		"name": "Hành lang chính",
		"rect": Rect2(Vector2(-12.0, -2.0), Vector2(24.0, 4.0)),
		"door": Vector3(0.0, 0.0, 0.0),
		"waypoint": Vector3(0.0, 0.0, 0.0),
	},
	# Các phòng và khu vực Tầng 2 (tâm phòng offset X = +50.0m)
	"201": {
		"name": "Phòng chẩn đoán hình ảnh (X-Quang / CT)",
		"rect": Rect2(Vector2(38.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(42.0, 0.0, -2.0),
		"waypoint": Vector3(42.0, 0.0, -5.2),
	},
	"204": {
		"name": "Phòng chẩn đoán hình ảnh (X-Quang / CT)",
		"rect": Rect2(Vector2(38.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(42.0, 0.0, -2.0),
		"waypoint": Vector3(42.0, 0.0, -5.2),
	},
	"205": {
		"name": "Khoa tiêu hóa",
		"rect": Rect2(Vector2(46.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(50.0, 0.0, -2.0),
		"waypoint": Vector3(50.0, 0.0, -5.2),
	},
	"210": {
		"name": "Phòng khám tai mũi họng",
		"rect": Rect2(Vector2(54.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(58.0, 0.0, -2.0),
		"waypoint": Vector3(58.0, 0.0, -5.2),
	},
	"220": {
		"name": "Khoa da liễu",
		"rect": Rect2(Vector2(38.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(41.0, 0.0, 2.0),
		"waypoint": Vector3(41.0, 0.0, 5.2),
	},
	"sanh_t2": {
		"name": "Sảnh chờ tầng 2",
		"rect": Rect2(Vector2(44.0, 2.0), Vector2(12.0, 7.0)),
		"door": Vector3(50.0, 0.0, 2.0),
		"waypoint": Vector3(50.0, 0.0, 5.2),
	},
	"wc_t2": {
		"name": "Nhà vệ sinh tầng 2",
		"rect": Rect2(Vector2(56.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(59.0, 0.0, 2.0),
		"waypoint": Vector3(59.5, 0.0, 6.5),
	},
	"thang_may_t2": {
		"name": "Thang máy tầng 2",
		"rect": Rect2(Vector2(56.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(59.0, 0.0, 2.0),
		"waypoint": Vector3(59.0, 0.0, 4.6),
	},
	"hanh_lang_t2": {
		"name": "Hành lang tầng 2",
		"rect": Rect2(Vector2(38.0, -2.0), Vector2(24.0, 4.0)),
		"door": Vector3(50.0, 0.0, 0.0),
		"waypoint": Vector3(50.0, 0.0, 0.0),
	},
	# Các phòng và khu vực Tầng 3 (tâm phòng offset X = +100.0m)
	"301": {
		"name": "Khoa tim mạch",
		"rect": Rect2(Vector2(88.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(92.0, 0.0, -2.0),
		"waypoint": Vector3(92.0, 0.0, -5.2),
	},
	"dept_tim_mach": {
		"name": "Khoa tim mạch",
		"rect": Rect2(Vector2(88.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(92.0, 0.0, -2.0),
		"waypoint": Vector3(92.0, 0.0, -5.2),
	},
	"302": {
		"name": "Phòng siêu âm tim",
		"rect": Rect2(Vector2(96.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(100.0, 0.0, -2.0),
		"waypoint": Vector3(100.0, 0.0, -5.2),
	},
	"303": {
		"name": "Phòng điện tâm đồ (ECG)",
		"rect": Rect2(Vector2(104.0, -9.0), Vector2(8.0, 7.0)),
		"door": Vector3(108.0, 0.0, -2.0),
		"waypoint": Vector3(108.0, 0.0, -5.2),
	},
	"315": {
		"name": "Khoa cơ xương khớp",
		"rect": Rect2(Vector2(88.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(91.0, 0.0, 2.0),
		"waypoint": Vector3(91.0, 0.0, 5.2),
	},
	"dept_co_xuong_khop": {
		"name": "Khoa cơ xương khớp",
		"rect": Rect2(Vector2(88.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(91.0, 0.0, 2.0),
		"waypoint": Vector3(91.0, 0.0, 5.2),
	},
	"sanh_t3": {
		"name": "Sảnh chờ tầng 3",
		"rect": Rect2(Vector2(94.0, 2.0), Vector2(12.0, 7.0)),
		"door": Vector3(100.0, 0.0, 2.0),
		"waypoint": Vector3(100.0, 0.0, 5.2),
	},
	"wc_t3": {
		"name": "Nhà vệ sinh tầng 3",
		"rect": Rect2(Vector2(106.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(109.0, 0.0, 2.0),
		"waypoint": Vector3(109.5, 0.0, 6.5),
	},
	"thang_may_t3": {
		"name": "Thang máy tầng 3",
		"rect": Rect2(Vector2(106.0, 2.0), Vector2(6.0, 7.0)),
		"door": Vector3(109.0, 0.0, 2.0),
		"waypoint": Vector3(109.0, 0.0, 4.6),
	},
	"hanh_lang_t3": {
		"name": "Hành lang tầng 3",
		"rect": Rect2(Vector2(88.0, -2.0), Vector2(24.0, 4.0)),
		"door": Vector3(100.0, 0.0, 0.0),
		"waypoint": Vector3(100.0, 0.0, 0.0),
	},
}

const CANONICAL_ROOM_KEYS: Array[String] = [
	"101", "110", "112", "nha_thuoc", "tiep_don", "thang_may", "hanh_lang",
	"201", "205", "210", "220", "sanh_t2", "wc_t2", "thang_may_t2", "hanh_lang_t2",
	"301", "302", "303", "315", "sanh_t3", "wc_t3", "thang_may_t3", "hanh_lang_t3"
]

const FLOOR2_SPAWN_RECT := Rect2(Vector2(44.4, -1.8), Vector2(11.2, 10.2))
const FLOOR3_SPAWN_RECT := Rect2(Vector2(94.4, -1.8), Vector2(11.2, 10.2))

## Vùng đặt bệnh nhân, khớp HospitalShiftEnv._sample_patient_spawn_solo (src/training/hospital_env.py):
## 60% hành lang, 40% sảnh chính; cách đồ vật/tường ≥ 0.65 m và NPC ≥ 0.8 m (hộp nở vuông như Python is_blocked).
const PATIENT_CORRIDOR_RECT := Rect2(Vector2(-10.0, -1.3), Vector2(20.0, 2.6))
const PATIENT_LOBBY_RECT := Rect2(Vector2(-3.2, 2.2), Vector2(6.4, 2.8))
const PATIENT_CORRIDOR_PROB: float = 0.6
const PATIENT_CLEARANCE_M: float = 0.65
const PATIENT_NPC_CLEARANCE_M: float = 0.8
const PATIENT_NPC_HALF_M: float = 0.25

@onready var _furniture: Node3D = $Furniture
@onready var _interior_walls: Node3D = get_node_or_null(^"InteriorWalls")
@onready var _ceiling: MeshInstance3D = get_node_or_null(^"Shell/Ceiling")
@onready var _floor2_node: Node3D = get_node_or_null(^"Floor2")
@onready var _floor3_node: Node3D = get_node_or_null(^"Floor3")
@onready var _robot_dock: Node3D = get_node_or_null(^"Entrance/RobotDock")


## Ẩn hoặc hiện trần nhà (hữu ích cho camera nhìn từ trên xuống TOP_DOWN kiểu RimWorld).
func set_ceiling_visible(v: bool) -> void:
	if _ceiling != null:
		_ceiling.visible = v
	if _floor2_node != null:
		var c2: MeshInstance3D = _floor2_node.get_node_or_null(^"Shell/Ceiling")
		if c2 != null:
			c2.visible = v
	if _floor3_node != null:
		var c3: MeshInstance3D = _floor3_node.get_node_or_null(^"Shell/Ceiling")
		if c3 != null:
			c3.visible = v


## Xác định tầng (1, 2 hoặc 3) dựa trên tọa độ X
static func get_floor(pos: Vector3) -> int:
	if pos.x >= 75.0:
		return 3
	elif pos.x >= 25.0:
		return 2
	return 1


## Xác định tầng của một mã phòng
static func get_room_floor(room_key: String) -> int:
	var k: String = room_key.strip_edges().to_lower()
	if k in ["301", "302", "303", "315", "sanh_t3", "wc_t3", "thang_may_t3", "hanh_lang_t3", "dept_tim_mach", "dept_co_xuong_khop"]:
		return 3
	elif k in ["201", "204", "205", "210", "220", "sanh_t2", "wc_t2", "thang_may_t2", "hanh_lang_t2", "dept_tieu_hoa", "dept_tai_mui_hong"]:
		return 2
	return 1


## Lấy node ElevatorStation của Tầng 1, Tầng 2 hoặc Tầng 3
func get_elevator_station(floor_num: int) -> ElevatorStation:
	if floor_num == 3:
		if _floor3_node != null:
			return _floor3_node.get_node_or_null(^"Floor3Elevator") as ElevatorStation
		return get_node_or_null(^"Floor3/Floor3Elevator") as ElevatorStation
	elif floor_num == 2:
		if _floor2_node != null:
			return _floor2_node.get_node_or_null(^"Floor2Elevator") as ElevatorStation
		return get_node_or_null(^"Floor2/Floor2Elevator") as ElevatorStation
	return get_node_or_null(^"Furniture/HospitalElevator") as ElevatorStation


## Điểm ngẫu nhiên trên sàn theo tầng
func get_free_position_on_floor(floor_num: int, min_clearance: float, rng: RandomNumberGenerator = null) -> Vector3:
	if floor_num == 3:
		return _sample_in_rect(FLOOR3_SPAWN_RECT, min_clearance, rng)
	elif floor_num == 2:
		return _sample_in_rect(FLOOR2_SPAWN_RECT, min_clearance, rng)
	return get_free_position(min_clearance, rng)


func is_ceiling_visible() -> bool:
	return _ceiling != null and _ceiling.visible


## Điểm ngẫu nhiên trên sàn (y = 0) trong Sảnh chính + Hành lang trung tâm,
## cách tường và mọi đồ vật ≥ `min_clearance`.
func get_free_position(min_clearance: float, rng: RandomNumberGenerator = null) -> Vector3:
	return _sample_in_rect(DEFAULT_SPAWN_RECT, min_clearance, rng)


## Trạm robot ngay trong cửa chính (đầu Tây hành lang tầng 1): {"position", "yaw"}; ca trực bắt đầu ở đây.
func get_robot_dock() -> Dictionary:
	if _robot_dock == null:
		return {"position": Vector3.ZERO, "yaw": 0.0}
	return {"position": Vector3(_robot_dock.global_position.x, 0.0, _robot_dock.global_position.z),
			"yaw": _robot_dock.global_rotation.y}


## Điểm đặt bệnh nhân ngẫu nhiên trên tầng `floor_num` (hành lang / sảnh chính, xem PATIENT_*).
func get_patient_spawn_position(floor_num: int, rng: RandomNumberGenerator) -> Vector3:
	var x_base: float = 100.0 if floor_num == 3 else (50.0 if floor_num == 2 else 0.0)
	var footprints: Array[Rect2] = get_obstacle_footprints()
	var npc_rects: Array[Rect2] = []
	for node: Node in find_children("*", "", true, false):
		if node is HospitalNpc:
			var c: Vector3 = (node as Node3D).global_position
			npc_rects.append(Rect2(c.x - PATIENT_NPC_HALF_M, c.z - PATIENT_NPC_HALF_M, 2.0 * PATIENT_NPC_HALF_M, 2.0 * PATIENT_NPC_HALF_M))
	for i: int in 250:
		var r: Rect2 = PATIENT_CORRIDOR_RECT if rng.randf() < PATIENT_CORRIDOR_PROB else PATIENT_LOBBY_RECT
		var p := Vector3(x_base + rng.randf_range(r.position.x, r.end.x), 0.0, rng.randf_range(r.position.y, r.end.y))
		if Room.is_clear_box(p, footprints, PATIENT_CLEARANCE_M) and Room.is_clear_box(p, npc_rects, PATIENT_NPC_CLEARANCE_M):
			return p
	return Vector3(x_base, 0.0, 4.0)


## Điểm ngẫu nhiên trên sàn (y = 0) nằm trong phòng `room_key`, cách tường phòng và đồ vật ≥ `min_clearance`.
func get_free_position_in_room(room_key: String, min_clearance: float, rng: RandomNumberGenerator = null) -> Vector3:
	if not ROOMS.has(room_key):
		push_error("Room.get_free_position_in_room: unknown room_key '%s'" % room_key)
		return Vector3.ZERO
	var r: Rect2 = ROOMS[room_key]["rect"]
	return _sample_in_rect(r, min_clearance, rng)


func _sample_in_rect(bounds: Rect2, min_clearance: float, rng: RandomNumberGenerator = null) -> Vector3:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	var x_min: float = bounds.position.x + min_clearance
	var x_max: float = bounds.end.x - min_clearance
	var z_min: float = bounds.position.y + min_clearance
	var z_max: float = bounds.end.y - min_clearance
	if x_min <= x_max and z_min <= z_max:
		var footprints: Array[Rect2] = get_obstacle_footprints()
		for i: int in MAX_TRIES:
			var p := Vector3(rng.randf_range(x_min, x_max), 0.0, rng.randf_range(z_min, z_max))
			if is_clear(p, footprints, min_clearance):
				return p
	push_error("Room.get_free_position: no free position for clearance %.2f" % min_clearance)
	return Vector3.ZERO


## Trả tọa độ đích (waypoint) cho RL / dẫn đường ứng với mã phòng hoặc cơ sở.
func get_room_waypoint(room_key: String) -> Vector3:
	if ROOMS.has(room_key):
		return ROOMS[room_key]["waypoint"]
	return Vector3.ZERO


## Trả mã phòng chứa điểm `pos` (chiếu xuống mặt phẳng XZ). Không thuộc phòng nào ➔ "".
func get_room_at(pos: Vector3) -> String:
	var p := Vector2(pos.x, pos.z)
	for key: String in CANONICAL_ROOM_KEYS:
		var r: Rect2 = ROOMS[key]["rect"]
		if r.has_point(p):
			return key
	return ""


## Hình chiếu XZ (Rect2) của collision từng đồ vật trong node `Furniture`.
func get_furniture_footprints() -> Array[Rect2]:
	return _collect_footprints(_furniture)


## Hình chiếu XZ (Rect2) của các tường ngăn nội thất trong node `InteriorWalls`.
func get_wall_footprints() -> Array[Rect2]:
	return _collect_footprints(_interior_walls)


## Hình chiếu XZ (Rect2) của cả đồ vật (`Furniture`) và tường ngăn nội thất (`InteriorWalls`).
func get_obstacle_footprints() -> Array[Rect2]:
	var rects: Array[Rect2] = _collect_footprints(_furniture)
	if _interior_walls != null:
		rects.append_array(_collect_footprints(_interior_walls))
	if _floor2_node != null:
		var f2_furn: Node3D = _floor2_node.get_node_or_null(^"Furniture")
		if f2_furn != null:
			rects.append_array(_collect_footprints(f2_furn))
		var f2_walls: Node3D = _floor2_node.get_node_or_null(^"InteriorWalls")
		if f2_walls != null:
			rects.append_array(_collect_footprints(f2_walls))
	if _floor3_node != null:
		var f3_furn: Node3D = _floor3_node.get_node_or_null(^"Furniture")
		if f3_furn != null:
			rects.append_array(_collect_footprints(f3_furn))
		var f3_walls: Node3D = _floor3_node.get_node_or_null(^"InteriorWalls")
		if f3_walls != null:
			rects.append_array(_collect_footprints(f3_walls))
	return rects


static func _collect_footprints(root: Node3D) -> Array[Rect2]:
	var rects: Array[Rect2] = []
	if root == null:
		return rects
	for node: Node in root.find_children("*", "CollisionShape3D", true, false):
		var cs := node as CollisionShape3D
		if cs == null or cs.disabled:
			continue
		var box := cs.shape as BoxShape3D
		if box == null:
			continue
		var h: Vector3 = box.size / 2.0
		var rect := Rect2()
		for i: int in 8:
			var corner := Vector3(h.x if i & 1 else -h.x, h.y if i & 2 else -h.y, h.z if i & 4 else -h.z)
			var w: Vector3 = cs.global_transform * corner
			var p := Vector2(w.x, w.z)
			rect = Rect2(p, Vector2.ZERO) if i == 0 else rect.expand(p)
		rects.append(rect)
	return rects


static func distance_to_rect(p: Vector2, r: Rect2) -> float:
	var dx: float = maxf(maxf(r.position.x - p.x, 0.0), p.x - r.end.x)
	var dz: float = maxf(maxf(r.position.y - p.y, 0.0), p.y - r.end.y)
	return sqrt(dx * dx + dz * dz)


## Như is_clear nhưng nở hộp hình vuông (khoảng cách Chebyshev), khớp is_blocked() bên Python.
static func is_clear_box(p: Vector3, footprints: Array[Rect2], clearance: float) -> bool:
	for r: Rect2 in footprints:
		var dx: float = maxf(maxf(r.position.x - p.x, 0.0), p.x - r.end.x)
		var dz: float = maxf(maxf(r.position.y - p.z, 0.0), p.z - r.end.y)
		if maxf(dx, dz) <= clearance:
			return false
	return true


static func is_clear(p: Vector3, footprints: Array[Rect2], clearance: float) -> bool:
	var q := Vector2(p.x, p.z)
	for r: Rect2 in footprints:
		if distance_to_rect(q, r) < clearance:
			return false
	return true
