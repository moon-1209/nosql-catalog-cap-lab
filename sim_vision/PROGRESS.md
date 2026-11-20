# Tiến độ

| Prompt | Trạng thái | Test | Ghi chú |
| :-- | :-- | :-- | :-- |
| G1 | Xong | GUT 3/3 pass | |
| G2 | Xong | pytest 36/36 pass | |
| G3 | Xong | GUT 9/9 pass | Ảnh render đạt |
| G4 | Xong | GUT 16/16 pass, gate 320/320 | Gate đạt 100% mọi mốc |
| G5 | Xong | GUT 27/27 pass | |
| G6 | Xong | GUT 41/41 pass | 5 Hz, nối lại 2.0 s |
| G7 | Xong | GUT 61/61 pass | |
| G8 | Xong | GUT 69/69 pass | H_TARGET đổi 0.65 ➔ 0.85 |
| G9 | Xong | GUT 78/78 pass | 148 dòng / 30 s |
| G10 | Xong | GUT 81/81, pytest 40/40 | Batch 10/10 |
| G11 | Xong | pytest voice 26/26 | 70 clip A; 17 file gốc bị ngắt sát cuối câu |
| G12 | Xong | pytest 118/118 (voice 78) | MPS, 250–360 ms/câu |
| G13 | Xong | pytest 138/138 | WER 16.3% (sạch 5.4%) |
| G14 | Xong | pytest 198/198 | Intent 100% trên text_ref, 97–99% trên STT (SNR 20, 1 m); recall cap_cuu 74% toàn lưới |
| G15 | Xong | GUT 94/94 | NPC quay, phát clip, dừng khi robot đi |
| G16 | Xong | GUT 115/115 | Một lượt hội thoại trọn vẹn trong cửa sổ thật |
| G17 | Xong | GUT 5, pytest 6 | 38/40 (95%), recall cap_cuu 3/3; 2 episode NPC không nói (sát ngưỡng 2.0 m) |
| G18 | Xong | pytest 223/223 | 20 lớp; train 2642, val 360, test_ref 40, test_stt 1440 |
| G19 | Xong (thiếu đo lặp lại) | pytest 9/9 | val macro-F1 1.0 (lạc quan), ngưỡng 0.6; nạp lại giống hệt |
| G20 | Xong | pytest 16/16 | `--nlu rule|phobert`, `action`/`target`; 83 câu trả lời, không lời khuyên y khoa |
| G21 | Xong | pytest 19/19 | VieNeu offline từ local; cache hit < 10 ms, miss ~2 s/câu (CPU) |
| G22 | Xong | GUT 135/135 | Robot nói qua loa 3D; TTS lỗi ➔ phụ đề 4 s |
| G23 | Xong một phần | pytest 279/279 | PhoBERT kém luật trên test (McNemar p 0.0014); e2e 38/40, trễ 1.2 s; WER khứ hồi 2.2% |

## G1: Bootstrap & Config (2026-10-21)

**Đã xong**
- Cấu trúc thư mục theo Mục 1: `godot/{scenes,scripts,assets,tests,tools,addons}`, `python/tests`, `logs/`.
- `godot/project.godot` (Forward+, bật plugin GUT), `scenes/main.tscn` rỗng.
- `godot/scripts/config.gd`: 19 hằng số Mục 2.1, `enum RobotState`, `state_name()`.
- GUT 9.7.1, `godot/tests/test_config.gd`.
- `python/requirements.txt` có ghim phiên bản; venv `python/.venv`.
- `.gitignore`, `ASSUMPTIONS.md`, `PROGRESS.md`, `godot/assets/CREDITS.md`.

**Kiểm chứng**
- [x] `godot --headless --import` và chạy scene chính 60 frame: không có ERROR/WARNING.
- [x] `pip install -r requirements.txt` chạy được.
- [x] GUT: `test_config.gd` 3/3 pass (23 assert).

**Chạy test**
```bash
cd sim_vision/godot
godot --headless -s addons/gut/gut_cmdln.gd -gconfig=res://.gutconfig.json
```

**Vấn đề tồn tại:** chưa có.

## G2: YOLO Server (2026-10-21)

**Đã xong**
- `python/protocol.py`: `parse_frame`, `build_detections`, `build_error`, `ProtocolError` (không phụ thuộc ultralytics).
- `python/detector.py`: interface `Detector`, `normalize_boxes`, `YoloDetector` (import ultralytics trễ).
- `python/yolo_server.py`: server WebSocket `127.0.0.1:8765`, `--model`, `--port`; suy luận qua `asyncio.to_thread`; mỗi client chỉ xử lý frame mới nhất.
- `python/send_image.py`: gửi ảnh thử. Test: `python/tests/` (FakeDetector, không gọi YOLO thật).

**Kiểm chứng**
- [x] `pytest python/tests`: 36/36 pass (JSON hỏng, thiếu trường, sai kiểu, JPEG hỏng, tọa độ chuẩn hóa, sắp conf, server không dừng sau lỗi, frame dồn chỉ xử lý frame mới nhất, thiếu model thoát mã ≠ 0).
- [x] YOLO thật: `bus.jpg` ➔ 3 người, conf 0.87/0.85/0.83, 34.1 ms; `zidane.jpg` ➔ 2 người, conf 0.83/0.83, 22.1 ms (CPU).
- [x] Model không tồn tại ➔ `ERROR: model file not found: ...`, exit 1, không tự tải. (Thử bằng đường dẫn không tồn tại thay vì xóa file thật của người dùng.)

**Chạy**
```bash
cd sim_vision/python
.venv/bin/python -m pytest tests
.venv/bin/python yolo_server.py --model yolov8n.pt
.venv/bin/python send_image.py <ảnh.jpg>
```

**Vấn đề tồn tại:** chưa có.

## G3: Căn phòng (2026-10-21)

**Đã xong**
- `godot/scenes/room.tscn`: phòng 8 × 6 × 3 m, gốc ở tâm sàn; sàn, tường, trần PBR (albedo + normal + roughness, thêm AO cho sàn và trần); cửa sổ ở tường bắc; nắng (`DirectionalLight3D`) và 2 đèn trần (`OmniLight3D`), đều bật bóng; `WorldEnvironment` SDFGI + SSAO + ACES; 4 đồ vật sát tường có `StaticBody3D` + collision.
- `godot/scripts/room.gd` (`class_name Room`): `get_free_position`, `get_furniture_footprints`, `distance_to_rect`, `is_clear`.
- Asset CC0 trong `godot/assets/`, nguồn và hướng dẫn tải lại ở `godot/assets/CREDITS.md`.
- `godot/tests/test_room.gd`.

