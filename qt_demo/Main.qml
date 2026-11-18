import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    objectName: "trafficWindow"
    required property QtObject controller
    property int initialSeed: 1000
    property var sceneData: controller ? controller.scene : ({nodes: [], roads: [], roadNames: [], pairs: [], proof: "", totalDemand: 0})
    property var frameData: controller ? controller.frame : ({ready: false, step: 0, calls: 0, GA: {}, WOA: {}})
    property int selectedRoad: roadPicker.currentIndex
    property color ink: "#142e41"
    property color muted: "#4d6777"
    property color ga: "#087b70"
    property color woa: "#674cbb"

    width: 1400
    height: 850
    minimumWidth: 1000
    minimumHeight: 740
    visible: true
    title: "Đồ án Trí tuệ nhân tạo | Phân luồng giao thông"
    color: "#f1f6f9"
    font.pixelSize: 14
    palette.highlight: "#167e85"
    palette.highlightedText: "#ffffff"

    function resetRoad() {
        let focus = sceneData.roadNames.indexOf(sceneData.focus)
        roadPicker.currentIndex = focus < 0 ? 0 : focus
    }
    function loadText(name) {
        if (selectedRoad < 0 || !frameData.ready) return "Chờ lượt chạy"
        let flow = frameData[name].flows[selectedRoad]
        let cap = sceneData.roads[selectedRoad].capacity
        let count = Number(flow).toLocaleString(Qt.locale("vi_VN"), "f", 1)
        return cap === 0 ? count + " xe · đóng" : count + " / " + cap + " xe"
    }

    Connections {
        target: window.controller
        function onSceneChanged() {
            replay.stop()
            Qt.callLater(window.resetRoad)
        }
    }
    Component.onCompleted: {
        resetRoad()
        controller.startRun(initialSeed)
    }
    Timer {
        id: replay
        interval: 130
        repeat: true
        onTriggered: {
            if (window.frameData.step >= window.controller.steps) stop()
            else window.controller.chooseStep(window.frameData.step + 1)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 11

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 82
            radius: 16
            color: "#16384e"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 12
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text { text: "ĐỒ ÁN TRÍ TUỆ NHÂN TẠO"; font.pixelSize: 11; font.letterSpacing: 1.1; font.bold: true; color: "#b9e7e4" }
                    Text { text: "Phân luồng giao thông"; font.pixelSize: 29; font.bold: true; color: "white" }
                }
                Text {
                    Layout.fillWidth: true
                    text: window.sceneData.nodes.length + " nút  ·  " + window.sceneData.roads.length + " cạnh có hướng\nGA và WOA dùng cùng dữ liệu đầu vào"
                    horizontalAlignment: Text.AlignRight
                    font.pixelSize: 13
                    color: "#e4f1f5"
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 240
                Layout.fillHeight: true
                radius: 16
                color: "white"
                border.color: "#dce7ed"
                ScrollView {
                    id: inputs
                    anchors.fill: parent
                    anchors.margins: 13
                    contentWidth: availableWidth
                    clip: true
                    ColumnLayout {
                        width: inputs.availableWidth
                        spacing: 8
                        Text { text: "Thiết lập lượt chạy"; color: window.ink; font.pixelSize: 17; font.bold: true }
                        ComboBox {
                            objectName: "casePicker"
                            Layout.fillWidth: true
                            enabled: window.controller && !window.controller.working
                            model: window.controller ? window.controller.labels : []
                            currentIndex: window.controller ? window.controller.caseIndex : -1
                            onActivated: index => window.controller.chooseCase(index)
                            Accessible.name: "Kịch bản"
                        }
                        Text {
                            Layout.fillWidth: true
                            text: window.sceneData.description || ""
                            wrapMode: Text.WordWrap
                            color: window.muted
                            font.pixelSize: 13
                        }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#e4edf2" }
                        Text {
                            text: "Nhu cầu · " + window.sceneData.totalDemand + " xe mỗi kỳ"
                            color: window.ink
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Repeater {
                            model: window.sceneData.pairs
                            delegate: RowLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Text { text: parent.modelData.name; color: window.muted; font.pixelSize: 13 }
                                Item { Layout.fillWidth: true }
                                Text { text: parent.modelData.demand; color: window.ink; font.pixelSize: 13; font.bold: true }
                            }
                        }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#e4edf2" }
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Seed"; color: window.ink; font.bold: true }
                            Item { Layout.fillWidth: true }
                            SpinBox {
                                id: seedBox
                                objectName: "seedBox"
                                Layout.preferredWidth: 137
                                editable: true
                                enabled: window.controller && !window.controller.working
                                from: 0; to: 2147483647
                                value: window.initialSeed
                                Accessible.name: "Seed"
                            }
                        }
                        Button {
                            id: runButton
                            objectName: "runButton"
                            Layout.fillWidth: true
                            enabled: window.controller && !window.controller.working
                            text: window.controller && window.controller.working ? "Đang tính…" : "Chạy GA và WOA"
                            font.bold: true
                            onClicked: {
                                replay.stop()
                                window.controller.startRun(seedBox.value)
                            }
                            background: Rectangle { radius: 6; color: runButton.enabled ? (runButton.down ? "#0f666c" : "#167e85") : "#6a9295" }
                            contentItem: Text { text: runButton.text; color: "white"; font: runButton.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: window.controller ? (window.controller.errorText || window.controller.budget + " lượt chấm mỗi thuật toán") : ""
                            color: window.controller && window.controller.errorText ? "#a82c45" : window.muted
                            wrapMode: Text.WordWrap
                            font.pixelSize: 12
                        }
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#e4edf2" }
                        Text { text: "Đọc cùng một cạnh"; color: window.ink; font.pixelSize: 14; font.bold: true }
                        ComboBox {
                            id: roadPicker
                            objectName: "roadPicker"
                            Layout.fillWidth: true
                            model: window.sceneData.roadNames
                            Accessible.name: "Chọn cạnh"
                        }
                        Text {
                            Layout.fillWidth: true
                            text: window.selectedRoad < 0 ? "" : window.sceneData.roads[window.selectedRoad].start
                                  + " → " + window.sceneData.roads[window.selectedRoad].end
                            color: window.muted
                        }
                        Text { text: "GA    " + window.loadText("GA"); color: window.ga; font.pixelSize: 13; font.bold: true }
                        Text { text: "WOA    " + window.loadText("WOA"); color: window.woa; font.pixelSize: 13; font.bold: true }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 8

                Rectangle {
                    objectName: "proofBanner"
                    visible: !!window.sceneData.proof
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? proofText.implicitHeight + 17 : 0
                    radius: 9
                    color: "#fdebf0"
                    Text {
                        id: proofText
                        objectName: "proofText"
                        anchors.left: parent.left; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 11; anchors.rightMargin: 11
                        text: window.sceneData.proof
                        font.bold: true
                        color: "#94283d"
                        wrapMode: Text.WordWrap
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 9
                    NetworkPane {
                        Layout.fillWidth: true; Layout.fillHeight: true; Layout.preferredWidth: 1
                        algorithm: "GA"; accent: window.ga
                        scene: window.sceneData; score: window.frameData.GA
                        selected: window.selectedRoad
                    }
                    NetworkPane {
                        Layout.fillWidth: true; Layout.fillHeight: true; Layout.preferredWidth: 1
                        algorithm: "WOA"; accent: window.woa
                        scene: window.sceneData; score: window.frameData.WOA
                        selected: window.selectedRoad
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: "Xanh · đang tải     Cam · từ 90% sức chứa     Đỏ · vượt sức chứa     Nét đứt · đóng cạnh"
                    font.pixelSize: 12
                    color: window.muted
                    wrapMode: Text.WordWrap
                }
                HistoryPane {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 170
                    series: window.controller ? window.controller.chart : ({})
                    calls: window.frameData.calls
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        objectName: "playButton"
                        text: replay.running ? "Dừng" : "Phát lại"
                        enabled: window.frameData.ready
                        onClicked: {
                            if (replay.running) replay.stop()
                            else {
                                if (window.frameData.step >= window.controller.steps) window.controller.chooseStep(0)
                                replay.start()
                            }
                        }
                    }
                    Slider {
                        objectName: "stepSlider"
                        Layout.fillWidth: true
                        enabled: window.frameData.ready
                        from: 0
                        to: window.controller ? window.controller.steps : 1
                        stepSize: 1
                        value: window.frameData.step
                        onMoved: {
                            replay.stop()
                            window.controller.chooseStep(Math.round(value))
                        }
                        Accessible.name: "Vòng tối ưu"
                    }
                    Text {
                        objectName: "stepLabel"
                        text: "Vòng " + window.frameData.step + "  ·  " + window.frameData.calls + " lượt chấm"
                        color: window.ink
                        font.pixelSize: 13
                        font.bold: true
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: window.frameData.ready && !window.frameData.GA.valid && !window.frameData.WOA.valid
                          ? "Mức vi phạm cộng xe chưa phân bổ và phần vượt sức chứa trên từng cạnh."
                          : "Phát lại nghiệm tốt nhất đã gặp tại từng vòng. Mỗi khung là một phương án chia luồng xe trong kỳ."
                    color: window.muted
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
