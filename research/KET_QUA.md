# Kết quả sàng lọc và xác nhận

Vòng đầu có **21 ca × 8 seed × 2 thuật toán = 336 lượt**. Vòng xác nhận có **4 ca × 30 seed mới × 2 thuật toán = 240 lượt**. Mỗi lượt dùng 2.912 lần chấm, kể cả quần thể ban đầu. Danh sách được khóa sau vòng đầu rồi mới dùng seed 1000–1029. Phép tăng số vòng, phép đo quy mô và bộ hàm ở Extras có ngân sách và mục đích riêng.

`many_to_one` được chọn vì là ca có nghiệm trong đó tỷ lệ hợp lệ của hai phương pháp lệch nhau ở vòng đầu. `light` có cả hai bên 8/8 hợp lệ, với số lần trong 1% lệch 8 so với 1. Mốc ngày thường và ca vô nghiệm đã được giữ theo giao thức.

## Bốn tình huống đưa vào bài chính

| Ca xác nhận | Hợp lệ GA / WOA | Trong 1% GA / WOA | Gap trung vị GA / WOA |
|---|---:|---:|---:|
| Ngày thường, `normal` | 30/30 · 30/30 | 0/30 · 5/30 | 3,30% · 4,41% |
| Năm nguồn về một đích, `many_to_one` | 30/30 · 28/30 | 0/30 · 0/30 | 4,73% · 6,59% |
| Tải nhẹ, `light` | 30/30 · 30/30 | 28/30 · 17/30 | 0,48% · 0,61% |
| Cao điểm và đóng E23, `cut` | 0/30 · 0/30 | Không có đích chi phí | Không có nghiệm hợp lệ |

Gap tính với cận dưới của chuẩn số và chỉ lấy các lượt hợp lệ. Kèm bảng này với đường hội tụ theo **số lượt chấm**, thay vì chỉ chiếu một seed may mắn. [Hình hội tụ](results/Hoi_tu_xac_nhan.svg) · [Bảng tổng hợp](results/confirm_summary.csv) · [So từng cặp seed](results/confirm_paired.csv)

- **Ngày thường.** GA có trung vị thấp hơn. WOA có 5 lượt trong 1%, gồm một nghiệm 5.036,96 xe·phút so với cận dưới 5.035,93. WOA cho đuôi kết quả tốt hơn trong một số lượt, đồng thời phần giữa phân bố rộng hơn. Khoảng bootstrap của chênh lệch trung vị theo cặp bao gồm 0, nên tránh diễn giải rằng GA thường có lợi thế rõ trên mọi seed.
- **Nhiều nguồn chung một đích.** WOA có trung vị tìm thấy nghiệm hợp lệ 128 lượt chấm trong 28 lượt thành công. GA là 210 lượt chấm trên 30 lượt thành công. Tính cả những lần phải dùng hết ngân sách, ERT để tìm nghiệm hợp lệ là khoảng 227 cho GA và 332 cho WOA. Chỉ có hai cặp trượt lệch về một phía, nên xem chênh lệch tỷ lệ 30 so với 28 là tín hiệu trong mẫu. Trong 28 cặp cùng hợp lệ, trung vị chi phí GA thấp hơn khoảng 1,94% của chuẩn, với khoảng bootstrap mô tả từ 1,07% đến 2,53%.
- **Tải nhẹ.** GA đạt ngưỡng ở nhiều lượt hơn, 28/30 so với 17/30. Trong các lượt chạm đích, WOA mất trung vị 274 lần chấm và GA mất 2.463. ERT tới ngưỡng, có tính cả các lượt trượt, lần lượt khoảng 2.514 cho WOA và 2.670 cho GA. Do đó câu hỏi “chạm nhanh tới mức nào” và “một lượt đáng tin cậy tới mức nào” có hai câu trả lời.
- **Vô nghiệm.** 590 xe phải qua lát cắt có sức chứa 520. Cả hai kết thúc với vi phạm trung vị 70. Giới hạn dưới 70 đến từ lát cắt. Cột chi phí hợp lệ để trống.

Thời gian trung vị tìm kiếm của mỗi lượt khoảng 115 đến 127 mili giây ở cấu hình đã chạy, có chi phí ghi từng lần chấm, trên Linux x86-64 và Python 3.12.14. Chênh lệch cỡ vài mili giây phụ thuộc cách cài, máy và tải nền. Số lượt gọi hàm chấm là đơn vị chính khi so tốc độ tìm nghiệm.

## Đào sâu case tải nhẹ bằng cách tăng số vòng

Dùng 12 seed khác, 2000–2011. Mỗi thuật toán được chạy lại từ đầu ở 90 và 180 vòng. Mỗi cặp giữ quần thể 32 và cùng điểm xuất phát. Từ 90 tới 180 vòng, GA giảm chi phí ở 12/12 cặp và trung vị gap đi từ khoảng 0,46% xuống 0,009%. WOA giảm chi phí ở 2 cặp, ngang ở 6 và tăng ở 4. Số lượt WOA trong 1% là 9/12 ở 90 vòng và 8/12 ở 180 vòng.

