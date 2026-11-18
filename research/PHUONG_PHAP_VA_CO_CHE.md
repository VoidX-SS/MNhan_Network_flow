# Đo GA và WOA trên cùng bài chia luồng

Câu hỏi chính là khi nào một thuật toán **tìm được cách chia xe sớm**, khi nào nó **thường xuyên đạt chi phí thấp**, và điều gì khiến kết luận đổi. Mạng chính có 50 nút, 61 cạnh có hướng và 25 trọng số chia xe. Cả hai lõi nhận cùng dữ liệu, cách chuẩn hóa trọng số, ràng buộc sức chứa và ngân sách gọi hàm chấm. Chương trình ghi riêng nghiệm hợp lệ, mức gần tối ưu và thời gian. Xem [giao thức](PROTOCOL.md) và [kết quả](KET_QUA.md) cùng nhau.

## Chuẩn đối chiếu và cách đọc số lần đạt đích

Gọi `xᵣ` là số xe đi tuyến `r` và `fₑ` là tổng xe trên cạnh `e`. Khi có tuyến mở, các trọng số của mỗi cặp nguồn đích được chuẩn hóa thành tỷ lệ. Mọi cách chia không âm và cộng đủ nhu cầu của cặp đều biểu diễn được bằng một bộ trọng số trong `[0, 1]`. Do đó có thể kiểm chứng trong không gian số xe trên tuyến.

- Mỗi cặp cần `Σ xᵣ = qₖ`, với `xᵣ ≥ 0`. Cạnh mở cần `fₑ ≤ cₑ`. Tất cả là ràng buộc tuyến tính khi tập tuyến đã cố định. Đóng một cạnh loại các tuyến đi qua cạnh đó.
- BPR cho chi phí trên cạnh là `t₀ₑ × (fₑ + 0,15 fₑ⁵/cₑ⁴)`. Đạo hàm bậc hai theo `fₑ` là `3t₀ₑ fₑ³/cₑ⁴ ≥ 0` khi `fₑ ≥ 0` và `cₑ > 0`. Tổng chi phí lồi theo luồng tuyến vì mỗi `fₑ` là tổng tuyến tính của các `xᵣ`.
- `oracle.py` dùng quy hoạch tuyến tính để kiểm tra khả thi. Nó lấy `U` từ một nghiệm hợp lệ đã được chấm lại và lấy `L` từ cận tiếp tuyến lồi, có chừa dung sai số. Với bài cùng tập tuyến, kết quả dùng khoảng số `L ≤ F* ≤ U` và chỉ gắn `certified` khi khoảng tương đối rộng tối đa 0,01%.
- Ghi một lần **trong 1%** khi nghiệm hợp lệ và `F ≤ 1,01L`. Nếu `F` gần mốc nhưng vẫn cao hơn đích bảo thủ này, lượt đó chưa được đếm. Khoảng chuẩn số và giá trị thực nghiệm đều lưu trong CSV. Có thể kiểm tra bài 4 nút bằng phép tính tay riêng.

Ví dụ ở ca ngày thường, chuẩn số nằm sát 5.035,928 xe·phút. Một lượt 5.200 xe·phút hoàn toàn có thể hợp lệ mà vẫn nằm ngoài 1%. Một lượt WOA có thể đạt ngưỡng này dù trung vị WOA cao hơn trung vị GA. Đó là lý do nên trình bày cả số lần đạt đích và phân bố kết quả.

