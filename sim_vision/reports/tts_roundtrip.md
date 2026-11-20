# Độ dễ nghe của giọng robot: WER khứ hồi TTS ➔ STT (G23)

Giọng: **Ngọc Huyền** (VieNeu-TTS v3 Turbo, ONNX/CPU). STT: PhoASR-whisper-small, không ồn, 1 m. Tham chiếu là câu sau `text_for_tts` (số đọc bằng chữ).

| Chỉ số | Giá trị |
| :-- | :-- |
| Số câu | 83 (thiếu cache: 0) |
| WER khứ hồi (corpus), so nguyên văn | 18.0% |
| **WER sau khi đổi số STT sang chữ** (chỉ còn lỗi nghe) | 2.2% |
| Câu WER (đã đổi số) = 0 | 60/83 |
| Câu WER (đã đổi số) > 20% | 0 |

WER nguyên văn cao chủ yếu vì STT viết số bằng chữ số ("205", "1-1-2") còn robot đọc bằng chữ.

## Câu có WER (đã đổi số) > 20%

Không có.
