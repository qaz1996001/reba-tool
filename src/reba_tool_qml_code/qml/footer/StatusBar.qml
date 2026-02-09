import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../style" as Style

/**
 * 底部狀態列
 * 左側：裝置 / 儲存空間
 * 右側：綠色圓點 + 狀態文字
 */
Rectangle {
    id: root
    implicitHeight: Style.Theme.footerHeight
    color: Style.Theme.bgDeepNavy

    property bool systemReady: true
    property string statusText: "SYSTEM READY"

    // ── 頂部邊線 ──
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 1
        color: Style.Theme.surface800
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16

        // 左側資訊
        Row {
            spacing: 16
            Text {
                text: "DEVICE: GPU ACCELERATED"
                font.pixelSize: Style.Theme.fontXs
                color: Style.Theme.textMuted
            }
            Text {
                text: "RECORDS: " + dataBridge.recordCount
                font.pixelSize: Style.Theme.fontXs
                color: Style.Theme.textMuted
            }
        }

        Item { Layout.fillWidth: true }

        // 右側狀態
        Row {
            spacing: 6
            Rectangle {
                width: 6; height: 6
                radius: 3
                anchors.verticalCenter: parent.verticalCenter
                color: root.systemReady ? "#10b981" : "#ef4444"
            }
            Text {
                text: root.statusText
                font.pixelSize: Style.Theme.fontXs
                color: Style.Theme.textMuted
            }
        }
    }
}
