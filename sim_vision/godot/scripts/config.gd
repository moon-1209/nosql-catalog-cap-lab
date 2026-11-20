class_name Config
extends RefCounted
## Hằng số dùng chung (Mục 2.1) và trạng thái robot (Mục 2.3) của godot_robot_yolo_prompt.md,
## cộng hằng số Mục 2.1 / trạng thái Mục 2.3 của godot_npc_stt_prompt.md (G11–G17).
## Tên và giá trị phải khớp đúng file kế hoạch; không thêm hằng số ngoài kế hoạch ở đây.

const WS_URL: String = "ws://127.0.0.1:8765"
const CAPTURE_HZ: int = 5
const IMG_W: int = 640
const IMG_H: int = 480
const JPEG_QUALITY: float = 0.8
const YOLO_CONF: float = 0.4
const V_MAX: float = 0.8            # m/s
const OMEGA_MAX: float = 1.5        # rad/s
const K_ANG: float = 2.0
const K_LIN: float = 1.5
const H_TARGET: float = 0.85
const H_HYST: float = 0.10
const ALIGN_TOL: float = 0.25
const LOST_TIMEOUT_S: float = 1.5
const SEARCH_OMEGA: float = 0.5     # rad/s
const STALE_MS: int = 500
const SAFE_DIST_HUMAN: float = 0.8  # m
const SAFE_DIST_OBSTACLE: float = 0.5  # m
const RECONNECT_S: float = 2.0

# Sim_Voice (godot_npc_stt_prompt.md Mục 2.1). DATA_DIR, STT_MODEL_ID, SAMPLE_RATE chỉ dùng phía Python.
const STT_WS_URL: String = "ws://127.0.0.1:8766"
const TALK_TRIGGER_DIST: float = 2.0  # m
const TURN_DURATION_S: float = 0.6
const STT_TIMEOUT_S: float = 10.0
const NPC_COOLDOWN_S: float = 8.0
const MAX_TURNS: int = 1
const SUBTITLE_S: float = 4.0
const REF_DIST_M: float = 1.0
const DEFAULT_SNR_DB: float = 20.0

# NLU + TTS (nlu_tts_dialogue_prompt.md Mục 2.1), phần Godot dùng.
const TTS_WS_URL: String = "ws://127.0.0.1:8767"
const TTS_TIMEOUT_S: float = 8.0
const MAX_CLARIFY: int = 2
## Tạm chọn, chờ người dùng nghe reports/voices/ (U4); phải trùng ROBOT_VOICE của tts/config.py.
const ROBOT_VOICE: String = "Ngọc Huyền"

# LISTEN, THINK, RESPOND thêm sau ARRIVED (Mục 2.3 Sim_Voice); giá trị cũ giữ nguyên.
enum RobotState { SEARCH, APPROACH, ARRIVED, LISTEN, THINK, RESPOND }


## Trả tên trạng thái đúng chuỗi ở Mục 2.3; giá trị lạ ➔ push_error và trả "".
static func state_name(s: int) -> String:
	match s:
		RobotState.SEARCH:
			return "SEARCH"
		RobotState.APPROACH:
			return "APPROACH"
		RobotState.ARRIVED:
			return "ARRIVED"
		RobotState.LISTEN:
			return "LISTEN"
		RobotState.THINK:
			return "THINK"
		RobotState.RESPOND:
			return "RESPOND"
	push_error("Config.state_name: unknown state %d" % s)
	return ""
