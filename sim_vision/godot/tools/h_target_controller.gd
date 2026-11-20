class_name HTargetController
extends Controller
## Chỉ dùng cho batch G17: robot dừng ở chiều cao box `h_target` thay cho Config.H_TARGET, không sửa controller.gd.
## Phóng chiều cao box theo tỉ lệ Config.H_TARGET / h_target trước khi gọi Controller.step, nên h thật = h_target
## tương đương h = Config.H_TARGET với controller gốc (tốc độ tiến cũng co theo cùng tỉ lệ).

var h_target: float = Config.H_TARGET


func step(state: int, dets: Array, time_since_seen_s: float) -> Dictionary:
	return super.step(state, HTargetController.scale_dets(dets, Config.H_TARGET / h_target), time_since_seen_s)


static func scale_dets(dets: Array, k: float) -> Array:
	var out: Array = []
	for d: Dictionary in dets:
		var s: Dictionary = d.duplicate()
		s["y2"] = float(d["y1"]) + (float(d["y2"]) - float(d["y1"])) * k
		out.append(s)
	return out
