# Từ năm nhóm xe đến một cách phân luồng

## Đề bài

Giả sử trong một giờ có năm nhóm xe đi từ năm điểm xuất phát tới năm điểm đến. Xe có nhiều tuyến hợp lệ để lựa chọn và có thể dùng chung một đoạn ở giữa. Mỗi cạnh có một chiều đi, một thời gian lúc vắng và một mức sức chứa. Nhóm cần quyết định mỗi tuyến nhận bao nhiêu xe để tổng thời gian của tất cả xe nhỏ nhất, đồng thời đáp ứng đủ nhu cầu và sức chứa.

- Nhập bản đồ dưới dạng đồ thị có hướng và số xe cần đi của từng cặp nguồn và đích.
- Chia đủ xe của mỗi cặp cho các tuyến đúng chiều, từ đúng nguồn tới đúng đích.
- Tính luồng trên từng cạnh bằng cách cộng xe từ **mọi** tuyến sử dụng cạnh đó. Cạnh đã đóng nhận 0 xe. Cạnh còn mở cần giữ luồng trong sức chứa.
- Trong các phương án hợp lệ, ưu tiên phương án có tổng xe·phút thấp hơn. Hiển thị số đo từng cạnh, số xe từng tuyến, phương án tốt nhất và tiến trình tìm kiếm.
- Giải **cùng bài toán** bằng GA và WOA tự cài. Đo riêng khả năng tìm nghiệm hợp lệ, chất lượng nghiệm, số lượt chấm và thời gian tính.

Ví dụ trên mạng minh họa 8 nút, tuyến `O1 → A → C → T1` có 50 xe, tuyến `O2 → A → C → T2` có 20 xe. Riêng `E05` nối `A → C` chịu 70 xe. Cách cộng xe từ nhiều tuyến cũng áp dụng y như vậy ở mạng 50 nút.

## Dữ liệu và phạm vi

| Thành phần | Quy ước của nhóm |
|---|---|
| Một kỳ | Một khung 1 giờ. Số xe là luồng tổng hợp, có thể có phần lẻ trong mô hình |
| Cạnh `e` | Thời gian đường vắng `t₀ₑ` tính bằng phút/xe, sức chứa `cₑ` tính bằng xe mỗi kỳ |
| Cặp `k` | Một nguồn và một đích, với nhu cầu `qₖ`. Ngày thường 5 cặp lần lượt có 90, 96, 105, 84 và 85 xe |
| Tuyến `r` | Chuỗi nút đi đúng chiều. Mạng chính khai báo 5 tuyến cho mỗi cặp, mỗi tuyến đi qua một hành lang |
| Dữ liệu | Mạng giả lập 50 nút và 61 cạnh có hướng để thực nghiệm. Mạng 8 nút dùng để minh họa và bài 4 nút dùng để tính tay |
| Phạm vi | Phân bổ tĩnh trong một kỳ với thời gian theo tải. Mỗi nghiệm là một cách chia luồng, không phải quỹ đạo từng chiếc xe |

Trên mạng chính, năm hàng nối nguồn bên trái với đích bên phải. Hai dãy đường dọc cho xe chuyển hàng trước và sau khi vượt qua giữa bản đồ. Mỗi cặp có thể giữ hàng của mình hoặc vòng sang một trong bốn hàng kia, đi qua hành lang đó rồi trở về hàng của đích. Nhờ vậy, cả 50 nút và 61 cạnh đều được dùng trong ít nhất một tuyến ứng viên.

## Từ 25 núm vặn ra số xe

Một ứng viên trên mạng chính là vector `X` gồm 25 số từ 0 đến 1, chia thành 5 nhóm, mỗi nhóm 5 số dành cho một cặp nguồn và đích. Mỗi số là **trọng số** của một tuyến. Nếu chỉ có hai tuyến mở mang trọng số 0,2 và 0,8 thì tỷ lệ là 20% và 80%. Nếu là 0,1 và 0,4 thì tỷ lệ vẫn như thế. Cả hai thuật toán đổi cùng một loại vector, nên cùng một vector cho cùng cách chia xe.

Với cặp `k`, `Rₖ` là các tuyến mở. Với `r ∈ Rₖ`, gọi `gᵣ` là trọng số của tuyến. Số xe đi tuyến đó là `xᵣ = qₖ × gᵣ / Σ(gⱼ)` với tổng lấy trên các tuyến mở của cặp. Nếu tất cả trọng số mở bằng 0, đặt `xᵣ = qₖ / |Rₖ|`. Tuyến chứa cạnh đóng nhận 0. Nếu cả cặp hết tuyến mở, ghi `qₖ` xe chưa gán. Việc chia theo tỷ lệ khiến tổng xe của mỗi cặp bằng nhu cầu ngay khi còn tuyến mở. Vì xe luôn đi trọn tuyến, các nút trung gian cũng bảo toàn luồng.

