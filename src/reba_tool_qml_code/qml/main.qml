import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "style" as Style
import "panels"
import "footer"

/**
 * REBA Unified Dashboard - 主視窗
 * 深色霓虹主題，對應 code.html 設計稿
 *
 * 佈局結構：
 * ┌──────────────────────────────────────┐
 * │            HeaderBar (48px)          │
 * ├─────────────────────┬────────────────┤
 * │                     │   SidePanel    │
 * │     VideoArea       │   (320px)      │
 * │     (flex-1)        │  參數/趨勢/匯出 │
 * │                     │                │
 * ├──────┬──────────────┴───┬────────────┤
 * │Joint │   GroupScores    │ TableC     │
 * │Table │   (flex-1)       │ Matrix     │
 * │(25%) │                  │ (35%)      │
 * ├──────┴──────────────────┴────────────┤
 * │           StatusBar (24px)           │
 * └──────────────────────────────────────┘
 */
ApplicationWindow {
    id: window
    visible: true
    width: 1400
    height: 900
    minimumWidth: 1100
    minimumHeight: 700
    title: "REBA Unified Dashboard"
    color: Style.Theme.bgDeepNavy

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ══════════════════════════════════
        // 頂部標題列
        // ══════════════════════════════════
        HeaderBar {
            Layout.fillWidth: true
            Layout.preferredHeight: Style.Theme.headerHeight
        }

        // ══════════════════════════════════
        // 中間主區域：影片 + 右側面板
        // ══════════════════════════════════
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 300
            spacing: 0

            // 影片區（彈性填充）
            VideoArea {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 500
            }

            // 右側面板（固定寬度）
            SidePanel {
                Layout.preferredWidth: Style.Theme.sidePanelWidth
                Layout.minimumWidth: Style.Theme.sidePanelMinWidth
                Layout.fillHeight: true
            }
        }

        // ── 中間/底部分隔線 ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            Layout.maximumHeight: 1
            color: Style.Theme.borderNavy
        }

        // ══════════════════════════════════
        // 底部三欄面板
        // ══════════════════════════════════
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: Style.Theme.bottomHeight
            Layout.maximumHeight: Style.Theme.bottomHeight
            spacing: 0

            // 左欄：關節角度表（25%）
            JointTable {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: 25  // ratio
                Layout.minimumWidth: 200
            }

            // 中欄：群組評分（flex-1）
            GroupScores {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: 40  // ratio
                Layout.minimumWidth: 300
            }

            // 右欄：Table C 矩陣（35%）
            TableCMatrix {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: 35  // ratio
                Layout.minimumWidth: 250
            }
        }

        // ══════════════════════════════════
        // 底部狀態列
        // ══════════════════════════════════
        StatusBar {
            Layout.fillWidth: true
            Layout.preferredHeight: Style.Theme.footerHeight
        }
    }
}