**Kiểm chứng**
- [x] Render 4 góc nhìn (cửa sổ Godot thật, không headless): sàn và tường có vân, nắng qua cửa sổ tạo mảng sáng và bóng, đồ vật có bóng, không có mảng đen.
- [x] GUT 9/9 pass (gồm 100 lần gọi `get_free_position(0.5)`: đều nằm trong phòng và cách đồ vật ≥ 0.5 m).
- Lỗi tìm được nhờ test: ghế bành xoay 45° làm hộp collision lòi ra ngoài tường ➔ đã dời ghế vào trong.

**Vấn đề tồn tại**
- Ảnh hơi sáng (trần gần như trắng). Chưa chỉnh vì chưa biết ảnh hưởng tới YOLO; sẽ xem lại ở cổng kiểm tra G4.

## G4: Người tả thực (2026-10-21)

**Đã xong**
- Model Rocketbox `Male_Adult_06` (MIT) trong `godot/assets/models/human_m06/`; hướng dẫn tải từng bước và nguồn ở `godot/assets/CREDITS.md`.
- `godot/tools/extract_human_anims.gd` ➔ `anims/idle.res`, `anims/walk.res`.
- `godot/scenes/human.tscn` (`CharacterBody3D`, material PBR cho thân, đầu, tóc; capsule va chạm; `AnimationPlayer` thư viện `human/idle`, `human/walk`) và `godot/scripts/human.gd` (`walks`, `waypoints`, 0.5 m/s).
- `godot/tools/detect_gate.tscn` + `detect_gate.gd`; `godot/tests/test_human.gd`.

**Kiểm chứng**
- [x] Render 4 hướng: da, tóc, quần áo có texture, không có màu hồng/trắng do thiếu texture; chân chạm sàn; người cao ≈ 1.75 m.
- [x] GUT: 16/16 pass (thêm 7 test cho human: collision, animation, material, chiều cao, `step_towards`, waypoint, tốc độ đi 0.5 m/s).
- [x] Cổng nhận diện (YOLO thật, `YOLO_CONF` giữ 0.4, ngưỡng tính trúng 0.5): **20/20 ở cả 16 mốc**, `infer_ms` trung bình 27.2 ms (CPU).
  - Yêu cầu ≥ 90% ở 1–4 m với yaw 0°/45°: đạt 100%.
  - Yêu cầu ≥ 70% ở 2 m với yaw 90°/180°: đạt 100%.

`logs/detect_gate.csv`:

| distance_m | yaw_deg | hits/n | mean_top_conf |
| :-- | :-- | :-- | :-- |
| 1 | 0 / 45 / 90 / 180 | 20/20 cả 4 | 0.935 / 0.919 / 0.868 / 0.936 |
| 2 | 0 / 45 / 90 / 180 | 20/20 cả 4 | 0.925 / 0.908 / 0.845 / 0.931 |
| 4 | 0 / 45 / 90 / 180 | 20/20 cả 4 | 0.906 / 0.881 / 0.821 / 0.905 |
| 6 | 0 / 45 / 90 / 180 | 20/20 cả 4 | 0.899 / 0.872 / 0.792 / 0.897 |

**Chạy cổng kiểm tra**
```bash
cd sim_vision/python && .venv/bin/python yolo_server.py --model yolov8n.pt   # cửa sổ 1
cd sim_vision/godot && godot --path . res://tools/detect_gate.tscn           # cửa sổ 2
```

**Vấn đề tồn tại**
- Ảnh mẫu `d1_yaw0` (ảnh đầu tiên của lượt chạy) bị ngược sáng: người đứng sát tường tây, xa đèn. Vẫn nhận ra (conf 0.935), nhưng phần chính diện của người tối hơn ngoài đời thật.
- Gate đạt 100% vì cảnh đơn giản (1 người, nền sáng). Chưa thử khi người bị đồ vật che khuất một phần.

## G5: Robot, Camera & Ô góc nhìn (2026-10-21)

**Đã xong**
- `godot/scenes/robot.tscn` + `godot/scripts/robot.gd` (`set_command`, `get_camera_viewport`, `front_obstacle_distance`, differential drive bằng `move_and_slide`).
- `godot/scenes/view_overlay.tscn` + `godot/scripts/view_overlay.gd` (`show_detections`, vẽ box bằng `_draw` trên node `Boxes`).
- `godot/tests/test_robot.gd` (11 test).

**Kiểm chứng**
- [x] `set_command(0.3, 0.5)`: robot đi vòng tròn, khoảng cách xa nhất tới điểm xuất phát 1.197 m (lý thuyết 1.2 m).
- [x] Chạy `V_MAX` thẳng vào tường: dừng ở x = 3.738 (giới hạn 3.75), không xuyên tường.
- [x] Ô góc nhìn hiện đúng hình camera robot, ảnh thay đổi giữa các frame (không đứng hình); box, nhãn, trạng thái, chữ tiếng Việt hiển thị đúng.
- [x] GUT 27/27 pass.

**Vấn đề tồn tại**
- Test raycast ban đầu fail khi chạy chung với test khác: robot của test trước chưa kịp giải phóng nên `move_and_slide` đẩy robot mới lùi 0.35 m. Đã sửa bằng cách đặt robot và tường của test đó ở x = 50. Không phải lỗi của `robot.gd`.
- Camera người xem đặt ngoài phòng thì bị trần che ➔ G8 sẽ cho camera này bỏ qua lớp render của trần.

## G6: Vision Client (2026-10-21)

**Đã xong**
- `godot/scripts/vision_client.gd` (`class_name VisionClient`): `setup`, `parse_message`, signal `detections_received`, `connection_changed`; chụp 5 Hz, JPEG 0.8, base64; bỏ frame cũ/trễ; tự nối lại.
- `godot/tests/test_vision_client.gd` (14 test).

