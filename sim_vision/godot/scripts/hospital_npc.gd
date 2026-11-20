class_name HospitalNpc
extends CharacterBody3D
## NPC trong bệnh viện (Nhân viên y tế: Bác sĩ, Điều dưỡng; Bệnh nhân cao tuổi / ngồi chờ).
## Hỗ trợ cả đứng/ngồi tại chỗ lẫn đi bộ theo `waypoints` (`walks = true`) và tự động
## bước sang một bên nhường đường ("pardon") khi robot đi ngang qua (`pardon_enabled = true`).
## Hỗ trợ State Machine (SITTING -> STANDING -> WALKING -> SITTING) cho bệnh nhân
## và hỗ trợ được dẫn đường (ESCORTED) bởi robot.

const NpcScript = preload("res://scripts/npc.gd")
const WALK_ANIM_RES: String = "res://assets/models/human_m06/anims/walk.res"
const IDLE_ANIM_RES: String = "res://assets/models/human_m06/anims/idle.res"
const SIT_ANIM_RES: String = "res://assets/models/human_m06/anims/f_sit_waiting.res"

const ARRIVE_TOL: float = 0.08
const PARDON_TRIGGER_DIST: float = 1.4
const PARDON_CLEAR_DIST: float = 1.85
const PARDON_MIN_ROBOT_V: float = 0.05    # robot đứng yên (vd. tới nói chuyện) ➔ không né
const PARDON_LANE_HALF_W: float = 0.75    # chỉ né khi chắn làn robot (bán kính robot 0.32 + nửa thân 0.25 + dư)
const PARDON_LANE_CLEAR_M: float = 0.8    # né tới cách đường đi của robot 0.8 m (ra hẳn ngoài làn)
const PARDON_FLIP_MAX_LATERAL: float = 0.3  # chỉ né sang phía bên kia khi đứng gần giữa làn (không băng qua đầu robot)
const PARDON_CLEARANCE_M: float = 0.35    # khoảng trống cần có sau điểm né
const PARDON_MAX_S: float = 4.0           # né quá 4 s (vd. lỡ đứng chắn cửa robot cần qua) ➔ đi tiếp lộ trình...
const PARDON_COOLDOWN_S: float = 3.0      # ...và 3 s sau mới được né lại
const PARDON_DOORWAY_KEEP_CLEAR_M: float = 1.2  # điểm né không chắn cửa (đường robot có thể rẽ vào cửa)
const PERSONAL_SPACE_M: float = 0.9       # không bước lại gần tâm robot hơn 0.9 m; đứng chờ...
const BLOCKED_TURN_S: float = 2.0         # ...chờ quá 2 s khi đi tuần ➔ quay đầu về điểm tuần còn lại

enum State { SITTING, STANDING, WALKING, ESCORTED }

@export var tex_dir: String = "res://assets/models/medical_f01/textures"
@export var anim_path: String = "res://assets/models/human_m06/anims/f_idle.res"
@export var anim_offset: float = 0.0
@export var is_seated: bool = false
@export var staff_role: String = ""  # "nurse" | "doctor" | "patient"
@export var badge_text: String = ""
@export var has_cane: bool = false
@export var walks: bool = false
@export var waypoints: Array[Vector3] = []
@export var walk_speed: float = 0.48
@export var pardon_enabled: bool = true
@export var current_state: State = State.SITTING
@export var sit_duration_range: Vector2 = Vector2(15.0, 30.0)
@export var stand_duration_range: Vector2 = Vector2(3.0, 6.0)
@export var use_t_pose: bool = true

var robot_ref: Node3D = null
@export var can_speak: bool = true
@export var speaker_gender: String = "auto"

var _npc: Node = null

var _anim_player: AnimationPlayer
var _wp_index: int = 0
var _home_pos: Vector3 = Vector3.ZERO
var _home_yaw: float = 0.0
var _home_seat_pos: Vector3 = Vector3.ZERO
var _home_seat_yaw: float = 0.0
var _anchor_pos: Vector3 = Vector3.ZERO
var _is_pardoning: bool = false
var _pardon_target: Vector3 = Vector3.ZERO
var _pardon_elapsed_s: float = 0.0
var _pardon_cooldown_s: float = 0.0
var _blocked_s: float = 0.0
var _state_timer: float = 0.0


