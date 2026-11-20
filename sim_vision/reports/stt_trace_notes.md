# Dò vết STT (G13.3) — viết tay, không bị `eval_stt` ghi đè

Nguồn: `stt_eval_20261021_224132.csv` (PhoASR-whisper-small, beam 1, seed 0, lưới default). Không nghe được audio sau mô phỏng bằng tai; nguyên nhân suy ra từ hyp ở các điều kiện khác nhau.

## 3 clip có WER (gộp mọi điều kiện) cao nhất

| Clip | WER | Ref | Hyp (sạch, 1 m) | Nguyên nhân |
| :-- | :-- | :-- | :-- | :-- |
| A_07_r | 0.66 | Phòng khám số 205 đi đường nào? | Phòng khám số hai trăm linh lăm đi đường nào? | **Cách viết số**: model viết số bằng chữ ➔ 1 từ "205" thành 4 từ (1 thay + 3 chèn), WER 0.57 ngay cả khi nghe đúng. Ở babble 5 dB 3 m mất hết phần sau ("Phòng khám số"). |
| A_C04_r | 0.48 | Phòng siêu âm số 304 ở đâu? | Phòng siêu âm số ba không bốn ở đâu? | **Cách viết số** như trên (đọc từng chữ số). Ở babble 5 dB 3 m: "Số Pán Phục Bốn ở đâu hả." |
| A_C05_r | 0.42 | Quầy thu ngân ở đâu? | Quầy thu ngưng ở đâu? | **Câu ngắn** (5 từ ➔ mỗi lỗi = 20%) và nhầm "ngân" ➔ "ngưng" ngay cả khi sạch. Babble 5 dB 3 m: "Ngày nay chờ mừng quay đầu." (hỏng hoàn toàn). |

- Bỏ 2 câu có số, WER tổng là 0.144 (thay vì 0.163) và WER khi không ồn là 0.034.
- Babble được ghép từ **chính giọng A** (chưa có người nói khác) ➔ khó hơn babble thật nhiều người, đặc biệt ở SNR thấp: babble 5 dB cho WER 0.50, white 5 dB 0.26.

## Intent trên kết quả STT

- `text_ref`: 100% (70 câu). STT ở SNR 20, 1 m: babble 98.6%, white 97.1%; không ồn 1 m: 98.6% (sai duy nhất A_C05_r "Quầy thu ngưng ở đâu?" ➔ unknown).
- **Recall `cap_cuu` trên toàn lưới: 74.3% (107/144)**. Bỏ sót chủ yếu vì STT nghe sai từ khóa: "cấp cứu" ➔ "cấp cũ" / "sấp cứu" (thành hoi_khoa hoặc unknown), "khó thở" ➔ "khó khăn" / "khó mở", "gọi bác sĩ" ➔ "bảo bác sĩ" / "gọi bé xỉ". Chưa sửa luật để tránh khớp theo chính dữ liệu đánh giá; cần cân nhắc (vd khớp gần đúng, hoặc mô hình intent) trước khi dùng thật.
