# Kịch bản thu âm: người bệnh hỏi robot dẫn đường

Hai kịch bản dành cho hai người thu âm, đều 20 tuổi:
- **Kịch bản A (nam):** sinh viên đi khám cho mình, và đưa bố đi khám.
- **Kịch bản B (nữ):** sinh viên đi khám cho mình, và đưa bà đi khám.

Mỗi kịch bản có 30 câu riêng và 10 câu chung (cả hai cùng đọc để so sánh giọng nam với giọng nữ). File này cũng là **transcript chuẩn** để tính WER và **nhãn intent** để đánh giá phần hiểu ý định.

---

## 1. Hướng dẫn thu âm (gửi kèm cho bạn)

**Trước khi thu**
- Phòng yên tĩnh, tắt quạt và điều hòa nếu được. Không thu trong phòng tắm vì bị vang.
- Dùng điện thoại cũng được. Để micro cách miệng khoảng 20 đến 30 cm, không cầm sát.
- Ứng dụng: ghi âm mặc định của điện thoại, hoặc Audacity trên máy tính.
- Định dạng: **WAV** nếu chọn được (16 kHz trở lên, mono). Không có WAV thì gửi M4A, mình tự chuyển.

**Khi thu**
- Mỗi câu thu thành **1 file riêng**. Im lặng khoảng 1 giây trước và sau mỗi câu.
- Mỗi câu thu **2 lần**:
  - Lần 1 (`_r`): đọc rõ, tốc độ bình thường.
  - Lần 2 (`_n`): nói tự nhiên như đang hỏi thật. Được ngập ngừng, thêm "ờ", "à", "dạ", đổi vài chữ cho quen miệng.
- Nói bằng giọng quê quán thật của bạn, không cần cố nói giọng chuẩn.
- Đọc sai thì thu lại câu đó, không cần thu lại cả bài.

**Đặt tên file**
```
<mã người>_<mã câu>_<r hoặc n>.wav
Ví dụ: A_07_r.wav, A_07_n.wav, B_C03_n.wav
```

**Gửi lại:** nén cả thư mục thành `A.zip` hoặc `B.zip`.

---

## 2. Phiếu đồng ý (mỗi người ký 1 bản)

> Tôi đồng ý cho Mạnh sử dụng giọng nói của tôi trong các file thu âm này **chỉ cho mục đích đồ án môn học** (huấn luyện và đánh giá nhận dạng giọng nói). Giọng nói không được công khai lên mạng, không chia sẻ cho bên thứ ba, và sẽ bị xóa khi tôi yêu cầu.
>
> Họ tên: ................................ Mã người: A / B
> Giới tính: ........ Tuổi: ........ Quê quán (tỉnh): ........................
> Ngày: ............ Ký tên: ............

Quê quán dùng để ghi nhận vùng giọng (Bắc, Trung, Nam), không ghi địa chỉ cụ thể.

---

## 3. Kịch bản A: nam, 20 tuổi

**Bối cảnh:** bạn là sinh viên. Phần đầu bạn tự đi khám vì đau dạ dày. Phần sau bạn đưa bố (khoảng 55 tuổi) đi khám tim.