**Kiểm chứng**
- [x] GUT 41/41 pass.
- [x] Server thật + cảnh (người cách robot 3 m): nhận đúng 5 kết quả/giây (giây đầu là 4 vì mới kết nối), conf ~0.92, `infer_ms` 34–51 ms.
- [x] Tắt server ➔ `connection_changed(false)` ngay. Bật lại ➔ `connection_changed(true)` sau 2.04 s kể từ lệnh bật (tính cả thời gian nạp model), dưới 3 s.
- [x] Hết lượt chạy, `sent_at` còn 0 mục.

**Vấn đề tồn tại**
- Lần chạy kiểm chứng đầu tiên không nhận được kết quả nào: script dựng cảnh gọi `robot.get_camera_viewport()` trước khi robot `_ready` nên nhận null. Đã sửa `robot.gd` (xem ASSUMPTIONS [G6]). Scene bình thường (G8) không gặp lỗi này.

## G7: Controller (2026-10-21)

**Đã xong**
- `godot/scripts/controller.gd` (`class_name Controller`, `step`, `pick_target`), đúng thứ tự điều kiện của pseudocode G7.2.
- `godot/tests/test_controller.gd`: 9 ví dụ của bảng G7.3 + 11 test biên (cx = 0/1, h ≈ 0 kẹp `V_MAX`, omega luôn trong giới hạn, h = `H_TARGET`, cận dưới vùng trễ, `t_lost` = `LOST_TIMEOUT_S`, ARRIVED vừa mất dấu, |e| = `ALIGN_TOL`, bằng conf chọn box cao hơn, hàm thuần).

**Kiểm chứng**
- [x] GUT 61/61 pass (20 test controller).
- [x] Dò vết `cx=0.55, h=0.30`: e = 0.05 ➔ omega = −2.0 × 0.05 = −0.1; v = 1.5 × (0.65 − 0.30) = 0.525; |e| ≤ 0.25 nên giữ v ➔ khớp test.
- [x] Dấu omega: `omega = -K_ANG * e` (`controller.gd`). Người bên phải (cx > 0.5, e > 0) ➔ omega < 0 ➔ quay phải, đúng Mục 2.4. Kết hợp với G5 (omega > 0 làm `rotation.y` tăng, hướng trước lệch về −X, tức bên trái) ➔ cả chuỗi điều khiển đúng chiều.

**Vấn đề tồn tại:** chưa có.

## G8: Main Scene & An toàn (2026-10-21)

**Đã xong**
- `godot/scenes/main.tscn` (Room, Human, Robot, Controller, VisionClient, ViewerCamera, UI/ViewOverlay) — scene chạy chính của project.
- `godot/scripts/main.gd` (`class_name Main`): luồng `detections_received ➔ controller.step ➔ apply_safety ➔ robot.set_command`; `apply_safety` và `pick_start_positions` là hàm thuần; `@export seed`, `@export controller_path`; phím R/Esc; signal `cycle_completed` cho G9.
- `godot/tests/test_main.gd` (8 test).

**Kiểm chứng**
- [x] Bật server, chạy scene (seed 0, người cách 4.32 m): SEARCH (quay 0.5 rad/s) ➔ thấy người ở giây 8.4 ➔ APPROACH (quay thẳng rồi tiến) ➔ ARRIVED ở giây 21.2. Ô góc nhìn hiện box `person 0.92` và trạng thái.
- [x] Tắt server giữa chừng: lệnh về (0, 0), robot đứng yên trong 3 s (dịch chuyển 0.0000 m), trạng thái giữ nguyên, ô báo "YOLO: mất kết nối".
- [x] GUT 69/69 pass.

**Vấn đề tồn tại — CẦN NGƯỜI DÙNG QUYẾT ĐỊNH**
- Robot dừng (ARRIVED) ở **khoảng cách thật 2.21 m**, trong khi G10 chỉ tính là thành công nếu dừng trong khoảng **[0.8, 1.5] m**. Theo hình học, camera cao 1.2 m, FOV dọc 70°, người cao 1.75 m thì `h = H_TARGET = 0.65` ứng với khoảng 2.1–2.2 m. Muốn dừng ở 1.5 m thì cần `h` ≈ 0.80. Đây là mâu thuẫn giữa Mục 2.1 (`H_TARGET`), G5 (FOV 70°) và tiêu chí G10. Chưa sửa gì; sẽ hỏi trước khi làm G10.

## G9: Run Logger (2026-10-21)

**Đã xong**
- `godot/scripts/run_logger.gd` (`class_name RunLogger`): `open`, `log_row`, `flush`, `close`, `format_row`, `signed_angle_deg`; ghi đệm, flush mỗi 1 s và khi thoát.
- `main.tscn` thêm node `RunLogger`; `main.gd` thêm `build_log_row`, `human_angle_deg`.
- `godot/tests/test_run_logger.gd` (9 test).

**Kiểm chứng**
- [x] GUT 78/78 pass.
- [x] Chạy scene chính 30 s (seed 0) ➔ `logs/run_20261021_170133.csv`: 148 dòng (5.04 dòng/s), đủ 13 cột đúng thứ tự.
- [x] pandas: `true_distance_m` giảm đều 4.32 ➔ 2.21 m trong suốt APPROACH (64/64 bước không tăng). `corr(h, true_distance_m)` = −0.969, `corr(cx, true_angle_deg)` = −0.999. Dòng không có detection thì `conf/cx/h` trống.

**Vấn đề tồn tại**
- Vẫn là mâu thuẫn ở G8: ARRIVED ở 2.21 m, ngoài khoảng thành công [0.8, 1.5] m của G10.

## Đổi H_TARGET 0.65 ➔ 0.85 (2026-10-21)

Người dùng chọn đổi `H_TARGET` để G10 có thể đạt. Cập nhật config, file kế hoạch (Mục 2.1, bảng G7.3, dò vết G7.4) và test; GUT 78/78 pass.

Đo lại bằng chạy thật (seed 0, `logs/run_20261021_170425.csv`): ARRIVED ở **1.46 m** (trước đây 2.21 m), sát biên trên 1.5 m của G10. Khi người ở gần thì chân ra khỏi khung hình nên `h` tăng rất chậm (0.81 ở 1.63 m, 0.825 ở 1.55 m, 0.845 ở 1.46 m); APPROACH mất 14 s, phần cuối robot chỉ nhích chậm vì v = 1.5·(0.85 − h) rất nhỏ.

