# Số đo, tiêu chí và bài học từ Dijkstra

Tài liệu này giữ phép đo cơ sở để đối chiếu lúc tập chạy. Phần dùng cho báo cáo hiện tại là [kết quả sàng lọc và xác nhận](../research/KET_QUA.md).

## Số đo trên mạng chính 50 nút

Dữ liệu ở `results/`. Mạng có 50 nút, 61 cạnh và 5 cặp nguồn và đích. Mỗi cặp có 5 tuyến ứng viên. Mỗi kịch bản chạy GA và WOA với seed 0 đến 29, 32 ứng viên, 90 vòng cập nhật, tổng 2.912 lượt chấm mỗi bên. Các cặp cùng seed mở đầu từ cùng một quần thể. Tỉ lệ hợp lệ đếm số lượt cuối có phương án hợp lệ. Chi phí, Q1 và Q3 chỉ tính trên các lượt hợp lệ. Thời gian tính đo riêng, không tính form, tạo quần thể đầu và xuất file. Xem cấu hình trong `results/environment.json`.

| Kịch bản | Hợp lệ GA | Hợp lệ WOA | Trung vị GA (xe·phút) | Trung vị WOA (xe·phút) |
|---|---:|---:|---:|---:|
| Ngày thường | 30/30 | 30/30 | 5.205,35 | 5.281,83 |
| Giờ cao điểm | 30/30 | 30/30 | 7.088,82 | 7.300,64 |
| Hẹp làn E23 | 30/30 | 30/30 | 5.487,20 | 5.661,16 |
| Đóng E23 | 30/30 | 30/30 | 5.699,91 | 5.921,08 |
| Cao điểm + đóng E23 | 0/30 | 0/30 | Không có | Không có |

- **Ngày thường.** GA có chi phí trung vị thấp hơn và đứng trước WOA ở 19 trong 30 cặp seed. WOA lại có lượt tốt nhất khoảng 5.037,07 xe·phút (seed 9), thấp hơn lượt tốt nhất của GA khoảng 5.121,31 (seed 16). Đây là hai câu hỏi khác nhau khi đọc kết quả. Trung vị mô tả một lượt điển hình, còn nghiệm tốt nhất cho thấy cấu hình từng đạt mức nào.
- **Hẹp làn.** GA thấp hơn ở 24 trong 30 cặp seed. Seed 7 cho 5.472,50 xe·phút ở GA và 5.609,92 ở WOA. Tại seed này, luồng E23 giảm từ 149,70 còn 79,70 xe với GA và từ 125,21 còn 80,00 xe với WOA. So thêm E05 và E14 trên form để thấy xe được chia lại.
- **Đóng E23.** Hai thuật toán vẫn tìm được cách chở đủ 460 xe ở cả 30 lượt. Đổi sang cao điểm, 590 xe cần qua và lát cắt chỉ còn sức chứa 520. Trung vị điểm vi phạm của hai bên là 70,00. Chứng cứ vô nghiệm đến từ phép đếm sức chứa, còn điểm vi phạm mô tả phương án thử.

## Hành lang nào nhạy nhất với việc giảm sức chứa?

Giữ nhu cầu 460 xe. Lần lượt giảm 50% sức chứa từng cạnh trong năm cạnh bắc qua lát cắt. Mỗi cạnh dùng seed 0 đến 7. Với cùng thuật toán và seed, lấy `100 × (chi phí khi hẹp / chi phí ngày thường − 1)` nếu cả hai lượt hợp lệ. Sau đó lấy trung vị của tám chênh lệch.

| Cạnh bị giảm 50% | Sức chứa mới | Trung vị tăng GA | Trung vị tăng WOA | Cặp hợp lệ mỗi bên |
|---|---:|---:|---:|---:|
| E05 | 65 | 0,69% | 2,54% | 8/8 |
| E14 | 67,5 | 3,48% | 1,79% | 8/8 |
| E23 | 80 | 5,79% | 3,06% | 8/8 |
| E32 | 62,5 | 2,13% | 1,94% | 8/8 |
| E41 | 65 | 0,31% | 0,24% | 8/8 |

