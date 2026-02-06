import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

ColumnLayout {
    id: root

    spacing: Style.Theme.spacing

    // REBA 分數屬性
    property int rebaScore: 0
    property string riskLevelZh: ""
    property string riskColor: "#FFFFFF"
    property string riskDescription: ""
    property bool dataLocked: false

    // 參數屬性
    property string side: "right"
    property real loadWeight: 0.0
    property string coupling: "good"

    // 信號
    signal sideSelected(string value)
    signal loadWeightEdited(real value)
    signal couplingSelected(string value)
    signal dataLockToggled(bool locked)
    signal tableCClicked()
    signal copyDataClicked()

    // 參數面板
    ParameterPanel {
        Layout.fillWidth: true
        side: root.side
        loadWeight: root.loadWeight
        coupling: root.coupling
        onSideSelected: function(value) { root.sideSelected(value) }
        onLoadWeightEdited: function(value) { root.loadWeightEdited(value) }
        onCouplingSelected: function(value) { root.couplingSelected(value) }
    }

    // REBA 評估群組
    GroupBox {
        Layout.fillWidth: true
        Layout.fillHeight: true
        title: "關節角度與REBA分數"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.groupboxFontSize
        font.bold: true

        background: Rectangle {
            y: parent.topPadding - parent.bottomPadding
            width: parent.width
            height: parent.height - parent.topPadding + parent.bottomPadding
            color: Style.Theme.surface
            border.color: Style.Theme.border
            radius: 4
        }

        label: Text {
            text: parent.title
            font: parent.font
            color: Style.Theme.text
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 6

            // 分數和風險等級
            RebaScorePanel {
                Layout.fillWidth: true
                rebaScore: root.rebaScore
                riskLevelZh: root.riskLevelZh
                riskColor: root.riskColor
            }

            // 分數明細表
            ScoreDetailTable {
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            // 風險描述
            Text {
                text: root.riskDescription
                font.family: Style.Theme.fontFamily
                font.pixelSize: Style.Theme.riskDescFontSize
                color: Style.Theme.textSecondary
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                visible: root.riskDescription.length > 0
            }

            // 資料操作按鈕
            RowLayout {
                Layout.fillWidth: true
                spacing: Style.Theme.spacing

                CheckBox {
                    id: lockCheck
                    text: "鎖定資料"
                    checked: root.dataLocked
                    font.family: Style.Theme.fontFamily
                    font.pixelSize: Style.Theme.checkboxFontSize
                    onCheckedChanged: root.dataLockToggled(checked)

                    contentItem: Text {
                        text: lockCheck.text
                        font: lockCheck.font
                        color: Style.Theme.text
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: lockCheck.indicator.width + lockCheck.spacing
                    }
                }

                Button {
                    text: "Table C"
                    font.family: Style.Theme.fontFamily
                    font.pixelSize: Style.Theme.buttonFontSize
                    onClicked: root.tableCClicked()

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
                    }
                }

                Button {
                    text: "複製資料"
                    font.family: Style.Theme.fontFamily
                    font.pixelSize: Style.Theme.buttonFontSize
                    onClicked: root.copyDataClicked()

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
                    }
                }
            }
        }
    }

    Item { Layout.fillHeight: true }
}