## G10: Test tổng thể & README (2026-10-21)

**Đã xong**
- `godot/tools/batch_run.tscn` + `batch_run.gd` (`class_name BatchRun`, hàm thuần `is_success`, `touches`, `format_summary_row`); `godot/tests/test_batch_run.gd`.
- `python/analyze_logs.py` + `python/tests/test_analyze_logs.py`.
- `README.md` (cài đặt, lấy model người, chạy server, chạy scene, test, batch, giải thích hằng số).

**Kiểm chứng**
- [x] Batch 10 lượt (seed 0–9): **10/10 thành công** (yêu cầu ≥ 9/10).
- [x] **0 va chạm với người** ở mọi lượt.
- [x] `mean_infer_ms` = **33.9 ms** trên CPU (yêu cầu < 100 ms).
- [x] Thời gian tới đích trung bình 18.65 s (13.97 – 23.55 s).
- [x] GUT 81/81, pytest 40/40.
- [ ] "Làm theo README từ máy sạch chạy được": **chưa kiểm**, mới chạy trên máy phát triển.

`logs/batch_summary.csv`:

| seed | success | time_to_arrive_s | final_distance_m | collisions | frames | mean_infer_ms |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 0 | true | 20.52 | 1.450 | 0 | 103 | 34.4 |
| 1 | true | 13.97 | 1.499 | 0 | 70 | 33.2 |
| 2 | true | 20.37 | 1.461 | 0 | 102 | 34.0 |
| 3 | true | 23.55 | 1.496 | 0 | 118 | 33.8 |
| 4 | true | 17.93 | 1.498 | 0 | 90 | 34.3 |
| 5 | true | 15.17 | 1.478 | 0 | 76 | 33.6 |
| 6 | true | 22.98 | 1.498 | 0 | 115 | 33.9 |
| 7 | true | 16.97 | 1.453 | 0 | 85 | 33.7 |
| 8 | true | 20.73 | 1.455 | 0 | 104 | 34.0 |
| 9 | true | 14.32 | 1.485 | 0 | 72 | 34.2 |

**Vấn đề tồn tại**
- **Biên an toàn mỏng:** cả 10 lượt dừng ở 1.45–1.50 m, 4 lượt ở 1.496–1.499 m, sát biên trên 1.5 m. Lý do: khi người ở gần thì chân ra khỏi khung hình nên `h` tăng rất chậm theo khoảng cách (xem `logs/h_vs_distance.png`). Chỉ cần nhiễu nhỏ (đổi model người, cao hơn/thấp hơn, đổi FOV) là có thể dừng ở > 1.5 m và bị tính là thất bại. Nếu cần biên rộng hơn: tăng `H_TARGET` lên ~0.88–0.90, hoặc đổi tiêu chí thành công. Chưa đổi gì, chờ người dùng quyết định.
- Phần cuối APPROACH chậm (v = 1.5·(0.85 − h) rất nhỏ khi h gần 0.85), chiếm phần lớn thời gian tới đích.
- Batch không chạy được ở chế độ headless (đã ghi trong README).

## Checklist quyết định (theo file kế hoạch)

| Bước | Tiêu chí | Kết quả |
| :-- | :-- | :-- |
| G1 | Project mở được, hằng số đúng Mục 2.1, GUT chạy | Đạt |
| G2 | Server đúng Mục 2.2, lỗi không làm dừng server, không tự tải model | Đạt |
| G3 | Phòng PBR, ánh sáng có bóng, `get_free_position` đúng | Đạt |
| G4 | Người tả thực, gate ≥ 90% tại 1–4 m, không hạ ngưỡng | Đạt (100% ở mọi mốc) |
| G5 | Robot kẹp vận tốc, ô góc nhìn đúng, box đúng tọa độ | Đạt |
| G6 | Bỏ frame cũ/trễ, message sai không crash, tự nối lại | Đạt |
| G7 | Đúng bảng ví dụ (theo H_TARGET 0.85), dấu omega đúng, hàm thuần | Đạt |
| G8 | Robot tìm và tiến lại gần, an toàn ghi đè, mất kết nối thì dừng | Đạt |
| G9 | CSV đủ cột, góc có dấu đúng, flush khi thoát | Đạt |
| G10 | ≥ 9/10 lượt thành công, không va người, README | 10/10, 0 va chạm; chưa thử README trên máy sạch |

# Sim_Voice (G11–G17)

## G11: Chuẩn bị dữ liệu & manifest (2026-10-21)

**Đã xong**
- `python/voice/config.py` (Mục 2.1 + `RAW_SUBDIR`, `SCRIPT_MD`), `transcripts.py`, `prepare_data.py`, `sync_voices.py`.
- Test `tests/voice/test_prepare_data.py` (26 test): đủ 30 + 30 + 10×2 câu kịch bản, regex tên (kể cả `Nam_Cxx`), resample 16 kHz mono, cắt im lặng giữ 200 ms, quá ngắn/rỗng/quá dài bị bỏ, cờ clipping, giải mã `.m4a` qua ffmpeg, idempotent, file nguồn đổi thì xử lý lại, `text_fixed` được ưu tiên, trùng `clip_id`, sync + `clips.json` không chứa text.

**Kiểm chứng**
- [x] `pytest tests/voice -k prepare`: 26/26 pass.
- [x] Dữ liệu thật: 70 file ➔ manifest 70 + skipped 0 = 70. Chạy lần 2: 0 file xử lý lại, kết quả giống hệt.
- [x] `missing.csv`: 90 dòng = 80 clip của B (chưa thu) + 10 `A_Cxx_n` (câu chung chỉ thu một lần).
- [x] Manifest: 40 `_r` (`ref_verified = true`), 30 `_n` (false); độ dài 1.75–10.36 s (trung vị 3.99 s); RMS −31.4 đến −20.1 dBFS; 0 clip bị rè.
- [~] Nghe thử: không nghe được bằng tai. Thay bằng đo năng lượng 50 ms đầu/cuối mỗi clip (trung vị −52.7 / −41.2 dB so với đỉnh). Ngoài ra nhận dạng thử A_07_r, A_25_r, A_07_n bằng PhoASR ra đủ câu.

