# Đề cương đồ án: Robot trợ lý dẫn đường bệnh viện

Oct 21, 2026 · @Manh

## Bối cảnh và vấn đề

Đồ án xây dựng một robot trợ lý dẫn đường trong bệnh viện, được kiểm chứng hoàn toàn trong mô phỏng Godot dựa trên số liệu khảo sát thực tế. Robot không được chế tạo thật.

- Người cao tuổi, người khiếm thị, người đi xe lăn và người ít dùng công nghệ thường gặp khó khi dùng kiosk tự phục vụ và đọc biển chỉ dẫn.
- Những người này phải hỏi nhân viên, làm tăng tải cho quầy tiếp đón vốn đã thiếu người vào giờ cao điểm.
- Một trợ lý biết đọc giấy tờ, nghe và nói tiếng Việt, rồi dẫn người bệnh đến đúng phòng ban có thể giảm phần việc lặp lại này.

## Mục tiêu và phạm vi

Mục tiêu chính là chứng minh một policy học tăng cường (RL) dẫn người bệnh đến đích tốt hơn cách làm dựa trên luật, trong một bệnh viện mô phỏng có đông người.

**Trong phạm vi**

- Khảo sát một bệnh viện thật để lấy sơ đồ tầng, lưu lượng người và các câu hỏi hay gặp.
- Mô phỏng một tầng bệnh viện trong Godot 4 và train policy dẫn đường bằng Godot RL Agents.
- Phát hiện và bám theo người trên video thật, dùng kết quả để mô hình hóa nhiễu trong mô phỏng.
- Đọc CCCD và so khuôn mặt, dùng dữ liệu tổng hợp.
- Hỏi đáp bằng giọng nói tiếng Việt về phòng ban và thủ tục.

**Ngoài phạm vi**

- Chế tạo và vận hành robot thật.
- Tư vấn y khoa hay chẩn đoán.
- Kết nối với hệ thống thông tin của bệnh viện và xử lý CCCD thật.

## Kiến trúc hệ thống

&#91;embedded content: kiến trúc hệ thống · 3 module, 1 policy, 1 môi trường\]

Vision, giọng nói và CCCD cung cấp đầu vào cho policy RL. Policy được train và kiểm chứng trong Godot, có tham số lấy từ khảo sát bệnh viện.

## Module RL dẫn đường trong Godot

Đây là lõi của đồ án. RL phù hợp vì robot phải cân bằng nhiều mục tiêu cùng lúc (đến đích, chờ bệnh nhân, tránh đám đông), và việc thử sai diễn ra an toàn trong mô phỏng.

**Công cụ:** Godot 4 và Godot RL Agents, giao diện Gymnasium, train bằng Stable-Baselines3 (PPO), xuất policy ra ONNX để chạy trong Godot khi demo.

**Môi trường**

- Bản đồ một tầng bệnh viện dựng từ sơ đồ khảo sát: hành lang, các khoa, quầy tiếp đón, thang máy. Vùng đi được dùng NavigationRegion3D.
- Người đi lại dùng NavigationAgent3D có bật tránh va chạm, mật độ thay đổi theo giờ lấy từ số liệu khảo sát.
- Bệnh nhân cần dẫn có nhiều kiểu: đi chậm, hay dừng, ngồi xe lăn.

**Bài toán RL**

| Thành phần | Thiết kế |
| --- | --- |
| Quan sát | Raycast giống lidar (RaycastSensor3D), vị trí tương đối của bệnh nhân và đích, vận tốc robot |
| Hành động | Vận tốc tiến và vận tốc quay (liên tục) |
| Điểm thưởng | Cộng khi tiến gần đích và khi giữ cách bệnh nhân 1 đến 2 m; trừ khi va chạm, khi đi quá sát người lạ, và trừ dần theo thời gian |
| Tăng độ khó | Bản đồ trống, rồi vật cản, rồi đám đông, cuối cùng là bệnh nhân hay dừng |

