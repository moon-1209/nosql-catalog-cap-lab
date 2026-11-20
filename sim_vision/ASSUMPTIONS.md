# Giả định

Định dạng: `[G<số>] <giả định> — <lý do>`.

## G1
- [G1] Dùng Godot 4.7.2-stable (`config/features` = "4.7") — kế hoạch yêu cầu ≥ 4.3; đây là bản người dùng đã cài.
- [G1] GUT 9.7.1 cài vào `godot/addons/gut/`, cấu hình chạy ở `godot/.gutconfig.json` — bản GUT mới nhất, hỗ trợ Godot 4.x.
- [G1] Thư mục `sim_vision/` nằm ở gốc repo `Data-Science-Major-Project/` — Mục 1 không nói rõ vị trí.
- [G1] Python 3.12 (Homebrew) trong venv `python/.venv` — `python3` của hệ thống là 3.9, thấp hơn yêu cầu 3.10+.
- [G1] Phiên bản ghim trong `requirements.txt` là bản mới nhất trên PyPI tại 2026-10-21, đã cài chung và chạy được. `ultralytics` tự kéo thêm `opencv-python` (không headless) làm phụ thuộc; hai gói cùng phiên bản nên không xung đột.
- [G1] `Config` là `class_name Config extends RefCounted`, kiểu: `IMG_W`, `IMG_H`, `CAPTURE_HZ`, `STALE_MS` là `int`, còn lại `float`/`String` — Mục 2.1 không nêu kiểu; chọn theo bản chất giá trị.
- [G1] `Config.state_name()` với giá trị không thuộc enum ➔ `push_error` và trả `""` — Mục 2.3 không nói về giá trị lạ; không bịa thêm tên trạng thái.
- [G1] `main.tscn` tạm thời chỉ có node gốc `Node3D` tên `Main` — nội dung thật làm ở G8.
- [G1] `pandas`, `matplotlib` (cần cho G10) chưa thêm vào `requirements.txt` — G1 chỉ liệt kê 6 gói; sẽ thêm ở G10.

## G2
- [G2] Thứ tự kiểm tra trường: `type` ➔ `frame_id` ➔ `jpeg_b64` ➔ `width` ➔ `height` — để khớp ví dụ `{"type":"frame","frame_id":4}` ➔ `missing field: jpeg_b64` (message này thiếu cả `width`, `height`).
- [G2] Chuỗi lỗi ngoài ví dụ: `missing field: <tên>`, `invalid field: <tên>` (sai kiểu/giá trị, kể cả `type` ≠ `"frame"`), `invalid jpeg` (base64 hỏng hoặc không giải mã được), `size mismatch` (`width`/`height` khác kích thước ảnh thật) — Mục 2.2 chỉ cho định dạng message `error`, không liệt kê nội dung `message`.
- [G2] JSON hợp lệ nhưng không phải object (vd `[1,2]`, `42`) ➔ `invalid json` — server chỉ hiểu message dạng object.
- [G2] `frame_id` là `true`/`false` hoặc số thực ➔ không hợp lệ — Mục 2.2: số nguyên.
- [G2] Box được kẹp về [0, 1], làm tròn 4 chữ số; box suy biến sau khi kẹp (x1 ≥ x2 hoặc y1 ≥ y2) bị bỏ — để luôn đúng ràng buộc `0 ≤ x1 < x2 ≤ 1`.
- [G2] `conf` làm tròn 4 chữ số, `infer_ms` làm tròn 1 chữ số — ví dụ Mục 2.2 dùng `23.5`, `21.4`.
- [G2] `YoloDetector` chạy nháp 1 lần với ảnh đen 640×480 lúc khởi động — để `infer_ms` của frame đầu không tính thời gian khởi tạo.
- [G2] Suy luận chạy trên CPU (mặc định của ultralytics trên macOS, không dùng MPS) — G10 yêu cầu `mean_infer_ms` < 100 ms trên CPU.
- [G2] "Chỉ xử lý frame mới nhất": mỗi kết nối giữ đúng 1 message đang chờ; message mới ghi đè message chờ cũ (kể cả message hỏng ghi đè frame hợp lệ đang chờ). Frame bị bỏ không có phản hồi.
- [G2] Hằng số phía Python (`WS_HOST`, `WS_PORT`, `YOLO_CONF`) đặt trong `protocol.py`, giá trị lấy từ `WS_URL`, `YOLO_CONF` của Mục 2.1 — G2 chỉ cho phép 3 file `protocol.py`, `detector.py`, `yolo_server.py`.
- [G2] `python/yolov8n.pt` là symlink tới `models/yolov8n/yolov8n.pt` (file người dùng đã cung cấp) — tránh copy file 6.5 MB.
- [G2] Thêm `python/send_image.py` để gửi ảnh thật khi kiểm chứng; ảnh người thật dùng `bus.jpg`, `zidane.jpg` có sẵn trong gói ultralytics (không tải gì thêm).
- [G2] Thêm `python/pytest.ini` (`pythonpath = .`, `asyncio_mode = auto`) — repo gốc đã có `pytest.ini` riêng trỏ tới `tests/`, nên cần file riêng cho `sim_vision/python`.

## G3
- [G3] Phòng có 1 cửa sổ 2 m × 1.4 m (x ∈ [-1, 1], y ∈ [0.9, 2.3]) ở tường bắc (z = -3), không có kính — để `DirectionalLight3D` "giả nắng qua cửa sổ" thật sự chiếu vào phòng kín có bật bóng.
- [G3] Đồ vật: bàn làm việc kim loại, ghế bành, chậu cây, xe lăn (Poly Haven, CC0) — chọn đồ hợp bối cảnh bệnh viện; xe lăn hợp với đồ án.
- [G3] Texture: sàn Tiles028, tường PaintedPlaster017, trần OfficeCeiling001 (ambientCG, CC0, bản 1K). Mapping triplanar theo tọa độ thế giới, lặp lại mỗi 2 m (`uv1_scale = 0.5`) — các mảng tường ghép liền vân, không méo.
- [G3] Collision đồ vật là 1 `BoxShape3D` bao AABB của model (đo sau khi import) — đủ cho va chạm và cho `get_free_position`; không cần lưới chính xác.
- [G3] `get_free_position(min_clearance, rng = null)` có thêm tham số tùy chọn `rng` — G8 cần đặt vị trí lặp lại được theo `seed`; gọi đúng chữ ký G3.1 vẫn chạy (ngẫu nhiên).
- [G3] "Cách đồ vật ≥ min_clearance" tính bằng khoảng cách trên mặt phẳng XZ từ điểm tới hình chiếu (AABB thế giới) của collision đồ vật; cách tường cũng ≥ `min_clearance` (khớp ví dụ `|x| ≤ 3.5`, `|z| ≤ 2.5` với 0.5).
- [G3] `min_clearance` lớn tới mức không còn vùng hợp lệ (vd ≥ 3 m) ➔ báo lỗi ngay, không thử 100 lần.
- [G3] Thông số ánh sáng/môi trường: nắng `light_energy` 2.0 chếch 35°; 2 `OmniLight3D` tại (±2, 2.7, 0), năng lượng 1.2, tầm 7 m; SDFGI (bật occlusion), SSAO, ACES, nền và ánh sáng môi trường từ `ProceduralSkyMaterial` (năng lượng 0.5) — đặc tả không cho số; chỉnh tiếp ở G4 nếu cổng nhận diện không đạt.
- [G3] `room.tscn` được sinh một lần bằng script Python tạm (không lưu trong repo); từ giờ sửa trực tiếp trong Godot editor.