func _ready() -> void:
	_home_pos = global_position
	_home_seat_pos = global_position
	_anchor_pos = global_position
	_home_yaw = rotation.y
	_home_seat_yaw = rotation.y

	if can_speak:
		_setup_speech()

	var model := get_node_or_null(^"Model") as Node3D
	if model != null and is_seated:
		model.position = Vector3(0.0, 0.0, 0.06)

	if model != null:
		var mesh_node := _find_mesh(model)
		if mesh_node != null and mesh_node.mesh != null:
			var mat_body := _make_part_mat("body")
			var mat_head := _make_part_mat("head")
			var mat_opacity := _make_opacity_mat()
			var fallback: Array[Material] = [mat_body, mat_head, mat_opacity]
			for s: int in mesh_node.mesh.get_surface_count():
				var orig_mat: Material = mesh_node.mesh.surface_get_material(s)
				var mname: String = orig_mat.resource_name.to_lower() if orig_mat != null else ""
				if "opacity" in mname:
					mesh_node.set_surface_override_material(s, mat_opacity)
				elif "head" in mname:
					mesh_node.set_surface_override_material(s, mat_head)
				elif "body" in mname:
					mesh_node.set_surface_override_material(s, mat_body)
				elif s < fallback.size():
					mesh_node.set_surface_override_material(s, fallback[s])

		var skel := model.get_node_or_null(^"Skeleton3D") as Skeleton3D
		if skel != null and staff_role == "nurse":
			_attach_nurse_cap(skel)

	if badge_text != "":
		_create_role_badge()

	if has_cane:
		_create_walking_cane()

	if anim_path != "" and ResourceLoader.exists(anim_path) and model != null:
		_anim_player = AnimationPlayer.new()
		_anim_player.name = "AnimationPlayer"
		model.add_child(_anim_player)
		var lib := AnimationLibrary.new()
		var anim_res: Animation = load(anim_path)
		lib.add_animation(&"loop", anim_res)
		if ResourceLoader.exists(WALK_ANIM_RES):
			lib.add_animation(&"walk", load(WALK_ANIM_RES))
		if ResourceLoader.exists(IDLE_ANIM_RES):
			lib.add_animation(&"idle", load(IDLE_ANIM_RES))
		if "sit" in anim_path:
			lib.add_animation(&"sit", anim_res)
		elif ResourceLoader.exists(SIT_ANIM_RES):
			lib.add_animation(&"sit", load(SIT_ANIM_RES))
		_anim_player.add_animation_library(&"npc", lib)

	# Khởi tạo trạng thái ban đầu
	if staff_role == "doctor" or staff_role == "nurse":
		if walks and waypoints.size() >= 2:
			set_state(State.WALKING)
		else:
			set_state(State.STANDING)
	else:
		if is_seated:
			set_state(State.SITTING)
		elif walks and waypoints.size() >= 2:
			set_state(State.WALKING)
		else:
			set_state(State.STANDING)

	if use_t_pose and _anim_player != null:
		_anim_player.stop()
	elif anim_offset > 0.0 and _anim_player != null:
		_anim_player.advance(anim_offset)


func setup_robot(robot_node: Node3D, state_fn: Callable = Callable()) -> void:
	robot_ref = robot_node
	if _npc != null and _npc.has_method("setup"):
		var fn: Callable = state_fn
		if not fn.is_valid():
			fn = func() -> int:
				var m = get_tree().current_scene if get_tree() != null else null
				return m.state if m != null and "state" in m else Config.RobotState.SEARCH
		_npc.setup(robot_node, fn)


func is_pardoning() -> bool:
	return _is_pardoning


