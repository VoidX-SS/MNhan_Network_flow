import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes

Rectangle {
    id: panel
    required property var series
    required property int calls
    property color ga: "#087b70"
    property color woa: "#674cbb"
    radius: 16
    color: "white"
    border.color: "#dce7ed"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 13
        spacing: 4
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: !panel.series.ready ? "Nhật ký hội tụ" : panel.series.valid
                      ? "Chi phí nghiệm hợp lệ · xe·phút" : "Mức vi phạm tổng hợp"
                font.pixelSize: 15
                font.bold: true
                color: "#142e41"
            }
            Item { Layout.fillWidth: true }
            Text { text: "● GA"; color: panel.ga; font.pixelSize: 13 }
            Text { text: "● WOA"; color: panel.woa; font.pixelSize: 13 }
        }
        Item {
            id: plot
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 82
            property real plotLeft: 73
            property real plotRight: width - 14
            property real plotTop: 9
            property real plotBottom: height - 24
            function xAt(call) {
                return plotLeft + (call - panel.series.first) / (panel.series.last - panel.series.first) * (plotRight - plotLeft)
            }
            function yAt(value) {
                return plotBottom - (value - panel.series.low) / (panel.series.high - panel.series.low) * (plotBottom - plotTop)
            }
            function coords(values) {
                if (!panel.series.ready || !values) return []
                return values.map(p => Qt.point(xAt(p[0]), yAt(p[1])))
            }
            Text {
                anchors.centerIn: parent
                visible: !panel.series.ready
                text: "Bấm Chạy GA và WOA để vẽ kết quả theo lượt chấm."
                color: "#4d6777"
                font.pixelSize: 14
            }
            Repeater {
                model: panel.series.ready ? 3 : 0
                delegate: Item {
                    required property int index
                    property real v: panel.series.low + (panel.series.high - panel.series.low) * index / 2
                    x: 0; y: plot.yAt(v)
                    Rectangle { x: plot.plotLeft; width: plot.plotRight - plot.plotLeft; height: 1; color: "#e5edf2" }
                    Text {
                        anchors.verticalCenter: parent.top
                        width: plot.plotLeft - 8
                        horizontalAlignment: Text.AlignRight
                        text: Number(parent.v).toLocaleString(Qt.locale("vi_VN"), "f", 1)
                        font.pixelSize: 11; color: "#4d6777"
                    }
                }
            }
            Rectangle {
                visible: !!panel.series.ready
                x: visible ? plot.xAt(panel.calls) : 0
                y: plot.plotTop
                width: 1
                height: plot.plotBottom - plot.plotTop
                color: "#a5bac7"
            }
            Shape {
                anchors.fill: parent
                ShapePath { strokeColor: panel.ga; strokeWidth: 2.5; fillColor: "transparent"; PathPolyline { path: plot.coords(panel.series.GA) } }
                ShapePath { strokeColor: panel.woa; strokeWidth: 2.5; fillColor: "transparent"; PathPolyline { path: plot.coords(panel.series.WOA) } }
            }
            RowLayout {
                visible: !!panel.series.ready
                x: plot.plotLeft; y: plot.plotBottom + 5
                width: plot.plotRight - plot.plotLeft
                Text { text: panel.series.first || 0; font.pixelSize: 11; color: "#4d6777" }
                Item { Layout.fillWidth: true }
                Text { text: "Số lượt chấm"; font.pixelSize: 11; color: "#4d6777" }
                Item { Layout.fillWidth: true }
                Text { text: panel.series.last || 0; font.pixelSize: 11; color: "#4d6777" }
            }
        }
    }
}