## G4
- [G4] Người: Microsoft Rocketbox `Male_Adult_06` (MIT), áo đỏ, quần jean — người dùng chọn Rocketbox; áo đỏ tương phản tốt với tường và sàn sáng màu.
- [G4] Dùng file FBX gốc, Godot 4.7 import trực tiếp; không chuyển sang `.glb` — G4.1 cho `.glb`/`.gltf`, nhưng chuyển định dạng cần Blender và không làm thay đổi gì khi chạy; khi import Godot cũng tạo ra scene giống như từ glTF.
- [G4] Material gán lại trong `human.tscn` (FBX trỏ tới texture theo đường dẫn tuyệt đối trên máy tác giả). Roughness = `1 − specular` của Rocketbox. Normal map dùng nguyên bản, không lật kênh Y (ảnh render không thấy lỗi bóng đổ ngược).
- [G4] Tóc và lông mi (surface `opacity`) dùng `ALPHA_DEPTH_PRE_PASS`, hiển thị cả hai mặt — tránh tóc bị thủng hoặc sắp xếp sai thứ tự trong suốt.
- [G4] Animation `idle` = `m_idle_neutral_01` (tại chỗ), `walk` = `m_walk_neutral` (bản tách chuyển động `xy`, đi tại chỗ; script tự di chuyển 0.5 m/s). Tách ra `idle.res`/`walk.res` bằng `tools/extract_human_anims.gd`, bỏ track của 41 xương không có trong avatar.
- [G4] Gốc `human.tscn` là `CharacterBody3D` (đi bằng `move_and_slide`, không có trọng lực, y giữ nguyên) — cần va chạm để robot (G8) và raycast phát hiện được.
- [G4] Quy ước hướng: mặt người là +Z cục bộ. Khi đi, `rotation.y = atan2(dx, dz)`. Waypoint lặp vòng; `walks = true` mà có < 2 waypoint ➔ đứng yên (idle).
- [G4] Capsule va chạm: bán kính 0.25 m, cao 1.75 m — chiều cao người ≈ 1.75 m (xương đầu ở 1.59 m).
- [G4] Cổng kiểm tra: camera nhìn ngang (không chúc xuống) ở 1.2 m, đặt tại x = −3.6 nhìn về +X để đủ chỗ cho 6 m trong phòng 8 m; yaw 0° = người nhìn thẳng vào camera; ánh sáng ±10% nhân vào mọi `Light3D` của phòng; camera lệch ngẫu nhiên ±5° cả ngang và dọc; seed cố định 0.
- [G4] "Có detection conf ≥ 0.5" = detection đầu tiên (conf cao nhất) có conf ≥ 0.5. CSV thêm cột `mean_top_conf` (trung bình conf cao nhất của 20 ảnh, 0 nếu không thấy ai). Lưu 1 ảnh mẫu mỗi mốc vào `logs/detect_gate/` (chỉ tool này lưu ảnh, server thì không).
- [G4] `detect_gate` tự kết nối WebSocket tối giản (có `outbound_buffer_size` = 4 MB vì ảnh base64 vượt quá 64 KB mặc định) — VisionClient G6 chưa có. G6 cũng cần tăng buffer này.

## G5
- [G5] Thân robot: trụ cao 1.0 m, bán kính 0.25 m; đầu là hộp 0.3 × 0.25 × 0.3 m, tâm ở 1.1 m. Collision là một hình trụ cao 1.225 m (bao cả đầu). Vật liệu robot là màu trơn — yêu cầu PBR ở G3 chỉ áp cho phòng.
- [G5] Camera robot (trong `SubViewport`) bám theo đầu robot nhờ `RemoteTransform3D` đặt ở (0, 1.2, −0.16), tức mặt trước của đầu; `near = 0.05` để không thấy chính đầu robot.
- [G5] `RayCast3D` đặt ở mặt trước thân (0, 0.3, −0.25), dài 1.0 m về −Z. Độ cao 0.3 m để chạm được đồ thấp (chậu cây 0.63 m). `front_obstacle_distance` đo từ mặt trước thân robot và gọi `force_raycast_update()` để luôn có kết quả mới.
- [G5] Robot không có trọng lực, y giữ nguyên; hướng trước là −Z; mỗi khung vật lý `rotation.y += omega·dt` (omega > 0 quay trái, đúng Mục 2.4).
- [G5] Kích thước `SubViewport` đặt bằng `Config.IMG_W/IMG_H` trong `_ready`; `fov = 70` (đặc tả G5.1, không có trong Mục 2.1) ghi trong scene.
- [G5] Ô góc nhìn: viền 2 px là một `ColorRect` sáng màu phía sau ảnh; chữ dùng font mặc định của Godot (hiển thị được tiếng Việt), cỡ 13. Trạng thái robot ở góc trên trái của ô, trạng thái kết nối ở góc dưới trái (đỏ khi mất kết nối).
- [G5] Thêm `ViewOverlay.set_viewport(vp)` để gắn ảnh camera, cùng các hàm thuần `norm_to_pixel`, `label_text`, `connection_text` để test được — G5.2 chỉ yêu cầu `show_detections`.
- [G5] `Robot.get_command()` và `Robot.clamp_command()` thêm vào để test và để G8/G9 đọc lệnh đang chạy.