func set_state(new_state: State) -> void:
	current_state = new_state
	var model := get_node_or_null(^"Model") as Node3D
	var badge := get_node_or_null(^"RoleBadge") as Label3D
	var head := get_node_or_null(^"Head") as Node3D

	match current_state:
		State.SITTING:
			is_seated = true
			velocity = Vector3.ZERO
			_state_timer = randf_range(sit_duration_range.x, sit_duration_range.y)
			if model != null:
				model.position = Vector3(0.0, 0.0, 0.06)
			if badge != null:
				badge.position.y = 1.48
			if head != null:
				head.position.y = 1.2
			_play_anim(&"npc/sit")
		State.STANDING:
			is_seated = false
			velocity = Vector3.ZERO
			_state_timer = randf_range(stand_duration_range.x, stand_duration_range.y)
			if model != null:
				model.position = Vector3.ZERO
			if badge != null:
				badge.position.y = 1.84
			if head != null:
				head.position.y = 1.6
			_play_anim(&"npc/idle")
		State.WALKING:
			is_seated = false
			if model != null:
				model.position = Vector3.ZERO
			if badge != null:
				badge.position.y = 1.84
			if head != null:
				head.position.y = 1.6
			_wp_index = 0
			_play_anim(&"npc/walk")
		State.ESCORTED:
			if is_seated:
				if waypoints.size() >= 2:
					global_position = waypoints[1]
					_anchor_pos = waypoints[1]
				else:
					var fwd: Vector3 = -global_transform.basis.z.normalized()
					global_position = global_position + fwd * 0.9
					_anchor_pos = global_position
			is_seated = false
			if model != null:
				model.position = Vector3.ZERO
			if badge != null:
				badge.position.y = 1.84
			if head != null:
				head.position.y = 1.6
			_play_anim(&"npc/walk")


## Trả về vị trí tương tác (nơi robot tiếp cận và nói chuyện, cũng như nơi bệnh nhân đứng dậy bắt đầu đi).
## Nếu NPC đang ngồi và có waypoints (trong đó waypoints[1] là điểm đứng ngoài hành lang),
## trả về waypoints[1] để tránh robot tiếp cận từ sau lưng ghế hoặc kẹt vào va chạm của ghế.
func get_interaction_position() -> Vector3:
	if is_seated:
		if waypoints.size() >= 2:
			return waypoints[1]
		var fwd: Vector3 = -global_transform.basis.z.normalized()
		return global_position + fwd * 0.9
	return global_position


## Hỗ trợ dẫn đường: robot gọi mỗi frame trong pha GUIDE_ESCORT
func escort_step_towards(target: Vector3, max_step: float, delta: float) -> void:
	if current_state != State.ESCORTED or is_seated:
		if is_seated:
			if waypoints.size() >= 2:
				global_position = waypoints[1]
				_anchor_pos = waypoints[1]
			else:
				var fwd: Vector3 = -global_transform.basis.z.normalized()
				global_position = global_position + fwd * 0.9
				_anchor_pos = global_position
		set_state(State.ESCORTED)
	var model := get_node_or_null(^"Model") as Node3D
	if model != null and model.position != Vector3.ZERO:
		model.position = Vector3.ZERO
	var to := Vector3(target.x - global_position.x, 0.0, target.z - global_position.z)
	var d: float = to.length()
	if d < 1e-4 or max_step <= 0.0:
		escort_stop()
		return
	var disp: Vector3 = to / d * minf(max_step, d)
	rotation.y = atan2(disp.x, disp.z)
	if is_inside_tree() and get_world_3d() != null and get_world_3d().space != RID():
		velocity = disp / maxf(delta, 1e-4)
		move_and_slide()
		velocity = Vector3.ZERO
	else:
		global_position += disp
	_play_anim(&"npc/walk")


func escort_stop() -> void:
	current_state = State.ESCORTED
	velocity = Vector3.ZERO
	_play_anim(&"npc/idle")


func end_escort() -> void:
	set_state(State.STANDING)
	_anchor_pos = global_position
	velocity = Vector3.ZERO


