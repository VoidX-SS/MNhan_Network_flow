# Điều phối luồng giao thông bằng GA và WOA

**Tên đăng ký đề tài** Ứng dụng thuật toán Di truyền (GA) và Whale Optimization Algorithm (WOA) cho bài toán tối ưu luồng giao thông trên mạng lưới.

Năm nhóm xe dùng chung các hành lang. Chương trình tìm cách chia xe giữa các tuyến sao cho chở đủ nhu cầu, giữ luồng trong sức chứa và giảm tổng thời gian. Mạng chính giả lập **50 nút, 61 cạnh có hướng, 5 cặp nguồn và đích**. GA và WOA được tự cài bằng Python, dùng cùng bộ chấm điểm. Mạng 8 nút dùng để giải thích, mạng 4 nút để tính tay.

Vòng đầu sàng lọc 21 tình huống. Vòng xác nhận chạy seed mới trên bốn ca **Ngày thường**, **Nhiều nguồn, một đích**, **Tải nhẹ** và **Cao điểm + đóng E23**. Bảng chính đọc cả tỷ lệ hợp lệ, tỷ lệ trong 1% chuẩn số và tốc độ. [Kết quả và danh mục 21 ca](research/KET_QUA.md)

## Mở demo và báo cáo

1. Giải nén cả thư mục. Mở terminal ở thư mục chứa `README.md`. Python 3.12 là phiên bản đã thử với Qt.
2. Cài và mở form PySide6 với hai lệnh dưới đây. Chọn case và chạy hai thuật toán. Chọn một cạnh để xem luồng hai bên. Tua hoặc phát lại từng vòng để thấy các nghiệm thay đổi.
3. Khi trình bày offline, mở **`DEMO_DU_PHONG.html`**. Bốn case, bản đồ seed mẫu 1000 và bảng xác nhận đã có sẵn. Form Tkinter cho mạng cơ sở mở bằng `python app.py` hoặc `MO_DEMO_WINDOWS.bat`. Có thể dùng Tkinter với `--network small` để giảng mạng 8 nút.
4. Mở [Khung báo cáo Word theo mẫu](docs/Khung_Bao_Cao_Theo_Mau.docx). Điền tên, đóng góp, GitHub, ảnh máy nhóm và kết quả Turnitin thật. Kiểm tra mục lục sau khi cập nhật trường trong Word.

```text
python -m pip install -r qt_demo/requirements.txt
python qt_demo/main.py
```

## Đọc theo việc cần làm

| Việc cần làm | Mở file |
|---|---|
| Hiểu đề, biến quyết định và tính thử 60/40 | [01 Đề bài và mô hình](docs/01_De_Bai_Va_Mo_Hinh.md) |
| Lần từ nút bấm tới hàm chấm, GA và WOA | [02 Đọc code và luồng chạy](docs/02_Doc_Code_Va_Luong_Chay.md) |
| Giao phần cho 5 người và duyệt bàn giao | [03 Kế hoạch 5 người](docs/03_Ke_Hoach_5_Nguoi.md) |
| Viết đúng bốn chương và biết phần nào đưa xuống phụ lục | [04 Dàn ý báo cáo](docs/04_Dan_Y_Bao_Cao.md) |
| Tập demo và trả lời vấn đáp | [05 Demo và vấn đáp](docs/05_Demo_Va_Van_Dap.md) |
| Đọc Big O, chứng cứ gần tối ưu, đối chứng và giới hạn | [Phương pháp và cơ chế](research/PHUONG_PHAP_VA_CO_CHE.md) |
| Đọc quy tắc sàng lọc và kết quả xác nhận | [Giao thức](research/PROTOCOL.md) · [Kết quả](research/KET_QUA.md) |
| Xem hoạt ảnh GA, benchmark và giả thuyết nâng cao | [Extras](Extras/README.md) |

## Chạy lại phần nghiên cứu

Cài gói nghiên cứu khi cần dựng lại chuẩn số và hình. GA, WOA, CLI, Tkinter và việc mở các kết quả đã lưu đều dùng được riêng. Tạo thư mục mới cho lần đo mới để đối chiếu với CSV đã đóng gói.

```text
python -m unittest discover -s tests -v
python run.py --case split
python -m pip install -r research/requirements.txt
python -m research.measure screen --out ket_qua_may_nhom
python -m research.measure confirm --out ket_qua_may_nhom
python -m research.budget_followup --out ket_qua_may_nhom
python -m research.scale --out ket_qua_may_nhom
python -m research.plots --out ket_qua_may_nhom
python make_backup.py --study ket_qua_may_nhom --out DEMO_MAY_NHOM.html
```

`research/results/` chứa số đo chính, cận chuẩn, shortlist, nhật ký hội tụ và hình SVG. `results/` là phép đo cơ sở từ vòng trước để đối chiếu khi tập chạy Tkinter. [Ghi chú kết quả cơ sở](docs/06_Ket_Qua_Va_Doi_Chieu.md)

## Bản đồ code

| Chỗ sửa | Nội dung |
|---|---|
| `data/`, `model.py` | Đồ thị, tuyến, hàm chia xe và chấm luồng, chứng cứ lát cắt |
| `algorithms/ga.py`, `algorithms/woa.py`, `solver.py` | Lõi thuật toán và lối gọi chung với seed, ngân sách, nhật ký |
| `research/scenarios.py`, `research/oracle.py`, `research/measure.py` | Case bank, chuẩn đối chiếu và phép đo chính |
| `qt_demo/`, `app.py`, `views.py` | Form QML và form Tkinter để chạy dự phòng |
| `Extras/` | Trình phát GA, bộ hàm đa cực và hướng nghiên cứu thêm |

Nhóm có thể khóa phạm vi ở bốn ca, một bảng kết quả chính, một đồ thị hội tụ và một demo chạy thật. Mỗi thành viên cần giải thích được đoạn code của mình và biết một kết luận có thể thay đổi thế nào khi đổi seed hoặc ngân sách.
