# Extras

Đây là phần mở rộng để nhóm tìm hiểu cách GA và WOA hoạt động trên bài có đáp án biết trước. Khi trình bày đồ án, nhóm có thể mở phần này nếu cần minh họa toán tử hoặc giải thích giới hạn của phép đo.

| Mở gì | Xem được gì |
|---|---|
| [GA_Animation.html](GA_Animation.html) | Tua từng bước chọn bố mẹ, lai, đột biến và chấm một con. Mở bằng trình duyệt, chạy offline |
| [benchmarks_results/summary.csv](benchmarks_results/summary.csv) | Kết quả gộp của 360 lượt trên Sphere, Rastrigin và Ackley dịch tâm |
| [benchmarks_results/runs.csv](benchmarks_results/runs.csv) | Từng lượt với seed, điểm đầu, sai số cuối và lần chạm ngưỡng đầu tiên |
| [benchmarks_results/instances.csv](benchmarks_results/instances.csv) | Tọa độ nghiệm tối ưu để kiểm chứng lại |
| [benchmarks_results/metadata.json](benchmarks_results/metadata.json) | Phiên bản Python, ngân sách, các seed và miền tìm kiếm |

## Nhìn một lần sinh con

Animation dùng đúng hàm chọn bố mẹ và sinh con trong `algorithms/ga.py`. Quần thể có 6 cá thể, mỗi cá thể có hai gene. Ví dụ này tối thiểu hóa bình phương khoảng cách tới điểm (0,32 | 0,68). Bố mẹ là P3 và P2. Con sau lai ở khoảng (0,446 | 0,748), rồi đột biến gene y còn 0,553. Điểm của con xấu đi trong lần đột biến đó, dù vẫn tốt hơn ứng viên dẫn đầu ban đầu. Nhờ vậy dễ thấy đột biến là cách thử vị trí mới, còn hàm chấm mới xác định thử đó có ích hay không.

Để xem số bốc và tọa độ đầy đủ, chạy từ thư mục chứa `solver.py`.

```bash
python -m Extras.ga_trace
```

## Các hàm biết trước nghiệm toàn cục

Mỗi thuật toán tìm vector `u` trong `[0, 1]^D`. Bộ chấm đổi sang `z_i = độ_rộng × (u_i − tâm_i)` rồi tính hàm. Tâm nằm bên trong miền và mỗi thành phần có thể khác nhau. Giá trị tốt nhất đều bằng 0 tại `u = tâm`. Bộ tối ưu nhận điểm qua hàm chấm như lúc chạy mạng, còn tọa độ tâm chỉ dùng để tạo dữ liệu và kiểm chứng.

| Hàm | Mục đích | Cách chấm với vector z |
|---|---|---|
| Sphere | Một lòng chảo lồi, đo khả năng tiến sát nghiệm | Tổng `z_i²` |
| Rastrigin | Nhiều lòng chảo cục bộ, đo khả năng thử các vùng khác nhau | Tổng `z_i² + 10(1 − cos(2πz_i))` |
| Ackley | Vùng ngoài tương đối phẳng, có gợn và hố sâu ở giữa | Công thức Ackley với `a = 20`, `b = 0,2`, `c = 2π` |

Mỗi hàm có hai mức 4 và 10 chiều. Mỗi mức dùng 30 cặp lượt, seed 0 tới 29, chia đều cho 3 tâm cố định. Một cặp GA và WOA có cùng tâm, cùng quần thể đầu, cùng cấu hình 32 cá thể và 90 vòng. Tổng ngân sách mỗi lượt là 2.912 lần chấm kể cả quần thể đầu. Thứ tự chạy hai thuật toán đổi qua lại theo seed. Độ rộng miền chuẩn hóa là 10,24 cho Sphere và Rastrigin, 65,536 cho Ackley.