func _physics_process(delta: float) -> void:
	if current_state == State.ESCORTED:
		return

	# Xử lý nhường đường (Pardon) khi robot lại gần
	if pardon_enabled and robot_ref != null and is_instance_valid(robot_ref) and current_state != State.SITTING:
		var dist_robot: float = Human.flat_distance(global_position, robot_ref.global_position)
		_pardon_cooldown_s = maxf(0.0, _pardon_cooldown_s - delta)
		if _is_pardoning:
			_pardon_elapsed_s += delta
		if not _is_pardoning and _pardon_cooldown_s <= 0.0 and dist_robot <= PARDON_TRIGGER_DIST \
				and HospitalNpc.should_pardon(global_position, robot_ref):
			var target: Variant = HospitalNpc.pick_clear_pardon_target(self, _anchor_pos, robot_ref)
			if target != null:
				_is_pardoning = true
				_pardon_target = target
				_pardon_elapsed_s = 0.0
		elif _is_pardoning and dist_robot >= PARDON_CLEAR_DIST:
			_is_pardoning = false
		elif _is_pardoning and _pardon_elapsed_s >= PARDON_MAX_S:
			_is_pardoning = false
			_pardon_cooldown_s = PARDON_COOLDOWN_S

	if _is_pardoning:
		var d_target: float = Human.flat_distance(global_position, _pardon_target)
		if d_target > ARRIVE_TOL:
			_move_step_towards(_pardon_target, walk_speed * delta, delta)
		else:
			velocity = Vector3.ZERO
			_play_anim(&"npc/idle")
			if robot_ref != null and is_instance_valid(robot_ref):
				rotation.y = atan2(
					robot_ref.global_position.x - global_position.x,
					robot_ref.global_position.z - global_position.z
				)
		return

	# Máy trạng thái cho bệnh nhân
	if staff_role == "patient" or staff_role == "":
		match current_state:
			State.SITTING:
				velocity = Vector3.ZERO
				_state_timer -= delta
				if _state_timer <= 0.0:
					set_state(State.STANDING)
				return
			State.STANDING:
				velocity = Vector3.ZERO
				_state_timer -= delta
				if _state_timer <= 0.0:
					if waypoints.size() >= 2:
						set_state(State.WALKING)
					else:
						set_state(State.SITTING)
				return
			State.WALKING:
				if waypoints.is_empty():
					set_state(State.STANDING)
					return
				var target: Vector3 = waypoints[_wp_index]
				if Human.flat_distance(global_position, target) <= ARRIVE_TOL:
					_wp_index += 1
					if _wp_index >= waypoints.size():
						# Đã đi hết vòng tuần và quay về ghế ngồi
						global_position = _home_seat_pos
						rotation.y = _home_seat_yaw
						velocity = Vector3.ZERO
						set_state(State.SITTING)
						return
					target = waypoints[_wp_index]
				_move_step_towards(target, walk_speed * delta, delta)
				if _blocked_s >= BLOCKED_TURN_S:
					_wp_index = (_wp_index + 1) % waypoints.size()
					_blocked_s = 0.0
				_anchor_pos = global_position
				return

	# Logic tuần tra cho nhân viên y tế (Bác sĩ, Điều dưỡng)
	if _can_walk():
		var target: Vector3 = waypoints[_wp_index]
		if Human.flat_distance(global_position, target) <= ARRIVE_TOL:
			_wp_index = Human.next_waypoint_index(_wp_index, waypoints.size())
			target = waypoints[_wp_index]
		_move_step_towards(target, walk_speed * delta, delta)
		if _blocked_s >= BLOCKED_TURN_S:
			_wp_index = Human.next_waypoint_index(_wp_index, waypoints.size())
			_blocked_s = 0.0
		_anchor_pos = global_position
	else:
		var d_home: float = Human.flat_distance(global_position, _home_pos)
		if d_home > ARRIVE_TOL:
			_move_step_towards(_home_pos, walk_speed * delta, delta)
		else:
			global_position = _home_pos
			rotation.y = _home_yaw
			velocity = Vector3.ZERO
			_play_anim(&"npc/idle")


func _can_walk() -> bool:
	return current_state == State.WALKING or (not is_seated and walks and waypoints.size() >= 2)