## G6
- [G6] Mỗi lần thử kết nối tạo một `WebSocketPeer` mới, `outbound_buffer_size` = 4 MB (mặc định 64 KB nhỏ hơn 1 ảnh JPEG base64 ~60–100 KB). Thử kết nối ngay khi bắt đầu, sau đó mỗi `RECONNECT_S` khi đang ở trạng thái CLOSED.
- [G6] Bộ đếm thời gian chụp đặt lại về 0 mỗi khi trạng thái kết nối đổi; frame đầu tiên gửi sau 1/`CAPTURE_HZ` giây kể từ lúc kết nối.
- [G6] Kết quả chỉ được nhận khi `frame_id` có trong `sent_at` (Godot đã gửi frame này) — `frame_id` lạ bị bỏ, coi như trễ.
- [G6] `sent_at` được dọn mỗi khung: bỏ frame ≤ frame đã nhận gần nhất và frame đã gửi quá `STALE_MS` (không thể nhận nữa) ➔ chỉ còn vài mục.
- [G6] Message `type == "error"` ➔ `push_warning` kèm `frame_id` và `message`; không phát signal.
- [G6] JSON của Godot đọc mọi số thành `float` ➔ `frame_id` hợp lệ là số ≥ 0 không có phần lẻ. `infer_ms` phải là số ≥ 0. `conf` cũng phải nằm trong [0, 1].
- [G6] Dùng `JSON.new().parse()` thay cho `JSON.parse_string()` — hàm sau in lỗi engine khi gặp JSON hỏng, trái với yêu cầu "`push_warning`, bỏ qua".
- [G6] Thêm `is_server_connected()`, `record_sent()`, `pending_count()`, `handle_message(text, now_ms)` và hàm thuần `is_fresh()`, `is_valid_detection()` để test logic bỏ frame cũ/trễ mà không cần socket thật. Không dùng tên `is_connected` vì `Object.is_connected` đã có.
- [G6] `Robot.get_camera_viewport()` đổi sang `get_node()` thay vì biến `@onready` — gọi trước `_ready` (vd từ script dựng cảnh) trước đây trả null.

## G7
- [G7] `Controller` kế thừa `Node` (không phải `RefCounted`) — G8 chọn bộ điều khiển qua `@export var controller_path: NodePath`, nên phải là node. `step` vẫn là hàm thuần: không dùng biến thành viên, không đọc scene hay thời gian.
- [G7] `state` truyền vào và trả ra là giá trị enum `Config.RobotState` (int); đổi sang chuỗi bằng `Config.state_name()` khi hiển thị/ghi log.
- [G7] `target` là đúng dictionary detection được chọn (không thêm `cx`, `h`) — G7.1 chỉ ghi `target: Dictionary`.
- [G7] Bằng `conf` và bằng `h` ➔ chọn detection đứng trước trong danh sách.
- [G7] Với `cx` ∈ [0, 1] thì |omega| ≤ `K_ANG`·0.5 = 1.0 < `OMEGA_MAX`, nên phép kẹp omega không bao giờ xảy ra với input hợp lệ. Test biên kiểm tra omega luôn trong giới hạn thay vì ép kẹp.

## G8
- [G8] Camera người xem là `ViewerCamera` đặt trong phòng, sát trần ở góc tây nam (−3.8, 2.85, 2.75), nhìn chéo xuống giữa phòng, FOV 80° — camera ngoài phòng bị tường và trần che.
- [G8] Người cũng quay mặt theo hướng ngẫu nhiên (cùng `rng`) — G8.1 chỉ nói robot hướng ngẫu nhiên; người quay lưng hay quay ngang vẫn được YOLO nhận ra (gate G4) và gần thực tế hơn.
- [G8] Robot và người lấy vị trí lần lượt từ cùng một `rng` (robot trước, người sau), thử tối đa 100 cặp để có khoảng cách ≥ 3 m; không được ➔ `push_error` và dùng cặp cuối.
- [G8] `time_since_seen_s` = `INF` khi chưa từng thấy người kể từ lúc bắt đầu hoặc nhấn R.
- [G8] Khi kết nối mà quá `LOST_TIMEOUT_S` không có kết quả mới, `controller.step(state, [], t)` được gọi mỗi khung cho tới khi có kết quả lại; các lần gọi này không phát `cycle_completed` (G9 chỉ ghi log khi có kết quả nhận diện).
- [G8] Mất kết nối ➔ `set_command(0, 0)`, trạng thái giữ nguyên; kết nối lại ➔ mốc "kết quả gần nhất" đặt về lúc kết nối.
- [G8] Thêm signal `cycle_completed(info)` (frame_id, dets, cmd sau an toàn, infer_ms, connected) để G9 ghi log mà không phải sửa luồng chính; thêm `human_distance()` (khoảng cách XZ giữa tâm robot và tâm người).
- [G8] Biến `@export var seed` trùng tên hàm toàn cục `seed()` của GDScript ➔ thêm `@warning_ignore("shadowed_global_identifier")` để giữ đúng tên trong đặc tả.
- [G8] Có thêm nhãn hướng dẫn "R: đặt lại vị trí   Esc: thoát" ở góc trên trái.

## G9
- [G9] `conf`, `cx`, `h` lấy từ detection mà controller chọn (`cmd.target`), không phải detection đầu tiên — để log khớp với thứ robot đang bám theo.
- [G9] `time_s` tính từ lúc `main.gd` bắt đầu (`_ready`), không reset khi nhấn R.
- [G9] `connected` ghi `true`/`false` (pandas tự đọc thành bool); `frame_id`, `n_det` là số nguyên; `state` là tên chuỗi.
- [G9] `true_angle_deg` đúng bằng ±180 (người ở ngay sau lưng) ghi là 180. Hướng trước hoặc hướng tới người không có thành phần XZ ➔ 0.
- [G9] Ngoài `NOTIFICATION_WM_CLOSE_REQUEST`, logger còn flush và đóng file trong `_exit_tree` — thoát bằng phím Esc (`get_tree().quit()`) không phát WM_CLOSE_REQUEST.
- [G9] Thư mục log mặc định là `sim_vision/logs/` (cạnh thư mục `godot/`), tự tạo nếu chưa có; tạo không được hoặc mở file không được ➔ `push_error` một lần, `log_row` không làm gì nữa.
- [G9] `main.gd` có node `RunLogger` thì ghi log, không có thì bỏ qua (`get_node_or_null`) — test và batch (G10) có thể bỏ logger.

## Thay đổi hợp đồng (2026-10-21)
- [G8➔G10] `H_TARGET` 0.65 ➔ **0.85** (người dùng quyết định). Lý do: với 0.65 robot dừng ở 2.21 m, ngoài khoảng thành công [0.8, 1.5] m của G10. Đã sửa `config.gd`, `test_config.gd`, Mục 2.1 và bảng ví dụ G7.3/G7.4 trong `docs/PROMPT/godot_robot_yolo_prompt.md`, 4 ví dụ và 3 test biên trong `test_controller.gd`. Logic controller không đổi.