| Mã | Câu | Intent |
| :-- | :-- | :-- |
| A_01 | Chào bạn, cho mình hỏi chỗ đăng ký khám ở đâu vậy? | dang_ky_kham |
| A_02 | Mình khám lần đầu thì phải làm thủ tục gì trước? | dang_ky_kham |
| A_03 | Mình có bảo hiểm y tế, đưa thẻ ở quầy nào? | bao_hiem |
| A_04 | Mình quên mang thẻ bảo hiểm, dùng căn cước công dân được không? | bao_hiem |
| A_05 | Mình bị đau bụng mấy hôm nay thì nên khám khoa nào? | hoi_khoa |
| A_06 | Khoa tiêu hóa ở tầng mấy? | hoi_khoa |
| A_07 | Phòng khám số 205 đi đường nào? | hoi_phong |
| A_08 | Bác sĩ bảo mình đi nội soi dạ dày, phòng nội soi ở đâu? | hoi_phong |
| A_09 | Xét nghiệm máu thì lấy máu ở đâu? | hoi_phong |
| A_10 | Mình phải nhịn ăn trước khi xét nghiệm không? | khong_ho_tro |
| A_11 | Bao lâu thì có kết quả xét nghiệm? | thoi_gian_cho |
| A_12 | Lấy kết quả ở đâu vậy bạn? | hoi_phong |
| A_13 | Đóng tiền viện phí ở quầy nào? | thanh_toan |
| A_14 | Ở đây có thanh toán bằng chuyển khoản không? | thanh_toan |
| A_15 | Nhà thuốc bệnh viện ở đâu? | nha_thuoc |
| A_16 | Thang máy gần nhất ở đâu? | tien_ich |
| A_17 | Cho mình hỏi nhà vệ sinh nam ở đâu? | tien_ich |
| A_18 | Mình muốn gửi xe máy thì gửi ở đâu? | tien_ich |
| A_19 | Bố mình bị đau ngực, khám tim mạch ở đâu? | hoi_khoa |
| A_20 | Bố mình đi lại hơi khó, bệnh viện có cho mượn xe lăn không? | ho_tro_di_chuyen |
| A_21 | Bạn dẫn bố con mình đến phòng siêu âm tim được không? | dan_duong |
| A_22 | Đi chậm thôi nhé, bố mình đi không nhanh được. | dieu_chinh_toc_do |
| A_23 | Khoan, dừng lại chút, bố mình mệt. | dung_lai |
| A_24 | Được rồi, đi tiếp đi. | tiep_tuc |
| A_25 | Bố mình đang khó thở quá, gọi bác sĩ giúp mình với! | cap_cuu |
| A_26 | Khoa cấp cứu ở đâu? | cap_cuu |
| A_27 | Mình muốn gặp nhân viên hướng dẫn. | gap_nhan_vien |
| A_28 | Phòng điện tim là phòng mấy? | hoi_phong |
| A_29 | Bây giờ còn bao nhiêu người nữa thì tới số của mình? | thoi_gian_cho |
| A_30 | Ok, cảm ơn bạn nhiều nha. | cam_on |

---

## 4. Kịch bản B: nữ, 20 tuổi

**Bối cảnh:** bạn là sinh viên. Phần đầu bạn tự đi khám vì đau họng, sốt. Phần sau bạn đưa bà (khoảng 75 tuổi, nghe hơi kém, đau khớp gối) đi khám.

| Mã | Câu | Intent |
| :-- | :-- | :-- |
| B_01 | Dạ cho em hỏi lấy số khám bệnh ở đâu ạ? | dang_ky_kham |
| B_02 | Em có đặt lịch khám online rồi thì đến quầy nào ạ? | dang_ky_kham |
| B_03 | Thẻ bảo hiểm của em ở tỉnh khác thì có dùng được không ạ? | bao_hiem |
| B_04 | Em bị sốt với đau họng thì khám khoa nào ạ? | hoi_khoa |
| B_05 | Khoa tai mũi họng đi lối nào vậy ạ? | hoi_khoa |
| B_06 | Phòng 112 ở tầng một hay tầng hai ạ? | hoi_phong |
| B_07 | Chụp X-quang phổi ở đâu ạ? | hoi_phong |
| B_08 | Em cần nộp phiếu chỉ định ở đâu ạ? | hoi_phong |
| B_09 | Chỗ ngồi chờ khám ở đâu ạ? | tien_ich |
| B_10 | Em có cần đeo khẩu trang không ạ? | khong_ho_tro |
| B_11 | Em đợi lâu quá rồi mà chưa tới lượt, hỏi ai ạ? | gap_nhan_vien |
| B_12 | Em muốn trả tiền bằng thẻ ngân hàng được không ạ? | thanh_toan |
| B_13 | Lấy thuốc bảo hiểm ở đâu ạ? | nha_thuoc |
| B_14 | Nhà vệ sinh nữ ở đâu ạ? | tien_ich |
| B_15 | Ở đây có chỗ bán đồ ăn không ạ? | tien_ich |
| B_16 | Bà em bị đau đầu gối, đi khám xương khớp ở đâu ạ? | hoi_khoa |
| B_17 | Bà em lớn tuổi rồi, có quầy ưu tiên cho người già không ạ? | dang_ky_kham |
| B_18 | Bà em nghe không rõ, bạn nói to hơn được không? | dieu_chinh_am_luong |
| B_19 | Bạn nói lại lần nữa được không, em chưa nghe kịp. | nhac_lai |
| B_20 | Bạn dẫn bà em tới khoa cơ xương khớp giúp em với. | dan_duong |
| B_21 | Đi chậm chậm thôi bạn ơi. | dieu_chinh_toc_do |
| B_22 | Bà em muốn ngồi nghỉ một chút. | dung_lai |
| B_23 | Rồi, mình đi tiếp nha. | tiep_tuc |
| B_24 | Có thang máy không, bà em không leo cầu thang được. | tien_ich |
| B_25 | Bà em bị chóng mặt, sắp ngã rồi, giúp em với! | cap_cuu |
| B_26 | Phòng vật lý trị liệu ở đâu ạ? | hoi_phong |
| B_27 | Khám xong thì quay lại chỗ bác sĩ để đọc kết quả hả bạn? | hoi_phong |
| B_28 | Mấy giờ thì bệnh viện nghỉ trưa ạ? | thoi_gian_cho |
| B_29 | Em không hiểu, bạn chỉ lại đường giúp em được không? | nhac_lai |
| B_30 | Dạ em cảm ơn ạ. | cam_on |