## Di chuyển về `target` dùng move_and_slide() và kiểm tra khoảng cách an toàn với robot.
func _move_step_towards(target: Vector3, max_step: float, delta: float = 0.0) -> void:
	var next_pos: Vector3 = Human.step_towards(global_position, target, max_step)
	if robot_ref != null and is_instance_valid(robot_ref):
		var d_next: float = Human.flat_distance(next_pos, robot_ref.global_position)
		if d_next < PERSONAL_SPACE_M and d_next < Human.flat_distance(global_position, robot_ref.global_position):
			_blocked_s += delta
			velocity = Vector3.ZERO
			_play_anim(&"npc/idle")
			return

	_blocked_s = 0.0
	var dir := Vector3(next_pos.x - global_position.x, 0.0, next_pos.z - global_position.z)
	if dir.length() > 1e-5:
		rotation.y = atan2(dir.x, dir.z)
	if is_inside_tree() and get_world_3d() != null and get_world_3d().space != RID():
		velocity = dir / maxf(delta, 1e-4)
		move_and_slide()
		velocity = Vector3.ZERO
	global_position = next_pos
	_play_anim(&"npc/walk")


func _play_anim(anim_name: StringName) -> void:
	if use_t_pose:
		if _anim_player != null and _anim_player.is_playing():
			_anim_player.stop()
		return
	if _anim_player == null:
		return
	if _anim_player.has_animation(anim_name):
		if _anim_player.current_animation != anim_name:
			_anim_player.play(anim_name, 0.25)
	elif _anim_player.has_animation(&"npc/loop"):
		if _anim_player.current_animation != &"npc/loop":
			_anim_player.play(&"npc/loop", 0.25)


## Tính vị trí bước sang ngang ("pardon") vuông góc với hướng đi của robot, ưu tiên phía xa đường đi của robot.
static func should_pardon(npc_pos: Vector3, robot: Node3D) -> bool:
	var v: Variant = robot.get("v")
	if v != null and absf(float(v)) < PARDON_MIN_ROBOT_V:
		return false
	var fwd: Vector3 = -robot.global_transform.basis.z
	var fwd_2d := Vector2(fwd.x, fwd.z).normalized()
	var rel := Vector2(npc_pos.x - robot.global_position.x, npc_pos.z - robot.global_position.z)
	var ahead: float = rel.dot(fwd_2d)
	var lateral: float = absf(rel.dot(Vector2(-fwd_2d.y, fwd_2d.x)))
	return ahead > -0.2 and lateral < PARDON_LANE_HALF_W


static func pick_clear_pardon_target(npc: Node3D, anchor: Vector3, robot: Node3D) -> Variant:
	var fwd: Vector3 = -robot.global_transform.basis.z
	var space: PhysicsDirectSpaceState3D = npc.get_world_3d().direct_space_state
	var exclude: Array[RID] = []
	for body: Node in [npc, robot]:
		if body is CollisionObject3D:
			exclude.append((body as CollisionObject3D).get_rid())
	var fwd_2d := Vector2(fwd.x, fwd.z).normalized()
	var rel := Vector2(anchor.x - robot.global_position.x, anchor.z - robot.global_position.z)
	var lateral: float = absf(rel.dot(Vector2(-fwd_2d.y, fwd_2d.x)))
	for flip: bool in [false, true]:
		if flip and lateral >= PARDON_FLIP_MAX_LATERAL:
			break
		var target: Vector3 = HospitalNpc.compute_pardon_target(anchor, robot.global_position, fwd, PARDON_LANE_CLEAR_M, flip)
		if HospitalNpc.near_doorway(npc, target):
			continue
		var from := Vector3(npc.global_position.x, 0.5, npc.global_position.z)
		var dir := Vector3(target.x - from.x, 0.0, target.z - from.z)
		if dir.length() < 1e-4:
			continue
		var to: Vector3 = from + dir + dir.normalized() * PARDON_CLEARANCE_M
		var query := PhysicsRayQueryParameters3D.create(from, to)
		query.exclude = exclude
		if space == null or space.intersect_ray(query).is_empty():
			return target
	return null


