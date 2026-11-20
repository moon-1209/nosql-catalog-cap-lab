# Hướng dẫn cài đặt và chạy: robot dẫn đường bệnh viện (Sim_Vision + giọng nói)

Tài liệu cho các thành viên trong nhóm: cài model, chuẩn bị dữ liệu, chạy mô phỏng có hội thoại bằng giọng nói, và những gì đã làm tới ngày 2026-10-22. Chi tiết từng bước kỹ thuật nằm ở `sim_vision/README.md`, `sim_vision/PROGRESS.md` (kết quả kiểm chứng) và `sim_vision/ASSUMPTIONS.md` (các giả định, quyết định).

## 1. Hệ thống làm gì

Trong Godot có một căn phòng, một người (NPC) và một robot. Robot dùng camera + YOLO tìm người và tiến lại gần. Khi robot tới đủ gần (≤ 2 m), NPC quay sang và **hỏi bằng giọng thu âm thật**. Robot nghe, hiểu câu hỏi và **trả lời thành tiếng**.

```
camera robot ──▶ YOLO server (8765) ──▶ robot tìm và tiến tới người
NPC nói (clip thu âm) ──▶ STT server (8766): trộn ồn theo khoảng cách ➔ PhoASR-whisper-small ➔ văn bản
                                    ➔ NLU: luật khẩn cấp ➔ PhoBERT (hoặc luật) ➔ slot từ bản đồ bệnh viện
                                    ➔ policy: chọn câu trả lời mẫu / hỏi lại / gọi nhân viên
Godot ──speak──▶ TTS server (8767): VieNeu-TTS v3 Turbo ➔ âm thanh ➔ loa trên đầu robot + phụ đề
```

Mọi model chạy **trên máy, không cần mạng** sau khi đã tải về.

## 2. Yêu cầu

| Thứ cần có | Phiên bản đã thử | Ghi chú |
| :-- | :-- | :-- |
| Godot | 4.7.2 (≥ 4.3) | Cần GPU Vulkan/Metal; batch không chạy được `--headless` |
| Python | 3.12 | Hai venv: chính và TTS (mục 3) |
| Java | OpenJDK 17 | Cho bộ tách từ VnCoreNLP (PhoBERT cần câu đã tách từ) |
| ffmpeg | bất kỳ | Đọc file ghi âm `.m4a` |
| Dung lượng | ~4 GB cho model | Xem bảng mục 4 |

macOS (Apple Silicon) đã thử; STT và PhoBERT chạy trên GPU qua MPS, TTS chạy trên CPU.

## 3. Cài môi trường

Mọi lệnh Python chạy trong `sim_vision/python/`.

```bash
cd sim_vision/python

# venv chính: YOLO, STT, PhoBERT, đánh giá, test
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# venv riêng cho TTS (gói vieneu kéo theo gradio, onnxruntime... tách ra để không đụng venv chính)
python3.12 -m venv .venv-tts
.venv-tts/bin/pip install vieneu==3.8.3 websockets

# Java cho VnCoreNLP (macOS). Bản Homebrew là "keg-only", code tự tìm ở đường dẫn dưới.
brew install openjdk@17 ffmpeg
```

Nếu Java ở chỗ khác (Linux, Windows), đặt biến `JAVA_HOME` trỏ tới thư mục JDK có `lib/server/libjvm.*`. Mặc định code dùng `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home`.

## 4. Tải model

Tất cả đặt trong `models/` ở gốc repo. File nặng (`*.safetensors`, `*.bin`, `*.onnx`, `*.data`, `*.npz`, `*.gguf`) đã bị gitignore, **mỗi người tự tải**. Cách tải: `hf download` (có sẵn trong venv chính, gói `huggingface_hub`).

