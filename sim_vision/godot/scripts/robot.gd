class_name Robot
extends CharacterBody3D
## Robot differential drive (G5). Hướng trước là −Z cục bộ.
## omega > 0 ➔ quay trái (ngược chiều kim đồng hồ nhìn từ trên xuống), đúng Mục 2.4.
## Trang bị cảm biến: Camera RGB trước, FrontRay (0.8m), và LiDAR 2D 17 tia (200°, tầm xa 6.0 m) cho RL.

const LIDAR_NUM_RAYS: int = 17
const LIDAR_FOV_DEG: float = 200.0
const LIDAR_MAX_RANGE: float = 6.0
const LIDAR_HEIGHT_Y: float = 0.35

var _v: float = 0.0
var _omega: float = 0.0
var _lidar_rays: Array[RayCast3D] = []

var v: float:
	get:
		return _v
	set(val):
		set_command(val, _omega)

var omega: float:
	get:
		return _omega
	set(val):
		set_command(_v, val)


@onready var _viewport: SubViewport = $CameraViewport
@onready var _front_ray: RayCast3D = $FrontRay


func _ready() -> void:
	_viewport.size = Vector2i(Config.IMG_W, Config.IMG_H)
	_setup_lidar_fan()


func _setup_lidar_fan() -> void:
	if not _lidar_rays.is_empty():
		return
	var holder := Node3D.new()
	holder.name = "LidarFan"
	holder.position = Vector3(0.0, LIDAR_HEIGHT_Y, 0.0)
	add_child(holder)
	for i: int in LIDAR_NUM_RAYS:
		var frac: float = float(i) / float(LIDAR_NUM_RAYS - 1) - 0.5  # [-0.5, +0.5]
		var angle_rad: float = deg_to_rad(frac * LIDAR_FOV_DEG)
		var ray := RayCast3D.new()
		ray.name = "LidarRay_%02d" % i
		# Hướng trước cục bộ là -Z; góc dương quay sang phải, góc âm sang trái (quét từ trái sang phải)
		ray.target_position = Vector3(sin(angle_rad) * LIDAR_MAX_RANGE, 0.0, -cos(angle_rad) * LIDAR_MAX_RANGE)
		ray.enabled = true
		ray.add_exception(self)
		holder.add_child(ray)
		_lidar_rays.append(ray)


## Trả mảng 17 giá trị khoảng cách LiDAR đã chuẩn hóa về [0.0, 1.0] (1.0 = không chạm trong tầm 6.0m).
func get_lidar_readings() -> PackedFloat32Array:
	if _lidar_rays.is_empty():
		_setup_lidar_fan()
	var out := PackedFloat32Array()
	out.resize(LIDAR_NUM_RAYS)
	for i: int in LIDAR_NUM_RAYS:
		var ray: RayCast3D = _lidar_rays[i]
		ray.force_raycast_update()
		if not ray.is_colliding():
			out[i] = 1.0
		else:
			var dist: float = ray.global_position.distance_to(ray.get_collision_point())
			out[i] = clampf(dist / LIDAR_MAX_RANGE, 0.0, 1.0)
	return out


## Khoảng cách nhỏ nhất (m) từ mảng LiDAR 17 tia.
func min_lidar_distance() -> float:
	var readings: PackedFloat32Array = get_lidar_readings()
	var min_norm: float = 1.0
	for v: float in readings:
		min_norm = minf(min_norm, v)
	return min_norm * LIDAR_MAX_RANGE


## Nhận lệnh vận tốc; v kẹp về [0, V_MAX], omega kẹp về [-OMEGA_MAX, OMEGA_MAX].
func set_command(v: float, omega: float) -> void:
	var c: Vector2 = Robot.clamp_command(v, omega)
	_v = c.x
	_omega = c.y


func get_command() -> Vector2:
	return Vector2(_v, _omega)


func get_camera_viewport() -> SubViewport:
	return get_node(^"CameraViewport") as SubViewport  # dùng được cả trước _ready


## Khoảng cách từ đầu raycast phía trước tới vật cản; không chạm ➔ INF.
func front_obstacle_distance() -> float:
	_front_ray.force_raycast_update()
	if not _front_ray.is_colliding():
		return INF
	return _front_ray.global_position.distance_to(_front_ray.get_collision_point())


func _physics_process(delta: float) -> void:
	rotation.y += _omega * delta
	var forward: Vector3 = -global_transform.basis.z
	velocity = Vector3(forward.x, 0.0, forward.z).normalized() * _v
	move_and_slide()


static func clamp_command(v: float, omega: float) -> Vector2:
	return Vector2(clampf(v, 0.0, Config.V_MAX), clampf(omega, -Config.OMEGA_MAX, Config.OMEGA_MAX))