**Vấn đề dữ liệu (cần người dùng xem)**
- 17 file gốc dừng ghi ngay khi vừa nói xong (50 ms cuối của file gốc chỉ thấp hơn đỉnh 8–24 dB, kịch bản yêu cầu im lặng 1 s): A_07_n, A_07_r, A_08_n, A_09_r, A_10_r, A_11_r, A_13_r, A_16_n, A_16_r, A_18_n, A_18_r, A_20_r, A_24_r, A_C01_r, A_C05_r, A_C06_r, A_C09_r. Không do bước cắt im lặng (bước này không cắt gì ở đuôi các file đó). Có thể mất một phần âm cuối; theo dõi ở G13.
- `transcripts_n_todo.csv` (30 dòng) chờ người dùng nghe và điền `text_fixed` (việc U2) — trước đó WER chỉ tính trên 40 clip `_r`.

## G12: STT server (2026-10-21)

**Đã xong**
- `voice/audio_sim.py` (`render`, `distance_gain`, `make_babble`, `fit_length`, `measured_snr_db`), `voice/transcriber.py` (`Transcriber`, `PhoWhisperTranscriber`, `FakeTranscriber`, `check_audio`, `pick_device`), `voice/stt_server.py`, `voice/send_utterance.py`.
- Test `tests/voice/test_stt_server.py` (52 test): gain theo khoảng cách; SNR đo lại ±0.5 dB (white 16 tổ hợp khoảng cách × SNR, babble, file); ví dụ 2 m ➔ 13.98 dB; `none` ➔ inf; cùng seed cùng kết quả; kẹp [−1, 1]; kiểm tra 16 kHz/mono/float32 và cắt > 30 s; parse message; clip không có; JSON hỏng; ồn không có; hàng chờ đầy ➔ "stt busy"; lỗi model ➔ error; log không chứa text; thiếu manifest ➔ exit 1.

**Kiểm chứng**
- [x] pytest toàn bộ 118/118 (G1–G10: 40, voice: 78).
- [x] Server thật trên **MPS** (Apple Silicon), beam 1: `A_07_r`, 1 m, không ồn ➔ "Phòng khám số hai trăm linh lăm đi đường nào?" — đúng câu, nhưng số đọc thành chữ (và "năm" ➔ "lăm").
- [x] `stt_ms` cho câu 1.75–3.84 s: 253–360 ms (mục tiêu < 1500 ms cho câu 3 s). Lần đầu sau khi load ~2.6 s, đã xử lý bằng chạy nháp lúc khởi động.
- [x] Ồn làm giảm chất lượng đúng hướng: A_07_r ở 3 m, SNR 5 (hiệu dụng −4.5 dB) ➔ "Hai mấy phòng khám số hai trăm năm mươi lăm." (babble), "…năm mươi liên hệ." (white).
- [x] Log server chỉ có `utt_id, clip_id, audio_s, stt_ms`; không dòng nào chứa nội dung câu.

**Lưu ý cho G13/G14:** PhoASR viết số bằng chữ ("hai trăm linh năm") ➔ cột `number_mismatch` của G13 sẽ bắt được; G14 cần đọc được số viết bằng chữ để lấy slot `room`.

## G13: Đánh giá WER offline (2026-10-21)

**Đã xong**
- `voice/text_norm.py` (`normalize`, `has_number_mismatch`), `voice/eval_stt.py` (lưới, cache, WER/CER bằng jiwer, bootstrap theo clip, bảng + 2 biểu đồ, cột intent khi có G14).
- Test `tests/voice/test_eval_stt.py` (20 test): normalize (dấu câu, hoa thường, NFC/NFD, khoảng trắng, giữ số); number_mismatch; WER = 0 khi ref = hyp; bootstrap chứa giá trị trung bình; bỏ clip chưa xác minh khỏi WER nhưng vẫn tính intent; cache trúng thì không gọi transcriber (đổi beams thì không trúng); lỗi một clip không dừng cả lượt; bảng SNR bỏ `none`; CLI `--fake` end-to-end.

**Kiểm chứng**
- [x] pytest 138/138.
- [x] `FakeTranscriber` trên dữ liệu thật (2520 dòng): WER = 0 mọi ô.
- [x] Chạy thật (2520 lượt nhận dạng, 14 phút trên MPS): WER tổng **16.3%** [13.1, 20.5] trên 40 clip `_r`; không ồn 5.4%.
  - Theo SNR: 30 dB 5.9% ➔ 20 dB 7.5% ➔ 10 dB 18.7% ➔ 5 dB 38.4%.
  - Theo khoảng cách: 0.5 m 6.8% ➔ 1 m 8.8% ➔ 2 m 18.7% ➔ 3 m 30.8%.
  - Theo loại ồn: none 5.4%, white 13.4%, babble 21.8%.
  - WER tăng đều khi SNR giảm và khi khoảng cách tăng ➔ `audio_sim` hoạt động đúng hướng.
- [x] Dò vết 3 clip WER cao nhất: `reports/stt_trace_notes.md`. Hai clip đầu do **cách viết số** (205 ➔ "hai trăm linh năm"), clip thứ ba do câu ngắn và nhầm "ngân" ➔ "ngưng".
- Báo cáo: `reports/stt_summary.md`, `reports/wer_vs_snr.png`, `reports/wer_vs_distance.png`; chi tiết `reports/stt_eval_20261021_224132.csv` (gitignore).

**Lưu ý:** babble đang ghép từ chính giọng A (chưa có giọng khác) ➔ khó hơn thực tế. WER `_n` chưa có vì `transcripts_n_todo.csv` chưa được sửa tay.

## G14: Intent & câu trả lời (2026-10-21)

**Đã xong**
- `voice/intent.py` (luật từ khóa theo thứ tự ưu tiên, khớp nguyên từ, cụm ghép, đọc số bằng chữ, slot department/room/floor/facility), `voice/hospital_map.json` (giả lập, `is_mock: true`, 13 khoa, 15 phòng, 12 quầy/tiện ích), `voice/responses.py`.
- Test `tests/voice/test_intent.py` (60 test): độ chính xác trên kịch bản + in ma trận nhầm lẫn; 5 ví dụ G14.2; khớp nguyên từ ("đâu" ≠ "đau", "nhi" ≠ "nhiều", "dẫn" trong "hướng dẫn"); 10 ca thứ tự ưu tiên; đọc số ("hai trăm linh năm", "ba không bốn", "chín mươi mốt"…); mọi khoa/phòng trong kịch bản có trong bản đồ; câu trả lời (ví dụ phòng 205, cap_cuu cố định, hỏi lại khi thiếu slot, không có lời khuyên y khoa).
- STT server tự dùng G14 (log khởi động không còn cảnh báo "intent module not available").

