# Giao diện phát lại bằng PySide6 và QML

Mở terminal ở thư mục dự án với Python 3.12 rồi chạy hai lệnh dưới đây. Lượt cài đầu tải các thành phần Qt. Sau khi cài, demo chạy với dữ liệu cục bộ.

```text
python -m pip install -r qt_demo/requirements.txt
python qt_demo/main.py
```

Chọn một trong bốn kịch bản đã chốt rồi bấm **Chạy GA và WOA**. Mỗi bên chấm 2.912 phương án với cùng seed. Chọn mã cạnh để đọc sức chứa và luồng xe ở cả hai bản đồ. Thanh trượt hoặc **Phát lại** mở các bản chụp nghiệm tốt nhất đã lưu, mỗi bản chụp ứng với một vòng tối ưu. Đường hội tụ so chi phí khi có nghiệm hợp lệ. Khi cả hai lượt đều chưa tìm được nghiệm hợp lệ, đồ thị hiện mức vi phạm cộng xe chưa phân bổ và phần vượt sức chứa trên từng cạnh. Kịch bản đóng E23 vào giờ cao điểm có thêm chứng minh lát cắt 590 xe so với 520 chỗ.

Chạy từ một kịch bản cụ thể bằng `python qt_demo/main.py --case cut --seed 1000`. Các mã khác là `normal`, `many_to_one` và `light`. Seed 1000 nằm trong bộ xác nhận của đồ án. Mở `python app.py` để dùng form Tkinter hoặc mở `DEMO_DU_PHONG.html` trực tiếp trong trình duyệt.

`main.py` gọi lõi GA và WOA tự cài ở `solver.py`. QML chỉ nhận dữ liệu để vẽ và phát lại. Cạnh dùng `QtQuick.Shapes`, hoạt ảnh đổi màu và độ dày dùng dữ liệu từ nhật ký. Qt dùng tọa độ độc lập mật độ màn hình để vẽ lại nét khi thay kích thước cửa sổ. PySide6 và PyQt6 đều là các binding Python cho Qt. Dự án dùng PySide6 Essentials để giữ một hướng dẫn cài và một bộ kiểm thử giao diện.

Đã kiểm thử cả bốn kịch bản trên Linux, Python 3.12 và PySide6 6.8.3 với Qt Quick software renderer. Ảnh dùng seed 1000 để minh họa một lượt. Xem bảng xác nhận 30 seed để so kết quả tổng thể. [Ảnh chạy case nhiều nguồn, một đích](preview.png).

Tài liệu chính thức để đọc thêm gồm [Cài Qt for Python](https://doc.qt.io/qtforpython-6/gettingstarted.html), [Qt Quick Shapes](https://doc.qt.io/qt-6/qtquick-shapes-qmlmodule.html), [NumberAnimation](https://doc.qt.io/qt-6/qml-qtquick-numberanimation.html), [High DPI](https://doc.qt.io/qt-6/highdpi.html) và [PyQt6](https://www.riverbankcomputing.com/software/pyqt/intro).