## G10
- [G10] Một lượt kết thúc ngay khi thành công (ARRIVED và khoảng cách thật trong [0.8, 1.5] m) hoặc khi hết 30 s mô phỏng; `final_distance_m` là khoảng cách lúc kết thúc.
- [G10] Thời gian mô phỏng là tổng `delta` của các khung vật lý, bắt đầu tính khi `VisionClient` đã kết nối (robot đứng yên trước đó) ➔ vị trí ban đầu giống hệt khi chạy `main.tscn` cùng seed.
- [G10] `collisions` = số lần robot **chạm người** (va chạm trượt với người, hoặc tâm cách nhau ≤ tổng bán kính + 2 cm), đếm theo sườn lên — tiêu chí G10.3 là "không va chạm với người". Chạm tường/đồ vật không tính.
- [G10] `frames` = số chu kỳ nhận diện (số lần `cycle_completed`); `mean_infer_ms` = trung bình `infer_ms` của các chu kỳ đó.
- [G10] Tham số dòng lệnh `-- --runs=N --max-time=S` (mặc định 10 lượt và 30 s). Batch cần cửa sổ có render; khi `--headless` thì tự thoát với mã 2.
- [G10] `analyze_logs.py` đọc mọi file `logs/run_*.csv` ở thư mục gốc `logs/` (không đọc thư mục con) và `logs/batch_summary.csv`; biểu đồ lưu ở `logs/h_vs_distance.png`. Log chạy thử trước batch đã chuyển sang `logs/archive_pre_batch/`.
- [G10] Thêm `pandas==3.0.6`, `matplotlib==3.11.2` vào `requirements.txt`.

# Sim_Voice (G11–G17, `docs/PROMPT/godot_npc_stt_prompt.md`)

## Quyết định của người dùng (2026-10-21), khác kế hoạch
- [G11–G17] Model STT là **Qualcomm PhoASR-whisper-small** bản local ở `models/PhoASR-whisper-small`, không phải `vinai/PhoWhisper-small`. `STT_MODEL_ID` mặc định trỏ tới thư mục này (đổi được qua biến môi trường `STT_MODEL_ID`); không tải gì từ mạng.
- [G11] Dữ liệu nguồn ở `data/raw/real_voice/` (một thư mục phẳng, file `.m4a`), không phải `data/A`, `data/B` như Mục 2.4. Hằng số `RAW_SUBDIR = "raw/real_voice"`. File `data/processed/real_voice/*.wav` có sẵn từ `scripts/convert_audio.py` không được dùng và không bị đụng tới.
- [G11] Câu chung đặt tên `Nam_Cxx.m4a` (một lần thu) được coi là `A_Cxx_r` (đọc rõ, `ref_verified = true`); `A_Cxx_n` nằm trong `missing.csv`. Tương tự `Nu_Cxx` ➔ `B_Cxx_r` (giả định theo cùng quy ước, chưa có file).
- [G11–G17] Hiện chỉ có giọng A (nam, 70 clip). Code hỗ trợ đủ A và B; B nằm trong `missing.csv`, chạy lại G11 khi có file.

## G11
- [G11] Kịch bản đọc từ `docs/kich_ban_thu_am.md` (kế hoạch ghi `recordings/kich_ban_thu_am.md`, thư mục này không tồn tại).
- [G11] Văn bản kịch bản được chuẩn hóa Unicode NFC khi đọc. Mã câu trùng ➔ báo lỗi (không âm thầm ghi đè).
- [G11] Cắt im lặng bằng `librosa.effects.trim(top_db=40, frame_length=512, hop_length=128)` rồi giữ lại tối đa 200 ms mỗi bên. Khung mặc định 2048 mẫu làm dư ~70 ms mỗi bên nên đã thu nhỏ.
- [G11] Giới hạn độ dài (< 0.3 s, > 15 s) kiểm tra **sau khi cắt im lặng**; file toàn im lặng ➔ "too short".
- [G11] "Chạm ±1.0" tính là `|x| ≥ 0.999` trên tín hiệu đã chuyển về 16 kHz mono (trước khi cắt). Cột `clipping` thêm vào cuối nhóm cột của manifest, trước `src_path`.
- [G11] `.m4a` giải mã bằng `ffmpeg -ac 1 -ar 16000 -f f32le`; `.wav` đọc bằng `soundfile`, trộn kênh bằng trung bình, resample bằng `librosa`. ffmpeg báo lỗi ➔ `skipped.csv` lý do "decode error".
- [G11] Idempotent: `data/processed/.prepare_cache.json` lưu `(src, size, mtime_ns)` và thông số của mỗi clip; khớp và file wav còn ➔ không xử lý lại. Hai file nguồn cùng `clip_id` (vd `Nam_C01.m4a` và `A_C01_r.m4a`) ➔ file sau theo thứ tự tên bị bỏ, lý do "duplicate clip_id".
- [G11] `src_path` ghi đường dẫn tương đối so với `DATA_DIR` (không lộ đường dẫn máy).
- [G11] `missing.csv` có cột `clip_id, text`. `transcripts_n_todo.csv` có cột `clip_id, text_script, text_fixed`; `text_fixed` cũ được giữ, kể cả khi clip đó tạm thời không còn file.
- [G11] `sync_voices` chỉ copy file mới hoặc đã đổi nội dung, xóa wav (và `.import`) không còn trong manifest. `godot/assets/voices/` được thêm vào `.gitignore`.
- [G11] Test voice không dùng `conftest.py` riêng (sẽ trùng tên module với `tests/conftest.py` khi `from conftest import`); fixture nằm trong `tests/voice/voice_testutil.py`.
- [G11] Thêm `torch`, `transformers`, `librosa`, `soundfile`, `jiwer` (ghim phiên bản đã cài) vào `requirements.txt`. `transformers` 5.20.2 mới hơn bản tạo model (4.48.0) nhưng đã chạy thử được.

## G12
- [G12] Model load từ thư mục local (`--model`, mặc định `STT_MODEL_ID`); không phải thư mục ➔ báo lỗi và thoát mã 1 (không tải từ Hub). Khởi động chạy nháp 1 s im lặng để lần nhận dạng đầu không chậm (lần đầu trên MPS mất ~2.6 s).
- [G12] `Transcriber.transcribe(audio, sr, clip_id=None)`: thêm tham số tùy chọn `clip_id` để `FakeTranscriber` trả đúng `text_ref`; model thật bỏ qua tham số này.
- [G12] Babble: "clip khác người" ➔ ưu tiên clip của người nói khác; hiện chỉ có giọng A nên lấy các clip cùng người nhưng **khác câu** (khác `sentence_id`). Chọn 4–6 clip không lặp, mỗi clip lặp/dịch thời gian ngẫu nhiên và giảm 20 dB, rồi cả tổng được chỉnh mức để đạt đúng `snr_db` (yêu cầu SNR ±0.5 dB được ưu tiên, nên mức −20 dB chỉ ảnh hưởng tỉ lệ giữa các clip, không ảnh hưởng mức ồn cuối).
- [G12] Công suất tiếng nói tính trên toàn clip đã cắt im lặng (còn ≤ 200 ms im lặng mỗi bên), không dùng VAD.
- [G12] SNR đo lại = công suất tiếng nói sau giảm âm so với phần dư (tín hiệu trộn − tiếng nói); test đạt ±0.5 dB với white, babble và file ồn.
- [G12] `noise="none"` ➔ `effective_snr_db = inf` trong `render`; trong message JSON ghi `null` (JSON không biểu diễn được inf).
- [G12] Seed mỗi utterance = `zlib.crc32("<utt_id>:<clip_id>")` (ổn định giữa các lần chạy; `hash()` của Python bị ngẫu nhiên hóa với chuỗi).
- [G12] Kiểm tra message theo thứ tự type ➔ utt_id ➔ clip_id ➔ distance_m (số hữu hạn, ≥ 0) ➔ snr_db (số hữu hạn) ➔ noise (chuỗi khác rỗng); lỗi `"missing field: X"`, `"invalid field: X"`, `"invalid json"`. Tên ồn không phải none/white/babble và không có `data/noise/<tên>.wav` ➔ `"noise not found: <tên>"`. Lỗi lúc chạy model ➔ `"stt failed: <loại lỗi>"` (không gửi chi tiết).
- [G12] Một worker dùng chung model cho mọi kết nối, xử lý lần lượt theo thứ tự đến; hàng chờ tối đa 4 utterance **không tính cái đang chạy**; đầy ➔ `"stt busy"` ngay. Message lỗi định dạng được trả lời ngay, không vào hàng chờ.
- [G12] `stt_ms` chỉ đo thời gian model (không gồm đọc file và mô phỏng âm thanh); làm tròn 1 chữ số, `audio_s` và `effective_snr_db` làm tròn 2 chữ số.
- [G12] Thêm CLI `python -m voice.send_utterance <clip_id>` để gửi thử (tương tự `send_image.py`).

