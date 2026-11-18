# Buổi demo và vấn đáp

Cả nhóm tập một mạch. Bài tính tay giúp đọc cách chấm. Demo 50 nút cho thấy tốc độ tìm và khả năng đạt đích trả lời hai câu hỏi khác nhau. Case vô nghiệm kết thúc bằng chứng cứ 590 xe và 520 chỗ.

| Slide | Hình hoặc số chính | Ai trình bày |
|---|---|---|
| 1 · Câu hỏi | Mạng 50 nút và 460 xe ngày thường | M1 |
| 2 · Cách chấm | Bài 4 nút, chia 60/40 ra 208,34 xe·phút | M2 |
| 3 · Hai thuật toán | Một phép lai GA và một bước cập nhật WOA | M3 và M4 |
| 4 · Cách kiểm chứng | 21 ca sàng lọc, bốn ca khóa trước seed mới, 2.912 lượt chấm và chuẩn 1% | M1 |
| 5 · Demo | Hai bản đồ, chọn cùng một cạnh, tua kết quả, mở case vô nghiệm | M5 cùng M2 |
| 6 · Kết quả | Bảng xác nhận và hình hội tụ. Giải thích GA và WOA nhanh theo tiêu chí nào | M1, M3 và M4 |
| 7 · Chốt | Nêu giới hạn tập tuyến, mở sẵn code để hỏi đáp | M1 |

## Thứ tự thao tác demo

1. Mở `python qt_demo/main.py` sau khi cài Qt. Dùng seed 1000. Sẵn màn hình `DEMO_DU_PHONG.html` để chuyển nhanh sang bản ghi offline nếu cần.
2. Chọn **Ngày thường** rồi chạy. Chọn mã cạnh để đọc luồng và sức chứa. Kéo về đầu để chỉ vì sao quần thể mở màn cùng seed có cùng điểm.
3. Chuyển **Nhiều nguồn, một đích** để thấy 5 cặp dồn về T3. Chiếu số liệu 30 seed để đọc 30/30 và 28/30, đồng thời đọc ERT 227 và 332 lượt chấm. Nếu seed mẫu cho WOA có chi phí thấp, chỉ rõ vì sao bảng nhiều seed vẫn cần thiết.
4. Đọc biểu đồ **Tải nhẹ**. GA đạt đích 28/30, WOA 17/30, còn WOA có nhiều lượt chạm đích sớm. Chốt rằng tỷ lệ đạt và tốc độ trong các lượt đạt cần đọc cùng nhau.
5. Chọn **Cao điểm + đóng E23**. Đọc chứng cứ 590 vượt 520 trước khi chạy. Màu đỏ và đường hội tụ lúc này biểu diễn vi phạm. Nếu dùng HTML, nói rõ đang chiếu kết quả đã ghi của seed 1000.

Lúc tập, mỗi thành viên chỉ bằng tay một biến trên form rồi tìm đúng dòng tạo biến đó. Ai đứng demo cũng cần giải thích được cận dưới, số lượt chấm, và lý do hai thuật toán có thể kết thúc khác nhau.

## Những câu nên trả lời được khi thầy mở code

