import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 底部最左欄：評估參數設定
 * 從 SidePanel 抽出，包含分析側邊、握持品質、負荷重量
 */
Rectangle {
    id: root
    color: Style.Theme.bgCharcoal

    // ── 右側邊線 ──
    Rectangle {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 1; color: Style.Theme.surface800
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Style.Theme.padding
        spacing: 12

        // 標題
        Row {
            spacing: 8
            Text {
                text: "\u2699"  // ⚙
                font.pixelSize: Style.Theme.fontLg
                color: Style.Theme.textMuted
            }
            Text {
                text: "評估參數設定"
                font.pixelSize: Style.Theme.fontLg
                font.bold: true
                font.letterSpacing: 3
                font.capitalization: Font.AllUppercase
                color: Style.Theme.textMuted
            }
        }

        // 分析側邊
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            Text {
                text: "分析側邊"
                font.pixelSize: Style.Theme.fontMd
                color: Style.Theme.textMuted
            }
            ComboBox {
                id: sideCombo
                Layout.fillWidth: true
                model: ["右側 (Right)", "左側 (Left)"]
                font.pixelSize: Style.Theme.fontMd
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

        // 握持品質
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            Text {
                text: "握持品質"
                font.pixelSize: Style.Theme.fontMd
                color: Style.Theme.textMuted
            }
            ComboBox {
                id: couplingCombo
                Layout.fillWidth: true
                model: ["優良 (Good)", "普通 (Fair)", "不良 (Poor)", "不可接受 (Unacceptable)"]
                font.pixelSize: Style.Theme.fontMd
                currentIndex: {
                    if (settingsBridge.coupling === "fair") return 1;
                    if (settingsBridge.coupling === "poor") return 2;
                    if (settingsBridge.coupling === "unacceptable") return 3;
                    return 0;
                }
                onActivated: {
                    var vals = ["good", "fair", "poor", "unacceptable"];
                    settingsBridge.setCoupling(vals[currentIndex]);
                    videoBridge.setParameters(
                        settingsBridge.side,
                        settingsBridge.loadWeight,
                        settingsBridge.coupling);
                }
            }
        }

        // 負荷重量
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            Text {
                text: "負荷重量 (kg)"
                font.pixelSize: Style.Theme.fontMd
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

        // 彈性填充
        Item { Layout.fillHeight: true }
    }
}
