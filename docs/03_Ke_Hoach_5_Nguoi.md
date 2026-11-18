# Phân công nhóm 5 người

Gắn tên thật vào M1 đến M5 sau buổi đầu. M1 là leader. Vì bốn người đã làm WOA chung, giao M4 cho một bạn có thể giải thích ngay ba nhánh cập nhật. M2 hoặc M3 có thể ghép người mới với một bạn cũ trong buổi đọc code đầu tiên. Mỗi phần có sản phẩm code, số đo hoặc bài kiểm tra, và một câu vấn đáp mà người phụ trách phải trả lời được.

| Người | Phần code chính | Bàn giao kiểm được | Đoạn nói và câu cần nắm |
|---|---|---|---|
| **M1 · Minh Nhân** | `solver.py`, `research/measure.py`, ghép lệnh chạy và khóa cấu hình đo | Cùng seed cho cùng quần thể đầu. Chạy đủ ngân sách. Có `confirm_summary.csv`, `confirm_paired.csv`, tổng hợp điều cần xác nhận với thầy | Đề và thiết kế phép đo. Chỉ ra ngay nơi đếm lượt chấm và lý do ghép cặp seed |
| **M2 · Mô hình và dữ liệu** | `data/`, `make_problem`, `road_time`, `evaluate` trong `model.py` | Tính tay 60/40 và 50/50, kiểm thử đóng cạnh, tải cộng từ hai cặp, công thức và sơ đồ mạng | Từ 25 trọng số đến xe·phút. Chỉ đúng dòng cộng luồng qua một cạnh chung |
| **M3 · Lõi GA** | `algorithms/ga.py`, kiểm thử chọn bố mẹ, giới hạn trọng số và giữ nghiệm tốt | Giải thích được một lần lai với số cụ thể, bảo toàn ngân sách chấm. Đọc ca tải nhẹ và kiểm tra số lần đạt đích bằng một lượt tự chạy | Chọn, lai, đột biến, giữ kỷ lục. Giải thích được một kịch bản GA ra số tốt hơn hoặc ngang WOA |
| **M4 · Lõi WOA** | `algorithms/woa.py`, kiểm thử ba nhánh và `clip` | Ghi được `A`, `C`, `D`, `D′`, `X*` và một bước tính. Đối chiếu khác biệt với mã seminar. Đọc tiến trình WOA ở seed 1000 và giải thích vì sao đổi tổng vòng làm đổi lịch `a` | Giải thích khi nào bơi theo `X*`, khi nào bơi theo bạn ngẫu nhiên, khi nào xoắn |
| **M5 · Form và kiểm tra vô nghiệm** | `qt_demo/`, trang offline và `cut_proof` trong `model.py` | Điều khiển được form, chứng minh `590 > 520`, test chuyển case, chọn cạnh, tua và chạy lại. Đọc được `route_flows` và `edge_flows` khi gắn vào bảng | Demo một lượt hoàn chỉnh. Lần từ form tới `solver.solve` và `evaluate` và giải thích màu đỏ hoặc nét đứt |

M2 chốt hợp đồng dữ liệu trong `model.py` trước, rồi M5 bổ sung hoặc kiểm tra `cut_proof` trên cùng file. M3 và M4 đọc chéo thuật toán của nhau. M2 và M5 đổi vai khi tập giải thích lát cắt và hàm chấm. M1 gọi một seed bất kỳ để các bạn chỉ vị trí lỗi hoặc số liệu ngay trong code. Bản dự phòng dùng chung để đối chiếu. Khi có phần nhóm tự thay hoặc cải tiến, ghi lại thay đổi và chạy lại các bài kiểm tra liên quan.

## Hợp đồng ghép việc

| Chỗ giao nhau | Đầu vào | Đầu ra cần giữ |
|---|---|---|
| M2 → M3 và M4 | `problem`, `genes` trong `[0, 1]` | `evaluate` trả `rank`, `valid`, `route_flows`, `edge_flows`, `total_minutes` |
| M3 và M4 → M1 | Quần thể đầu, `evaluate`, số vòng, RNG, callback | `history` từ vòng 0, `calls`, nghiệm tốt nhất, `details` |
| M1 → M5 | `solver.solve(problem, name, size, steps, seed)` | Hai kết quả chung cấu trúc. Giao diện chỉ đọc các trường đã chốt |
| M1 đến M5 → báo cáo | Một bảng hoặc hình có đơn vị, một đoạn giải thích, một bài kiểm tra | M1 ghép thành một mạch, từng người đọc lại và xác nhận phần mình |

## Lộ trình theo mốc

1. **Khóa đề và phạm vi.** Kiểm tra slot, mẫu báo cáo, thời lượng, cách nộp, thuật toán hoặc nội dung từng được dặn miệng. Điền vai trò. Tất cả chạy bản đóng gói và tính bài hai tuyến bằng tay.
2. **Khóa đầu vào và hàm chấm.** M2 đưa sơ đồ 50 nút, danh sách 5 hành lang và bảng tuyến. M3 và M4 dùng bài nhỏ để kiểm tra lõi. M5 xem trước cách hiển thị dữ liệu trả về. M1 chốt ngân sách và dãy seed trước khi đọc kết quả.
3. **Ghép một lượt chạy đầy đủ.** Cả nhóm chạy ngày thường, nhiều nguồn chung đích, tải nhẹ và kịch bản vô nghiệm. Gặp lỗi ở đâu thì sửa theo hợp đồng, cập nhật số liệu từ đầu. Mỗi người diễn giải một vòng của phần mình với người đọc chéo.
4. **Đo chính thức trên máy nhóm.** Lưu CSV, bảng tóm tắt, ảnh đại diện cùng seed và log cấu hình. Chọn ba nhận xét có số để trình bày. Giữ một bản ZIP đã kiểm thử trên máy dùng để trình chiếu và một bản trên máy thành viên khác.
5. **Hoàn tất báo cáo và diễn tập.** Mỗi người gửi nội dung phần mình cùng dữ liệu gốc. M1 gom một bộ slide, cả nhóm luyện demo và lần code. Chạy thử offline. Điền đóng góp thực tế, rà mẫu thầy và đính Turnitin thật theo yêu cầu.

Một phần được xem là bàn giao khi bạn phụ trách chạy được, bạn đọc chéo chạy lại được, và người phụ trách trả lời được “hàm nhận gì, trả gì, dữ liệu được dùng ở đâu”. Đến mốc cuối, mỗi người tập giải thích cả GA, WOA và hàm chấm ở mức đọc code, kể cả khi chỉ trình bày một đoạn ngắn.
