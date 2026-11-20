extends GutTest

const RobotScene: PackedScene = preload("res://scenes/robot.tscn")
const HumanScene: PackedScene = preload("res://scenes/human.tscn")


func test_is_success() -> void:
	var A: int = Config.RobotState.ARRIVED
	assert_true(BatchRun.is_success(A, 1.2))
	assert_true(BatchRun.is_success(A, 0.8))
	assert_true(BatchRun.is_success(A, 1.5))
	assert_false(BatchRun.is_success(A, 1.51))
	assert_false(BatchRun.is_success(A, 0.79))
	assert_false(BatchRun.is_success(Config.RobotState.APPROACH, 1.2), "phải ở ARRIVED")


func test_format_summary_row() -> void:
	var r := {"seed": 3, "success": true, "time_to_arrive_s": 12.5, "final_distance_m": 1.46,
			"collisions": 0, "frames": 70, "mean_infer_ms": 33.21}
	assert_eq(BatchRun.format_summary_row(r), "3,true,12.5000,1.4600,0,70,33.2100")
	r["success"] = false
	r["time_to_arrive_s"] = null
	assert_eq(BatchRun.format_summary_row(r), "3,false,,1.4600,0,70,33.2100")


func test_touches_by_distance() -> void:
	var robot := RobotScene.instantiate() as Robot
	var human := HumanScene.instantiate() as Human
	robot.position = Vector3(80, 0, 0)
	human.position = Vector3(80.5, 0, 0)
	add_child_autofree(robot)
	add_child_autofree(human)
	assert_true(BatchRun.touches(robot, human), "0.5 m = tổng bán kính")
	human.position = Vector3(81.0, 0, 0)
	assert_false(BatchRun.touches(robot, human))