| Câu hỏi | Câu trả lời ngắn để luyện | Chỉ chỗ trong code |
|---|---|---|
| Một ứng viên đại diện cho gì? | Một bộ trọng số ưu tiên 25 tuyến của năm nhóm. Cùng tỷ lệ trong một nhóm cho cùng cách chia xe. | `model.evaluate`, biến `weight_sum` |
| Vì sao chắc chắn đủ xe cho từng cặp? | Nếu còn tuyến mở, các tỷ lệ của cặp cộng thành 1. Nếu hết tuyến, ghi cả nhu cầu vào `unassigned` và đánh vi phạm. | `evaluate`, khối chia `demand` |
| Nếu hai tuyến chồng lên E23? | Mỗi tuyến cộng luồng của nó lên mọi cạnh đi qua. E23 nhận cả hai khoản. | `edge_flows[road_index] += flow` |
| 5.186,30 xe·phút nghĩa gì? | Tổng số phút của tất cả xe qua mọi cạnh. Chia cho 460 khi hợp lệ sẽ ra trung bình khoảng 11,27 phút/xe. | `total_minutes += flow * minutes` |
| Tại sao điểm phút thấp vẫn bị loại? | So ô vi phạm trước. Một phương án chưa chở đủ hoặc vượt sức chứa không dùng để so chi phí hợp lệ. | `rank` và `row_for` |
| Khi 0 sức chứa có chia cho 0? | Các tuyến chứa cạnh đó bị bỏ khi chia xe. `road_time` trả `None` cho cạnh đóng. | `make_problem`, `road_time` |
| Cho xem một lần lai của GA. | Hai giá trị 0,7 và 0,3, hệ số 0,25 thì ra 0,4. Từng núm có thể đột biến rồi bị chặn trong biên. | `select_parent`, `make_child` |
| GA giữ nghiệm tốt cũ bằng cách nào? | Nếu thế hệ mới chưa có kỷ lục tốt hơn, có thể đặt ứng viên tốt đã biết vào chỗ con kém nhất. Điểm đó đã được chấm. | `ga.solve`, đoạn `elite_kept` |
| Trong WOA, khi nào nghe một cá voi ngẫu nhiên? | Khi `p < 0,5` và `abs(A) ≥ 1`. Nếu `p < 0,5` và `abs(A) < 1` thì dùng `X*`. Từ `p ≥ 0,5` chọn xoắn. | `move_whale` |
| `l` và `D′` là gì? | `l` là số ngẫu nhiên cho hệ số xoắn, còn `D′` là độ lệch tuyệt đối giữa núm hiện tại và núm tốt nhất. | `move_whale`, nhánh `spiral` |
| Vì sao cùng seed vẫn ra nghiệm khác? | Hai bên chia sẻ ứng viên vòng 0. Sau đó GA lai/đột biến, WOA cập nhật theo ba nhánh nên quần thể khác nhau. | `solver.solve` |
| 2.912 lượt chấm từ đâu? | 32 ứng viên vòng đầu và 32 ứng viên mới ở mỗi trong 90 vòng, nên `32 × 91`. | `score_population`, `checkpoint` |
| Kéo slider có chạy lại WOA? | Slider chọn một record trong `history`. Hàm vẽ chỉ dùng số đã lưu. | `change_step`, `evaluation`, `render` |
| 0/30 có đủ chứng minh vô nghiệm? | 0/30 là số lần chưa tìm được. Với case đóng E23 lúc cao điểm, lát cắt `590 > 520` mới chứng minh vô nghiệm. | `cut_proof` |
| Đo đoạn ảnh hưởng nhất bằng cách nào? | Lần lượt giảm 50% sức chứa từng cạnh trong năm hành lang, giữ 460 xe và ghép cùng seed với ngày thường. So phần trăm thay đổi trong cặp hợp lệ. | `scan_roads`, `sensitivity.csv` |
| Đạt 1% có nghĩa là đã tìm đúng tối ưu? | Chuẩn số cho cận dưới L và cận trên U. Chi phí hợp lệ F ≤ 1,01L là mốc bảo thủ để đếm gần tối ưu. | `research/oracle.py`, `near_target` |
| Thuật toán nào nhanh hơn? | Đọc đúng thước đo. Ở tải nhẹ WOA chạm đích sớm hơn trong lượt thành công, GA đạt đích nhiều lần hơn. | `first_hit_calls`, `ert_1pct_calls` |
| 5.000 nút có nghĩa là xử lý mọi bài 5.000 nút? | Mốc đã chạy dùng chia cạnh, 25 gene và 304 lần chấm. Bài nhiều tuyến hoặc nhiều cặp có chi phí khác. | `research/scale.py` |

## Luyện theo cách thầy từng hỏi nhóm Dijkstra

Mỗi người có 90 giây bấm một case và kể luồng từ ô nhập tới một số trên màn hình. Người còn lại ngắt ở một chỗ để hỏi biến ấy đến từ đâu. Lượt hai đổi người đứng máy. Ai phụ trách GUI tự mở `evaluate` và tính một cạnh. Ai viết thuật toán tự chọn case, đọc tải và giải thích vì sao đỏ. Leader đứng ngoài trả lời khi đã tới lượt của mình.

Thử một lượt với máy trình chiếu không có mạng. Tập cả ba phương án gồm form chạy sống, CLI và HTML. Mỗi người mở được file của mình trong thư mục giải nén và biết quay về `README.md` khi cần tìm lệnh.