**Baseline để so sánh:** robot đi theo đường tính bằng NavMesh hoặc A\*, kèm luật giữ khoảng cách với bệnh nhân.

**Mẹo train:** chạy không hiển thị và tăng tốc thời gian, đặt nhiều bản sao môi trường trong một scene, dùng hình khối đơn giản trước và làm đẹp sau.

## Module vision: phát hiện và bám theo người

Module này chạy trên video thật và cung cấp mức nhiễu thực tế cho mô phỏng, nhờ đó nối hai phần với nhau.

1. Phát hiện người bằng YOLO.
2. Bám theo người qua các khung hình bằng ByteTrack hoặc DeepSORT.
3. Re-ID để không bám nhầm người khác giữa đám đông.
4. Đo tỉ lệ mất dấu, tỉ lệ nhầm người và sai số vị trí trên video quay trong đợt khảo sát (nếu được phép) hoặc video công khai.

**Đưa vào mô phỏng:** robot không được biết chính xác vị trí người. Mô phỏng lấy vị trí thật, cộng nhiễu, thỉnh thoảng cho mất dấu hoặc nhầm người theo đúng các tỉ lệ đo được ở bước 4. Nhờ vậy policy học được cách xử lý khi nhận diện sai.

## Module CCCD và xác thực khuôn mặt

Module này dùng hoàn toàn dữ liệu tổng hợp, vì CCCD và khuôn mặt thật là dữ liệu nhạy cảm.

**Dữ liệu tổng hợp:** tạo thẻ mẫu với thông tin giả và ảnh mặt do GAN sinh ra, đóng dấu "MẪU". Sau đó tạo thêm biến thể bị lóa, mờ, chụp nghiêng, nền khác nhau.

**Quy trình**

1. Phát hiện thẻ và chỉnh thẳng ảnh.
2. Đọc mã QR trên CCCD gắn chip (dễ và chính xác hơn OCR); OCR bằng PaddleOCR hoặc VietOCR làm phương án dự phòng.
3. Cắt ảnh mặt trên thẻ.
4. So với mặt camera thấy bằng ArcFace hoặc InsightFace.
5. Chống giả mạo (liveness), ví dụ người dùng giơ ảnh in thay cho mặt thật.

**Mục đích so mặt:** xác thực đúng người khi đăng ký khám. Hệ thống phải xin đồng ý trước khi quét.

## Module giọng nói và hướng dẫn phòng ban

Người bệnh hỏi bằng giọng nói, ví dụ "khám tim ở đâu?", và robot trả lời bằng giọng nói kèm chữ to trên màn hình, rồi dẫn đường.

1. Nhận dạng giọng nói tiếng Việt bằng PhoWhisper.
2. Hiểu ý định bằng PhoBERT (phân loại khoảng 30 đến 50 intent) hoặc LLM kèm RAG trên thông tin bệnh viện.
3. Tổng hợp giọng nói tiếng Việt để trả lời.
4. Gửi điểm đến cho module RL dẫn đường.

**Giới hạn:** hệ thống chỉ chỉ đường và hướng dẫn thủ tục. Nếu nhận triệu chứng để gợi ý khoa khám thì dùng bảng ánh xạ đã được nhân viên y tế duyệt, kèm câu miễn trừ trách nhiệm. Khi không chắc chắn, robot chuyển cho nhân viên.

## Dữ liệu và khảo sát bệnh viện

Khảo sát bệnh viện cung cấp số liệu để chỉnh tham số mô phỏng; các bộ dữ liệu công khai dùng để train và đánh giá từng module.