Một lượt GA dài có thể tiếp tục đúng đường đi của lượt ngắn vì toán tử của bản này không dùng tổng số vòng. WOA tính lịch `a` từ tổng số vòng, nên đổi số vòng làm các bước đầu khác đi. Kết quả **tốt nhất đã lưu trong từng lượt** vẫn có thể cải thiện qua các vòng. Kết quả của **hai lượt WOA có lịch khác nhau** có thể chênh theo cả hai hướng. [Số từng lượt](results/light_budget_runs.csv) · [Bảng ghép cặp](results/light_budget_paired.csv)

## Các đối chứng và case giữ ở phụ lục

- `tight_cut_100` thực sự có nghiệm, nhưng GA và WOA đều 0/8 trong vòng đầu. Năm hành lang có sức chứa `[88,92,108,87,85]`, tổng đúng 460. Một cách chia để tự kiểm là O1 `[88,0,2,0,0]`, O2 `[0,92,1,3,0]`, O3 `[0,0,105,0,0]`, O4 `[0,0,0,84,0]`, O5 `[0,0,0,0,85]`. Tổng từng dòng bằng nhu cầu và từng cột bằng sức chứa. Phép chấm kiểm tra cả cạnh trước và sau lát cắt. Với 8 seed mới, khởi tạo ngẫu nhiên vẫn trượt cả 8, còn đưa phương án tính tay vào quần thể đầu thì cả hai giữ được nghiệm hợp lệ cả 8. Thử riêng này đưa thông tin khả thi vào khởi tạo. [Đối chứng có gợi ý](../Extras/tight_cut_witness.csv)
- `irregular_layout` đổi tọa độ hiển thị. Kết quả khớp ngày thường ở 16/16 lượt đối chứng. `far_detour` đổi **thời gian** đường chuyển hàng, làm chi phí chuẩn tăng từ khoảng 5.540,20 ở ca đóng E23 lên 5.886,20 xe·phút. Hai thay đổi trả lời hai câu hỏi khác nhau.
- `sparse_routes` dùng 13 gene và giữ chi phí chuẩn gần như ngày thường. `shortcuts` dùng 35 gene, chuẩn giảm từ 5.035,93 xuống 4.987,40. Thay số tuyến đồng thời thay tập phương án, nên bảng chỉ cho thấy tác động tổng hợp. Ví dụ này giúp giải thích vì sao cần đo chất lượng tìm được ngay cả khi bài toán mới có chuẩn tốt hơn.
- `overpass` và `at_grade` làm rõ chuyện đường cắt nhau. Cặp mô hình đi từ chuẩn 261,08 đến 323,55 xe·phút khi hai tuyến phải dùng chung đoạn giới hạn sức chứa. Hai nét giao nhau trên hình tự chúng không tạo ràng buộc.

## Mạng lớn nhất đã chạy

| Nút | Cạnh | Giây tìm kiếm GA / WOA | Đỉnh cấp phát Python GA / WOA |
|---:|---:|---:|---:|
| 50 | 61 | 0,012 · 0,011 | 0,39 · 0,41 MiB |
| 100 | 111 | 0,022 · 0,018 | 0,58 · 0,61 MiB |
| 250 | 261 | 0,039 · 0,039 | 1,13 · 1,19 MiB |
| 500 | 511 | 0,077 · 0,077 | 2,07 · 2,18 MiB |
| 1.000 | 1.011 | 0,178 · 0,169 | 4,00 · 4,23 MiB |
| 2.000 | 2.011 | 0,306 · 0,311 | 7,71 · 8,14 MiB |
| **5.000** | **5.011** | **0,747 · 0,737** | **19,10 · 20,27 MiB** |

Giây là trung vị ba seed với 304 lượt chấm. Đỉnh cấp phát lấy ở một lượt riêng. Mọi nút và cạnh đều nằm trên ít nhất một tuyến. Chia cạnh giữ 25 trọng số và giữ chi phí của cùng một phân bổ hợp lệ, nhưng làm tăng số đoạn được chấm. Lượng vi phạm của ứng viên sai có thể được tính trên nhiều đoạn con, nên phép đo dùng để đọc chi phí xử lý. Mốc 5.000 là cỡ lớn nhất đã kiểm tra theo giao thức này. Độ khó của một bài có thêm nhiều cặp và tuyến cũng phụ thuộc số gene và miền hợp lệ. [Hình quy mô](results/Quy_mo.svg) · [CSV quy mô](results/scale_summary.csv)

## Benchmark ngoài mạng

