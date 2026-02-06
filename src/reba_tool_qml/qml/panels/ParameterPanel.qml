import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

GroupBox {
    id: root

    title: "評估參數"
    font.family: Style.Theme.fontFamily
    font.pixelSize: Style.Theme.groupboxFontSize
    font.bold: true

    property string side: "right"
    property real loadWeight: 0.0
    property string coupling: "good"

    signal sideSelected(string value)
    signal loadWeightEdited(real value)
    signal couplingSelected(string value)

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
        rowSpacing: 6

        Text {
            text: "分析側邊:"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.paramLabelFontSize
            color: Style.Theme.text
        }
        ComboBox {
            id: comboSide
            model: ["right", "left"]
            currentIndex: root.side === "left" ? 1 : 0
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.comboboxFontSize
            Layout.fillWidth: true
            onCurrentTextChanged: root.sideSelected(currentText)
        }

        Text {
            text: "負荷重量(kg):"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.paramLabelFontSize
            color: Style.Theme.text
        }
        SpinBox {
            id: spinLoad
            from: 0
            to: 10000   // 代表 0.0 ~ 100.0 kg
            value: root.loadWeight * 100
            stepSize: 100
            editable: true
            Layout.fillWidth: true
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.paramLabelFontSize

            property real realValue: value / 100.0

            textFromValue: function(value, locale) {
                return (value / 100.0).toFixed(1);
            }
            valueFromText: function(text, locale) {
                return Math.round(parseFloat(text) * 100);
            }

            onValueChanged: root.loadWeightEdited(realValue)
        }

        Text {
            text: "握持品質:"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.paramLabelFontSize
            color: Style.Theme.text
        }
        ComboBox {
            id: comboCoupling
            model: ["good", "fair", "poor", "unacceptable"]
            currentIndex: {
                var idx = model.indexOf(root.coupling);
                return idx >= 0 ? idx : 0;
            }
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.comboboxFontSize
            Layout.fillWidth: true
            onCurrentTextChanged: root.couplingSelected(currentText)
        }
    }
}