| Thư mục trong `models/` | Nguồn | Dung lượng | Dùng cho |
| :-- | :-- | --: | :-- |
| `yolov8n/yolov8n.pt` | Ultralytics YOLOv8n | 6 MB | Tìm người (đã có trong repo nhóm) |
| `PhoASR-whisper-small` | `Qualcomm-AI-Research/PhoASR-whisper-small` | 930 MB | STT |
| `PhoBert-base-v2` | `vinai/phobert-base-v2` | 520 MB | Model gốc để fine-tune NLU |
| `VnCoreNLP` | GitHub `vncorenlp/VnCoreNLP` (chỉ phần tách từ) | 27 MB | Tách từ cho PhoBERT |
| `Vie-neu-v3-turbo` | `pnnbao-ump/VieNeu-TTS-v3-Turbo` | 2.0 GB | TTS (dùng thư mục con `onnx_update`) |
| `MOSS-Audio-Tokenizer-Nano-ONNX` | `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX` | 86 MB | Codec âm thanh của VieNeu (bản dùng trên Mac/CPU) |
| `MOSS-Audio-Tokenizer-Nano` | `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano` | 84 MB | Bản PyTorch của codec, chỉ cần khi chạy VieNeu trên GPU NVIDIA; **không bắt buộc** |

```bash
cd <gốc repo>
HF=sim_vision/python/.venv/bin/hf
$HF download Qualcomm-AI-Research/PhoASR-whisper-small --local-dir models/PhoASR-whisper-small
$HF download vinai/phobert-base-v2                     --local-dir models/PhoBert-base-v2
$HF download pnnbao-ump/VieNeu-TTS-v3-Turbo            --local-dir models/Vie-neu-v3-turbo
$HF download OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX --local-dir models/MOSS-Audio-Tokenizer-Nano-ONNX

# VnCoreNLP: chỉ jar + 2 file tách từ (không cần POS/NER/parse)
D=models/VnCoreNLP; B=https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master
mkdir -p $D/models/wordsegmenter
curl -fL -o $D/VnCoreNLP-1.2.jar $B/VnCoreNLP-1.2.jar
curl -fL -o $D/models/wordsegmenter/vi-vocab $B/models/wordsegmenter/vi-vocab
curl -fL -o $D/models/wordsegmenter/wordsegmenter.rdr $B/models/wordsegmenter/wordsegmenter.rdr
```

YOLO server đọc `sim_vision/python/yolov8n.pt`, là symlink tới model trong `models/`:

```bash
ln -s ../../models/yolov8n/yolov8n.pt sim_vision/python/yolov8n.pt
```

Kiểm tra sau khi tải:
- `models/PhoASR-whisper-small/model.safetensors` phải có (lần đầu tải bị đứt mạng và thiếu đúng file này; tải lại nếu thiếu).
- `models/Vie-neu-v3-turbo/onnx_update/vieneu_prefill.onnx` phải có.
- Mạng chập chờn khi tải file lớn: chạy lại đúng lệnh `hf download`, nó tải tiếp phần còn thiếu.

**Model tự tạo (không tải):** `models_finetuned/phobert-intent/` là PhoBERT đã fine-tune, sinh ra ở mục 6 (khoảng 15 phút trên Mac M-series). Thư mục này cũng bị gitignore.

### Vì sao VieNeu cần làm thêm một bước

Thư viện `vieneu` đọc được model chính từ thư mục local, nhưng **không cho truyền đường dẫn codec local** (tham số có ở tầng trong nhưng lớp ngoài không chuyển xuống), nên mặc định nó sẽ đòi tải codec từ Hugging Face. Code của mình (`tts/tts_engine.py`) tự tạo một thư mục cache Hugging Face giả ở `data/tts_cache/hf_hub/` gồm các symlink trỏ tới `models/MOSS-Audio-Tokenizer-Nano-ONNX`, rồi bật chế độ offline. **Không cần làm gì bằng tay**, chỉ cần tải đúng thư mục codec ONNX như bảng trên.

## 5. Dữ liệu giọng nói

