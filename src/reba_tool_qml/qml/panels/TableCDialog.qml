import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

Dialog {
    id: root

    title: "REBA Table C - Score A \u00d7 Score B \u2192 Score C"
    width: 650
    height: 500
    modal: false

    // tableCModel 由 rootContext 提供
    property var tableCModel: null

    background: Rectangle {
        color: Style.Theme.surface
        border.color: Style.Theme.border
        radius: 4
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Text {
            text: "Table C: 由 Score A (列) 與 Score B (欄) 查詢 Score C"
            font.family: Style.Theme.fontFamily
            font.pixelSize: 12
            font.bold: true
            color: Style.Theme.text
            Layout.alignment: Qt.AlignHCenter
        }

        // 表格
        GridLayout {
            id: grid
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 13
            rowSpacing: 1
            columnSpacing: 1

            Repeater {
                model: 13 * 13

                Rectangle {
                    property int row: Math.floor(index / 13)
                    property int col: index % 13

                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    color: {
                        if (!root.tableCModel) return Style.Theme.surface;
                        var c = root.tableCModel.data(root.tableCModel.index(row, col), 257);
                        return c ? c : Style.Theme.surface;
                    }

                    Text {
                        anchors.centerIn: parent
                        text: {
                            if (!root.tableCModel) return "";
                            var val = root.tableCModel.data(root.tableCModel.index(row, col), 0);
                            return val ? val : "";
                        }
                        font.family: Style.Theme.fontFamily
                        font.pixelSize: {
                            if (!root.tableCModel) return 10;
                            var s = root.tableCModel.data(root.tableCModel.index(row, col), 259);
                            return s ? s : 10;
                        }
                        font.bold: {
                            if (!root.tableCModel) return false;
                            var b = root.tableCModel.data(root.tableCModel.index(row, col), 258);
                            return b ? true : false;
                        }
                        color: {
                            if (!root.tableCModel) return Style.Theme.text;
                            var fg = root.tableCModel.data(root.tableCModel.index(row, col), 260);
                            return fg ? fg : Style.Theme.text;
                        }
                    }
                }
            }
        }

        // 圖例
        RowLayout {
            spacing: 8
            Layout.alignment: Qt.AlignHCenter

            Text {
                text: "圖例:"
                font.family: Style.Theme.fontFamily
                font.pixelSize: 10
                color: Style.Theme.text
            }

            Repeater {
                model: [
                    { color: "#10b981", label: "1 可忽略" },
                    { color: "#34d399", label: "2-3 低風險" },
                    { color: "#fbbf24", label: "4-7 中風險" },
                    { color: "#f43f5e", label: "8-10 高風險" },
                    { color: "#ff0000", label: "11-12 極高風險" }
                ]

                Row {
                    spacing: 2
                    Rectangle {
                        width: 12; height: 12
                        color: modelData.color
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: modelData.label
                        font.family: Style.Theme.fontFamily
                        font.pixelSize: 9
                        color: Style.Theme.text
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        Button {
            text: "關閉"
            Layout.alignment: Qt.AlignHCenter
            onClicked: root.close()

            background: Rectangle {
                color: parent.pressed ? Style.Theme.buttonPressed
                       : parent.hovered ? Style.Theme.buttonHover
                       : Style.Theme.buttonBg
                border.color: Style.Theme.border
                radius: 4
            }
            contentItem: Text {
                text: parent.text
                font.family: Style.Theme.fontFamily
                font.pixelSize: Style.Theme.buttonFontSize
                color: Style.Theme.buttonText
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
