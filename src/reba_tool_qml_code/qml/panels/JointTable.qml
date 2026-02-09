import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 底部左側：關節角度與評分表
 * 6 列資料：頸部、軀幹、腿部、上臂、前臂、手腕
 * 即時從 rebaBridge 讀取角度與分數
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
        spacing: 10

        // 標題
        Row {
            spacing: 8
            Text {
                text: "\uD83E\uDDD1\u200D\uD83E\uDD1D\u200D\uD83E\uDDD1"  // 👥
                font.pixelSize: Style.Theme.fontXl
            }
            Text {
                text: "關節角度與評分"
                font.pixelSize: Style.Theme.fontXl
                font.bold: true
                font.letterSpacing: 3
                font.capitalization: Font.AllUppercase
                color: Style.Theme.textMuted
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        // 表格
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 4
            color: "transparent"
            border.color: Style.Theme.surface800
            border.width: 1
            clip: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // ── 表頭 ──
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    color: Style.Theme.surface800

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        Item {
                            width: parent.width * 0.4; height: parent.height
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "部位"
                                font.pixelSize: Style.Theme.fontXl
                                color: Style.Theme.textMuted
                            }
                        }
                        Item {
                            width: parent.width * 0.3; height: parent.height
                            Text {
                                anchors.centerIn: parent
                                text: "角度"
                                font.pixelSize: Style.Theme.fontXl
                                color: Style.Theme.textMuted
                            }
                        }
                        Item {
                            width: parent.width * 0.3; height: parent.height
                            Text {
                                anchors.centerIn: parent
                                text: "評分"
                                font.pixelSize: Style.Theme.fontXl
                                color: Style.Theme.textMuted
                            }
                        }
                    }
                }

                // ── 6 行關節資料 ──
                Repeater {
                    id: jointRepeater
                    model: 6

                    // 關節定義
                    property var jointNames: ["頸部", "軀幹", "腿部", "上臂", "前臂", "手腕"]

                    Rectangle {
                        id: rowDelegate
                        property int rowIndex: index

                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: rowIndex % 2 === 0 ? "transparent"
                                                  : Qt.rgba(Style.Theme.surface800.r,
                                                            Style.Theme.surface800.g,
                                                            Style.Theme.surface800.b, 0.3)

                        // 取得原始角度 float
                        property real rawAngle: {
                            switch (rowIndex) {
                                case 0: return rebaBridge.neckAngle;
                                case 1: return rebaBridge.trunkAngle;
                                case 2: return rebaBridge.legAngle;
                                case 3: return rebaBridge.upperArmAngle;
                                case 4: return rebaBridge.forearmAngle;
                                case 5: return rebaBridge.wristAngle;
                                default: return 0;
                            }
                        }
                        // 格式化為兩位小數 + 度符號
                        property string angleValue: rawAngle !== 0
                            ? rawAngle.toFixed(2) + "\u00B0" : "--"

                        // 取得分數值
                        property int scoreValue: {
                            switch (rowIndex) {
                                case 0: return rebaBridge.neckScore;
                                case 1: return rebaBridge.trunkScore;
                                case 2: return rebaBridge.legScore;
                                case 3: return rebaBridge.upperArmScore;
                                case 4: return rebaBridge.forearmScore;
                                case 5: return rebaBridge.wristScore;
                                default: return 0;
                            }
                        }

                        property bool isHigh: scoreValue >= 3

                        // 底部分隔線
                        Rectangle {
                            anchors.left: parent.left; anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 1
                            color: Qt.rgba(Style.Theme.surface800.r,
                                           Style.Theme.surface800.g,
                                           Style.Theme.surface800.b, 0.5)
                        }

                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            Item {
                                width: parent.width * 0.4; height: parent.height
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: jointRepeater.jointNames[rowDelegate.rowIndex]
                                    font.pixelSize: Style.Theme.fontMd
                                    color: Style.Theme.textSecondary
                                }
                            }
                            Item {
                                width: parent.width * 0.3; height: parent.height
                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.right: parent.right
                                    anchors.rightMargin: 8
                                    text: rowDelegate.angleValue
                                    font.pixelSize: Style.Theme.fontXl
                                    font.family: "Consolas"
                                    color: Style.Theme.accentNeonBlue
                                    horizontalAlignment: Text.AlignRight
                                }
                            }
                            Item {
                                width: parent.width * 0.3; height: parent.height
                                Text {
                                    anchors.centerIn: parent
                                    text: rowDelegate.scoreValue > 0
                                          ? rowDelegate.scoreValue.toString() : "--"
                                    font.pixelSize: Style.Theme.fontXl
                                    font.bold: true
                                    color: rowDelegate.isHigh ? Style.Theme.riskHigh
                                                              : Style.Theme.textPrimary
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
