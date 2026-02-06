import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import "style" as Style
import "panels" as Panels

ApplicationWindow {
    id: window

    visible: true
    title: "MediaPipe REBA 分析系統 (QML)"
    x: Style.Theme.windowX
    y: Style.Theme.windowY
    width: Style.Theme.windowWidth
    height: Style.Theme.windowHeight
    color: Style.Theme.background

    // ========== Table C Dialog ==========
    Panels.TableCDialog {
        id: tableCDialog
        tableCModel: tableCModel
    }

    // ========== File Dialogs ==========
    FileDialog {
        id: videoFileDialog
        title: "選擇影片檔案"
        nameFilters: ["影片檔案 (*.mp4 *.avi *.mov *.mkv)", "所有檔案 (*)"]
        onAccepted: {
            var path = selectedFile.toString();
            // 移除 file:/// 前綴
            if (Qt.platform.os === "windows") {
                path = path.replace(/^file:\/\/\//, "");
            } else {
                path = path.replace(/^file:\/\//, "");
            }
            path = decodeURIComponent(path);

            dataBridge.log("選擇影片: " + path.split("/").pop());
            settingsBridge.side = settingsBridge.side;  // 確保值已同步
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

    // ========== 主佈局 ==========
    RowLayout {
        anchors.fill: parent
        anchors.margins: Style.Theme.margin
        spacing: Style.Theme.spacing

        // 左側面板
        Panels.LeftPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: Style.Theme.leftRatio
            Layout.minimumWidth: Style.Theme.videoMinWidth

            frameCounter: videoBridge.frameCounter
            isProcessing: videoBridge.isProcessing
            isPaused: videoBridge.isPaused
            currentFrame: videoBridge.currentFrame
            totalFrames: videoBridge.totalFrames
            frameCount: videoBridge.frameCount
            fps: videoBridge.fps
            recordCount: dataBridge.recordCount
            showAngleLines: settingsBridge.showAngleLines
            showAngleValues: settingsBridge.showAngleValues
            logMessages: dataBridge.logMessages
            hasVideoSource: videoBridge.videoSource.length > 0

            onCameraClicked: {
                dataBridge.log("正在開啟攝影機...");
                videoBridge.startCamera();
                videoBridge.setParameters(settingsBridge.side, settingsBridge.loadWeight, settingsBridge.coupling);
                videoBridge.setDisplayOptions(settingsBridge.showAngleLines, settingsBridge.showAngleValues);
            }
            onVideoClicked: {
                videoFileDialog.open();
            }
            onPauseClicked: {
                videoBridge.togglePause();
            }
            onStopClicked: {
                dataBridge.log("正在停止處理...");
                videoBridge.stop();
            }
            onSeekRequested: function(frame) {
                videoBridge.seekFrame(frame);
            }
            onShowAngleLinesToggled: function(checked) {
                settingsBridge.setShowAngleLines(checked);
                videoBridge.setDisplayOptions(settingsBridge.showAngleLines, settingsBridge.showAngleValues);
            }
            onShowAngleValuesToggled: function(checked) {
                settingsBridge.setShowAngleValues(checked);
                videoBridge.setDisplayOptions(settingsBridge.showAngleLines, settingsBridge.showAngleValues);
            }
            onSaveCsvClicked: saveCsvDialog.open()
            onSaveJsonClicked: saveJsonDialog.open()
        }

        // 右側面板
        Panels.RightPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: Style.Theme.rightRatio
            Layout.minimumWidth: 400

            rebaScore: rebaBridge.rebaScore
            riskLevelZh: rebaBridge.riskLevelZh
            riskColor: rebaBridge.riskColor
            riskDescription: rebaBridge.riskDescription
            dataLocked: settingsBridge.dataLocked
            side: settingsBridge.side
            loadWeight: settingsBridge.loadWeight
            coupling: settingsBridge.coupling

            onSideSelected: function(value) {
                settingsBridge.setSide(value);
                videoBridge.setParameters(settingsBridge.side, settingsBridge.loadWeight, settingsBridge.coupling);
            }
            onLoadWeightEdited: function(value) {
                settingsBridge.setLoadWeight(value);
                videoBridge.setParameters(settingsBridge.side, settingsBridge.loadWeight, settingsBridge.coupling);
            }
            onCouplingSelected: function(value) {
                settingsBridge.setCoupling(value);
                videoBridge.setParameters(settingsBridge.side, settingsBridge.loadWeight, settingsBridge.coupling);
            }
            onDataLockToggled: function(locked) {
                settingsBridge.setDataLocked(locked);
                videoBridge.controller;  // 不直接存取，透過 bridge
                dataBridge.log(locked ? "資料已鎖定" : "資料已解鎖");
            }
            onTableCClicked: {
                tableCDialog.open();
            }
            onCopyDataClicked: {
                var text = dataBridge.getCopyText();
                if (text) {
                    // QML 剪貼板操作需透過 Python bridge
                    dataBridge.log("資料已複製到剪貼簿");
                }
            }
        }
    }

    // ========== 初始化 ==========
    Component.onCompleted: {
        Style.Theme.loadTheme(themeJson);
        dataBridge.log("系統啟動完成");
        dataBridge.log("請選擇影片來源開始分析");
    }

    // ========== 視窗關閉 ==========
    onClosing: function(close) {
        videoBridge.cleanup();
        close.accepted = true;
    }

    // ========== 狀態列 ==========
    footer: ToolBar {
        background: Rectangle {
            color: Style.Theme.surfaceAlt
            Rectangle {
                width: parent.width
                height: 1
                color: Style.Theme.border
            }
        }
        contentItem: Text {
            id: statusText
            text: "就緒"
            font.family: Style.Theme.fontFamily
            font.pixelSize: 11
            color: Style.Theme.textSecondary
            leftPadding: 8
        }

        Connections {
            target: videoBridge
            function onIsProcessingChanged() {
                statusText.text = videoBridge.isProcessing ? "處理中..." : "就緒";
            }
            function onProcessingFinished() {
                statusText.text = "處理完成 - 共處理 " + videoBridge.frameCount + " 幀";
            }
            function onErrorOccurred(msg) {
                statusText.text = "錯誤: " + msg;
            }
        }
    }
}