**Kiểm chứng**
- [x] pytest 198/198. Độ chính xác trên `text_ref`: **100%** (70/70 câu khác nhau) ≥ 95%.
- [x] `classify` trên hyp của G13 ở SNR 20, 1 m: babble **98.6%**, white **97.1%** (70 clip, cả `_r` và `_n`); không ồn 1 m 98.6%. STT làm giảm 1.4–2.9 điểm ở điều kiện này. Toàn lưới: `_r` 86.3%, `_n` 85.6%; 0.5 m 97.3% ➔ 3 m 71.9%.
- [x] Đọc toàn bộ câu trả lời của 70 câu kịch bản: chỉ chỉ đường / gọi nhân viên / hỏi lại; không có lời khuyên y khoa (test kiểm tra thêm danh sách cụm cấm).
- [!] **Recall `cap_cuu` toàn lưới chỉ 74.3%** (107/144) — STT nghe sai từ khóa ("cấp cứu" ➔ "cấp cũ", "khó thở" ➔ "khó khăn"). Đã ghi vào `reports/stt_trace_notes.md`; chưa sửa luật (tránh khớp theo dữ liệu đánh giá).

## G15: NPC quay lại và nói (2026-10-21)

**Đã xong**
- `godot/scripts/npc.gd` (`next_state`, `shortest_turn`, `yaw_towards`, `pick_clip`, `load_clips`, `load_voice`; tween quay mặt; phát clip; signal `talk_started`, `talk_aborted`, `utterance_finished`; `on_reply_shown`, `reset`).
- `human.tscn`: thêm `Head/Voice` (AudioStreamPlayer3D, INVERSE_DISTANCE, unit_size 1.0) và node `Npc`. `config.gd`: hằng số Sim_Voice.
- Test `godot/tests/test_npc.gd` (13 test): 4 ví dụ G15.3 + biên; quay 170° ➔ −170° là 20°; mọi cặp góc quay ≤ 180°; chọn clip theo speaker/intent và seed; tích hợp với `human.tscn`: NOTICE ➔ quay đúng hướng ➔ TALK ➔ phát xong ➔ WAIT_REPLY ➔ `on_reply_shown`; robot rời xa khi đang nói ➔ dừng phát, không gửi utterance; dừng/tiếp tục đi bộ; clip hỏng ➔ IDLE, không crash.

**Kiểm chứng**
- [x] GUT 94/94 (81 cũ + 13 mới). Audio phát xong và phát `finished` được cả khi chạy headless.
- [ ] Nghe âm 3D khi đi vòng quanh NPC: không nghe được bằng tai — cần người dùng thử (`AudioStreamPlayer3D` đặt ở đầu NPC, giảm âm theo khoảng cách nghịch đảo).

## G16: STT client & Dialogue manager (2026-10-21)

**Đã xong**
- `stt_client.gd` (`parse_transcript`, `build_utterance`, tự nối lại), `dialogue_manager.gd`, `dialogue_logger.gd`, `subtitle.gd` + `subtitle.tscn`. Sửa `main.gd` (giữ robot đứng yên ở LISTEN/THINK/RESPOND, R đặt lại hội thoại), `config.gd` (enum mở rộng), `view_overlay.gd` (dòng STT), `main.tscn`.
- Test `godot/tests/test_dialogue.gd` (21 test): parse transcript (ví dụ G16.3, null từ server thiếu G14, 12 ca lỗi, error của server); logic timeout; bỏ utt_id cũ; tích hợp trên `main.tscn` với STT giả: LISTEN ➔ THINK ➔ RESPOND ➔ ARRIVED, timeout ➔ xin lỗi, lỗi server, mất kết nối, robot đứng yên dù controller muốn quay, R đặt lại.

**Kiểm chứng**
- [x] GUT 115/115 (cũ và mới).
- [x] Cửa sổ thật, 2 server bật (seed 1): SEARCH ➔ APPROACH ➔ ARRIVED 1.50 m ➔ NPC quay (0.6 s) ➔ LISTEN ➔ THINK ➔ RESPOND ➔ ARRIVED. Clip A_06_n, hyp "Khoa tiêu hóa ở bệnh viện này ở từng máy." ➔ hoi_khoa ➔ "Dạ, khoa Tiêu hóa ở tầng 2, phòng 205. Mời anh chị đi theo tôi." Từ lúc NPC nói xong đến khi có phụ đề ~1.0 s (stt_ms 1007 khi chạy cùng Godot + YOLO). Phụ đề tiếng Việt hiển thị đúng dấu.
- [x] Tắt STT server (seed 2): robot trả lời "Xin lỗi, tôi chưa nghe rõ…", log `stt disconnected`, về ARRIVED, không treo. Ô góc nhìn hiện "STT: mất kết nối" màu đỏ ngay từ đầu (đã sửa: trước đó dòng này chỉ hiện sau lần kết nối đầu tiên). Bật lại server giữa chừng ➔ tự nối lại, lượt sau hoàn tất bình thường.

## G18: Dữ liệu intent & tách từ (2026-10-22)

**Đã xong**
- Cài `openjdk@17` (Homebrew), `py_vncorenlp`, tải RDRSegmenter vào `models/VnCoreNLP/`.
- `python/nlu/{config,vi_numbers,segment,asr_noise,build_dataset}.py`; `data/nlu/seed.csv` (100 câu, 5 mỗi intent, tự viết).
- `python -m nlu.build_dataset` ➔ `data/nlu/{train,val,test_ref,test_stt,leak_removed}.csv`, `stats.md`.
- Test `tests/nlu/test_nlu_dataset.py` (25 test): cache tách từ, đọc số, ghép đủ slot, chỉ dùng giá trị trong bản đồ, biến đổi có quy tắc, lọc rò rỉ, chia phân tầng, lấy mẫu đều theo seed, asr_noise cùng seed cùng kết quả, chạy trọn và dừng khi thiếu câu.

