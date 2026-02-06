import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

RowLayout {
    id: root

    spacing: Style.Theme.spacing

    property bool isProcessing: false
    property bool isPaused: false
    property bool isRecording: false

    signal cameraClicked()
    signal videoClicked()
    signal pauseClicked()
    signal stopClicked()
    signal recordToggled()

    Button {
        id: btnCamera
        text: "開啟攝影機"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.buttonFontSize
        enabled: !root.isProcessing
        Layout.fillWidth: true
        onClicked: root.cameraClicked()

        background: Rectangle {
            color: btnCamera.pressed ? Style.Theme.buttonPressed
                   : btnCamera.hovered ? Style.Theme.buttonHover
                   : Style.Theme.buttonBg
            border.color: Style.Theme.border
            radius: 4
        }
        contentItem: Text {
            text: btnCamera.text
            font: btnCamera.font
            color: Style.Theme.buttonText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    Button {
        id: btnVideo
        text: "選擇影片"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.buttonFontSize
        enabled: !root.isProcessing
        Layout.fillWidth: true
        onClicked: root.videoClicked()

        background: Rectangle {
            color: btnVideo.pressed ? Style.Theme.buttonPressed
                   : btnVideo.hovered ? Style.Theme.buttonHover
                   : Style.Theme.buttonBg
            border.color: Style.Theme.border
            radius: 4
        }
        contentItem: Text {
            text: btnVideo.text
            font: btnVideo.font
            color: Style.Theme.buttonText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    Button {
        id: btnPause
        text: root.isPaused ? "恢復" : "暫停"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.buttonFontSize
        enabled: root.isProcessing
        Layout.fillWidth: true
        onClicked: root.pauseClicked()

        background: Rectangle {
            color: btnPause.pressed ? Style.Theme.buttonPressed
                   : btnPause.hovered ? Style.Theme.buttonHover
                   : Style.Theme.buttonBg
            border.color: Style.Theme.border
            radius: 4
        }
        contentItem: Text {
            text: btnPause.text
            font: btnPause.font
            color: Style.Theme.buttonText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    Button {
        id: btnRecord
        text: root.isRecording ? "停止錄影" : "錄影"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.buttonFontSize
        enabled: root.isProcessing
        Layout.fillWidth: true
        onClicked: root.recordToggled()

        background: Rectangle {
            color: root.isRecording ? "#cc3333"
                   : btnRecord.pressed ? Style.Theme.buttonPressed
                   : btnRecord.hovered ? Style.Theme.buttonHover
                   : Style.Theme.buttonBg
            border.color: root.isRecording ? "#ff4444" : Style.Theme.border
            radius: 4
        }
        contentItem: Text {
            text: btnRecord.text
            font: btnRecord.font
            color: root.isRecording ? "#ffffff" : Style.Theme.buttonText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    Button {
        id: btnStop
        text: "停止"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.buttonFontSize
        enabled: root.isProcessing
        Layout.fillWidth: true
        onClicked: root.stopClicked()

        background: Rectangle {
            color: btnStop.pressed ? Style.Theme.buttonPressed
                   : btnStop.hovered ? Style.Theme.buttonHover
                   : Style.Theme.buttonBg
            border.color: Style.Theme.border
            radius: 4
        }
        contentItem: Text {
            text: btnStop.text
            font: btnStop.font
            color: Style.Theme.buttonText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
}