## G13
- [G13] Chuẩn hóa bỏ thêm ngoặc kép/đơn kiểu chữ in (“ ” ‘ ’) và gạch dài (– —) ngoài danh sách Mục 2.6, vì cùng nghĩa với dấu câu đã liệt kê. Dấu câu được thay bằng khoảng trắng (không xóa dính) để "X-quang" ➔ "x quang".
- [G13] `has_number_mismatch(ref, hyp)`: `ref` có số viết bằng chữ số mà `hyp` không chứa đúng số đó (so theo token chữ số). Ref không có số ➔ false.
- [G13] WER/CER gộp theo corpus (tổng lỗi / tổng từ của ref) cho mọi bảng; WER từng dòng vẫn ghi trong CSV. KTC 95% bootstrap theo clip: lấy lại clip có hoàn lại, cộng lỗi và độ dài mọi dòng của clip đó, 1000 lần, seed cố định.
- [G13] `noise="none"` chạy với 1 SNR (giữ chỗ 30 dB) cho mỗi khoảng cách ➔ lưới mặc định 4 + 2 × 4 × 4 = 36 điều kiện × 70 clip = 2520 dòng. Bảng theo `snr_db` bỏ các dòng `none`.
- [G13] Seed mỗi dòng = crc32(`"<seed>:<clip_id>:<distance>:<snr>:<noise>"`), seed mặc định 0. Cache ở `reports/stt_cache/cache.jsonl` (JSON lines, khóa `[clip_id, distance, snr, noise, seed, model, beams]`; `model` là tên thư mục model).
- [G13] Kết quả ra `sim_vision/reports/`. `reports/*.csv` và `reports/stt_cache/` bị gitignore vì chứa văn bản nhận dạng từ giọng thật; `stt_summary.md` và 2 ảnh biểu đồ thì không.
- [G13] Biểu đồ WER theo SNR lấy trung bình mọi khoảng cách (đường `none` là đường ngang); WER theo khoảng cách lấy trung bình mọi SNR, mỗi loại ồn một đường.
- [G13] Có intent module (G14) thì cột `intent_pred`, `intent_ok` được điền cho mọi clip (kể cả `_n`); bảng độ chính xác intent theo `take`, `noise`, `distance_m` có trong báo cáo.
- [G13] Thêm `--grid quick` (2 khoảng cách × 2 SNR × babble + none) và `--fake` (FakeTranscriber) để kiểm tra đường ống nhanh.

## G14
- [G14] Thêm intent `ho_tro_di_chuyen` (câu A_20 "…cho mượn xe lăn không?"): nhãn này có trong bảng kịch bản nhưng thiếu ở bảng intent Mục 6. Theo thứ tự nguồn chân lý, nhãn trong kịch bản được giữ; xếp sau `dang_ky_kham` trong nhóm "còn lại".
- [G14] Thứ tự nhóm "các intent còn lại": khong_ho_tro ➔ nha_thuoc ➔ bao_hiem ➔ thanh_toan ➔ dang_ky_kham ➔ ho_tro_di_chuyen ➔ thoi_gian_cho ➔ tien_ich ➔ tiep_tuc ➔ cam_on. `nha_thuoc` trước `bao_hiem` vì "lấy thuốc bảo hiểm ở đâu" là `nha_thuoc`.
- [G14] `hoi_khoa`: khớp "khoa nào", "khám khoa" hoặc tên khoa trong `hospital_map.json` ➔ 1.0; chỉ có từ "khoa" ➔ 0.6. `hoi_phong`: có từ "phòng" ➔ 1.0; hoặc tên phòng/dịch vụ trong bản đồ **kèm** từ hỏi vị trí (ở đâu, đường nào, lối nào, chỗ…) ➔ 1.0. Điều kiện kèm vị trí để "bao lâu thì có kết quả xét nghiệm" thành `thoi_gian_cho` chứ không phải `hoi_phong`.
- [G14] Một số cụm từ được ghép thành một token trước khi khớp ("hướng dẫn", "tiếp đón", "nghỉ trưa", "nội soi") để từ đơn bên trong không khớp nhầm ("dẫn" ➔ dan_duong, "nghỉ" ➔ dung_lai).
- [G14] Slot `room`: số 100–999 viết bằng chữ số **hoặc đọc bằng chữ** ("hai trăm linh năm", "ba không bốn" ➔ 304) vì PhoASR viết số bằng chữ; không có số thì tra tên phòng trong bản đồ (vd "nội soi" ➔ 208). `department`: tên khoa viết thường theo bản đồ ("tiêu hóa"). `floor`: số ngay sau từ "tầng" (lấy lần xuất hiện đầu tiên).
- [G14] Thêm slot **`facility`** (key trong `facilities` của bản đồ, vd `nha_ve_sinh`) — ngoài 3 slot của G14.1 — để `tien_ich` biết người hỏi cần thang máy hay nhà vệ sinh; `slots` là dict tự do trong Mục 2.2 nên không đổi hợp đồng message. Nếu không muốn, bỏ slot này thì `tien_ich` sẽ luôn hỏi lại.
- [G14] `hospital_map.json` là dữ liệu bịa (`is_mock: true`): 13 khoa, 15 phòng, 12 tiện ích/quầy; tầng, số phòng, vị trí đều tự đặt. Phòng không có trong bản đồ ➔ tầng = chữ số đầu của số phòng (205 ➔ tầng 2).
- [G14] Câu trả lời chỉ chỉ đường, gọi nhân viên hoặc hỏi lại. `hoi_khoa` không có tên khoa (vd "đau bụng nên khám khoa nào") ➔ hỏi lại và gợi ý hỏi quầy tiếp đón, KHÔNG tự suy khoa từ triệu chứng (sẽ là lời khuyên y khoa). `bao_hiem`, `thanh_toan` chỉ chỉ quầy, không khẳng định chính sách (vd CCCD có thay thẻ BHYT được không).
- [G14] **Luật được viết dựa trên chính kịch bản** ➔ độ chính xác trên `text_ref` (100%) cao hơn thực tế; số liệu đáng tin hơn là độ chính xác trên kết quả STT (G13/G17).