static func near_doorway(npc: Node, p: Vector3) -> bool:
	for door: Node in npc.get_tree().get_nodes_in_group(&"sliding_doors"):
		if Human.flat_distance(p, (door as Node3D).global_position) < PARDON_DOORWAY_KEEP_CLEAR_M:
			return true
	return false


static func compute_pardon_target(npc_pos: Vector3, robot_pos: Vector3, robot_fwd: Vector3, lane_clear: float = PARDON_LANE_CLEAR_M, flip: bool = false) -> Vector3:
	var fwd_2d := Vector2(robot_fwd.x, robot_fwd.z)
	if fwd_2d.length() < 1e-4:
		fwd_2d = Vector2(0.0, -1.0)
	else:
		fwd_2d = fwd_2d.normalized()
	var perp := Vector2(-fwd_2d.y, fwd_2d.x)
	var rel := Vector2(npc_pos.x - robot_pos.x, npc_pos.z - robot_pos.z)
	var lateral: float = rel.dot(perp)
	var side_sign: float = 1.0 if lateral >= 0.0 else -1.0
	if flip:
		side_sign = -side_sign
	var offset: Vector2 = perp * (side_sign * lane_clear - lateral)
	var x_base: float = 50.0 if npc_pos.x >= 25.0 else 0.0
	return Vector3(
		clampf(npc_pos.x + offset.x, x_base - 11.4, x_base + 11.4),
		npc_pos.y,
		clampf(npc_pos.z + offset.y, -8.4, 8.4)
	)


func _make_part_mat(part: String) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
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
	return mat


func _make_opacity_mat() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	var o_path: String = "%s/opacity_color.png" % tex_dir
	if ResourceLoader.exists(o_path):
		mat.albedo_texture = load(o_path)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.roughness = 0.7
	return mat


static func _find_mesh(root: Node) -> MeshInstance3D:
	if root is MeshInstance3D:
		return root as MeshInstance3D
	for c: Node in root.get_children():
		var found := _find_mesh(c)
		if found != null:
			return found
	return null


func _attach_nurse_cap(skel: Skeleton3D) -> void:
	var head_idx: int = skel.find_bone("Bip01 Head")
	if head_idx == -1:
		return
	var attach := BoneAttachment3D.new()
	attach.name = "NurseCapAttachment"
	attach.bone_name = "Bip01 Head"
	skel.add_child(attach)

	var cap_white := StandardMaterial3D.new()
	cap_white.albedo_color = Color(0.96, 0.97, 0.99, 1.0)
	cap_white.roughness = 0.4

	var cap_blue := StandardMaterial3D.new()
	cap_blue.albedo_color = Color(0.09, 0.38, 0.68, 1.0)
	cap_blue.roughness = 0.35

	var cap_body := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.078
	cyl.bottom_radius = 0.072
	cyl.height = 0.055
	cyl.material = cap_white
	cap_body.mesh = cyl
	cap_body.position = Vector3(0.155, -0.015, 0.0)
	cap_body.rotation = Vector3(0.0, 0.0, -PI / 2.0)
	attach.add_child(cap_body)

	var stripe := MeshInstance3D.new()
	var stripe_cyl := CylinderMesh.new()
	stripe_cyl.top_radius = 0.08
	stripe_cyl.bottom_radius = 0.079
	stripe_cyl.height = 0.012
	stripe_cyl.material = cap_blue
	stripe.mesh = stripe_cyl
	stripe.position = Vector3(0.162, -0.015, 0.0)
	stripe.rotation = Vector3(0.0, 0.0, -PI / 2.0)
	attach.add_child(stripe)


func _create_role_badge() -> void:
	var lbl := Label3D.new()
	lbl.name = "RoleBadge"
	lbl.position = Vector3(0.0, 1.84 if not is_seated else 1.48, 0.0)
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.pixel_size = 0.0014
	lbl.font_size = 26
	lbl.outline_size = 5
	lbl.text = badge_text
	if staff_role == "doctor":
		lbl.modulate = Color(0.55, 0.92, 1.0, 1.0)
	elif staff_role == "nurse":
		lbl.modulate = Color(0.62, 0.98, 0.78, 1.0)
	else:
		lbl.modulate = Color(0.95, 0.95, 0.9, 1.0)
	add_child(lbl)


