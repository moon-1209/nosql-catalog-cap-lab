extends SceneTree
## Xuất bản đồ va chạm 2D (tường + đồ đạc, cả 2 tầng) và danh sách NPC (chế độ đầy đủ) cho env RL Python.
## Chỉ lấy hộp va chạm cắt ngang độ cao tia LiDAR (Robot.LIDAR_HEIGHT_Y); bỏ sàn/trần,
## cửa trượt tự mở cho robot (SlidingDoor) và NPC (HospitalNpc, động / bị tắt ở chế độ solo).
## Cửa chính (robot_can_open = false) giữ lại: với robot nó là tường. Kèm trạm robot (Entrance/RobotDock).
##
## Chạy: godot --headless --path sim_vision/godot -s res://tools/export_nav_layout.gd
## Ghi: src/training/hospital_layout.json (đường dẫn tính từ gốc repo)

const OUT_PATH: String = "res://../../src/training/hospital_layout.json"


func _init() -> void:
	var room: Node3D = (load("res://scenes/room.tscn") as PackedScene).instantiate()
	root.add_child(room)
	await process_frame

	var rects: Array = []
	for node: Node in room.find_children("*", "CollisionShape3D", true, false):
		var cs := node as CollisionShape3D
		var box := cs.shape as BoxShape3D
		if cs.disabled or box == null or cs.get_parent() is Area3D or _find_ancestor_of(cs, ["HospitalNpc"]) != null:
			continue
		var door := _find_ancestor_of(cs, ["SlidingDoor"]) as SlidingDoor
		if door != null and door.robot_can_open:
			continue
		var h: Vector3 = box.size / 2.0
		var lo := Vector3(INF, INF, INF)
		var hi := Vector3(-INF, -INF, -INF)
		for i: int in 8:
			var corner := Vector3(h.x if i & 1 else -h.x, h.y if i & 2 else -h.y, h.z if i & 4 else -h.z)
			var w: Vector3 = cs.global_transform * corner
			lo = lo.min(w)
			hi = hi.max(w)
		if lo.y > Robot.LIDAR_HEIGHT_Y or hi.y < Robot.LIDAR_HEIGHT_Y:
			continue
		rects.append({
			"name": str(room.get_path_to(cs)),
			"x0": snappedf(lo.x, 0.001), "z0": snappedf(lo.z, 0.001),
			"x1": snappedf(hi.x, 0.001), "z1": snappedf(hi.z, 0.001),
		})

	var npcs: Array = []
	for node: Node in room.find_children("*", "", true, false):
		var npc := node as HospitalNpc
		if npc == null:
			continue
		var half := Vector2(0.25, 0.25)
		for c: Node in npc.find_children("*", "CollisionShape3D", true, false):
			var box := (c as CollisionShape3D).shape as BoxShape3D
			if box != null:
				half = Vector2(box.size.x, box.size.z) / 2.0
		var wps: Array = []
		for w: Vector3 in npc.waypoints:
			wps.append([snappedf(w.x, 0.001), snappedf(w.z, 0.001)])
		npcs.append({
			"name": str(npc.name), "role": npc.staff_role, "seated": npc.is_seated,
			"x": snappedf(npc.global_position.x, 0.001), "z": snappedf(npc.global_position.z, 0.001),
			"half_x": half.x, "half_z": half.y,
			"walks": npc.walks and not npc.is_seated and wps.size() >= 2, "waypoints": wps,
			"walk_speed": npc.walk_speed, "pardon_enabled": npc.pardon_enabled,
		})

	var dock := room.get_node(^"Entrance/RobotDock") as Node3D
	var robot_dock := {
		"x": snappedf(dock.global_position.x, 0.001), "z": snappedf(dock.global_position.z, 0.001),
		"yaw": snappedf(dock.global_rotation.y, 0.0001),
	}
	var out := {
		"source": "sim_vision/godot/scenes/room.tscn", "lidar_height_y": Robot.LIDAR_HEIGHT_Y,
		"robot_dock": robot_dock, "rects": rects, "npcs": npcs,
	}
	var path: String = ProjectSettings.globalize_path(OUT_PATH)
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(out, "  ") + "\n")
	f.close()
	print("export_nav_layout: %d rects, %d npcs -> %s" % [rects.size(), npcs.size(), path])
	quit()


static func _find_ancestor_of(node: Node, class_names: Array[String]) -> Node:
	var p: Node = node.get_parent()
	while p != null:
		var script: Script = p.get_script()
		if script != null and script.get_global_name() in class_names:
			return p
		p = p.get_parent()
	return null