## G15
- [G15] `npc.gd` là node con `Npc` của `Human` (Godot chỉ gắn 1 script/node, `human.gd` giữ nguyên). Khi NOTICE: lưu `walks`, đặt `walks = false`; khi `on_reply_shown()`, `reset()` hoặc dừng nói giữa chừng thì khôi phục.
- [G15] Node `Head` (Node3D tại cao 1.6 m, lệch 8 cm ra phía trước mặt) chứa `AudioStreamPlayer3D` tên `Voice`. Không gắn vào xương đầu (BoneAttachment) vì NPC đứng yên khi nói.
- [G15] Chưa có animation `talk` ➔ dùng `idle`. Chỉ có model người nam ➔ speaker B (khi có) dùng chung model.
- [G15] Robot cần cho NPC được truyền qua `setup(robot, state_fn)`; `state_fn` trả trạng thái robot lúc gọi. Chưa setup ➔ NPC không làm gì (scene G4/G10 không bị ảnh hưởng).
- [G15] `clips.json` chỉ được đọc khi NPC bắt đầu nói lần đầu (không đọc trong `_ready`), để máy chưa chạy G11 không báo lỗi ở mọi scene có Human. Clip không nạp được ➔ `push_error`, về IDLE và đặt cooldown `NPC_COOLDOWN_S` để không báo lỗi mỗi khung hình.
- [G15] Wav nạp bằng `load()` nếu đã import, không thì `AudioStreamWAV.load_from_file()` (thư mục voices bị gitignore nên có thể chưa import). Thư mục voices đổi được qua biến `voices_dir` (test dùng `user://test_voices`).
- [G15] Chọn clip ngẫu nhiên: lọc theo `speaker`, ưu tiên intent chưa dùng; dùng hết intent thì xóa danh sách và chọn lại. Danh sách clip sắp xếp theo tên trước khi chọn ➔ cùng seed cùng kết quả.
- [G15] Thêm signal `talk_started(clip_id)` (để robot vào LISTEN) và `talk_aborted(clip_id)` (robot rời xa khi NPC đang nói) ngoài `utterance_finished`. Dừng giữa chừng không tính lượt và không đặt cooldown.
- [G15] Ngưỡng "robot bỏ đi" dùng `>` (đúng 3.0 m chưa tính); ngưỡng bắt đầu dùng `≤ TALK_TRIGGER_DIST` như pseudocode.

## G16
- [G16] `Config.RobotState` thêm LISTEN, THINK, RESPOND sau ARRIVED (giá trị 3, 4, 5; các giá trị cũ giữ nguyên). Thêm hằng số Sim_Voice dùng phía Godot vào `config.gd` (`DATA_DIR`, `STT_MODEL_ID`, `SAMPLE_RATE` chỉ dùng phía Python nên không thêm).
- [G16] `main.gd` chỉ sửa đúng phần Mục 2.3 cho phép: ở LISTEN/THINK/RESPOND không gọi controller (cả khi có detection lẫn khi mất người), lệnh robot = (0, 0), log G9 vẫn ghi với v = omega = 0. Thêm `is_dialogue_state()` và `set_dialogue_state()`; phím R còn đặt lại NPC và hội thoại. Về ARRIVED thì controller chạy lại từ frame nhận diện sau.
- [G16] `DialogueManager` là con của Main, tìm NPC / SttClient / Subtitle qua `NodePath` export. utt_id tăng mỗi lượt và không reset khi nhấn R, để transcript muộn của lượt trước bị bỏ.
- [G16] Timeout, `error` của server (đúng utt_id), mất kết nối khi đang THINK, hoặc gửi không được (chưa kết nối) ➔ câu xin lỗi hiện `SUBTITLE_S` giây nhưng robot về ARRIVED và `npc.on_reply_shown()` **ngay** (theo pseudocode `show_sorry(); log(error); finish()`). Lỗi trong log: `timeout`, `stt disconnected`, `server: <message>`.
- [G16] Server không có intent (`response = null`) ➔ dòng "Robot:" hiện câu xin lỗi.
- [G16] Thêm signal `turn_completed(row)` trên DialogueManager (cùng nội dung dòng log) cho batch G17.
- [G16] Log hội thoại do `DialogueLogger` riêng ghi (không dùng RunLogger của G9) vì `hyp_text` có dấu phẩy cần ngoặc kép; mỗi lượt ghi và flush ngay. Số thực 4 chữ số thập phân, ô thiếu để trống.
- [G16] Phụ đề dùng `SystemFont` (Helvetica Neue / Arial / Segoe UI / Noto Sans / DejaVu Sans) để có đủ dấu tiếng Việt; dòng trả lời 24 px, dòng "Nghe được" 18 px màu xám nhạt; nền đen 62% bo góc, cách đáy 24 px.
- [G16] Ô góc nhìn chỉ hiện dòng STT khi scene có hội thoại (sau lần gọi `set_stt_connected` đầu tiên), đặt ngay trên dòng YOLO.

