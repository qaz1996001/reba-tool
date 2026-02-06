import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 右側面板
 * - 評估參數設定（分析側邊、握持品質、負荷重量）
 * - 即時評分趨勢圖
 * - 匯出 CSV / 重設分析按鈕
 */
Rectangle {
    id: root
    color: Style.Theme.bgCharcoal

    // ── 信號（向上傳遞操作）──
    signal exportCsvClicked()
    signal resetClicked()

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
        // 區塊一：評估參數設定
        // ══════════════════════════════════
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: paramCol.implicitHeight + 32
            color: "transparent"

            // 底部分隔線
            Rectangle {
                anchors.left: parent.left; anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1; color: Style.Theme.surface800
            }

            ColumnLayout {
                id: paramCol
                anchors.fill: parent
                anchors.margins: Style.Theme.padding
                spacing: 12

                // 標題
                Row {
                    spacing: 8
                    Text {
                        text: "\u2699"  // ⚙
                        font.pixelSize: Style.Theme.fontSm
                        color: Style.Theme.textMuted
                    }
                    Text {
                        text: "評估參數設定"
                        font.pixelSize: Style.Theme.fontSm
                        font.bold: true
                        font.letterSpacing: 3
                        font.capitalization: Font.AllUppercase
                        color: Style.Theme.textMuted
                    }
                }

                // 兩欄：分析側邊 + 握持品質
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "分析側邊"
                            font.pixelSize: Style.Theme.fontXs
                            color: Style.Theme.textMuted
                        }
                        ComboBox {
                            id: sideCombo
                            Layout.fillWidth: true
                            model: ["右側 (Right)", "左側 (Left)"]
                            font.pixelSize: Style.Theme.fontXs
                            currentIndex: settingsBridge.side === "left" ? 1 : 0
                            onActivated: {
                                var val = currentIndex === 1 ? "left" : "right";
                                settingsBridge.setSide(val);
                                videoBridge.setParameters(
                                    settingsBridge.side,
                                    settingsBridge.loadWeight,
                                    settingsBridge.coupling);
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "握持品質"
                            font.pixelSize: Style.Theme.fontXs
                            color: Style.Theme.textMuted
                        }
                        ComboBox {
                            id: couplingCombo
                            Layout.fillWidth: true
                            model: ["優良 (Good)", "普通 (Fair)", "不良 (Poor)"]
                            font.pixelSize: Style.Theme.fontXs
                            currentIndex: {
                                if (settingsBridge.coupling === "fair") return 1;
                                if (settingsBridge.coupling === "poor") return 2;
                                return 0;
                            }
                            onActivated: {
                                var vals = ["good", "fair", "poor"];
                                settingsBridge.setCoupling(vals[currentIndex]);
                                videoBridge.setParameters(
                                    settingsBridge.side,
                                    settingsBridge.loadWeight,
                                    settingsBridge.coupling);
                            }
                        }
                    }
                }

                // 負荷重量
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Text {
                        text: "負荷重量 (kg)"
                        font.pixelSize: Style.Theme.fontXs
                        color: Style.Theme.textMuted
                    }
                    SpinBox {
                        id: loadSpinBox
                        Layout.fillWidth: true
                        from: 0; to: 10000; stepSize: 100
                        value: Math.round(settingsBridge.loadWeight * 100)
                        property int decimals: 1
                        textFromValue: function(value, locale) {
                            return (value / 100).toFixed(1)
                        }
                        valueFromText: function(text, locale) {
                            return Math.round(parseFloat(text) * 100)
                        }
                        onValueModified: {
                            settingsBridge.setLoadWeight(value / 100.0);
                            videoBridge.setParameters(
                                settingsBridge.side,
                                settingsBridge.loadWeight,
                                settingsBridge.coupling);
                        }
                    }
                }
            }
        }

        // ══════════════════════════════════
        // 區塊二：即時評分趨勢
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

            // ── 底部按鈕 ──
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
        }
    }
}