Các bài tham khảo cho phần này gồm mô hình hệ thống tối ưu, BPR và cận tiếp tuyến của bài lồi. [System optimum traffic assignment](https://www.civil.iitb.ac.in/tvm/nptel/206_lnTse/web/web.html) · [FHWA BPR](https://www.fhwa.dot.gov/policyinformation/analysisframework/docs/long-distance_model_implementation_report_final.pdf) · [Jaggi 2013](https://proceedings.mlr.press/v28/jaggi13.html) · [SciPy HiGHS](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html)

## Vì sao hai thuật toán có thể cho kết quả khác nhau

| Trong code | GA | WOA |
|---|---|---|
| Tạo nghiệm mới | Hai bố mẹ được chọn bằng đấu giải. Lai số thực lấy từng giá trị giữa bố và mẹ. Đột biến có thể đẩy một gene ra khỏi khoảng đó | Cá voi cập nhật theo nghiệm dẫn đầu, một cá voi ngẫu nhiên hoặc bước xoắn quanh nghiệm dẫn đầu. Giá trị được chặn về `[0, 1]` |
| Giữ thông tin tốt | Giữ nghiệm tốt nhất qua các vòng. Lai ghép có thể dùng một phần cách chia của nhiều bố mẹ | Giữ nghiệm dẫn đầu, dùng nó để hướng nhiều bước cập nhật của cả quần thể |
| Thăm vùng khác | Mỗi gene có xác suất đột biến `1/D`, tức trung bình khoảng một gene mỗi con. Bố mẹ được chọn lại mỗi con | Với lịch `a` giảm từ 2 đến 0, nhánh theo cá voi ngẫu nhiên cần `p < 0,5` và `abs(A) ≥ 1`. Nhánh đó chỉ có cơ hội xảy ra ở nửa đầu. Các nhánh còn lại vẫn cập nhật vị trí |
| Đọc kết quả | Ở tải nhẹ, nhiều lượt GA đạt đích vào cuối ngân sách | Một số lượt WOA chạm đích sớm. Một số khác dừng ở nghiệm hợp lệ có chi phí cao hơn. Đổi tổng số vòng còn đổi lịch `a` và đường đi của một lượt |

Trong bài chia luồng, đổi gene tức là đổi tỷ trọng của cả nhóm xe. Ví dụ tăng một gene có thể kéo nhiều xe lên cùng đoạn và làm các tỷ lệ khác của cặp nhỏ đi. Tìm gần một nghiệm tốt sớm và giữ sự đa dạng đủ lâu là hai ưu tiên khác nhau. Các kết quả quan sát gợi ý cách nhìn này. Bài BPR trên luồng tuyến là bài lồi, còn không gian trọng số có chuẩn hóa và chặn biên. Phần đo khả năng thăm nhiều vùng có các hàm đa cực ở [Extras](../Extras/README.md). [Mirjalili và Lewis 2016](https://doi.org/10.1016/j.advengsoft.2016.01.008) · [Eiben và Smith 2015](https://doi.org/10.1007/978-3-662-44874-8)

## Big O theo đúng cách cài trong ZIP

Ký hiệu `V` là số nút, `E` là số cạnh, `K` là số cặp, `D` là tổng số tuyến ứng viên hay số gene, `H` là tổng số lần xuất hiện của cạnh trong mọi tuyến. `P` là số ứng viên và `T` là số vòng cập nhật. Tra cứu `dict` và `set` lấy chi phí trung bình.

| Phần | Thời gian | Bộ nhớ bổ sung | Vì sao |
|---|---|---|---|
| Chuẩn bị dữ liệu | `O(V + E + K + D + H)` | `O(V + E + K + D + H)` | Đọc đồ thị, đánh dấu tuyến mở và lập danh sách chỉ số cạnh cho từng tuyến |
| Chấm một ứng viên | `O(K + D + H + E)` | `O(K + D + E)` | Chia xe từng cặp, cộng qua từng cạnh xuất hiện, rồi tính tải và thời gian từng cạnh |
| GA cập nhật một vòng | `O(PD)` ngoài gọi chấm | `O(PD)` cho bộ gene | Đấu giải cỡ cố định, lai và đột biến qua `D` vị trí của từng con |
| WOA cập nhật một vòng | `O(PD)` ngoài gọi chấm | `O(PD)` cho bộ gene | Chọn một nhánh rồi tính vị trí mới qua `D` vị trí của từng cá voi |
| Một lượt GA hoặc WOA | `O(P(T+1)(K+D+H+E))` | `O((P+T+1)(K+D+E))` ngoài dữ liệu chung | Cả hai chấm `P(T+1)` ứng viên. Các điểm số trong quần thể và nhật ký nghiệm tốt nhất chứa cả luồng tuyến lẫn luồng cạnh |

Cận bộ nhớ nhật ký là cận trên. Nhiều checkpoint có thể trỏ đến cùng một nghiệm tốt nhất. Các công thức trên tách khỏi chuẩn SciPy, vẽ và replay GUI. Cùng Big O vẫn có thể khác thời gian theo số phép toán và cách cài. Còn chất lượng phụ thuộc cấu hình và thời lượng tìm kiếm, nên đọc cùng ngân sách, tỷ lệ đạt đích và seed.

## Nút lộn xộn và dữ liệu thật

Cạnh, chiều đi, thời gian và sức chứa quyết định bài toán. Tọa độ của nút hiện dùng để vẽ. Case `irregular_layout` hoán vị tọa độ với mọi thông số mạng giữ nguyên. Kết quả giống nhau ở 16/16 lượt đối chứng, gồm cả lần chấm đầu tìm được nghiệm. Vì vậy trình bày mạng dạng hàng để dễ chỉ hướng đi. Khi muốn mô phỏng đường xa, cần đổi thời gian hoặc quy tắc cạnh, như `far_detour` tăng thời gian các đoạn chuyển hàng.

Một nét cắt nhau trên màn hình có thể là cầu vượt. `overpass` cho hai nhóm đi qua các cạnh độc lập. `at_grade` cho hai nhóm dùng chung một cạnh có sức chứa 80 xe, buộc san tải. Nếu muốn mô tả xung đột làn, đèn tín hiệu hay chuyển động từng xe, cần thêm mô hình và dữ liệu tương ứng.

Tọa độ thật là lựa chọn nếu câu hỏi nghiên cứu gắn với một mạng cụ thể. Mạng giả lập dùng để kiểm soát từng yếu tố và có ca chứng minh được bằng tay. Khi dùng mạng thật, ngoài vị trí cần chiều đi, thời gian, sức chứa, ma trận nhu cầu và dữ liệu kiểm tra. Bản đồ thật đơn thuần chỉ thay nền hình. [FHWA Traffic Analysis Toolbox](https://highways.dot.gov/media/88726)

## Phạm vi nộp và điểm dừng

Mẫu giảng viên có bốn chương và phụ lục phân công, cài đặt. Phần đánh giá ghi 4 điểm chương trình, 4 báo cáo, 2 trình bày và vấn đáp. Dành thân bài cho bốn case xác nhận, một hình hội tụ, một bảng tỷ lệ và phép tính tay ngắn. Cả nhóm cần lần được từ gene tới tải cạnh và biết vì sao chuẩn số có thể gọi một case vô nghiệm. Bảng toàn bộ 21 ca, thử ngân sách, benchmark hàm và hoạt ảnh GA chuyển ra tài liệu nghiên cứu hoặc Extras.

Chốt bản nộp khi lệnh chạy tái lập được số liệu chính, demo chạy trên máy trình bày và mỗi thành viên giải thích được một kết quả bằng code của nhóm. Tăng số tính năng khi nó giúp trả lời một câu hỏi trong đề. Phần tên, đóng góp, GitHub, ảnh chạy ở lớp và kết quả Turnitin lấy từ nhóm thật. Kiểm tra báo cáo bằng cấu hình mặc định theo yêu cầu dưới 30%, rồi nối minh chứng ở cuối.

## Giao diện Qt và trình bày số liệu

PySide6 là binding Qt for Python dùng trong bản Qt Quick. QML dựng các cạnh bằng hình học và nội suy khi chuyển checkpoint. PyQt cũng dùng Qt, nên chất lượng hình phụ thuộc thiết kế scene, tỷ lệ hiển thị và nền tảng. Bản này chọn một binding để nhóm cài và kiểm thử. Hoạt ảnh trên bản đồ biểu diễn thay đổi của phân bổ xe qua vòng tối ưu. Dùng phần số liệu để đối chiếu vị trí thanh phát và số lượt chấm.

[Tài liệu Qt for Python](https://doc.qt.io/qtforpython-6/gettingstarted.html) · [Qt Quick Scene Graph](https://doc.qt.io/qt-6/qtquick-visualcanvas-scenegraph.html) · [Qt Quick Shapes](https://doc.qt.io/qt-6/qtquick-shapes-qmlmodule.html) · [NumberAnimation](https://doc.qt.io/qt-6/qml-qtquick-numberanimation.html) · [PyQt của Riverbank](https://www.riverbankcomputing.com/software/pyqt/intro)

Phương pháp đếm lượt chấm tới đích và ERT tham khảo quy ước benchmark tối ưu hộp đen. Đây là phép đo riêng của nhóm với một ngân sách và một ngưỡng đã ghi, dùng cùng hàm chấm giữa hai thuật toán. [COCO Performance Assessment](https://arxiv.org/abs/1605.03560)
