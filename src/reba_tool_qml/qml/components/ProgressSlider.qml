import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

RowLayout {
    id: root

    spacing: 4

    property int currentFrame: 0
    property int totalFrames: 0
    property bool enabled: false

    signal seekRequested(int frame)

    function _formatTime(frame) {
        var fps = 30.0;
        var seconds = Math.floor(frame / fps);
        var min = Math.floor(seconds / 60);
        var sec = seconds % 60;
        return (min < 10 ? "0" : "") + min + ":" + (sec < 10 ? "0" : "") + sec;
    }

    Text {
        text: _formatTime(root.currentFrame)
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.timeLabelFontSize
        color: Style.Theme.text
    }

    Slider {
        id: slider
        Layout.fillWidth: true
        from: 0
        to: Math.max(1, root.totalFrames)
        value: root.currentFrame
        enabled: root.enabled && root.totalFrames > 0
        stepSize: 1

        onMoved: {
            root.seekRequested(Math.floor(value));
        }
    }

    Text {
        text: _formatTime(root.totalFrames)
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.timeLabelFontSize
        color: Style.Theme.text
    }
}
