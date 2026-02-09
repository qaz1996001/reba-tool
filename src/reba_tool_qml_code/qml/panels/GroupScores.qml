import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 底部中間：群組評分分解
 * 左側 2 格：Group A Score / Group B Score（含子分數分解）
 * 右側大格：Score C + Activity 修正
 */
Rectangle {
    id: root
    color: Style.Theme.bgCharcoal

    // ── 佔位資料（Phase 2 綁定）──
    property int groupAScore: 4
    property int groupBScore: 5
    property int scoreCValue: 6
    property int activityScore: 1

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
        spacing: 10

        // 標題
        Row {
            spacing: 8
            Text {
                text: "\uD83C\uDF33"  // 🌳
                font.pixelSize: Style.Theme.fontXl
            }
            Text {
                text: "群組評分分解"
                font.pixelSize: Style.Theme.fontXl
                font.bold: true
                font.letterSpacing: 3
                font.capitalization: Font.AllUppercase
                color: Style.Theme.textMuted
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        // 2x2 Grid
        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 2
            rowSpacing: 10
            columnSpacing: 10

            // ── Group A ──
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Style.Theme.borderRadius
                Layout.minimumWidth: 1.1
                color: Qt.rgba(Style.Theme.surface900.r,
                               Style.Theme.surface900.g,
                               Style.Theme.surface900.b, 0.5)
                border.color: Style.Theme.surface800
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    Column {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: "GROUP A SCORE"
                            font.pixelSize: Style.Theme.fontLg
                            font.bold: true
                            font.letterSpacing: 1
                            font.capitalization: Font.AllUppercase
                            color: Style.Theme.textMuted
                        }
                        Text {
                            text: "軀幹+頸部+腿部+荷重"
                            font.pixelSize: Style.Theme.fontLg
                            color: Style.Theme.textMuted
                            opacity: 0.6
                        }
                        Text {
                            text: rebaBridge.trunkScore + "+" + rebaBridge.neckScore + "+" + rebaBridge.legScore + "+" + rebaBridge.loadScore
                            font.pixelSize: Style.Theme.fontLg
                            font.family: "Consolas"
                            color: Style.Theme.accentNeonGreen
                            opacity: 0.8
                        }
                    }
                    Text {
                        text: root.groupAScore.toString()
                        font.pixelSize: Style.Theme.fontXxl
                        font.weight: Font.Black
                        color: Style.Theme.accentNeonGreen
                    }
                }
            }

            // ── Score C（右側大格，跨兩列高度）──
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.rowSpan: 2
                radius: 12
                border.color: Qt.rgba(Style.Theme.accentNeonBlue.r,
                                      Style.Theme.accentNeonBlue.g,
                                      Style.Theme.accentNeonBlue.b, 0.2)
                border.width: 1

                gradient: Gradient {
                    GradientStop {
                        position: 0.0
                        color: Qt.rgba(Style.Theme.accentNeonBlue.r,
                                       Style.Theme.accentNeonBlue.g,
                                       Style.Theme.accentNeonBlue.b, 0.05)
                    }
                    GradientStop {
                        position: 1.0
                        color: Qt.rgba(Style.Theme.surface900.r,
                                       Style.Theme.surface900.g,
                                       Style.Theme.surface900.b, 0.4)
                    }
                }

                // 背景大字裝飾
                Text {
                    anchors.centerIn: parent
                    text: "\uD83E\uDDEE"  // 🧮
                    font.pixelSize: 80
                    opacity: 0.05
                    color: Style.Theme.textPrimary
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 6

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "SCORE C"
                        font.pixelSize: Style.Theme.fontLg
                        font.bold: true
                        font.letterSpacing: 3
                        font.capitalization: Font.AllUppercase
                        color: Style.Theme.textMuted
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: root.scoreCValue.toString()
                        font.pixelSize: 52
                        font.weight: Font.Black
                        color: Style.Theme.accentNeonBlue
                    }
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: activityLabel.implicitWidth + 20
                        height: 26
                        radius: 13
                        color: Qt.rgba(Style.Theme.surface800.r,
                                       Style.Theme.surface800.g,
                                       Style.Theme.surface800.b, 0.8)
                        border.color: Style.Theme.borderNavy
                        border.width: 1
                        Text {
                            id: activityLabel
                            anchors.centerIn: parent
                            text: "Activity +" + root.activityScore
                            font.pixelSize: Style.Theme.fontLg
                            color: Style.Theme.textMuted
                        }
                    }
                }
            }

            // ── Group B ──
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Style.Theme.borderRadius
                color: Qt.rgba(Style.Theme.surface900.r,
                               Style.Theme.surface900.g,
                               Style.Theme.surface900.b, 0.5)
                border.color: Style.Theme.surface800
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    Column {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: "GROUP B SCORE"
                            font.pixelSize: Style.Theme.fontLg
                            font.bold: true
                            font.letterSpacing: 1
                            font.capitalization: Font.AllUppercase
                            color: Style.Theme.textMuted
                        }
                        Text {
                            text: "上臂+前臂+手腕+耦合"
                            font.pixelSize: Style.Theme.fontLg
                            color: Style.Theme.textMuted
                            opacity: 0.6
                        }
                        Text {
                            text: rebaBridge.upperArmScore + "+" + rebaBridge.forearmScore + "+" + rebaBridge.wristScore + "+" + rebaBridge.couplingScore
                            font.pixelSize: Style.Theme.fontLg
                            font.family: "Consolas"
                            color: Style.Theme.accentNeonBlue
                            opacity: 0.8
                        }
                    }
                    Text {
                        text: root.groupBScore.toString()
                        font.pixelSize: Style.Theme.fontXxl
                        font.weight: Font.Black
                        color: Style.Theme.accentNeonBlue
                    }
                }
            }
        }
    }
}
