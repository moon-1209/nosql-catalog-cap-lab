extends GutTest

const HumanScene: PackedScene = preload("res://scenes/human.tscn")


func test_scene_has_capsule_collision_and_idle() -> void:
	var human := HumanScene.instantiate() as Human
	add_child_autofree(human)
	var cs := human.get_node("Collision") as CollisionShape3D
	assert_true(cs.shape is CapsuleShape3D)
	var anim := human.get_node("AnimationPlayer") as AnimationPlayer
	assert_true(anim.has_animation(&"human/idle"))
	assert_true(anim.has_animation(&"human/walk"))
	assert_eq(anim.current_animation, "human/idle")
	assert_false(human.walks)


func test_materials_have_textures() -> void:
	var human := HumanScene.instantiate() as Human
	add_child_autofree(human)
	var mesh := human.get_node("Model/Skeleton3D/m011_hipoly_81_bones_opacity") as MeshInstance3D
	for s: int in mesh.mesh.get_surface_count():
		var mat := mesh.get_surface_override_material(s) as StandardMaterial3D
		assert_not_null(mat, "surface %d override" % s)
		assert_not_null(mat.albedo_texture, "surface %d albedo" % s)


func test_height_and_feet_on_floor() -> void:
	var human := HumanScene.instantiate() as Human
	add_child_autofree(human)
	await wait_physics_frames(5)
	var skel := human.get_node("Model/Skeleton3D") as Skeleton3D
	var lo: float = INF
	var head_y: float = (skel.global_transform * skel.get_bone_global_pose(skel.find_bone("Bip01 Head"))).origin.y
	for b: int in skel.get_bone_count():
		lo = minf(lo, (skel.global_transform * skel.get_bone_global_pose(b)).origin.y)
	assert_almost_eq(lo, 0.0, 0.05, "lowest bone near floor")
	# Xương đầu nằm ở khoảng giữa đầu; đỉnh đầu cao hơn ~0.1–0.2 m ➔ cao 1.6–1.8 m.
	assert_between(head_y, 1.45, 1.65)


func test_step_towards() -> void:
	var p: Vector3 = Human.step_towards(Vector3(0, 0, 0), Vector3(3, 5, 4), 0.5)
	assert_almost_eq(p.x, 0.3, 1e-6)
	assert_almost_eq(p.z, 0.4, 1e-6)
	assert_eq(p.y, 0.0, "giữ nguyên y")
	assert_eq(Human.step_towards(Vector3(0, 0, 0), Vector3(0.1, 0, 0), 0.5), Vector3(0.1, 0, 0))


func test_next_waypoint_index_wraps() -> void:
	assert_eq(Human.next_waypoint_index(0, 3), 1)
	assert_eq(Human.next_waypoint_index(2, 3), 0)
	assert_eq(Human.next_waypoint_index(0, 0), 0)


func test_walks_at_half_meter_per_second() -> void:
	var human := HumanScene.instantiate() as Human
	human.walks = true
	human.waypoints = [Vector3(0, 0, 0), Vector3(3, 0, 0)] as Array[Vector3]
	add_child_autofree(human)
	await wait_physics_frames(2)  # tới waypoint 0, chuyển sang waypoint 1
	var x0: float = human.global_position.x
	await wait_seconds(1.0)
	var speed: float = human.global_position.x - x0
	assert_between(speed, 0.4, 0.6, "≈0.5 m/s")
	assert_eq((human.get_node("AnimationPlayer") as AnimationPlayer).current_animation, "human/walk")


func test_walks_without_waypoints_stays_idle() -> void:
	var human := HumanScene.instantiate() as Human
	human.walks = true
	add_child_autofree(human)
	await wait_physics_frames(5)
	assert_eq(human.global_position, Vector3.ZERO)
