import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 右側面板
 * - 即時評分趨勢圖
 * - 匯出 CSV / 重設分析按鈕
 * - 錄影按鈕
 */
Rectangle {
    id: root
    color: Style.Theme.bgCharcoal

    // ── 信號（向上傳遞操作）──
    signal exportCsvClicked()
    signal resetClicked()
    signal recordToggleClicked()

    // ── 左側邊線 ──
    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 1
        color: Style.Theme.borderNavy
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 1
        spacing: 0

        // ══════════════════════════════════
        // 即時評分趨勢
        // ══════════════════════════════════
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: Style.Theme.padding
            spacing: 12

            // 標題
            Row {
                spacing: 8
                Text {
                    text: "\uD83D\uDCC8"  // 📈
                    font.pixelSize: Style.Theme.fontSm
                    color: Style.Theme.textMuted
                }
                Text {
                    text: "即時評分趨勢"
                    font.pixelSize: Style.Theme.fontSm
                    font.bold: true
                    font.letterSpacing: 3
                    font.capitalization: Font.AllUppercase
                    color: Style.Theme.textMuted
                }
            }

            // 趨勢圖區域
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Style.Theme.borderRadius
                color: Qt.rgba(Style.Theme.surface900.r,
                               Style.Theme.surface900.g,
                               Style.Theme.surface900.b, 0.5)
                border.color: Style.Theme.surface800
                border.width: 1

                // 趨勢圖 Canvas（使用 rebaBridge 歷史資料）
                Canvas {
                    id: trendCanvas
                    anchors.fill: parent
                    anchors.margins: 4

                    // 追蹤分數歷史
                    property var scoreHistory: []
                    property int maxPoints: 60

                    Connections {
                        target: rebaBridge
                        function onScoreChanged() {
                            var arr = trendCanvas.scoreHistory.slice();
                            arr.push(rebaBridge.rebaScore);
                            if (arr.length > trendCanvas.maxPoints) {
                                arr = arr.slice(arr.length - trendCanvas.maxPoints);
                            }
                            trendCanvas.scoreHistory = arr;
                            trendCanvas.requestPaint();
                        }
                    }

                    onPaint: {
                        var ctx = getContext("2d")
                        var w = width, h = height
                        ctx.clearRect(0, 0, w, h)

                        var pts = scoreHistory;
                        if (pts.length < 2) return;

                        var maxScore = 15;

                        // 填充漸層
                        var grad = ctx.createLinearGradient(0, 0, 0, h)
                        grad.addColorStop(0, "rgba(0, 242, 255, 0.15)")
                        grad.addColorStop(1, "rgba(10, 15, 29, 0)")
                        ctx.fillStyle = grad
                        ctx.beginPath()
                        var stepX = w / (pts.length - 1);
                        ctx.moveTo(0, h - (pts[0] / maxScore) * h)
                        for (var i = 1; i < pts.length; i++)
                            ctx.lineTo(i * stepX, h - (pts[i] / maxScore) * h)
                        ctx.lineTo(w, h)
                        ctx.lineTo(0, h)
                        ctx.closePath()
                        ctx.fill()

                        // 線條
                        ctx.strokeStyle = "#00f2ff"
                        ctx.lineWidth = 2
                        ctx.beginPath()
                        ctx.moveTo(0, h - (pts[0] / maxScore) * h)
                        for (var j = 1; j < pts.length; j++)
                            ctx.lineTo(j * stepX, h - (pts[j] / maxScore) * h)
                        ctx.stroke()
                    }
                }

                // 右下角標籤
                Text {
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 6
                    text: "time (sec)"
                    font.pixelSize: Style.Theme.fontXs
                    font.family: "Consolas"
                    font.capitalization: Font.AllUppercase
                    color: Style.Theme.textMuted
                    opacity: 0.6
                }
            }

            // ── 匯出/重設 按鈕 ──
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Button {
                    Layout.fillWidth: true
                    text: "匯出 CSV"
                    font.pixelSize: Style.Theme.fontSm
                    font.bold: true
                    font.capitalization: Font.AllUppercase
                    implicitHeight: 36
                    background: Rectangle {
                        radius: 4
                        color: Qt.rgba(Style.Theme.accentNeonBlue.r,
                                       Style.Theme.accentNeonBlue.g,
                                       Style.Theme.accentNeonBlue.b, 0.1)
                        border.color: Qt.rgba(Style.Theme.accentNeonBlue.r,
                                              Style.Theme.accentNeonBlue.g,
                                              Style.Theme.accentNeonBlue.b, 0.3)
                        border.width: 1
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        color: Style.Theme.accentNeonBlue
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: root.exportCsvClicked()
                }
                Button {
                    Layout.fillWidth: true
                    text: "重設分析"
                    font.pixelSize: Style.Theme.fontSm
                    font.bold: true
                    font.capitalization: Font.AllUppercase
                    implicitHeight: 36
                    background: Rectangle {
                        radius: 4
                        color: Style.Theme.surface800
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        color: Style.Theme.textMuted
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: root.resetClicked()
                }
            }

            // ── 錄影按鈕 ──
            Button {
                Layout.fillWidth: true
                text: videoBridge.isRecording ? "\u23F8 暫停錄影" : "\u23FA 開始錄影"
                font.pixelSize: Style.Theme.fontSm
                font.bold: true
                font.capitalization: Font.AllUppercase
                implicitHeight: 36
                background: Rectangle {
                    radius: 4
                    color: videoBridge.isRecording
                           ? Qt.rgba(0.96, 0.25, 0.37, 0.15)
                           : Qt.rgba(Style.Theme.accentNeonGreen.r,
                                     Style.Theme.accentNeonGreen.g,
                                     Style.Theme.accentNeonGreen.b, 0.1)
                    border.color: videoBridge.isRecording
                                  ? Qt.rgba(0.96, 0.25, 0.37, 0.4)
                                  : Qt.rgba(Style.Theme.accentNeonGreen.r,
                                            Style.Theme.accentNeonGreen.g,
                                            Style.Theme.accentNeonGreen.b, 0.3)
                    border.width: 1
                }
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: videoBridge.isRecording ? "#f43f5e" : Style.Theme.accentNeonGreen
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: root.recordToggleClicked()
            }

            // ── 顯示選項 ──
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Style.Theme.surface800
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                CheckBox {
                    text: "骨架"
                    font.pixelSize: Style.Theme.fontSm
                    checked: settingsBridge.showSkeleton
                    onToggled: settingsBridge.setShowSkeleton(checked)
                }
                CheckBox {
                    text: "角度線"
                    font.pixelSize: Style.Theme.fontSm
                    checked: settingsBridge.showAngleLines
                    onToggled: settingsBridge.setShowAngleLines(checked)
                }
                CheckBox {
                    text: "角度值"
                    font.pixelSize: Style.Theme.fontSm
                    checked: settingsBridge.showAngleValues
                    onToggled: settingsBridge.setShowAngleValues(checked)
                }
            }
        }
    }
}
