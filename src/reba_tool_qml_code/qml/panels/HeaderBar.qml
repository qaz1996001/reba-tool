import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 頂部標題列
 * 左側：Logo + 標題 + 版本號
 * 右側：FPS / Latency 指標 + 設定按鈕
 */
Rectangle {
    id: root
    implicitHeight: Style.Theme.headerHeight
    color: Style.Theme.bgCharcoal

    // ── 佔位屬性（Phase 2 由 bridge 綁定）──
    property real fpsValue: 30.2
    property real latencyValue: 12

    // ── 底部邊線 ──
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 1
        color: Style.Theme.borderNavy
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 12

        // ── 左側：Logo + Title ──
        Rectangle {
            width: 32; height: 32
            radius: 6
            color: Style.Theme.accentNeonBlue
            Text {
                anchors.centerIn: parent
                text: "\u26A1"  // ⚡
                font.pixelSize: 18
                font.bold: true
                color: Style.Theme.surface900
            }
        }

        Text {
            text: "REBA"
            font.pixelSize: Style.Theme.fontMd
            font.bold: true
            font.letterSpacing: 2
            color: Style.Theme.textPrimary
        }
        Text {
            text: "Unified Dashboard"
            font.pixelSize: Style.Theme.fontMd
            font.bold: true
            font.letterSpacing: 2
            color: Style.Theme.accentNeonBlue
        }
        Rectangle {
            width: versionLabel.implicitWidth + 12
            height: 22
            radius: 4
            color: Style.Theme.surface800
            Text {
                id: versionLabel
                anchors.centerIn: parent
                text: "V2.5.0"
                font.pixelSize: Style.Theme.fontXs
                color: Style.Theme.textMuted
            }
        }

        Item { Layout.fillWidth: true }

        // ── 右側：指標 ──
        RowLayout {
            spacing: 16

            Column {
                spacing: 2
                Text {
                    text: "FPS"
                    font.pixelSize: Style.Theme.fontXs
                    font.capitalization: Font.AllUppercase
                    color: Style.Theme.textMuted
                }
                Text {
                    text: root.fpsValue.toFixed(1)
                    font.pixelSize: Style.Theme.fontMd
                    font.family: "Consolas"
                    color: Style.Theme.accentNeonGreen
                }
            }
            Column {
                spacing: 2
                Text {
                    text: "LATENCY"
                    font.pixelSize: Style.Theme.fontXs
                    font.capitalization: Font.AllUppercase
                    color: Style.Theme.textMuted
                }
                Text {
                    text: root.latencyValue.toFixed(0) + "ms"
                    font.pixelSize: Style.Theme.fontMd
                    font.family: "Consolas"
                    color: Style.Theme.accentNeonBlue
                }
            }

            // 分隔線
            Rectangle {
                width: 1
                height: 28
                color: Style.Theme.borderNavy
            }

            // 設定按鈕
            Rectangle {
                width: 32; height: 32
                radius: 16
                color: settingsMA.containsMouse ? Style.Theme.surface800 : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "\u2699"  // ⚙
                    font.pixelSize: 18
                    color: Style.Theme.textMuted
                }
                MouseArea {
                    id: settingsMA
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                }
            }
        }
    }
}