- File ghi âm đặt ở `data/raw/real_voice/`, tên `A_07_r.m4a` (người A, câu 07, lần đọc `r` = đọc đúng kịch bản, `n` = nói tự nhiên). `Nam_C01.wav` được hiểu là `A_C01_r`. Kịch bản: `docs/kich_ban_thu_am.md`. Hiện **mới có 70 file của giọng A (nam)**; giọng B (nữ) chưa thu.
- **Đây là dữ liệu cá nhân:** không đưa lên dịch vụ ngoài, không commit file âm thanh; log của server không ghi nội dung câu nói.
- Không sửa file trong `data/raw/`; mọi thứ sinh ra nằm ở `data/processed/`.

```bash
cd sim_vision/python
.venv/bin/python -m voice.prepare_data    # ➔ data/processed/wav (16 kHz) + manifest.csv
.venv/bin/python -m voice.sync_voices     # ➔ godot/assets/voices (+ clips.json cho NPC)
```

`data/processed/transcripts_n_todo.csv`: các clip nói tự nhiên (`_n`) cần người nghe và ghi lại câu thật vào cột `text_fixed`; chưa ghi thì clip đó không được tính WER.

## 6. Chuẩn bị NLU và giọng robot (làm một lần)

```bash
cd sim_vision/python
.venv/bin/python -m nlu.build_dataset        # data/nlu/{train,val,test_ref,test_stt}.csv từ data/nlu/seed.csv
.venv/bin/python -m nlu.train_phobert        # models_finetuned/phobert-intent (~15 phút, 10 epoch)
.venv-tts/bin/python -m tts.pick_voice       # 25 giọng mẫu ➔ sim_vision/reports/voices/*.wav
.venv-tts/bin/python -m tts.pregen           # sinh sẵn giọng cho 83 câu trả lời ➔ data/tts_cache (~3 phút)
```

- `build_dataset` cần kết quả STT của G13 (`sim_vision/reports/stt_eval_*.csv`); thiếu thì chạy `python -m voice.eval_stt` trước (lâu, dùng GPU).
- **Câu train là câu sinh ra** từ 100 câu mẫu viết tay (`data/nlu/seed.csv`) ghép với tên khoa/phòng trong bản đồ. Không có câu nào lấy từ kịch bản thu âm; câu gần giống câu kịch bản bị lọc bỏ (`data/nlu/leak_removed.csv`).
- Đổi giọng robot: sửa `ROBOT_VOICE` ở **cả** `sim_vision/python/tts/config.py` và `sim_vision/godot/scripts/config.gd`, rồi chạy lại `tts.pregen`. Hiện tạm dùng "Ngọc Huyền".

## 7. Chạy mô phỏng (4 cửa sổ terminal)

```bash
# 1. YOLO
cd sim_vision/python && .venv/bin/python yolo_server.py
# 2. STT + NLU (--nlu phobert cần mục 6; --nlu rule dùng bộ luật, không cần PhoBERT)
cd sim_vision/python && .venv/bin/python -m voice.stt_server --nlu phobert
# 3. TTS
cd sim_vision/python && .venv-tts/bin/python -m tts.tts_server
# 4. Godot
cd sim_vision/godot && godot --path .
```

Lần đầu mở project Godot: `godot --headless --import` trong `sim_vision/godot`.

Trên màn hình:
- Ô góc phải là camera robot, có trạng thái robot (`SEARCH`, `APPROACH`, `ARRIVED`, `LISTEN`, `THINK`, `RESPOND`) và 3 dòng `YOLO / STT / TTS: đã kết nối`.
- Phụ đề dưới màn hình: "Nghe được: …" và "Robot: …".
- Câu cấp cứu ➔ chữ đỏ "GỌI NHÂN VIÊN Y TẾ". Câu hỏi đường ➔ "Đang dẫn đến: khoa …" (chưa dẫn đường thật; phần đó làm ở giai đoạn RL).
- Phím **R** đặt lại vị trí ngẫu nhiên, **C** đổi giữa 3 góc nhìn camera (FOLLOW sau lưng robot, TOP_DOWN toàn cảnh từ trên cao, LOBBY sảnh tiếp đón), **Esc** thoát.
- Tắt server nào thì robot vẫn chạy: mất STT ➔ robot xin lỗi; mất TTS ➔ chỉ hiện phụ đề 4 giây. Bật lại server thì tự nối lại.