---

## 5. Câu chung (cả A và B cùng đọc)

Dùng để so sánh trực tiếp giọng nam với giọng nữ trên cùng một câu.

| Mã | Câu | Intent |
| :-- | :-- | :-- |
| C01 | Cho tôi hỏi khoa tim mạch ở đâu? | hoi_khoa |
| C02 | Khoa nhi ở tầng mấy? | hoi_khoa |
| C03 | Phòng xét nghiệm máu đi đường nào? | hoi_phong |
| C04 | Phòng siêu âm số 304 ở đâu? | hoi_phong |
| C05 | Quầy thu ngân ở đâu? | thanh_toan |
| C06 | Nhà thuốc ở đâu? | nha_thuoc |
| C07 | Dẫn tôi đến khoa sản được không? | dan_duong |
| C08 | Đi chậm lại giúp tôi. | dieu_chinh_toc_do |
| C09 | Gọi nhân viên giúp tôi với. | gap_nhan_vien |
| C10 | Cảm ơn nhé. | cam_on |

---

## 6. Danh sách intent

| Intent | Ý nghĩa | Robot nên làm |
| :-- | :-- | :-- |
| dang_ky_kham | Đăng ký, lấy số, thủ tục | Chỉ quầy tiếp đón |
| bao_hiem | Thẻ BHYT, CCCD | Chỉ quầy BHYT |
| hoi_khoa | Hỏi khoa (có thể kèm triệu chứng) | Tra bảng khoa đã được duyệt, chỉ đường |
| hoi_phong | Hỏi phòng cụ thể | Chỉ đường |
| dan_duong | Nhờ dẫn đi | Bắt đầu dẫn đường |
| thanh_toan | Đóng tiền | Chỉ quầy thu ngân |
| nha_thuoc | Lấy thuốc | Chỉ nhà thuốc |
| tien_ich | Nhà vệ sinh, thang máy, gửi xe, ăn uống, ghế chờ | Chỉ đường |
| thoi_gian_cho | Hỏi thời gian, lượt | Đưa thông tin chung hoặc gọi nhân viên |
| dieu_chinh_toc_do | Đi chậm lại | Giảm tốc độ |
| dieu_chinh_am_luong | Nói to hơn | Tăng âm lượng |
| dung_lai | Dừng | Dừng và chờ |
| tiep_tuc | Đi tiếp | Tiếp tục dẫn |
| nhac_lai | Nói lại, chưa hiểu | Lặp lại, nói chậm hơn |
| gap_nhan_vien | Muốn gặp người thật | Gọi nhân viên |
| cap_cuu | Tình huống khẩn cấp | **Gọi nhân viên ngay, chỉ cấp cứu** |
| khong_ho_tro | Câu hỏi chuyên môn y khoa | Từ chối lịch sự, gợi ý hỏi bác sĩ |
| cam_on | Kết thúc | Chào |

---

## 7. Tổng số file mong đợi

| Người | Câu riêng | Câu chung | Số lần thu | Tổng file |
| :-- | :-- | :-- | :-- | :-- |
| A (nam) | 30 | 10 | 2 | 80 |
| B (nữ) | 30 | 10 | 2 | 80 |

Mỗi người mất khoảng 20 đến 30 phút.
