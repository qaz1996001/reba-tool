import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
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

    // ========== File Dialogs ==========
    FileDialog {
        id: videoFileDialog
        title: "選擇影片檔案"
        nameFilters: ["影片檔案 (*.mp4 *.avi *.mov *.mkv)", "所有檔案 (*)"]
        onAccepted: {
            var path = selectedFile.toString();
            if (Qt.platform.os === "windows") {
                path = path.replace(/^file:\/\/\//, "");
            } else {
                path = path.replace(/^file:\/\//, "");
            }
            path = decodeURIComponent(path);
            dataBridge.log("選擇影片: " + path.split("/").pop());
            videoBridge.startVideo(path);
            videoBridge.setParameters(settingsBridge.side, settingsBridge.loadWeight, settingsBridge.coupling);
            videoBridge.setDisplayOptions(settingsBridge.showAngleLines, settingsBridge.showAngleValues);
        }
    }

    FileDialog {
        id: saveCsvDialog
        title: "保存CSV檔案"
        nameFilters: ["CSV檔案 (*.csv)"]
        fileMode: FileDialog.SaveFile
        onAccepted: {
            var path = selectedFile.toString().replace(/^file:\/\/\//, "");
            path = decodeURIComponent(path);
            dataBridge.saveCsv(path);
        }
    }

    FileDialog {
        id: saveJsonDialog
        title: "保存JSON檔案"
        nameFilters: ["JSON檔案 (*.json)"]
        fileMode: FileDialog.SaveFile
        onAccepted: {
            var path = selectedFile.toString().replace(/^file:\/\/\//, "");
            path = decodeURIComponent(path);
            dataBridge.saveJson(path);
        }
    }

    FileDialog {
        id: saveImageDialog
        title: "保存標註影像"
        nameFilters: ["PNG圖片 (*.png)", "JPEG圖片 (*.jpg *.jpeg)", "所有檔案 (*)"]
        fileMode: FileDialog.SaveFile
        onAccepted: {
            var path = selectedFile.toString().replace(/^file:\/\/\//, "");
            path = decodeURIComponent(path);
            videoBridge.saveImage(path);
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ══════════════════════════════════
        // 頂部標題列
        // ══════════════════════════════════
        HeaderBar {
            Layout.fillWidth: true
            Layout.preferredHeight: Style.Theme.headerHeight
            fpsValue: videoBridge.fps
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

                frameCounter: videoBridge.frameCounter
                rebaScore: rebaBridge.rebaScore
                riskLabel: rebaBridge.riskLevelZh
                riskColor: rebaBridge.riskColor
                hasVideo: videoBridge.isProcessing
                isPlaying: videoBridge.isProcessing && !videoBridge.isPaused
                progress: videoBridge.totalFrames > 0
                         ? videoBridge.currentFrame / videoBridge.totalFrames : 0
                currentTime: {
                    if (videoBridge.fps > 0 && videoBridge.currentFrame >= 0) {
                        var sec = Math.floor(videoBridge.currentFrame / videoBridge.fps);
                        var m = Math.floor(sec / 60);
                        var s = sec % 60;
                        return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
                    }
                    return "00:00";
                }
                totalTime: {
                    if (videoBridge.fps > 0 && videoBridge.totalFrames > 0) {
                        var sec = Math.floor(videoBridge.totalFrames / videoBridge.fps);
                        var m = Math.floor(sec / 60);
                        var s = sec % 60;
                        return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
                    }
                    return "00:00";
                }

                onCameraClicked: {
                    dataBridge.log("正在開啟攝影機...");
                    videoBridge.startCamera();
                    videoBridge.setParameters(settingsBridge.side, settingsBridge.loadWeight, settingsBridge.coupling);
                    videoBridge.setDisplayOptions(settingsBridge.showAngleLines, settingsBridge.showAngleValues);
                }
                onVideoClicked: {
                    videoFileDialog.open();
                }
                onPlayPauseClicked: {
                    videoBridge.togglePause();
                }
                onStopClicked: {
                    dataBridge.log("正在停止處理...");
                    videoBridge.stop();
                }
                onSeekRequested: function(ratio) {
                    if (videoBridge.totalFrames > 0) {
                        videoBridge.seekFrame(Math.floor(ratio * videoBridge.totalFrames));
                    }
                }
            }

            // 右側面板（固定寬度）
            SidePanel {
                Layout.preferredWidth: Style.Theme.sidePanelWidth
                Layout.minimumWidth: Style.Theme.sidePanelMinWidth
                Layout.fillHeight: true

                onExportCsvClicked: {
                    saveCsvDialog.currentFile = "file:///" + videoBridge.suggestFilePath("csv");
                    saveCsvDialog.open();
                }
                onResetClicked: {
                    dataBridge.log("正在停止處理...");
                    videoBridge.stop();
                }
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

                groupAScore: rebaBridge.scoreA
                groupBScore: rebaBridge.scoreB
                scoreCValue: rebaBridge.scoreC
                activityScore: rebaBridge.activityScore
            }

            // 右欄：Table C 矩陣（35%）
            TableCMatrix {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: 35  // ratio
                Layout.minimumWidth: 250

                scoreA: tableCModel.scoreA
                scoreB: tableCModel.scoreB
            }
        }

        // ══════════════════════════════════
        // 底部狀態列
        // ══════════════════════════════════
        StatusBar {
            Layout.fillWidth: true
            Layout.preferredHeight: Style.Theme.footerHeight
            systemReady: true
            statusText: videoBridge.isProcessing ? "PROCESSING" : "SYSTEM READY"
        }
    }

    // ========== 初始化 ==========
    Component.onCompleted: {
        dataBridge.log("系統啟動完成");
        dataBridge.log("請選擇影片來源開始分析");
    }

    // ========== 視窗關閉 ==========
    onClosing: function(close) {
        videoBridge.cleanup();
        close.accepted = true;
    }

    // ========== 狀態連接 ==========
    Connections {
        target: videoBridge
        function onImageSaved(path) {
            dataBridge.log("影像已保存: " + path.split("/").pop());
        }
        function onRecordingStarted() {
            dataBridge.log("錄影開始");
        }
        function onRecordingStopped(path) {
            dataBridge.log("影片已保存: " + path.split("/").pop());
        }
    }
}
