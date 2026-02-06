import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style
import "../components" as Components

ColumnLayout {
    id: root

    spacing: Style.Theme.spacing

    // 屬性（由 main.qml 綁定）
    property int frameCounter: 0
    property bool isProcessing: false
    property bool isPaused: false
    property int currentFrame: 0
    property int totalFrames: 0
    property int frameCount: 0
    property real fps: 0.0
    property int recordCount: 0
    property bool showAngleLines: true
    property bool showAngleValues: true
    property var logMessages: []
    property bool hasVideoSource: false

    // 信號
    signal cameraClicked()
    signal videoClicked()
    signal pauseClicked()
    signal stopClicked()
    signal seekRequested(int frame)
    signal showAngleLinesToggled(bool checked)
    signal showAngleValuesToggled(bool checked)
    signal saveCsvClicked()
    signal saveJsonClicked()

    // 影片顯示
    Components.VideoDisplay {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumWidth: Style.Theme.videoMinWidth
        Layout.minimumHeight: Style.Theme.videoMinHeight
        frameCounter: root.frameCounter
    }

    // 控制按鈕
    Components.ControlBar {
        Layout.fillWidth: true
        isProcessing: root.isProcessing
        isPaused: root.isPaused
        onCameraClicked: root.cameraClicked()
        onVideoClicked: root.videoClicked()
        onPauseClicked: root.pauseClicked()
        onStopClicked: root.stopClicked()
    }

    // 進度條
    Components.ProgressSlider {
        Layout.fillWidth: true
        currentFrame: root.currentFrame
        totalFrames: root.totalFrames
        enabled: root.isProcessing && root.hasVideoSource
        onSeekRequested: function(frame) { root.seekRequested(frame) }
    }

    // 顯示選項
    Components.DisplayOptions {
        Layout.fillWidth: true
        showAngleLines: root.showAngleLines
        showAngleValues: root.showAngleValues
        onAngleLinesToggled: function(checked) { root.showAngleLinesToggled(checked) }
        onAngleValuesToggled: function(checked) { root.showAngleValuesToggled(checked) }
        onSaveCsvClicked: root.saveCsvClicked()
        onSaveJsonClicked: root.saveJsonClicked()
    }

    // 底部資訊區
    RowLayout {
        Layout.fillWidth: true
        Layout.maximumHeight: Style.Theme.logMaxHeight
        spacing: Style.Theme.spacing

        Components.LogPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            messages: root.logMessages
        }

        Components.StatsPanel {
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            frameCount: root.frameCount
            fps: root.fps
            recordCount: root.recordCount
        }
    }
}