Luồng cạnh là `fₑ = Σ xᵣ` trên các tuyến đi qua cạnh `e`. Một phương án hợp lệ khi số xe chưa gán bằng 0 và mọi cạnh thỏa `0 ≤ fₑ ≤ cₑ`, với dung sai số thực nhỏ `10⁻⁷` trên tổng vi phạm.

## Tính thời gian và chấm ứng viên

Trên cạnh mở, công thức BPR trong bản này là `tₑ(fₑ) = t₀ₑ × [1 + 0,15 × (fₑ/cₑ)⁴]`. Khi luồng bằng sức chứa, mỗi xe tốn thêm 15% so với lúc đường vắng theo công thức này. Hai hệ số là tham số mô hình minh họa. Sức chứa còn được áp như ràng buộc cứng ở bước kiểm tra hợp lệ. Với cạnh đóng, bỏ phép chia cho sức chứa. [Nguồn công thức BPR, FHWA](https://www.fhwa.dot.gov/policyinformation/analysisframework/docs/long-distance_model_implementation_report_final.pdf)

Tổng thời gian là `F = Σ(fₑ × tₑ(fₑ))` trên các cạnh mở. Đơn vị là xe·phút. Ví dụ 20 xe cùng mất 4 phút trên một đoạn thì đoạn đó đóng góp 80 xe·phút. Một xe có thể góp thời gian ở nhiều cạnh vì nó đi qua nhiều đoạn. Khi phương án hợp lệ và tổng nhu cầu dương, `F / Σqₖ` là số phút trung bình mỗi xe.

Điểm vi phạm là `V = xe chưa gán + Σ max(0, fₑ − cₑ)`. Phần tổng vượt tải đếm theo từng cạnh. Một nhóm 5 xe vượt tải qua hai cạnh có thể góp 10 vào tổng đó. Code so cặp `(V, F)` từ trái sang phải và đặt ô `V` thành 0 khi hợp lệ. Thế nên dù một cách chia vi phạm cho số phút nhỏ, nó vẫn đứng sau phương án hợp lệ. Bảng so chi phí chỉ lấy những lượt có nghiệm hợp lệ.

## Bài 100 xe để cả nhóm tính trên bảng

Dùng `data/mini.json`. Từ S tới T có hai tuyến, mỗi tuyến gồm hai cạnh. Cả bốn cạnh có `c = 75` xe và `t₀ = 1` phút. Thử trọng số `[0.6, 0.4]`.

1. Tuyến qua A nhận 60 xe, tuyến qua B nhận 40 xe. Mỗi cạnh của tuyến A có 60 xe và mỗi cạnh của tuyến B có 40 xe.
2. Cạnh trên tuyến A tốn `1 + 0,15 × (60/75)⁴ = 1,06144` phút/xe. Cạnh trên tuyến B tốn khoảng 1,01214 phút/xe.
3. Tổng là `2 × (60 × 1,06144 + 40 × 1,012136…) ≈ 208,34` xe·phút. Tất cả cạnh còn trong sức chứa.
4. Nếu chia 50/50, tổng giảm còn **205,925925… xe·phút**. Hai tuyến có cùng công thức. Phần chi phí tăng do tắc tỷ lệ với lũy thừa bậc 5 của luồng mỗi tuyến, nên với tổng 100 cố định, chia đều cho hai tuyến giống nhau cho tổng nhỏ nhất.
5. Nếu thử 80/20, hai cạnh tuyến A mỗi cạnh vượt 5 xe. `V = 10` và phương án bị xếp vào nhóm vi phạm.

## Một trường hợp chứng minh được vô nghiệm

Trong kịch bản **Cao điểm + đóng E23**, chia bản đồ thành 25 nút phía trái và 25 nút phía phải. Tất cả 590 xe đều phải sang phía phải. Năm cạnh E05, E14, E23, E32, E41 bắc qua lát cắt. Đóng E23 khiến tổng sức chứa còn `130 + 135 + 0 + 125 + 130 = 520`, thiếu ít nhất 70 chỗ. Với một chỉnh sửa khác trên form, nếu chưa tìm được lát cắt như vậy và kết quả vi phạm, cách diễn đạt là “lượt chạy chưa tìm được nghiệm hợp lệ”.