Ở 360 lượt trong [Extras](../Extras/README.md), dùng cùng 2.912 lượt chấm trên hàm dịch tâm. Với Sphere 4 chiều, ở ngưỡng 0,01, GA đạt 30/30, WOA 2/30. Sphere 10 chiều là 23/30 và 0/30. Rastrigin và Ackley dịch tâm đều 0/30 ở ngưỡng chặt đó trên cả hai chiều đã thử. Ngưỡng rộng hơn còn ghi nhận được tiến bộ, có thể xem ở bảng Extras. Phần này đo khả năng trên những bề mặt có tối ưu biết trước và nhiều cực tiểu, với đúng cấu hình đã cài.

## Danh mục 21 tình huống đã sàng lọc

Tỷ lệ là GA / WOA trên 8 seed. Cột 1% để trống khi chuẩn xác định vô nghiệm. Đọc kết quả sàng lọc như dữ liệu khám phá và ưu tiên bốn ca xác nhận khi kết luận.

| Ca | Thay đổi được kiểm tra | Hợp lệ GA / WOA | Trong 1% GA / WOA |
|---|---|---:|---:|
| `normal` | 460 xe qua 5 hành lang. Mốc để so sánh khi có sự cố. | 8/8 · 8/8 | 0/8 · 0/8 |
| `peak` | Tăng từ 460 lên 590 xe, giữ sức chứa các đoạn. | 8/8 · 8/8 | 0/8 · 0/8 |
| `incident` | Giữ 460 xe, sức chứa E23 giảm từ 160 còn 80. | 8/8 · 8/8 | 0/8 · 1/8 |
| `closed` | Giữ 460 xe. Các tuyến đi qua E23 được bỏ khi chia xe. | 8/8 · 8/8 | 0/8 · 1/8 |
| `cut` | 590 xe cần qua lát cắt. Bốn đoạn còn mở chỉ chứa 520 xe. | 0/8 · 0/8 | Không áp dụng |
| `light` | Còn 40% nhu cầu ngày thường, sức chứa giữ nguyên. | 8/8 · 8/8 | 8/8 · 1/8 |
| `skewed` | Giữ tổng 460 xe, tập trung nhu cầu tại O1 và O3. | 8/8 · 8/8 | 0/8 · 0/8 |
| `tight_cut_96` | 460 xe chia qua năm đoạn có tổng sức chứa 480. | 8/8 · 8/8 | 0/8 · 0/8 |
| `tight_cut_99` | 460 xe chia qua năm đoạn có tổng sức chứa 464. | 8/8 · 8/8 | 0/8 · 0/8 |
| `tight_cut_100` | 460 xe chia qua năm đoạn có tổng sức chứa 460. | 0/8 · 0/8 | 0/8 · 0/8 |
| `double_close_feasible` | Đóng E14 và E23, 330 xe đi qua ba hành lang còn mở. | 8/8 · 8/8 | 6/8 · 6/8 |
| `isolate_od` | Đóng E01 là lối ra duy nhất của O1. O1 vẫn phát 90 xe. | 0/8 · 0/8 | Không áp dụng |
| `sparse_routes` | Giữ tuyến đi thẳng và các tuyến đổi tối đa một hàng. Có 13 trọng số. | 8/8 · 8/8 | 8/8 · 4/8 |
| `far_detour` | Cùng ca đóng E23, thời gian đường vắng trên đường đổi hàng nhân ba. | 8/8 · 8/8 | 0/8 · 0/8 |
| `irregular_layout` | Xáo tọa độ nút, giữ nguyên cạnh, thời gian, sức chứa và các tuyến. | 8/8 · 8/8 | 0/8 · 0/8 |
| `many_to_one` | Năm nguồn đi về T3. Tổng 460 xe, vẫn có năm lựa chọn hành lang mỗi cặp. | 8/8 · 7/8 | 0/8 · 0/8 |
| `one_to_many` | O3 cấp xe cho năm đích. Tổng 460 xe, vẫn có năm lựa chọn hành lang mỗi cặp. | 8/8 · 8/8 | 0/8 · 0/8 |
| `cross_od_swap` | Đảo thứ tự đích từ T5 đến T1 để nhiều tuyến phải đổi hàng. | 8/8 · 8/8 | 0/8 · 0/8 |
| `shortcuts` | Thêm hai cạnh chéo qua lát cắt và 10 tuyến ứng viên. Có 35 trọng số. | 8/8 · 8/8 | 0/8 · 3/8 |
| `overpass` | Hai tuyến nhanh cắt nhau trên hình, sức chứa độc lập. Mỗi nhóm có 70 xe và một đường vòng. | 8/8 · 8/8 | 8/8 · 8/8 |
| `at_grade` | Hai tuyến nhanh chia một đoạn có sức chứa 80 xe. Mỗi nhóm có 70 xe và một đường vòng. | 8/8 · 8/8 | 8/8 · 8/8 |

[Danh mục và cận chuẩn](results/catalog.json) · [Toàn bộ lượt sàng lọc](results/screen_runs.csv) · [Tóm tắt sàng lọc](results/screen_summary.csv)
