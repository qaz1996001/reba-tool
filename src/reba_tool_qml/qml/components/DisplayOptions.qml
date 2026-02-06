import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

RowLayout {
    id: root

    spacing: Style.Theme.spacing

    property bool showAngleLines: true
    property bool showAngleValues: true

    signal angleLinesToggled(bool checked)
    signal angleValuesToggled(bool checked)
    signal saveCsvClicked()
    signal saveJsonClicked()

    CheckBox {
        id: checkLines
        text: "顯示角度線"
        checked: root.showAngleLines
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.checkboxFontSize
        onCheckedChanged: root.angleLinesToggled(checked)

        contentItem: Text {
            text: checkLines.text
            font: checkLines.font
            color: Style.Theme.text
            verticalAlignment: Text.AlignVCenter
            leftPadding: checkLines.indicator.width + checkLines.spacing
        }
    }

    CheckBox {
        id: checkValues
        text: "顯示角度數值"
        checked: root.showAngleValues
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.checkboxFontSize
        onCheckedChanged: root.angleValuesToggled(checked)

        contentItem: Text {
            text: checkValues.text
            font: checkValues.font
            color: Style.Theme.text
            verticalAlignment: Text.AlignVCenter
            leftPadding: checkValues.indicator.width + checkValues.spacing
        }
    }

    Item { Layout.fillWidth: true }

    Button {
        text: "保存CSV"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.buttonFontSize
        onClicked: root.saveCsvClicked()

        background: Rectangle {
            color: parent.pressed ? Style.Theme.buttonPressed
                   : parent.hovered ? Style.Theme.buttonHover
                   : Style.Theme.buttonBg
            border.color: Style.Theme.border
            radius: 4
        }
        contentItem: Text {
            text: parent.text
            font: parent.font
            color: Style.Theme.buttonText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    Button {
        text: "保存JSON"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.buttonFontSize
        onClicked: root.saveJsonClicked()

        background: Rectangle {
            color: parent.pressed ? Style.Theme.buttonPressed
                   : parent.hovered ? Style.Theme.buttonHover
                   : Style.Theme.buttonBg
            border.color: Style.Theme.border
            radius: 4
        }
        contentItem: Text {
            text: parent.text
            font: parent.font
            color: Style.Theme.buttonText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
}
