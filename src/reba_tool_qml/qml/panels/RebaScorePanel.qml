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
        color: Style.Theme.surface
        radius: 4
        border.color: root.rebaScore > 0 ? root.riskColor : Style.Theme.border
        border.width: root.rebaScore > 0 ? 2 : 1

        // 左側色條
        Rectangle {
            width: 4
            height: parent.height
            color: root.rebaScore > 0 ? root.riskColor : "transparent"
            anchors.left: parent.left
            radius: 2
        }

        Text {
            anchors.centerIn: parent
            text: root.rebaScore > 0 ? "分數: " + root.rebaScore : "分數: --"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.rebaScoreFontSize
            font.bold: true
            color: root.rebaScore > 0 ? root.riskColor : Style.Theme.textSecondary
        }
    }

    // 風險等級顯示
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 50
        color: Style.Theme.surface
        radius: 4
        border.color: root.rebaScore > 0 ? root.riskColor : Style.Theme.border
        border.width: root.rebaScore > 0 ? 2 : 1

        // 左側色條
        Rectangle {
            width: 4
            height: parent.height
            color: root.rebaScore > 0 ? root.riskColor : "transparent"
            anchors.left: parent.left
            radius: 2
        }

        Text {
            anchors.centerIn: parent
            text: root.riskLevelZh ? "風險等級: " + root.riskLevelZh : "風險等級: --"
            font.family: Style.Theme.fontFamily
            font.pixelSize: Style.Theme.riskLevelFontSize
            color: root.rebaScore > 0 ? root.riskColor : Style.Theme.textSecondary
        }
    }
}
