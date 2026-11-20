class_name Human
extends CharacterBody3D
## Người tả thực (Rocketbox Male_Adult_06 hoặc biến thể cao tuổi). Mặc định đứng yên (idle);
## `walks = true` ➔ đi chậm qua lần lượt các `waypoints` (lặp vòng).
## Hỗ trợ `pardon_enabled`: tự động bước sang một bên nhường đường khi robot đi ngang qua.
## Mặt người hướng về +Z cục bộ.

const WALK_SPEED: float = 0.5     # m/s (G4.1)
const ARRIVE_TOL: float = 0.05    # m, coi như đã tới waypoint
const PARDON_TRIGGER_DIST: float = 1.4
const PARDON_CLEAR_DIST: float = 1.85

@export var walks: bool = false
@export var waypoints: Array[Vector3] = []
@export var pardon_enabled: bool = false
@export var use_t_pose: bool = false

var robot_ref: Node3D = null

var _wp_index: int = 0
var _is_pardoning: bool = false
var _pardon_target: Vector3 = Vector3.ZERO
var _anchor_pos: Vector3 = Vector3.ZERO
var _escorted: bool = false  # đang được robot dẫn đường: main điều khiển bước đi, bỏ qua waypoint / pardon

@onready var _anim: AnimationPlayer = $AnimationPlayer


func _ready() -> void:
	_anchor_pos = global_position
	if not use_t_pose:
		_anim.play(&"human/walk" if _is_walking() else &"human/idle")
	elif _anim != null and _anim.is_playing():
		_anim.stop()


func setup_robot(robot_node: Node3D) -> void:
	robot_ref = robot_node


func is_pardoning() -> bool:
	return _is_pardoning


## Thay bộ texture (body/head/opacity) của `$Human` sang biến thể bệnh nhân cao tuổi bất kỳ.
func apply_variant_textures(tex_dir: String) -> void:
	var model := get_node_or_null(^"Model")
	if model == null:
		return
	var mesh_node := HospitalNpc._find_mesh(model)
	if mesh_node == null or mesh_node.mesh == null:
		return
	for s: int in mesh_node.mesh.get_surface_count():
		var orig_mat: Material = mesh_node.mesh.surface_get_material(s)
		var mname: String = orig_mat.resource_name.to_lower() if orig_mat != null else ""
		var mat := StandardMaterial3D.new()
		if "opacity" in mname or s == 2:
			var o_path: String = "%s/opacity_color.png" % tex_dir
			if ResourceLoader.exists(o_path):
				mat.albedo_texture = load(o_path)
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
			mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			mat.roughness = 0.7
		else:
			var part: String = "head" if ("head" in mname or s == 1) else "body"
			var c_path: String = "%s/%s_color.jpg" % [tex_dir, part]
			var n_path: String = "%s/%s_normal.png" % [tex_dir, part]
			var r_path: String = "%s/%s_roughness.jpg" % [tex_dir, part]
			if ResourceLoader.exists(c_path):
				mat.albedo_texture = load(c_path)
			if ResourceLoader.exists(r_path):
				mat.roughness_texture = load(r_path)
			if ResourceLoader.exists(n_path):
				mat.normal_enabled = true
				mat.normal_texture = load(n_path)
		mesh_node.set_surface_override_material(s, mat)


## Bước theo robot khi được dẫn đường (gọi mỗi physics frame từ RLEnvBridge.step_escorted_patient).
func escort_step_towards(target: Vector3, max_step: float, delta: float) -> void:
	_escorted = true
	var to := Vector3(target.x - global_position.x, 0.0, target.z - global_position.z)
	var d: float = to.length()
	if d < 1e-4 or max_step <= 0.0:
		escort_stop()
		return
	var disp: Vector3 = to / d * minf(max_step, d)
	rotation.y = atan2(disp.x, disp.z)
	velocity = disp / maxf(delta, 1e-4)
	move_and_slide()
	velocity = Vector3.ZERO
	_play(&"human/walk")


func escort_stop() -> void:
	_escorted = true
	velocity = Vector3.ZERO
	_play(&"human/idle")


## Kết thúc dẫn đường (reset / hoàn thành nhiệm vụ) ➔ hành vi thường.
func end_escort() -> void:
	_escorted = false
	_anchor_pos = global_position


func _physics_process(delta: float) -> void:
	if _escorted:
		return
	if pardon_enabled and robot_ref != null and is_instance_valid(robot_ref):
		var dist_robot: float = Human.flat_distance(global_position, robot_ref.global_position)
		if not _is_pardoning and dist_robot <= PARDON_TRIGGER_DIST \
				and HospitalNpc.should_pardon(global_position, robot_ref):
			_anchor_pos = global_position
			var target: Variant = HospitalNpc.pick_clear_pardon_target(self, _anchor_pos, robot_ref)
			if target != null:
				_is_pardoning = true
				_pardon_target = target
		elif _is_pardoning and dist_robot >= PARDON_CLEAR_DIST:
			_is_pardoning = false

	if _is_pardoning:
		if Human.flat_distance(global_position, _pardon_target) > ARRIVE_TOL:
			_play(&"human/walk")
			var p_step: Vector3 = Human.step_towards(global_position, _pardon_target, WALK_SPEED * delta)
			var p_dir := Vector3(p_step.x - global_position.x, 0.0, p_step.z - global_position.z)
			if p_dir.length() > 0.0:
				rotation.y = atan2(p_dir.x, p_dir.z)
				velocity = p_dir / delta
				move_and_slide()
		else:
			velocity = Vector3.ZERO
			_play(&"human/idle")
			if robot_ref != null and is_instance_valid(robot_ref):
				rotation.y = atan2(
					robot_ref.global_position.x - global_position.x,
					robot_ref.global_position.z - global_position.z
				)
		return

	if not _is_walking():
		_play(&"human/idle")
		return
	_play(&"human/walk")
	var target: Vector3 = waypoints[_wp_index]
	if Human.flat_distance(global_position, target) <= ARRIVE_TOL:
		_wp_index = Human.next_waypoint_index(_wp_index, waypoints.size())
		target = waypoints[_wp_index]
	var step: Vector3 = Human.step_towards(global_position, target, WALK_SPEED * delta)
	var dir := Vector3(step.x - global_position.x, 0.0, step.z - global_position.z)
	if dir.length() > 0.0:
		rotation.y = atan2(dir.x, dir.z)  # quay mặt (+Z) theo hướng đi
		velocity = dir / delta
		move_and_slide()


func _is_walking() -> bool:
	return walks and waypoints.size() >= 2


func _play(anim_name: StringName) -> void:
	if use_t_pose:
		if _anim != null and _anim.is_playing():
			_anim.stop()
		return
	if _anim != null and _anim.current_animation != anim_name:
		_anim.play(anim_name, 0.3)


static func flat_distance(a: Vector3, b: Vector3) -> float:
	return Vector2(a.x - b.x, a.z - b.z).length()


static func next_waypoint_index(i: int, count: int) -> int:
	return (i + 1) % count if count > 0 else 0


## Điểm mới sau khi tiến tối đa `max_dist` về `target` trên mặt phẳng XZ (giữ nguyên y).
static func step_towards(from: Vector3, target: Vector3, max_dist: float) -> Vector3:
	var d: float = flat_distance(from, target)
	if d <= max_dist or d == 0.0:
		return Vector3(target.x, from.y, target.z)
	var t: float = max_dist / d
	return Vector3(from.x + (target.x - from.x) * t, from.y, from.z + (target.z - from.z) * t)