func _create_walking_cane() -> void:
	var cane := Node3D.new()
	cane.name = "WalkingCane"
	cane.position = Vector3(-0.18, 0.0, 0.56) if is_seated else Vector3(-0.24, 0.0, 0.22)
	cane.rotation = Vector3(0.08, 0.0, 0.0) if is_seated else Vector3(0.0, 0.0, 0.0)
	add_child(cane)

	var wood_mat := StandardMaterial3D.new()
	wood_mat.albedo_color = Color(0.36, 0.2, 0.09, 1.0)
	wood_mat.roughness = 0.35

	var brass_mat := StandardMaterial3D.new()
	brass_mat.albedo_color = Color(0.78, 0.64, 0.24, 1.0)
	brass_mat.metallic = 0.75
	brass_mat.roughness = 0.25

	var rubber_mat := StandardMaterial3D.new()
	rubber_mat.albedo_color = Color(0.14, 0.14, 0.15, 1.0)
	rubber_mat.roughness = 0.85

	var shaft := MeshInstance3D.new()
	var shaft_cyl := CylinderMesh.new()
	shaft_cyl.top_radius = 0.013
	shaft_cyl.bottom_radius = 0.011
	shaft_cyl.height = 0.78
	shaft_cyl.material = wood_mat
	shaft.mesh = shaft_cyl
	shaft.position = Vector3(0.0, 0.40, 0.0)
	cane.add_child(shaft)

	var tip := MeshInstance3D.new()
	var tip_cyl := CylinderMesh.new()
	tip_cyl.top_radius = 0.015
	tip_cyl.bottom_radius = 0.018
	tip_cyl.height = 0.045
	tip_cyl.material = rubber_mat
	tip.mesh = tip_cyl
	tip.position = Vector3(0.0, 0.0225, 0.0)
	cane.add_child(tip)

	var collar := MeshInstance3D.new()
	var collar_cyl := CylinderMesh.new()
	collar_cyl.top_radius = 0.0145
	collar_cyl.bottom_radius = 0.0145
	collar_cyl.height = 0.022
	collar_cyl.material = brass_mat
	collar.mesh = collar_cyl
	collar.position = Vector3(0.0, 0.78, 0.0)
	cane.add_child(collar)

	var handle := MeshInstance3D.new()
	var handle_box := BoxMesh.new()
	handle_box.size = Vector3(0.028, 0.026, 0.13)
	handle_box.material = wood_mat
	handle.mesh = handle_box
	handle.position = Vector3(0.0, 0.80, -0.04)
	cane.add_child(handle)


func _setup_speech() -> void:
	var head := get_node_or_null(^"Head") as Node3D
	if head == null:
		head = Node3D.new()
		head.name = "Head"
		head.position = Vector3(0.0, 1.2 if is_seated else 1.6, 0.08)
		add_child(head)

	var voice_player := head.get_node_or_null(^"Voice") as AudioStreamPlayer3D
	if voice_player == null:
		voice_player = AudioStreamPlayer3D.new()
		voice_player.name = "Voice"
		voice_player.unit_size = 5.0
		voice_player.volume_db = 6.0
		head.add_child(voice_player)

	var npc_node := NpcScript.new()
	npc_node.name = "Npc"
	var spk: String = speaker_gender
	if spk == "auto":
		var t_lower: String = tex_dir.to_lower()
		var n_lower: String = name.to_lower()
		if "female" in t_lower or "f0" in t_lower or "f0" in n_lower or "nurse" in n_lower:
			spk = "B"
		else:
			spk = "A"
	npc_node.speaker = spk
	add_child(npc_node)
	_npc = npc_node


func has_npc() -> bool:
	return _npc != null


func get_npc() -> Node:
	return _npc