## G18 (nlu_tts_dialogue_prompt.md)
- [G18] **20 lớp intent, không phải 19**: bảng Mục 6 của `kich_ban_thu_am.md` thiếu `ho_tro_di_chuyen`, nhưng câu A_20 và luật G14 dùng nhãn này. Người dùng chọn giữ (2026-10-22) ➔ 19 intent + `unknown`. `nlu.config.INTENTS` = tập intent của G14, sắp chữ cái.
- [G18] Java: máy chưa có ➔ người dùng đồng ý cho cài `openjdk@17` qua Homebrew (keg-only). `segment.py` tự đặt `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home` nếu chưa có (pyjnius cần thư mục Home chứa `lib/server/libjvm.dylib`).
- [G18] VnCoreNLP: chỉ tải phần tách từ (`VnCoreNLP-1.2.jar`, `models/wordsegmenter/{vi-vocab,wordsegmenter.rdr}`) vào `models/VnCoreNLP/`, không tải POS/NER/parse. Đổi thư mục qua biến `VNCORENLP_DIR`. `py_vncorenlp` chdir vào thư mục model và không trả lại ➔ `segment.py` tự chdir lại.
- [G18] Tách từ trên văn bản đã `text_norm.normalize` (chữ thường, bỏ dấu câu), cho cả train, test và lúc chạy, để PhoBERT thấy cùng một dạng.
- [G18] `seed.csv` có thêm cột `kind` (`q` câu hỏi / `c` đề nghị, mệnh lệnh) để chọn từ đệm đầu và cuối câu phù hợp. Placeholder: `{department}`, `{room}`, `{room_name}`, `{facility}`; một loại placeholder mỗi câu.
- [G18] Giá trị slot: khoa = tên khoa viết thường + bí danh không chứa chữ "khoa" (bỏ khoa Cấp cứu vì A_26 "Khoa cấp cứu ở đâu" là `cap_cuu`); phòng = số phòng viết bằng chữ số, đọc theo hàng ("hai trăm linh năm") và đọc từng số ("hai không năm") vì STT viết số bằng chữ (G13); tên phòng = bí danh phòng trừ "kết quả", "xét nghiệm" (quá chung); tiện ích cho `tien_ich` = danh từ tự đặt ứng với 5 key trong `facilities` (thang máy, nhà vệ sinh, gửi xe, ghế chờ, căng tin), có kiểm tra key tồn tại.
- [G18] Biến đổi có quy tắc: đổi "tôi" ➔ em / mình / bác / cháu; bỏ chủ ngữ "tôi" đầu câu; từ đệm đầu câu (dạ, ờ, à, bạn ơi, robot ơi, cho X hỏi…) và cuối câu (ạ, vậy, nhỉ, nhé, nha, với…); chuyển "bạn ơi" ra cuối câu là phép đổi trật tự. Câu đã kết thúc bằng tiểu từ không thêm hậu tố.
- [G18] `unknown` có thêm 30 câu vô nghĩa ghép ngẫu nhiên từ 20 âm tiết (seed cố định).
- [G18] Pool đầy đủ (~54 nghìn câu) ➔ lấy tối đa 120 câu mỗi intent, **xoay vòng giữa các câu seed** để seed nào cũng có mặt ➔ chia 85/15 phân tầng ➔ thêm lỗi STT cho 30% câu train (câu lỗi là câu **thêm vào**, giữ câu gốc). Vì vậy train ~130 câu mỗi intent.
- [G18] Lọc rò rỉ so với **mọi câu trong `kich_ban_thu_am.md`** (cả B chưa thu âm) cộng `test_ref` và `test_stt`, không chỉ tập test, để tuân thủ "không đưa câu kịch bản vào train". So sánh trên văn bản đã chuẩn hóa.
- [G18] Chia train/val theo câu (đúng đặc tả), không theo nhóm seed ➔ câu val thường là biến thể của câu seed có trong train, nên **điểm val sẽ lạc quan**; số liệu đáng tin là trên test (G23).
- [G18] `test_ref` = 40 câu (40 clip `_r` của A, `ref_verified = true`). `test_stt` = 1440 dòng (40 clip × 36 điều kiện của lưới G13, file `reports/stt_eval_20261021_224132.csv`); có thêm cột `clip_id` (cả `test_ref`) để G23 tách theo điều kiện. Lỗi lớn của tập test: chỉ có 1 người nói, `dieu_chinh_am_luong`, `nhac_lai`, `unknown` chưa có câu test (là câu của B).
- [G18] Lỗi giả kiểu STT: bảng 23 cặp gần âm tự đặt (có "khám ➔ khá" thấy thật ở G13), bỏ dấu một chữ, xóa hoặc nhân đôi một từ ≤ 3 ký tự; mỗi câu 1–2 phép.

## G17
- [G17] Người dùng chọn **cách 1** (2026-10-22): `h_target` 0.75 / 0.80 / 0.85 thay cho 0.45 / 0.55 / 0.65 của đặc tả (các mức đó làm robot dừng ở 2.3–3.2 m, ngoài `TALK_TRIGGER_DIST` 2.0 m nên NPC không bao giờ nói). Làm bằng `tools/h_target_controller.gd` (kế thừa `Controller`, phóng chiều cao box theo tỉ lệ `Config.H_TARGET / h_target`), chỉ dùng trong batch; `controller.gd` không đổi.
- [G17] Mỗi episode: seed = chỉ số episode; clip theo vòng (intent sắp chữ cái, episode `e` lấy intent `e mod số intent`), gồm cả take `_r` và `_n`; điều kiện ồn xoay vòng `babble 20`, `babble 10`, `white 20`, `none`; `h_target` xoay vòng 3 mức. Speaker chỉ có A.
- [G17] Batch bỏ `RunLogger` và `DialogueLogger` của từng episode (không sinh 80 file), tự ghi `logs/dialogue_batch_<thời gian>.csv`. Episode "hoàn thành" = có `turn_completed` mà không có lỗi STT. `latency_ms` = thời gian thực từ `utterance_finished` của NPC đến `turn_completed` (lúc có phụ đề; từ G22 là lúc robot bắt đầu nói). Sau G22 thêm 7 cột TTS ở cuối, cột cũ giữ nguyên.
- [G17] WER trong báo cáo chỉ tính clip `ref_verified`; intent accuracy tính mọi lượt hoàn thành. So với G13: cùng clip, cùng noise/SNR, cột 1 m và 2 m.

## G19
- [G19] Không dùng `datasets`, `evaluate`, `Trainer` (chưa cài, cần thêm `accelerate`): vòng lặp torch thuần, AdamW, lịch tuyến tính có warmup 10%, kẹp gradient 1.0, không fp16. Tham số đúng G19.1.
- [G19] **Early stopping**: macro-F1 val bão hòa 1.0 từ epoch 2–3 (val là biến thể của câu seed có trong train, xem G18). Nếu chỉ tính "F1 tăng hẳn" thì checkpoint giữ lại là epoch 2 (loss 1.2, model chưa chắc chắn, ngưỡng tin cậy vô nghĩa). Đổi: **bằng F1 thì epoch có val loss thấp hơn được coi là cải thiện**. Lượt train đầu (luật cũ) bị dừng giữa chừng và chạy lại.
- [G19] Ngưỡng: các ngưỡng cho cùng macro-F1 cao nhất ➔ chọn ngưỡng gần 0.6 (điểm khởi đầu) nhất.
- [G19] `--repeat` train lần 2 cùng seed (không lưu) để ghi sai lệch vào `train_report.md`; MPS không tất định tuyệt đối.

