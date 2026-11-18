import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes

Rectangle {
    id: pane
    required property string algorithm
    required property color accent
    required property var scene
    required property var score
    property int selected: -1
    property bool animate: true

    radius: 16
    color: "#ffffff"
    border.color: "#dce7ed"

    function number(value) {
        return Number(value).toLocaleString(Qt.locale("vi_VN"), "f", 2)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 13
        spacing: 4

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Rectangle { color: pane.accent; width: 10; height: 10; radius: 5 }
            Text { text: pane.algorithm; color: "#142e41"; font.pixelSize: 20; font.bold: true }
            Item { Layout.fillWidth: true }
            Text {
                text: !pane.score.ready ? "Chưa chạy" : pane.score.valid ? "Hợp lệ" : "Vi phạm"
                color: !pane.score.ready ? "#667f8e" : pane.score.valid ? "#06756b" : "#a82c45"
                font.pixelSize: 14
                font.bold: true
            }
        }
        Text {
            Layout.fillWidth: true
            text: !pane.score.ready ? "Chờ kết quả lượt chạy" : pane.score.valid
                  ? pane.number(pane.score.minutes) + " xe·phút"
                  : pane.number(pane.score.violation) + " đơn vị vi phạm"
            color: "#142e41"
            font.pixelSize: 17
            elide: Text.ElideRight
        }

        Item {
            id: diagram
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 160
            clip: true
            function px(n) { return 23 + n * (width - 46) }
            function py(n) { return 10 + n * (height - 20) }

            Repeater {
                model: pane.scene.roads
                delegate: Item {
                    id: edge
                    required property int index
                    required property var modelData
                    anchors.fill: parent
                    property real ax: diagram.px(modelData.x1)
                    property real ay: diagram.py(modelData.y1)
                    property real bx: diagram.px(modelData.x2)
                    property real by: diagram.py(modelData.y2)
                    property real length: Math.max(1, Math.hypot(bx - ax, by - ay))
                    property real ux: (bx - ax) / length
                    property real uy: (by - ay) / length
                    property real lane: modelData.twoWay ? 2.5 : 0
                    property real x1: ax + 6 * ux - lane * uy
                    property real y1: ay + 6 * uy + lane * ux
                    property real x2: bx - 7 * ux - lane * uy
                    property real y2: by - 7 * uy + lane * ux
                    property real flow: pane.score.ready ? pane.score.flows[index] : 0
                    property real ratio: modelData.capacity > 0 ? flow / modelData.capacity : 0
                    property bool closed: modelData.capacity === 0
                    property color ink: closed ? "#74899b" : ratio > 1 + 1e-8 ? "#c13a54"
                                        : ratio >= .9 ? "#be7420" : flow > 0 ? "#0b887e" : "#c0d1da"

                    Shape {
                        anchors.fill: parent
                        ShapePath {
                            fillColor: "transparent"
                            strokeColor: edge.index === pane.selected ? "#c8e3fb" : "transparent"
                            strokeWidth: 8
                            capStyle: ShapePath.RoundCap
                            startX: edge.x1; startY: edge.y1
                            PathLine { x: edge.x2; y: edge.y2 }
                        }
                        ShapePath {
                            fillColor: "transparent"
                            strokeColor: edge.ink
                            strokeWidth: edge.closed ? 2 : 1.5 + Math.min(edge.ratio, 1.25) * 2.7
                            strokeStyle: edge.closed ? ShapePath.DashLine : ShapePath.SolidLine
                            dashPattern: [2, 2]
                            capStyle: ShapePath.RoundCap
                            startX: edge.x1; startY: edge.y1
                            Behavior on strokeColor { enabled: pane.animate; ColorAnimation { duration: 125 } }
                            Behavior on strokeWidth { enabled: pane.animate; NumberAnimation { duration: 125 } }
                            PathLine { x: edge.x2; y: edge.y2 }
                        }
                        ShapePath {
                            fillColor: "transparent"
                            strokeColor: edge.ink
                            strokeWidth: edge.closed ? 0 : 1.3
                            startX: edge.x2 - 4 * edge.ux + 2.5 * edge.uy
                            startY: edge.y2 - 4 * edge.uy - 2.5 * edge.ux
                            PathLine { x: edge.x2; y: edge.y2 }
                            PathLine { x: edge.x2 - 4 * edge.ux - 2.5 * edge.uy; y: edge.y2 - 4 * edge.uy + 2.5 * edge.ux }
                        }
                    }
                    Rectangle {
                        visible: edge.index === pane.selected
                        x: (edge.x1 + edge.x2) / 2 - width / 2
                        y: (edge.y1 + edge.y2) / 2 - height - 5
                        width: edgeText.implicitWidth + 8
                        height: 17
                        radius: 4
                        color: "#e7f2fc"
                        Text { id: edgeText; anchors.centerIn: parent; text: edge.modelData.code; color: "#194e74"; font.pixelSize: 11; font.bold: true }
                    }
                }
            }
            Repeater {
                model: pane.scene.nodes
                delegate: Rectangle {
                    required property var modelData
                    width: modelData.terminal ? 12 : 8
                    height: width
                    x: diagram.px(modelData.x) - width / 2
                    y: diagram.py(modelData.y) - height / 2
                    radius: width / 2
                    color: modelData.terminal ? "#15394e" : "white"
                    border.color: modelData.terminal ? "#15394e" : "#90aab9"
                    Text {
                        visible: parent.modelData.terminal
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.top
                        anchors.bottomMargin: 4
                        text: parent.modelData.name
                        color: "#15394e"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
            }
        }
    }
}