## 8. Chạy batch và xem báo cáo

```bash
# Cần đủ 3 server như mục 7
cd sim_vision/godot && godot --path . res://tools/dialogue_batch.tscn      # 40 episode, ~25 phút
cd ../python
.venv/bin/python -m voice.analyze_dialogue     # reports/dialogue_summary.md
.venv/bin/python -m voice.analyze_e2e          # reports/e2e_summary.md
.venv/bin/python -m nlu.eval_nlu               # reports/nlu_compare.md: luật vs PhoBERT trên tập test
.venv/bin/python -m tts.eval_tts_roundtrip     # reports/tts_roundtrip.md: giọng robot có dễ nghe không
```

Đừng chạy train PhoBERT cùng lúc với batch: cùng dùng GPU nên độ trễ STT đo được sẽ sai.

## 9. Test

```bash
cd sim_vision/python && .venv/bin/python -m pytest          # 279 test, không gọi model thật
cd sim_vision/godot && godot --headless -s addons/gut/gut_cmdln.gd -gconfig=res://.gutconfig.json   # 142 test pass
```

## 10. Những gì đã làm

Theo 3 file kế hoạch trong `docs/PROMPT/`: `godot_robot_yolo_prompt.md` (G1–G10), `godot_npc_stt_prompt.md` (G11–G17), `nlu_tts_dialogue_prompt.md` (G18–G23).

| Bước | Nội dung | Kết quả chính |
| :-- | :-- | :-- |
| G1–G10 | Phòng, người, robot, YOLO server, bộ điều khiển, an toàn, log, batch | Robot tới gần người 10/10 lượt |
| G11 | Chuẩn hóa 70 file ghi âm (16 kHz, cắt im lặng, manifest) | 17 file gốc bị cắt sát cuối câu |
| G12 | STT server PhoASR-whisper-small, trộn ồn theo khoảng cách và SNR | 250–360 ms/câu khi máy rảnh |
| G13 | Đánh giá STT trên lưới ồn × khoảng cách | WER 16.3%, sạch 5.4%, 5 dB 38% |
| G14 | Intent bằng luật từ khóa + câu trả lời mẫu + bản đồ bệnh viện **giả lập** | Đúng 100% câu chuẩn |
| G15–G16 | NPC quay sang hỏi; robot nghe, nghĩ, trả lời bằng phụ đề | Một lượt trọn vẹn trong cửa sổ thật |
| G17 | Batch hội thoại 40 episode | Hoàn thành 95% |
| G18 | Dữ liệu intent (20 lớp) từ câu mẫu, tách từ VnCoreNLP | Train 2642 câu, test 40 + 1440 câu |
| G19 | Fine-tune PhoBERT-base-v2 | Val F1 1.0 (lạc quan, val gần giống train) |
| G20 | NLU: luật khẩn cấp ➔ PhoBERT ➔ slot; policy trả lời an toàn | 83 câu trả lời có thể có, không có lời khuyên y khoa |
| G21 | TTS server VieNeu v3 Turbo, offline, có cache | Cache < 10 ms, câu mới ~2 s (CPU) |
| G22 | Robot nói qua loa 3D trên đầu; hỏi lại, cảnh báo cấp cứu | Robot nói thành tiếng trong mô phỏng |
| G23 | So sánh luật và PhoBERT; độ dễ nghe; batch đầu cuối | Xem dưới |