## G20
- [G20] `IntentResult` mới ở `nlu/nlu.py` (intent, intent_conf, slots, source, top3), khác `voice.intent.IntentResult` của G14. Chế độ `rule` cũng chạy luật khẩn cấp trước (cùng thứ tự với `phobert`), rồi `voice.intent.classify`; ngưỡng của `rule` cố định 0.6 (khớp mức "khớp từ đơn" của G14), của `phobert` lấy `threshold.json`.
- [G20] Luật khẩn cấp = toàn bộ cụm mạnh và từ đơn của `cap_cuu` trong G14 (kể cả "ngã", "ngất", "xỉu"), khớp ➔ conf 1.0.
- [G20] Slot giữ thêm `facility` (key tiện ích trong bản đồ) như G14 vì mẫu câu `tien_ich`, `dang_ky_kham` cần nó. Số phòng chỉ thành slot khi có trong `rooms` của bản đồ (G14 chấp nhận mọi số 100–999).
- [G20] `target`: bản đồ không có id ➔ tự đặt `dept_<tên khoa không dấu>` (vd `dept_tim_mach`, khớp ví dụ G20.3) và `room_<số>`.
- [G20] Policy: `hoi_khoa`, `hoi_phong`, `dan_duong` có khoa hoặc phòng trong bản đồ ➔ `guide` (hoi_phong ưu tiên phòng, còn lại ưu tiên khoa); thiếu ➔ hỏi lại bằng "Dạ, anh chị muốn đến khoa nào ạ?", riêng `hoi_phong` dùng `ASK_ROOM` của G14 ("…phòng nào ạ?") cho hợp câu hỏi. **Mọi** lần hỏi lại (kể cả thiếu slot) khi `clarify_count ≥ MAX_CLARIFY` ➔ `call_staff`. `nhac_lai` không có câu trước ➔ câu chào hỏi chung của G14. `gap_nhan_vien` theo bảng là `answer` (câu G14 "đang gọi nhân viên"); có thể đổi sang `call_staff` khi làm RL.
- [G20] `clarify_count` và `last_response` do STT server giữ **theo từng kết nối WebSocket** (message `utterance` không có các trường này): `clarify` ➔ +1, action khác ➔ về 0; `repeat` không đổi `last_response`. Kết nối mới ➔ trạng thái mới.
- [G20] `transcript` luôn có thêm `action`, `target` (null khi server chạy không có G20). `stt_server` mặc định `--nlu rule`.

## G21
- [G21] **Nạp local (đọc mã nguồn vieneu 3.8.3, người dùng duyệt cách làm 2026-10-22):** model chính bằng tham số công khai `Vieneu(mode="v3turbo", backend="onnx", backbone_repo=VIENEU_DIR, onnx_dir=VIENEU_DIR/onnx_update)`. Codec: `OnnxV3LiteEngine` có `codec_dir` nhưng `V3TurboVieNeuTTS` không chuyển tham số này xuống ➔ `tts_engine.prepare_codec_cache` dựng `data/tts_cache/hf_hub/models--OpenMOSS-Team--MOSS-Audio-Tokenizer-Nano-ONNX/{refs/main, snapshots/local/*}` (symlink tới `models/MOSS-Audio-Tokenizer-Nano-ONNX`), đặt `HF_HUB_CACHE` + `HF_HUB_OFFLINE=1` trước khi import `huggingface_hub`. Không sửa thư viện, không copy file. Giọng có sẵn nằm trong gói (`vieneu/assets/voices_v3_turbo.json`, 25 giọng). Bản PyTorch của codec (`MOSS_CODEC_DIR`) không dùng.
- [G21] `vieneu` cài trong venv riêng `python/.venv-tts` (kéo theo gradio, onnxruntime…), chỉ để chạy `tts_server`, `pregen`, `pick_voice`. Test chạy ở venv chính với `FakeTTS`; `tts_engine` chỉ import `vieneu` trong `VieneuEngine`.
- [G21] fp32 (`onnx_update`); không dùng int8 (cần CPU có VNNI, Apple Silicon không có). Không thử PyTorch/MPS.
- [G21] `ROBOT_VOICE` **tạm** là "Ngọc Huyền" (nữ, Bắc, giọng đọc tự nhiên) chờ người dùng nghe `reports/voices/` (U4). Đổi giọng: sửa `tts/config.py` và `godot/scripts/config.gd` rồi chạy lại `pregen`.
- [G21] `text_for_tts`: số sau "phòng"/"phòng số" đọc từng chữ số; số khác ≤ 999 đọc theo hàng ("tầng 2" ➔ "tầng hai", "15" ➔ "mười lăm"); số bắt đầu bằng 0 đọc từng chữ số; viết tắt BHYT, CCCD, WC, X-quang, CT. Cache theo văn bản **sau** chuẩn hóa. Resample bằng `soxr` (đã có qua librosa). `MODEL_VERSION` gồm phiên bản gói, subfolder và phiên bản hậu xử lý.
- [G21] Kiểm tra "text rỗng / > 300 ký tự" trên văn bản đã bỏ khoảng trắng đầu cuối, trước chuẩn hóa đọc số. Lỗi: `text empty`, `text too long`, `voice not found: X`, `tts failed: <Exception>`, `tts busy`. Server nới giới hạn message WebSocket lên 8 MiB.
- [G21] "Ngắt mạng" kiểm bằng `HF_HUB_OFFLINE=1` (huggingface_hub báo lỗi thay vì tải nếu thiếu file); không rút mạng vật lý.

## G22
- [G22] Sửa thêm ngoài danh sách của prompt (cần để chạy được): `stt_client.gd` đọc thêm `action`, `target` (thiếu/null ➔ ""); `npc.gd` thêm `alternate_clip()`, `get_clips()`, `say_again()` (logic G15 cũ không đổi); test G16 đếm cột log đổi 14 ➔ 21 (7 cột G22 thêm ở cuối).
- [G22] `TtsClient` đặt `inbound_buffer_size` 8 MiB (mặc định 64 KiB không đủ cho ~300 KB base64).
- [G22] Có TTS: phụ đề hiện **khi âm thanh tới** và ẩn khi robot nói xong; dòng log và `turn_completed` phát lúc biết kết quả TTS. Âm thanh không báo xong sau thời lượng + 2 s ➔ coi như xong. Không có node `TtsClient`/`Robot/Head/Voice` ➔ hành vi G16 (chỉ phụ đề).
- [G22] clarify: robot nói xong ➔ NPC nói clip cùng `sentence_id` khác `take` chưa dùng trong lượt (`Npc.alternate_clip`), robot về LISTEN; tối đa `MAX_CLARIFY` lần; hết clip ➔ kết thúc lượt. Hiện mỗi câu có tối đa 2 take nên chỉ nói lại được 1 lần; câu chung `Cxx` của A chỉ có take `r` nên không nói lại.
- [G22] emergency: chữ đỏ "GỌI NHÂN VIÊN Y TẾ" giữa ô góc nhìn, giữ đến lượt sau hoặc phím R; guide: "Đang dẫn đến: khoa <tên>" / "phòng <số>" lấy từ slot (Godot không đọc bản đồ).
- [G22] Loa robot: `AudioStreamPlayer3D` `Voice` (script `robot_voice.gd`) con của `Head`, cùng kiểu suy giảm với NPC (INVERSE_DISTANCE, unit_size 1).