Tài liệu của Simon Fraser University mô tả ba hàm gốc. Phép thử dùng tâm dịch chuyển và đếm lượt gọi hàm theo cách tiếp cận của COCO, với thiết lập riêng như bảng trên. [Sphere](https://www.sfu.ca/~ssurjano/spheref.html) · [Rastrigin](https://www.sfu.ca/~ssurjano/rastr.html) · [Ackley](https://www.sfu.ca/~ssurjano/ackley.html) · [Bộ BBOB](https://coco-platform.org/testsuites/bbob/overview.html) · [Phương pháp đánh giá COCO](https://doi.org/10.1109/TEVC.2022.3210897)

## Đọc kết quả

Đặt trước mốc gần tối ưu `f − f* ≤ 0,01` và mốc thăm dò dễ hơn `f − f* ≤ 1`. Với cả ba hàm, `f* = 0`. Cột `hit_call` đếm lần chấm đầu tiên đạt mốc 0,01. Ô trống nghĩa là lượt chạy chưa đạt trong 2.912 lần chấm.

| Hàm | Chiều | Gần tối ưu GA | Gần tối ưu WOA | Sai số cuối trung vị GA | Sai số cuối trung vị WOA |
|---|---:|---:|---:|---:|---:|
| Sphere | 4 | 30/30 | 2/30 | 0,000470 | 0,112 |
| Sphere | 10 | 23/30 | 0/30 | 0,00737 | 8,92 |
| Rastrigin | 4 | 0/30 | 0/30 | 0,559 | 12,7 |
| Rastrigin | 10 | 0/30 | 0/30 | 8,01 | 65,0 |
| Ackley | 4 | 0/30 | 0/30 | 0,483 | 6,88 |
| Ackley | 10 | 0/30 | 0/30 | 1,74 | 16,7 |

GA số thực hiện tại tiến sát nghiệm tốt hơn WOA trên Sphere trong phép đo này. Trên hai hàm nhiều cực tiểu, cả hai cấu hình đều trượt mốc 0,01. Ở mốc thăm dò 1, Rastrigin 4 chiều cho GA 16/30 và WOA 0/30. Ackley 4 chiều cho GA 30/30 và WOA 0/30. Mốc thăm dò giúp tách hai mức tiến bộ khi mốc chặt chưa có lượt đạt. Chẳng hạn, Rastrigin có nghiệm cục bộ khác nghiệm toàn cục nhưng vẫn có thể rơi dưới 1.

Cột `ert_calls` cộng lượt chấm tới đích của các lượt đạt và toàn bộ ngân sách của các lượt trượt rồi chia cho số lượt đạt. Đây là ước tính chi phí tới đích nếu xem mỗi lượt là một lần thử lại, nên có thể lớn hơn 2.912. Ô ERT để trống khi cả 30 lượt đều trượt. Trung vị của riêng lượt thành công có thể thấp ngay cả khi xác suất thành công rất thấp, vì vậy nên đọc cùng số lần đạt.

Các số liệu mô tả đúng bản cài GA và WOA trong dự án, ba tâm đã công bố và ngân sách trên. Sphere chỉ có một cực tiểu. Rastrigin và Ackley thêm bài kiểm tra nhiều cực tiểu, nhưng kết quả từ hai hàm vẫn chưa đủ để xếp hạng khả năng tìm kiếm toàn cục nói chung.

Chạy lại toàn bộ hoặc chạy nhanh để kiểm tra chương trình.

```bash
python -m Extras.benchmarks --out Extras/ket_qua_chay_lai
python -m Extras.benchmarks --seeds 3 --population 8 --steps 8 --out Extras/kiem_tra_nhanh
```

## Các giả thuyết để dành

Những dòng dưới đây là thiết kế thí nghiệm cho lần mở rộng sau, kèm cách nhận ra giả thuyết bị bác bỏ.

| Câu hỏi | Cách thử và dấu hiệu bác bỏ |
|---|---|
| Một tuyến được khai báo hai lần có đổi kết quả GA hoặc WOA không? | Nhân đôi tuyến nhưng giữ nguyên các cạnh và tổng luồng của hai bản sao. Tập luồng khả thi giữ nguyên. Nếu sai số và tỉ lệ đạt mục tiêu ổn định qua nhiều seed, chưa thấy tác động của cách mã hóa |
| Thêm nút trung gian có khiến bài toán khó hơn về nghiệm hay chỉ tốn thời gian chấm? | Chia một đoạn thành hai đoạn nối tiếp, giữ sức chứa mỗi đoạn và chia thời gian lúc vắng sao cho tổng bằng đoạn cũ. Đối chiếu nghiệm trước và sau rồi đo thời gian mỗi lượt chấm |
| WOA có nhạy hơn khi nghiệm gần biên? | Dùng cùng ba hàm và ngân sách, dời tâm tới gần biên rồi ghi số lần giá trị bị cắt về 0 hoặc 1. Giả thuyết yếu đi nếu tỉ lệ đạt và sai số của WOA đổi ít hơn hoặc ngang GA qua các tâm mới |
| Kết quả tốt trên Rastrigin còn giữ khi xoay địa hình không? | Xoay hệ tọa độ quanh nghiệm tối ưu để các chiều liên hệ với nhau. Giữ miền mã hóa và ngân sách, rồi đo lại. Nếu khoảng cách giữa hai cấu hình thay đổi lớn, thứ hạng cũ phụ thuộc hướng các trục |

## Thử cứu một ca vừa đủ sức chứa

`python -m Extras.tight_cut_witness` chạy `tight_cut_100` trên 8 seed mới 3000–3007. Với quần thể ngẫu nhiên, GA và WOA đều 0/8 hợp lệ. Khi thay một ứng viên đầu bằng cùng một phương án tính tay đã biết hợp lệ, cả hai đạt 8/8 hợp lệ và 8/8 trong 1%. Dữ liệu gốc ở [tight_cut_witness.csv](tight_cut_witness.csv).

Đây là phép can thiệp vào khởi tạo. Nghiệm gợi ý đã mang thông tin về sức chứa, nên hai nhóm khởi tạo có lượng thông tin khác nhau. Thử nghiệm giúp chẩn đoán vì sao ca sát biên khó. Có thể dùng hướng này để tìm hiểu khởi tạo có ràng buộc hoặc phép sửa nghiệm, với chi phí dựng phương án được ghi riêng. Phần chuẩn số của đồ án nằm ở [oracle.py](../research/oracle.py).
