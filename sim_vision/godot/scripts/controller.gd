class_name Controller
extends Node
## Bộ điều khiển tìm và tiến tới người (G7). `step` là hàm thuần: không đọc scene,
## không đọc thời gian hệ thống, không giữ trạng thái — RLController sau này giữ cùng giao diện.
## Dấu omega theo Mục 2.4: người bên phải ảnh (cx > 0.5) ➔ omega < 0 (quay phải).


## state: Config.RobotState; dets: detection Mục 2.2 (có thể rỗng);
## time_since_seen_s: thời gian từ lần cuối thấy người.
## Trả {state: Config.RobotState, v: float, omega: float, target: Dictionary}.
func step(state: int, dets: Array, time_since_seen_s: float) -> Dictionary:
	if dets.is_empty():
		if time_since_seen_s > Config.LOST_TIMEOUT_S or state == Config.RobotState.SEARCH:
			return _cmd(Config.RobotState.SEARCH, 0.0, Config.SEARCH_OMEGA, {})
		return _cmd(state, 0.0, 0.0, {})  # vừa mất dấu: đứng chờ
	var d: Dictionary = Controller.pick_target(dets)
	var cx: float = (float(d["x1"]) + float(d["x2"])) / 2.0
	var h: float = float(d["y2"]) - float(d["y1"])
	var e: float = cx - 0.5
	if h >= Config.H_TARGET:
		return _cmd(Config.RobotState.ARRIVED, 0.0, 0.0, d)
	if state == Config.RobotState.ARRIVED and h >= Config.H_TARGET - Config.H_HYST:
		return _cmd(Config.RobotState.ARRIVED, 0.0, 0.0, d)
	var omega: float = clampf(-Config.K_ANG * e, -Config.OMEGA_MAX, Config.OMEGA_MAX)
	var v: float = clampf(Config.K_LIN * (Config.H_TARGET - h), 0.0, Config.V_MAX)
	if absf(e) > Config.ALIGN_TOL:
		v = 0.0
	return _cmd(Config.RobotState.APPROACH, v, omega, d)


## Detection có conf cao nhất; bằng nhau ➔ box cao hơn (h lớn hơn); vẫn bằng ➔ cái đứng trước.
static func pick_target(dets: Array) -> Dictionary:
	var best: Dictionary = dets[0]
	for i: int in range(1, dets.size()):
		var d: Dictionary = dets[i]
		var c: float = float(d["conf"])
		var bc: float = float(best["conf"])
		if c > bc or (c == bc and _height(d) > _height(best)):
			best = d
	return best


static func _height(d: Dictionary) -> float:
	return float(d["y2"]) - float(d["y1"])


static func _cmd(state: int, v: float, omega: float, target: Dictionary) -> Dictionary:
	return {"state": state, "v": v, "omega": omega, "target": target}