**Kết quả đáng chú ý (G23):**
- NLU trên câu STT có ồn (1440 câu): **luật 86.3%, PhoBERT 83.8%**, luật tốt hơn có ý nghĩa thống kê. PhoBERT ít phải hỏi lại hơn và ngang luật ở mức ồn nặng. Lỗi lớn nhất của PhoBERT: "phòng … đi đường nào" bị hiểu là hỏi tiện ích, vì câu mẫu thiếu kiểu câu này.
- Câu cấp cứu: luật khẩn cấp luôn chạy trước PhoBERT; nhận đúng 100% câu chuẩn nhưng chỉ ~77% khi STT nghe sai từ khóa ("cấp cứu" ➔ "cấp cũ").
- Giọng robot: đưa 83 câu robot nói qua STT, chỉ **2.2%** số từ bị nghe sai (hay gặp: "Mời" ➔ "mười").
- Batch đầu cuối: 38/40 lượt hoàn thành; NPC nói xong ➔ robot bắt đầu nói **1.2 s**, gần hết là thời gian STT.

**Các quyết định quan trọng** (đầy đủ trong `ASSUMPTIONS.md`):
- 20 lớp intent (thêm `ho_tro_di_chuyen` mà danh sách trong kịch bản bỏ sót).
- Robot dừng ở chiều cao box 0.75 / 0.80 / 0.85 trong batch (~1.9 / 1.65 / 1.5 m) để NPC chịu nói (ngưỡng 2 m).
- Câu trả lời chỉ lấy từ mẫu và bản đồ; model không tự sinh câu, không đưa lời khuyên y khoa.
- Âm thanh NPC và robot không giảm trong bán kính 5 m, NPC +6 dB (trước đó quá nhỏ).

## 11. Việc còn lại

| Việc | Ai |
| :-- | :-- |
| Thu âm giọng B (nữ) theo `docs/kich_ban_thu_am.md` | Nhóm |
| Ghi `text_fixed` cho clip nói tự nhiên (`transcripts_n_todo.csv`) | Nhóm |
| Nghe `reports/voices/` và chọn giọng robot | Nhóm |
| Duyệt 83 câu robot có thể nói (`reports/robot_responses.md`) | Nhóm |
| Thay `hospital_map.json` giả lập bằng dữ liệu bệnh viện thật | Nhóm |
| Bổ sung câu mẫu `hoi_phong` kiểu "đi đường nào" rồi train lại PhoBERT | Quyết định chưa có |
| Mức dừng 0.75 cho khoảng cách ~2.0 m, sát ngưỡng NPC nói ➔ 2/40 episode NPC không nói; đổi 0.77 hoặc nới ngưỡng 2.1 m | Quyết định chưa có |
| Dẫn đường thật và phối hợp hành động bằng RL | Giai đoạn sau |

## 12. Lỗi hay gặp

| Triệu chứng | Cách xử lý |
| :-- | :-- |
| `Unable to find libjvm` / `JAVA_HOME not found` | Cài openjdk@17, hoặc đặt `JAVA_HOME` đúng thư mục JDK |
| `VnCoreNLP files missing` | Tải 3 file VnCoreNLP ở mục 4 |
| TTS server báo `không nạp được TTS từ local` | Thiếu `models/Vie-neu-v3-turbo/onnx_update` hoặc `models/MOSS-Audio-Tokenizer-Nano-ONNX` |
| `ROBOT_VOICE ... không có trong list_preset_voices()` | Tên giọng gõ sai; xem danh sách trong `reports/voices/index.md` |
| STT server: `manifest.csv not found` | Chạy `voice.prepare_data` |
| `--nlu phobert` lỗi thiếu `label_map.json` | Chưa fine-tune: chạy `nlu.train_phobert`, hoặc dùng `--nlu rule` |
| Ô góc nhìn hiện "mất kết nối" | Server chưa chạy hoặc sai cổng (8765 / 8766 / 8767) |
| Không nghe robot nói trong batch | Bản batch cũ (trước 2026-10-22) tắt scene khi âm thanh vừa tới; cập nhật code |
| Batch thoát mã 2 | Không chạy được với `--headless`, cần cửa sổ có render |
