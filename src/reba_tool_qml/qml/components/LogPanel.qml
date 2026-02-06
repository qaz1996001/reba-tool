import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

GroupBox {
    id: root

    title: "系統日誌"
    font.family: Style.Theme.fontFamily
    font.pixelSize: Style.Theme.groupboxFontSize
    font.bold: true

    property var messages: []

    background: Rectangle {
        y: root.topPadding - root.bottomPadding
        width: parent.width
        height: parent.height - root.topPadding + root.bottomPadding
        color: Style.Theme.surface
        border.color: Style.Theme.border
        radius: 4
    }

    label: Text {
        text: root.title
        font: root.font
        color: Style.Theme.text
    }

    ScrollView {
        anchors.fill: parent

        TextArea {
            id: logArea
            readOnly: true
            wrapMode: TextArea.Wrap
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.logTextFontSize
            color: Style.Theme.logText
            background: Rectangle {
                color: Style.Theme.logBackground
            }
            text: root.messages.join("\n")

            onTextChanged: {
                // 自動滾動到底部
                logArea.cursorPosition = logArea.length;
            }
        }
    }
}