E23 đứng đầu trong phép quét năm hành lang của cả hai cấu hình. Hàng giữa có thời gian đường vắng thấp, nhiều nhóm có thể rẽ vào dùng chung. Khi E23 chỉ còn 80 chỗ, ví dụ ở seed 7 cho thấy phần luồng trên hàng giữa giảm và các hành lang khác tiếp nhận thêm. Xếp hạng trên là kết quả trong năm cạnh được thử, ở mức giảm 50% và nhu cầu 460 xe.

## Đọc đúng các file kết quả

| File | Dùng khi |
|---|---|
| `runs.csv` | Xem từng seed, chi phí nếu hợp lệ, vi phạm, checkpoint hợp lệ đầu tiên và giây |
| `summary.csv` | Lấy tỉ lệ, trung vị, Q1/Q3, nghiệm hợp lệ tốt nhất và seed của nó |
| `paired.csv` | So theo cặp cùng seed. Cột `median_GA_minus_WOA` là trung vị của các hiệu theo cặp |
| `sensitivity.csv`, `sensitivity_runs.csv` | Kiểm tra phép quét 5 hành lang và đối chiếu số liệu theo seed |
| `sample_runs.json` | Xem luồng từng tuyến, từng cạnh và lịch sử mỗi vòng ở seed mẫu |
| `network_used.json` | Bản đồ, tuyến và kịch bản đúng như lúc chạy thực nghiệm |
| `results/demo_tkinter.png`, `DEMO_DU_PHONG.html` | Minh họa cho slide và mở nhanh nếu máy trình chiếu có vấn đề |

Bài nhỏ hai tuyến có đáp án chuẩn để kiểm thử. Mạng chính dùng so sánh các nghiệm tìm được trong tập tuyến cho trước và ngân sách đã ghi. Bản đo hiện tại dùng Python trên Linux. Nhóm có thể chạy lại trên máy trình chiếu và lưu vào thư mục mới trước khi chọn số nộp.

## Đối chiếu đề giảng viên

| Tiêu chí trong đề AI | Minh chứng trong folder | Việc nhóm hoàn tất trước nộp |
|---|---|---|
| Chương trình · 4đ | Lõi GA và WOA tự cài, hàm chấm chung, 5 kịch bản, kiểm thử, phép đo và form Tkinter | Cả nhóm chạy lại từ ZIP trên máy trình chiếu. Đối chiếu mọi yêu cầu bổ sung thầy xác nhận |
| Báo cáo · 4đ | Dàn ý, mô hình, công thức, ví dụ tính tay, bảng số liệu và nguồn | Lấy mẫu chính thức, ghi đúng việc từng người làm, tự diễn giải số đo và đính Turnitin thật theo đề |
| Trình bày và hỏi đáp · 2đ | Lộ trình slide, kịch bản demo, câu vấn đáp nối code với dữ liệu | Tập cả 5 người kể luồng, kiểm tra thời lượng và thử máy offline |
| Bổ sung thuật toán seminar | `algorithms/woa.py` giải cùng bài với GA | Nhắc rõ trong báo cáo cách WOA dùng phương trình gốc và khác kỹ thuật nào với mã seminar |
| Form và thư viện trong danh sách | `app.py` dùng Tkinter và Canvas. Tkinter có tên trong danh sách của đề | Xác nhận môi trường chạy và cách tính phần cộng nếu lớp có hướng dẫn riêng |