**Kiểm chứng**
- [x] pytest 223/223.
- [x] Đọc 2 lượt × 30 câu train ngẫu nhiên: 60/60 đúng nhãn. Lượt 1 thấy hậu tố chồng ("được không với", "nhé nha") ➔ sửa quy tắc hậu tố, chạy lại.
- [x] `leak_removed.csv`: 8 câu, đều đúng lý do: 7 biến thể của "cho tôi hỏi khoa tim mạch ở đâu" (= C01) và "nhà vệ sinh nam ở đâu ạ" (gần B_14 "nhà vệ sinh nữ ở đâu ạ", 0.913).
- [x] Mỗi intent ≥ 125 câu train (tối thiểu 60).
- [ ] U3: người dùng đọc 30 câu train ngẫu nhiên, sửa nhãn sai nếu có.

## G19: Fine-tune PhoBERT-base-v2 (2026-10-22)

**Đã xong**
- `python/nlu/train_phobert.py` (vòng lặp torch thuần, MPS), test đường ống 9 test (model Roberta nhỏ giả, 40 câu giả).
- `models_finetuned/phobert-intent/`: model, tokenizer, `label_map.json`, `threshold.json` (`conf_threshold` 0.6), `train_report.md`.

**Kiểm chứng**
- [x] Train offline 10 epoch × ~87 s; val macro-F1 1.0 từ epoch 2, val loss 0.0205 ở epoch 10 (checkpoint giữ lại). **Val lạc quan** vì là biến thể của câu seed có trong train (ASSUMPTIONS G18).
- [x] Ma trận nhầm lẫn val: không có câu sai, nên không có cặp nhầm nào để ghi. Cặp nhầm thật thấy ở test (G23): `hoi_phong` ➔ `tien_ich` ("… đi đường nào").
- [x] Nạp lại từ `PHOBERT_FT_DIR`: 100% cùng dự đoán, chênh lệch xác suất 0.
- [ ] Chạy lại cùng seed để đo sai lệch: lượt `--repeat` bị dừng theo yêu cầu người dùng. Hai lần train đầy đủ trước đó cho epoch 1 khác nhau nhẹ (val F1 0.95 / 0.91 / 0.94) ➔ MPS không tất định tuyệt đối. Lần đầu dừng giữa chừng làm mất model vì script chỉ lưu sau lượt 2; đã sửa để lưu ngay sau lượt 1.

## G20: NLU + Dialogue policy (2026-10-22)

**Đã xong**
- `python/nlu/{slots,nlu,policy,phobert_intent,dialogue}.py`; `stt_server.py` thêm `--nlu rule|phobert`, trường `action`, `target`, trạng thái hỏi lại theo kết nối.
- Test `tests/nlu/test_nlu_policy.py` (16 test, `FakeIntentModel`): luật khẩn cấp chạy trước PhoBERT, ngưỡng, từng dòng bảng policy, số phòng không có trong bản đồ, ví dụ G20.3, trạng thái clarify ➔ call_staff, stt_server trả đủ trường cũ + mới.

**Kiểm chứng**
- [x] pytest pass.
- [x] `stt_server --nlu phobert`, 5 clip (babble 20 dB, 1.5 m): A_25 ➔ cap_cuu/emergency; A_06 ➔ hoi_khoa/guide `dept_tieu_hoa`; A_10 ➔ khong_ho_tro/refuse; A_22 ➔ dieu_chinh_toc_do/adjust; **A_07 "phòng khám số hai trăm linh năm đi đường nào" ➔ tien_ich (sai)**, do seed `tien_ich` có "đi … lối nào" còn seed `hoi_phong` thiếu kiểu câu này.
- [x] In hết câu trả lời có thể có (`reports/robot_responses.md`, 83 câu): chỉ chỉ đường / gọi nhân viên / hỏi lại / từ chối; số phòng đều có trong bản đồ (test kiểm tra).
- [ ] U5: người dùng duyệt `reports/robot_responses.md`.

## G21: TTS server VieNeu-TTS v3 Turbo (2026-10-22)

**Đã xong**
- Đọc mã nguồn `vieneu` 3.8.3 ➔ cách nạp local (ASSUMPTIONS G21), người dùng duyệt cách vòng qua cho codec.
- `python/tts/{config,text_for_tts,tts_engine,tts_server,pregen,pick_voice}.py`; venv riêng `.venv-tts`.
- Test `tests/tts/test_tts.py` (19 test, `FakeTTS`): đọc số / viết tắt, cache hit/miss, resample 24 kHz, RMS −20 dBFS ±1, 100 ms im lặng, PCM đúng độ dài, text rỗng / quá dài / sai giọng, hàng chờ đầy ➔ `tts busy`, engine lỗi, dựng cache codec.

**Kiểm chứng**
- [x] `HF_HUB_OFFLINE=1`: server khởi động (nạp model ~5 s, 25 giọng) và tổng hợp được; không có request tải mạng.
- [x] `tts_ms` cache miss: câu 20 từ 2477 ms; `pregen` 83 câu trung bình 1982 ms (0.5–5.3 s), cùng lúc đang train PhoBERT trên MPS ➔ số thật khi máy rảnh có thể thấp hơn. Cache hit 0.8–7 ms.
- [x] `pregen.py`: 83/83 câu đã có trong `data/tts_cache` (giọng tạm "Ngọc Huyền").
- [ ] U4: người dùng nghe `reports/voices/*.wav` (25 giọng) và chọn `ROBOT_VOICE`; nghe 10 câu trả lời (đọc đúng dấu, số phòng rõ).

## G22: Robot nói trong Godot (2026-10-22)

**Đã xong**
- `godot/scripts/tts_client.gd` (`parse_audio`, `pcm16_to_stream`, tự nối lại, bộ đệm 8 MiB), `robot_voice.gd` (`Robot/Head/Voice`); cập nhật `dialogue_manager.gd`, `view_overlay.gd` (dòng TTS, cảnh báo đỏ, "Đang dẫn đến"), `config.gd`, `stt_client.gd` (action/target), `npc.gd` (nói lại), `dialogue_logger.gd` (7 cột), `main.tscn`, `robot.tscn`.
- Test `godot/tests/test_tts_dialogue.gd` (15 test): parse_audio (đúng + 10 lỗi), 9600 byte ➔ 0.2 s, loa ở đầu robot, lượt có TTS (bỏ audio utt cũ, phụ đề đến khi nói xong), TTS timeout, TTS tắt ➔ phụ đề 4 s + `tts_error = disconnected`, lỗi server, clarify ➔ NPC nói lại take khác, hết take ➔ kết thúc, emergency ➔ chữ đỏ.

