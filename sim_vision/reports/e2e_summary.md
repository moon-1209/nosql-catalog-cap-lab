# Batch đầu cuối: STT ➔ NLU PhoBERT ➔ policy ➔ TTS (G23)

Nguồn: `logs/dialogue_batch_20261022_012217.csv`. STT server chạy `--nlu phobert`; TTS server VieNeu v3 Turbo (cache sinh sẵn).

> **Hạn chế:** chỉ giọng A (nam, 20 tuổi); mỗi episode dừng ở lượt trả lời đầu tiên nên nhánh clarify (người bệnh nói lại) không chạy trong batch, chỉ được kiểm bằng test GUT.

## Tổng hợp

| Chỉ số | Giá trị |
| :-- | :-- |
| Episode | 40 |
| Hoàn thành lượt | 38/40 (95.0%) |
| Lỗi STT / episode | episode timeout: 2 |
| Kết quả TTS (lượt hoàn thành) | không lỗi: 38 |
| TTS cache hit | 100.0% |
| Intent accuracy | 92.1% |
| Recall cap_cuu | 100.0% (3 lượt) |

## Phân bố action

| action | số lượt |
| :-- | --: |
| answer | 24 |
| adjust | 5 |
| emergency | 3 |
| guide | 3 |
| clarify | 2 |
| refuse | 1 |

## Độ trễ (ms)

| Phần | TB | p50 | p95 |
| :-- | --: | --: | --: |
| Tổng (NPC nói xong ➔ robot bắt đầu nói) | 1212 | 1182 | 1476 |
| STT | 1122 | 1108 | 1316 |
| TTS | 3 | 2 | 7 |
| NLU + mạng + khung hình | 88 | 60 | 237 |

## Lượt cap_cuu bị bỏ sót

Không có.
