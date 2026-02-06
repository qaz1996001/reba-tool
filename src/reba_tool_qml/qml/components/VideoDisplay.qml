import QtQuick 2.15
import QtQuick.Controls 2.15
import "../style" as Style

Rectangle {
    id: root

    color: Style.Theme.videoBackground
    border.color: Style.Theme.videoBorder
    border.width: Style.Theme.videoBorderWidth

    property int frameCounter: 0

    Image {
        id: videoImage
        anchors.fill: parent
        anchors.margins: Style.Theme.videoBorderWidth
        fillMode: Image.PreserveAspectFit
        cache: false
        source: root.frameCounter > 0
                ? "image://video/frame?" + root.frameCounter
                : ""
        asynchronous: false
    }

    // 提示文字（無影像時顯示）
    Text {
        anchors.centerIn: parent
        text: "請選擇影片來源"
        color: "#aaaaaa"
        font.family: Style.Theme.fontFamily
        font.pixelSize: Style.Theme.videoHintFontSize
        visible: root.frameCounter === 0
    }
}
