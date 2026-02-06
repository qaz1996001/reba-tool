import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 影片顯示區域
 * - 黑色背景 + 圓角邊框
 * - 右上角 REBA 分數 overlay
 * - Hover 時顯示底部播放控制列
 * - 無影片時顯示佔位文字
 */
Rectangle {
    id: root
    color: "transparent"

    // ── 佔位屬性（Phase 2 綁定）──
    property int rebaScore: 7
    property string riskLabel: "中度風險"
    property color riskColor: Style.Theme.riskMedium
    property bool hasVideo: false
    property real progress: 0.33
    property string currentTime: "00:45"
    property string totalTime: "02:30"
    property bool isPlaying: false

    // ── 影片顯示框 ──
    Rectangle {
        id: videoFrame
        anchors.fill: parent
        anchors.margins: Style.Theme.padding
        radius: Style.Theme.borderRadius
        color: "#000000"
        border.color: Style.Theme.borderNavy
        border.width: 1
        clip: true

        // ── 佔位文字（無影片時）──
        Column {
            anchors.centerIn: parent
            spacing: 8
            visible: !root.hasVideo
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "\uD83C\uDFA5"  // 🎥
                font.pixelSize: 64
                color: Style.Theme.borderNavy
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Awaiting Video Input..."
                font.pixelSize: Style.Theme.fontXs
                font.capitalization: Font.AllUppercase
                font.letterSpacing: 3
                color: Style.Theme.textMuted
            }
        }

        // ── 影片 Image（Phase 2 綁定 image provider）──
        // Image {
        //     id: videoImage
        //     anchors.fill: parent
        //     source: "image://video/frame?" + frameCounter
        //     cache: false
        //     visible: root.hasVideo
        // }

        // ── REBA 分數 Overlay（右上角）──
        Rectangle {
            id: scoreOverlay
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 16
            anchors.rightMargin: 16
            width: 90
            height: scoreOverlayCol.implicitHeight + 20
            radius: 12
            color: Qt.rgba(0, 0, 0, 0.6)
            border.color: Qt.rgba(Style.Theme.accentNeonBlue.r,
                                  Style.Theme.accentNeonBlue.g,
                                  Style.Theme.accentNeonBlue.b, 0.5)
            border.width: 1

            Column {
                id: scoreOverlayCol
                anchors.centerIn: parent
                spacing: 4

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "REBA"
                    font.pixelSize: Style.Theme.fontXs
                    font.bold: true
                    font.letterSpacing: 4
                    font.capitalization: Font.AllUppercase
                    color: Style.Theme.textMuted
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: root.rebaScore.toString().padStart(2, '0')
                    font.pixelSize: Style.Theme.fontHuge
                    font.weight: Font.Black
                    color: Style.Theme.accentNeonBlue
                }
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: riskLabelText.implicitWidth + 16
                    height: 18
                    radius: 4
                    color: Qt.rgba(root.riskColor.r, root.riskColor.g, root.riskColor.b, 0.2)
                    Text {
                        id: riskLabelText
                        anchors.centerIn: parent
                        text: root.riskLabel
                        font.pixelSize: Style.Theme.fontXs
                        font.bold: true
                        color: root.riskColor
                    }
                }
            }
        }

        // ── Hover 播放控制列 ──
        Rectangle {
            id: controlBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 56
            opacity: videoHoverArea.containsMouse ? 1.0 : 0.0
            Behavior on opacity { NumberAnimation { duration: 200 } }

            gradient: Gradient {
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 1.0; color: "#000000" }
            }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12

                // 播放/暫停按鈕
                Text {
                    text: root.isPlaying ? "\u23F8" : "\u25B6"  // ⏸ / ▶
                    font.pixelSize: 22
                    color: Style.Theme.textPrimary
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                    }
                }

                // 進度條
                Rectangle {
                    Layout.fillWidth: true
                    height: 4
                    radius: 2
                    color: Style.Theme.surface800

                    Rectangle {
                        width: parent.width * root.progress
                        height: parent.height
                        radius: 2
                        color: Style.Theme.accentNeonBlue
                    }
                }

                // 時間標記
                Text {
                    text: root.currentTime + " / " + root.totalTime
                    font.pixelSize: Style.Theme.fontSm
                    font.family: "Consolas"
                    color: Style.Theme.textSecondary
                }
            }
        }

        // ── 整區 Hover 偵測 ──
        MouseArea {
            id: videoHoverArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
        }
    }
}
