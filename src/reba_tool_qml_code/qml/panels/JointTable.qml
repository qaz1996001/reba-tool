import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 底部左側：關節角度與評分表
 * 6 列資料：頸部、軀幹、腿部、上臂、前臂、手腕
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
                font.pixelSize: Style.Theme.fontLg
            }
            Text {
                text: "關節角度與評分"
                font.pixelSize: Style.Theme.fontSm
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

            ListView {
                id: jointListView
                anchors.fill: parent
                interactive: true
                clip: true

                // 靜態模型（Phase 2 替換為 bridge 資料）
                model: ListModel {
                    ListElement { part: "頸部"; angle: "15°"; score: 1; isHigh: false }
                    ListElement { part: "軀幹"; angle: "22°"; score: 2; isHigh: false }
                    ListElement { part: "腿部"; angle: "-";   score: 1; isHigh: false }
                    ListElement { part: "上臂"; angle: "45°"; score: 3; isHigh: true  }
                    ListElement { part: "前臂"; angle: "85°"; score: 1; isHigh: false }
                    ListElement { part: "手腕"; angle: "12°"; score: 2; isHigh: false }
                }

                headerPositioning: ListView.OverlayHeader
                header: Rectangle {
                    width: jointListView.width
                    height: 30
                    color: Style.Theme.surface800
                    z: 10

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        Item {
                            width: parent.width * 0.4; height: parent.height
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "部位"
                                font.pixelSize: Style.Theme.fontXs
                                color: Style.Theme.textMuted
                            }
                        }
                        Item {
                            width: parent.width * 0.3; height: parent.height
                            Text {
                                anchors.centerIn: parent
                                text: "角度"
                                font.pixelSize: Style.Theme.fontXs
                                color: Style.Theme.textMuted
                            }
                        }
                        Item {
                            width: parent.width * 0.3; height: parent.height
                            Text {
                                anchors.centerIn: parent
                                text: "評分"
                                font.pixelSize: Style.Theme.fontXs
                                color: Style.Theme.textMuted
                            }
                        }
                    }
                }

                delegate: Rectangle {
                    id: rowDelegate
                    property int rowIndex: index
                    width: jointListView.width
                    height: 32
                    color: rowIndex % 2 === 0 ? "transparent"
                                              : Qt.rgba(Style.Theme.surface800.r,
                                                        Style.Theme.surface800.g,
                                                        Style.Theme.surface800.b, 0.3)

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
                                text: model.part
                                font.pixelSize: Style.Theme.fontXs
                                color: Style.Theme.textSecondary
                            }
                        }
                        Item {
                            width: parent.width * 0.3; height: parent.height
                            Text {
                                anchors.centerIn: parent
                                text: model.angle
                                font.pixelSize: Style.Theme.fontXs
                                font.family: "Consolas"
                                color: Style.Theme.accentNeonBlue
                            }
                        }
                        Item {
                            width: parent.width * 0.3; height: parent.height
                            Text {
                                anchors.centerIn: parent
                                text: model.score
                                font.pixelSize: Style.Theme.fontXs
                                font.bold: true
                                color: model.isHigh ? Style.Theme.riskHigh
                                                    : Style.Theme.textPrimary
                            }
                        }
                    }
                }
            }
        }
    }
}
