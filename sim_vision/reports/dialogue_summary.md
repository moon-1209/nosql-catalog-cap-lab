# Batch hội thoại NPC ➔ robot (G17)

Nguồn: `logs/dialogue_batch_20261022_012217.csv`. Speaker: A.

> **Hạn chế:** kịch bản dự kiến 2 người nói 20 tuổi (A nam, B nữ) nhưng hiện mới có giọng A; kết quả chưa đại diện cho người cao tuổi, giọng nữ hay giọng địa phương khác. Bản đồ bệnh viện là giả lập.

## Tổng hợp

| Chỉ số | Giá trị |
| :-- | :-- |
| Episode | 40 |
| Hoàn thành một lượt | 38/40 (95.0%) |
| Lỗi | episode timeout: 2 |
| WER (clip ref_verified, 20 lượt) | 7.2% [KTC 95% 2.3%, 14.4%] |
| Intent accuracy (lượt hoàn thành) | 92.1% |
| **Recall cap_cuu** | 100.0% (3 lượt) |
| NPC nói xong ➔ có phụ đề (ms) | trung bình 1212.19, p50 1181.50, p95 1475.75 |
| stt_ms trung bình | 1124.93 |

## Theo khoảng cách (mức H_TARGET)

| h_target | n | completed | distance_m | wer | n_wer | intent_acc |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 0.75 | 14 | 13 | 1.97 | 16.3% | 7 | 84.6% |
| 0.80 | 13 | 13 | 1.67 | 3.3% | 6 | 92.3% |
| 0.85 | 13 | 12 | 1.48 | 3.5% | 7 | 100.0% |

## Theo điều kiện ồn

| noise | n | completed | distance_m | wer | n_wer | intent_acc |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| babble | 20 | 20 | 1.72 | 9.0% | 10 | 95.0% |
| none | 10 | 9 | 1.76 | 9.5% | 6 | 88.9% |
| white | 10 | 9 | 1.65 | 0.0% | 4 | 88.9% |

## So với G13 (cùng clip, cùng noise/SNR)

Batch có khoảng cách nói 1.4–2.0 m nên WER nên nằm giữa cột 1 m và 2 m của G13; số lượt nhỏ nên dao động lớn.

| noise | snr_db | batch_distance_m | batch_wer | n_batch | g13_wer_1m | g13_wer_2m |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| babble | 10.00 | 1.71 | 14.5% | 6 | 4.2% | 18.1% |
| babble | 20.00 | 1.64 | 0.0% | 4 | 4.2% | 3.6% |
| none | 30.00 | 1.71 | 9.5% | 6 | 3.0% | 3.0% |
| white | 20.00 | 1.77 | 0.0% | 4 | 4.8% | 5.4% |

## Lượt cap_cuu bị bỏ sót

Không có.

## 5 lượt sai tiêu biểu

| clip_id | hyp | intent dự đoán | intent đúng | WER |
| :-- | :-- | :-- | :-- | :-- |
| A_24_r | Được rồi, được rồi! | cam_on | tiep_tuc | 60.0% |
| A_07_r | Phòng khám số hai trăm linh lăm đi đường nào? | tien_ich | hoi_phong | 57.1% |
| A_03_r | Mình có bảo hiểm y tế chưa thể ở quầy nào. | bao_hiem | bao_hiem | 18.2% |
| A_C07_r | Dẫn tôi đến hoa sản được không? | dan_duong | dan_duong | 14.3% |
| A_07_n | Phòng khám số Hai trăm lẻ năm thì đi đường nào? | tien_ich | hoi_phong | — |
