import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

RowLayout {
    id: root

    spacing: Style.Theme.spacing

    property int rebaScore: 0
    property string riskLevelZh: ""
    property string riskColor: "#FFFFFF"

    // 分數顯示
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 50
        color: root.rebaScore > 0 ? root.riskColor : "transparent"
        radius: 4

        Text {
            anchors.centerIn: parent
            text: root.rebaScore > 0 ? "分數: " + root.rebaScore : "分數: --"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.rebaScoreFontSize
            font.bold: true
            color: Style.Theme.text
        }
    }

    // 風險等級顯示
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 50
        color: root.rebaScore > 0 ? root.riskColor : "transparent"
        radius: 4

        Text {
            anchors.centerIn: parent
            text: root.riskLevelZh ? "風險等級: " + root.riskLevelZh : "風險等級: --"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.riskLevelFontSize
            color: Style.Theme.text
        }
    }
}