**Kiểm chứng**
- [x] GUT 135/135 (120 cũ + 15 mới).
- [x] Batch 40 episode với 3 server thật (YOLO, STT `--nlu phobert`, TTS): robot trả lời thành tiếng, 38/38 lượt hoàn thành có âm thanh (không lỗi TTS, cache hit 100%).
- [x] **Sửa sau phản hồi người dùng** ("không nghe robot nói, NPC nhỏ"): (1) batch cũ kết thúc episode ngay khi audio tới nên cắt mất tiếng robot ➔ chờ robot nói xong (tối đa 15 s); (2) tai ở camera góc phòng cách 3–7 m, `unit_size` 1 m làm giảm 10–17 dB, clip gốc RMS −25.6 dBFS ➔ `unit_size` 5 m cho NPC và robot, NPC +6 dB (test G15 cập nhật).
- [x] Nhánh clarify chạy trong batch thật (A_05_n "đau bụng nên khám khoa nào" ➔ robot hỏi lại ➔ NPC nói lại); phát hiện batch ghi đè mốc thời gian ➔ độ trễ âm ở 1 episode, đã sửa batch và bỏ giá trị âm khi phân tích.
- [ ] Cửa sổ thật: tắt TTS server giữa chừng ➔ chỉ phụ đề (đã kiểm bằng GUT, chưa thử bằng tay); nghe âm lượng sau khi chỉnh (người dùng).

## G17: Batch hội thoại & báo cáo (2026-10-22)

**Đã xong**
- `godot/tools/dialogue_batch.{gd,tscn}`, `tools/h_target_controller.gd`, `python/voice/analyze_dialogue.py`, README mục 6. Test: GUT `test_dialogue_batch.gd` (5), pytest `test_analyze_dialogue.py` (6).
- Batch 40 episode (`logs/dialogue_batch_20261022_012217.csv`, chạy cùng TTS và NLU PhoBERT), `reports/dialogue_summary.md`.

**Kiểm chứng**
- [x] 38/40 = **95.0%** hoàn thành (đạt ngưỡng sát). 2 episode `episode timeout` không phải lỗi code STT/TTS: dò vết (`ep 6`, `ep 11` chạy lại riêng đều xong lượt, muộn). ep 6 (h_target 0.75) robot dừng ở **2.00 m, đúng ngưỡng `TALK_TRIGGER_DIST`** ➔ trong batch nhiều khả năng dừng ở 2.01 m nên NPC không nói. Mức 0.75 cho khoảng cách TB 1.97 m, quá sát ngưỡng; đề xuất 0.77 hoặc nới ngưỡng 2.1 m (chưa sửa, chờ người dùng). ep 11: chưa tái hiện.
- [x] Recall `cap_cuu` báo riêng: **3/3**; không lượt nào bỏ sót.
- [x] WER (20 lượt ref_verified) 7.2% [2.3%, 14.4%]; theo cặp noise/SNR nằm quanh cột 1 m – 2 m của G13 (babble 10 dB: 14.5% vs 4.2% / 18.1%), dao động lớn vì mỗi ô 4–6 lượt. Intent accuracy 92.1%. NPC nói xong ➔ robot bắt đầu nói: TB 1212 ms, p95 1476 ms.

## G23: So sánh luật và PhoBERT & batch đầu cuối (2026-10-22)

**Đã xong**
- `python/nlu/eval_nlu.py`, `python/tts/eval_tts_roundtrip.py`, `python/voice/analyze_e2e.py`, README mục 7; test `tests/nlu/test_eval_g23.py` (6).
- `reports/nlu_compare.md` (+ `.csv`, `nlu_f1_vs_snr.png`), `reports/tts_roundtrip.md`, `reports/e2e_summary.md`.

**Kết quả**
- test_ref (40 câu): luật 100% / F1 1.000; PhoBERT 92.5% / F1 0.964 [0.907, 1.000]; McNemar b 3, c 0, p 0.25.
- test_stt (1440): luật 86.3% / F1 0.917; PhoBERT 83.8% / F1 0.880; McNemar b 78, c 42, **p 0.0014 ➔ luật tốt hơn có ý nghĩa**. PhoBERT ít hỏi lại hơn (clarify 4.5% vs 12.1%), recall cap_cuu 77.8% vs 76.4% (luật khẩn cấp chung). Ở 5 dB và 10 dB PhoBERT gần bằng / nhỉnh accuracy.
- Lỗi PhoBERT lớn nhất: `hoi_phong` ➔ `tien_ich` (61 lượt STT; 2/3 lỗi test_ref) với câu "… đi đường nào": seed `hoi_phong` thiếu kiểu câu này còn seed `tien_ich` có "đi … lối nào". Theo G23.2 không sửa dựa trên test; sửa sẽ là bổ sung seed (G18) rồi train lại.
- NLU: luật 0.8 ms, PhoBERT 10.6 ms TB / 13.8 ms p95 trên test_stt (36.6 ms TB trên test_ref do lần chạy đầu của JVM/MPS).
- TTS khứ hồi: WER nguyên văn 18.0% nhưng chủ yếu do STT viết số bằng chữ số; **sau khi đổi số sang chữ 2.2%**, 60/83 câu đúng hoàn toàn. Lỗi nghe hay gặp: "Mời" ➔ "mười/người/ngồi".
- E2E 40 episode: 95% hoàn thành; action: answer 24, adjust 5, emergency 3, guide 3, clarify 2, refuse 1; độ trễ STT 1122 ms, TTS 3 ms (cache), NLU + mạng + khung hình 88 ms.

**Kiểm chứng**
- [x] Recall cap_cuu = 1.0 ở cả 2 cách trên test_ref (2 câu).
- [x] Cùng số câu cho luật và PhoBERT (40 / 1440).
- [x] test_stt thấp hơn test_ref ở cả 2 cách.
- [x] Batch ≥ 95% (38/40).