Đề danh sách ghi bài mạng/luồng giao thông dùng GA ở mục 17, ô GA × Network flow là 8. Phần bổ sung yêu cầu dùng đúng thuật toán seminar cho cùng bài toán. Mốc 16/11 của seminar thuộc lịch riêng. Mẫu báo cáo, slot và thời lượng của buổi cuối kỳ cần lấy theo thông báo của môn AI. [Danh sách thư viện GUI trong đề](https://www.pythonguis.com/faq/which-python-gui-library/)

## Rút kinh nghiệm từ bài Dijkstra

PDF cũ có 88 trang. Mục 6.2.5 đã chỉ ra luồng từ `BtnFindPath_Click` tới `FindShortestPath`, rồi lưu `result.Path` và vẽ lại bản đồ. Chương 9 cũng ghi cách sinh đồ thị thử, cấu hình máy và số lượt đo. Repo có mã `DijkstraEngine.cs`, dữ liệu CSV, lớp đồ thị và UI WinForms để mở đối chiếu. Phần có thể mang sang bài AI là sơ đồ luồng chương trình gắn với hàm thật và phép đo có dữ liệu gốc. [Repo Dijkstra](https://github.com/VoidX-SS/Dijkstra_Group-7_DSA) · [Hàm tìm đường trong repo](https://github.com/VoidX-SS/Dijkstra_Group-7_DSA/blob/main/Algorithms/DijkstraEngine.cs)

Nhận định của leader hợp lý ở chỗ thời gian dành cho việc cả nhóm hiểu và chạy được code đáng tăng lên. Theo phần leader kể, điểm vấn đáp tách nhau ngay ở các bạn ít chạm vào thuật toán. Mẫu cũ đã có luồng code trong báo cáo, nên việc bổ sung nhiều trang nữa khó thay được lúc một bạn phải tự lần dữ liệu trên màn hình. Bài AI vẫn dành 4 điểm cho báo cáo. Cách cân bằng là khóa nội dung báo cáo ở mức đủ mô hình, cách đo, số liệu và giải thích, rồi chuyển phần thời gian còn lại sang luyện nói và đọc code. Mỗi người vừa có phần làm thật, vừa có một người đọc chéo trước buổi chấm.

Vụ bảy thuật toán sắp xếp là dữ kiện từ trải nghiệm môn trước. Với môn AI, xác nhận sớm phần yêu cầu đã dặn miệng và giữ lại câu trả lời cùng checklist. Có thể nhắn giảng viên như sau.

> Thưa thầy, nhóm em đăng ký tối ưu luồng giao thông bằng GA và WOA. Nhóm tự cài hai thuật toán, làm form bằng Tkinter và đo trên cùng các kịch bản. Ngoài các tiêu chí trong PDF, buổi chấm có yêu cầu nào đã dặn trên lớp mà nhóm cần tích hợp từ seminar không ạ? Thầy cho nhóm xin mẫu báo cáo, cách nộp và thời lượng demo để nhóm chuẩn bị đúng ạ.

## Nguồn để đưa vào báo cáo

- S. Mirjalili và A. Lewis, *The Whale Optimization Algorithm*, Advances in Engineering Software, 95, 51–67, 2016. Dùng phần phương trình và giả mã. [DOI bài báo](https://doi.org/10.1016/j.advengsoft.2016.01.008)
- A. E. Eiben và J. E. Smith, *Introduction to Evolutionary Computing*, ấn bản 2, Springer, 2015. Dùng phần biểu diễn số thực, chọn lọc và toán tử tiến hóa. [Sách tham khảo](https://doi.org/10.1007/978-3-662-44874-8)
- FHWA, *Implementation Report for the Long-Distance Travel Demand Model*, mục 3.3 về hàm BPR và các tham số. [Tài liệu FHWA](https://www.fhwa.dot.gov/policyinformation/analysisframework/docs/long-distance_model_implementation_report_final.pdf)
- Python Software Foundation, tài liệu `tkinter`. Python GUIs, bài tổng hợp các thư viện GUI được liên kết trong đề. [Tài liệu Tkinter](https://docs.python.org/3/library/tkinter.html) · [Danh sách Python GUIs](https://www.pythonguis.com/faq/which-python-gui-library/)
- Tài liệu nội bộ gồm PDF *Danh sách đề tài, học phần Trí tuệ nhân tạo*, PDF đồ án Dijkstra, và ZIP seminar Đom Đóm để đối chiếu WOA. [Thư mục seminar](https://drive.google.com/drive/u/0/folders/1QLje38gUwd86hvxT4HNZrgJSJPdGkN34)