| Nguồn | Dùng cho | Ghi chú |
| --- | --- | --- |
| Khảo sát: sơ đồ tầng | Bản đồ Godot | Vẽ tay, đo hành lang, vị trí khoa và biển chỉ dẫn |
| Khảo sát: lưu lượng người theo giờ | Mật độ đám đông | Đếm người tại vài điểm, vài khung giờ |
| Khảo sát: tốc độ đi của người cao tuổi | Hành vi bệnh nhân mô phỏng | Quan sát, không ghi hình nếu chưa được phép |
| Khảo sát: câu hỏi hay gặp | Bộ intent | Hỏi nhân viên quầy tiếp đón |
| VIVOS, Common Voice (vi), VLSP | Nhận dạng giọng nói | Giọng người cao tuổi và giọng địa phương ít, nên tự thu thêm |
| Bộ intent tự xây | Hiểu ý định | 30 đến 50 intent, dùng LLM sinh thêm câu |
| MobilityAids (Freiburg) | Nhận diện xe lăn, nạng | Mở rộng tùy chọn |
| CCCD tổng hợp | Đọc thẻ, so mặt | Tự sinh, đóng dấu "MẪU" |

## Chỉ số đánh giá

Kết quả chính là bảng so sánh policy RL với baseline NavMesh/A\* trên cùng một bộ kịch bản mô phỏng.

| Module | Chỉ số |
| --- | --- |
| RL dẫn đường | Tỉ lệ đến đích (%), số va chạm mỗi lượt, thời gian đến đích (s), tỉ lệ thời gian giữ được khoảng cách 1 đến 2 m, tách theo mật độ đám đông và kiểu bệnh nhân |
| Vision | MOTA, IDF1, số lần đổi ID |
| CCCD | Độ chính xác từng trường thông tin, FAR và FRR của so mặt |
| Giọng nói | WER, độ chính xác intent, tỉ lệ hỏi đáp hoàn thành |

Nếu thời gian cho phép, cho 10 đến 20 người dùng thử bản demo hỏi đáp và chấm điểm mức dễ dùng.

## Rủi ro, pháp lý, đạo đức

Rủi ro lớn nhất là phạm vi quá rộng: nếu trễ tiến độ, giữ module RL và vision, rút gọn CCCD và giọng nói thành demo nhỏ.

| Rủi ro | Cách xử lý |
| --- | --- |
| Phạm vi quá rộng cho một đồ án | Ưu tiên RL và vision; CCCD và giọng nói làm mức tối thiểu |
| Khoảng cách giữa mô phỏng và thực tế | Chỉnh tham số từ số liệu khảo sát, thêm nhiễu nhận diện, nêu rõ giới hạn trong báo cáo |
| Train RL chậm hoặc không hội tụ | Tăng độ khó dần, chạy nhiều môi trường song song, kiểm tra reward trên bản đồ nhỏ trước |
| Không được bệnh viện cho phép khảo sát hoặc ghi hình | Xin giấy giới thiệu từ trường sớm; dùng sơ đồ công khai và video công khai làm phương án dự phòng |
| Dữ liệu sinh trắc học nhạy cảm (Nghị định 13/2023) | Chỉ dùng CCCD và khuôn mặt tổng hợp; thiết kế bước xin đồng ý; không lưu ảnh |
| Thẻ tổng hợp bị lạm dụng | Đóng dấu "MẪU", không công bố bộ sinh thẻ |
| Tiếng ồn bệnh viện, giọng địa phương | Thêm nhiễu vào dữ liệu train, tự thu thêm giọng |
| Robot bị hiểu là tư vấn y khoa | Giới hạn ở chỉ đường và thủ tục, có câu miễn trừ, chuyển nhân viên khi không chắc |

## Kế hoạch 14 tuần

&#91;embedded content: kế hoạch 14 tuần · 6 giai đoạn, 2 mốc kiểm tra\]

Nếu đến mốc 2 RL chưa vượt baseline, dành tuần 11 đến 12 để chỉnh reward và cắt CCCD xuống mức demo.

**Câu hỏi còn mở**

- Đồ án kéo dài bao lâu và làm mấy người? Kế hoạch trên giả định 14 tuần, một đến hai người.
- Bệnh viện nào sẽ khảo sát, và có được phép quay video không?
- Module CCCD có bắt buộc theo yêu cầu của giảng viên không, hay có thể là phần mở rộng?
