import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "../style" as Style

Window {
    id: root

    title: "REBA Table C - Score A \u00d7 Score B \u2192 Score C"
    width: 800
    height: 600
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
    color: Style.Theme.surface

    // tcModel 由 main.qml 傳入（不可用 tableCModel 作為 property 名，會遮蔽同名 context property）
    property var tcModel: null

    // 定位到主視窗右側（垂直置中），超出螢幕則改左側
    function positionToRight(winX, winY, winW, winH, screenRight, screenLeft, screenTop, screenBottom) {
        var newX = winX + winW + 10;
        var newY = winY + (winH - root.height) / 2;
        if (newX + root.width > screenRight)
            newX = winX - root.width - 10;
        if (newY < screenTop)
            newY = screenTop;
        if (newY + root.height > screenBottom)
            newY = screenBottom - root.height;
        root.x = newX;
        root.y = newY;
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
                    // 引用 scoreA/scoreB 建立響應式依賴，分數變化時所有 binding 重新求值
                    property int _sa: root.tcModel ? root.tcModel.scoreA : 0
                    property int _sb: root.tcModel ? root.tcModel.scoreB : 0

                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    color: {
                        var dep = _sa + _sb;
                        if (!root.tcModel) return Style.Theme.surface;
                        return root.tcModel.cellBgColor(row, col) || Style.Theme.surface;
                    }

                    Text {
                        anchors.centerIn: parent
                        text: {
                            var dep = parent._sa + parent._sb;
                            if (!root.tcModel) return "";
                            return root.tcModel.cellText(row, col);
                        }
                        font.family: Style.Theme.fontFamily
                        font.pixelSize: {
                            var dep = parent._sa + parent._sb;
                            if (!root.tcModel) return 10;
                            return root.tcModel.cellFontSize(row, col);
                        }
                        font.bold: {
                            var dep = parent._sa + parent._sb;
                            if (!root.tcModel) return false;
                            return root.tcModel.cellBold(row, col);
                        }
                        color: {
                            var dep = parent._sa + parent._sb;
                            if (!root.tcModel) return Style.Theme.text;
                            return root.tcModel.cellFgColor(row, col) || Style.Theme.text;
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
                    { color: "#047857", label: "1 可忽略" },
                    { color: "#059669", label: "2-3 低風險" },
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
