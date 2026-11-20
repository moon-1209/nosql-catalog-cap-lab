extends GutTest

const SlidingDoorScene: PackedScene = preload("res://scenes/props/sliding_door.tscn")

var door: SlidingDoor


func before_each() -> void:
	door = SlidingDoorScene.instantiate() as SlidingDoor
	add_child_autofree(door)


func test_initial_state_closed_and_solid() -> void:
	assert_false(door.is_open)
	assert_false(door.is_collision_disabled())
	assert_almost_eq(door.get_slide_progress(), 0.0, 1e-5)


func test_force_open_immediately_disables_collision_and_slides() -> void:
	door.force_open()
	assert_true(door.is_open)
	assert_true(door.is_collision_disabled(), "collision must disable immediately so RL raycasts pass through")
	door.step(0.125)
	assert_between(door.get_slide_progress(), 0.45, 0.55)
	door.step(0.20)
	assert_almost_eq(door.get_slide_progress(), 1.0, 1e-5)
	assert_almost_eq(door.get_panel_position().x, door.open_offset.x, 1e-4)


func test_proximity_enter_and_delayed_auto_close() -> void:
	var actor := CharacterBody3D.new()
	add_child_autofree(actor)
	var static_body := StaticBody3D.new()
	add_child_autofree(static_body)
	assert_true(SlidingDoor.is_valid_opener(actor))
	assert_false(SlidingDoor.is_valid_opener(static_body))

	door._on_body_entered(actor)
	assert_true(door.is_open)
	assert_true(door.is_collision_disabled())
	door.step(0.3)
	assert_almost_eq(door.get_slide_progress(), 1.0, 1e-5)

	# Khi actor rời khỏi vùng cảm biến, cửa đợi close_delay_s (1.5 s) mới đóng lại
	door._on_body_exited(actor)
	door.step(1.0)
	assert_true(door.is_open, "door remains open before close_delay_s expires")
	door.step(0.6)
	assert_false(door.is_open, "door closes after close_delay_s expires")
	assert_false(door.is_collision_disabled(), "collision re-enabled when closed")
	door.step(0.3)
	assert_almost_eq(door.get_slide_progress(), 0.0, 1e-5)


func test_main_entrance_door_ignores_robot_but_opens_for_people() -> void:
	door.robot_can_open = false
	var robot := (load("res://scenes/robot.tscn") as PackedScene).instantiate() as Robot
	add_child_autofree(robot)
	door._on_body_entered(robot)
	assert_false(door.is_open, "robot never opens the main entrance (stays inside the hospital)")
	var person := CharacterBody3D.new()
	add_child_autofree(person)
	door._on_body_entered(person)
	assert_true(door.is_open, "people still open the main entrance")
