import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

GroupBox {
    id: root

    title: "統計資訊"
    font.family: Style.Theme.fontFamily
    font.pixelSize: Style.Theme.groupboxFontSize
    font.bold: true

    property int frameCount: 0
    property real fps: 0.0
    property int recordCount: 0

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

    GridLayout {
        anchors.fill: parent
        columns: 2
        columnSpacing: 8
        rowSpacing: 4

        Text {
            text: "處理幀數:"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.statsFontSize
            font.bold: true
            color: Style.Theme.text
        }
        Text {
            text: root.frameCount.toString()
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.statsFontSize
            font.bold: true
            color: Style.Theme.text
        }

        Text {
            text: "FPS:"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.statsFontSize
            font.bold: true
            color: Style.Theme.text
        }
        Text {
            text: root.fps.toFixed(1)
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.statsFontSize
            font.bold: true
            color: Style.Theme.text
        }

        Text {
            text: "記錄數:"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.statsFontSize
            font.bold: true
            color: Style.Theme.text
        }
        Text {
            text: root.recordCount.toString()
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.statsFontSize
            font.bold: true
            color: Style.Theme.text
        }
    }
}
