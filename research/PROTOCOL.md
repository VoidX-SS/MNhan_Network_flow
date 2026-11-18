# Cách đo và quy tắc chọn tình huống

Chốt giao thức này trước khi đọc kết quả sàng lọc. Mục đích là tìm những điều kiện làm kết quả GA và WOA khác nhau trên **bài chia luồng có tập tuyến cho trước**. Mỗi lượt hai thuật toán có cùng danh sách ứng viên ban đầu và cùng số lượt gọi hàm chấm. Hai thuật toán được chạy với đúng cấu hình đang có trong đồ án.

## Hai vòng đo

| Vòng | Mẫu | Ngân sách mỗi thuật toán mỗi lượt | Công việc |
|---|---|---:|---|
| Sàng lọc | Seed 0–7 trên mọi case | 32 × (90 + 1) = 2.912 lượt chấm | Ghi cả kết quả thuận, bất lợi và đối chứng |
| Xác nhận | Seed 1000–1029 trên danh sách đã khóa | 2.912 lượt chấm | Đo lại chênh lệch, phân bố và đường hội tụ |
| Đo quy mô | Seed 1000–1002 trên mỗi cỡ mạng | 16 × (18 + 1) = 304 lượt chấm | Đổi số nút bằng chia cạnh, giữ nguyên số trọng số. Đo thời gian tìm kiếm và một lượt bộ nhớ riêng |

Seed cấp cho quần thể ban đầu giống nhau giữa hai thuật toán. RNG của phép cập nhật bắt đầu từ `seed + 1`, rồi hai thuật toán dùng số ngẫu nhiên theo cách riêng. Đảo thứ tự chạy theo seed chẵn hoặc lẻ. Báo chi phí giữa các seed cùng hợp lệ để đọc chênh lệch theo cặp, kèm số cặp được dùng.

## Đo đúng thứ đang hỏi

- **Hợp lệ** nghĩa là đủ nhu cầu và trong sức chứa theo dung sai của mô hình. Bộ chuẩn kiểm tra có tồn tại phân bổ hợp lệ trong tập tuyến đã khai báo. Một lượt tối ưu thất bại chưa đủ để kết luận vô nghiệm.
- **Gần tối ưu 1%** chỉ ghi ở case có khoảng chuẩn số được xác nhận. Với cận dưới `L` và chi phí tối ưu `F*`, `L ≤ F*`. Lượt chạy đạt đích nếu nghiệm hợp lệ có `F ≤ 1,01 × L`, nên cách dùng cận dưới bảo thủ. Không dùng phép so số thực đúng tuyệt đối để đếm nghiệm tối ưu.
- **Tốc độ tìm** đếm lượt gọi hàm chấm đầu tiên thấy hợp lệ hoặc đạt đích. ERT cộng lượt chấm tới đích của các lần thành công, cộng toàn ngân sách ở các lần trượt, rồi chia cho số lần thành công. Ô ERT để trống khi số lần thành công là 0.
- **Hội tụ** xem tỷ lệ lượt đã chạm đích ở mỗi checkpoint, kể cả các lượt chưa đạt đích. Đường trung vị gap chỉ lấy những lượt hợp lệ, đọc cùng tỷ lệ hợp lệ. Gap tính với cận dưới `L` nên là cận trên của khoảng cách tương đối đến tối ưu.
- **Thời gian và RAM** là số đo trên máy chạy. Thời gian tìm kiếm lấy từ đồng hồ của lõi, có chi phí ghi điểm đo. RAM ở phép đo quy mô là đỉnh cấp phát Python do `tracemalloc` quan sát trong lượt riêng, gồm chuẩn bị dữ liệu và tìm kiếm. Vẽ GUI và thời gian kiểm chứng chuẩn nằm ngoài hai phép đo.

## Chọn ca từ vòng sàng lọc

1. Luôn giữ `normal` làm mốc và `cut` để trình bày chứng cứ vô nghiệm.
2. Trong nhóm có nghiệm đã kiểm chứng, bỏ `normal` và đối chứng chỉ đổi tọa độ. Chọn **ca khó về tính hợp lệ** có lượt trượt. Xếp theo chênh lệch số lượt hợp lệ giữa GA và WOA, sau đó theo tổng số lượt trượt. Nếu không có ca trượt, dùng chênh lệch số lần đạt đích để chọn. Khi hòa dùng mã ca theo thứ tự chữ cái.
3. Chọn **ca khác biệt về chất lượng** từ các ca còn lại có cận chuẩn, hai bên mỗi bên ít nhất 6/8 lượt hợp lệ. Ưu tiên họ tình huống khác ca khó khi có ứng viên. Xếp theo chênh lệch số lần đạt đích 1%, sau đó theo độ lớn trung vị chênh lệch chi phí trên cùng seed. Khi hòa dùng mã ca theo thứ tự chữ cái.
4. Ghi mã đã chọn vào `shortlist.json` rồi chạy seed mới. Nếu khác biệt nhỏ đi hoặc đảo chiều, giữ nguyên case và báo đúng. Case được chọn để minh họa cơ chế và giới hạn trên mẫu này.

Phép đo quy mô dùng cùng một bài toán được chia thành nhiều đoạn hơn. Ngân sách nhỏ và số tuyến giữ cố định giúp nhìn chi phí chấm theo độ lớn đồ thị. Các ca sàng lọc với nhiều cặp hoặc ít tuyến cho thấy góc khác của bài toán, khi chính không gian phương án thay đổi.

## Kiểm tra thêm sau khi khóa case tải nhẹ

Vì kết quả xác nhận của `light` cho thấy khác biệt giữa tốc độ chạm đích và số lần chạm đích, dùng 12 seed mới 2000–2011 để thử tăng riêng số vòng từ 90 lên 180. Giữ quần thể 32, tập tuyến, cách chấm và ngưỡng. Chạy từng cấu hình từ đầu. Với GA hiện tại, lượt 180 vòng nối thêm các vòng sau cùng một tiền tố. Với WOA, lịch giảm `a` tính theo tổng số vòng nên lượt 180 vòng đi một quỹ đạo khác ngay trước vòng 90. Ghi cả số cặp tốt lên, ngang, xấu đi. Kết quả này trả lời câu hỏi về hai ngân sách cụ thể.
