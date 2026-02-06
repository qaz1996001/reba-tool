#!/usr/bin/env python3
"""
影片橋接 (Video Bridge)
包裝 VideoController，暴露控制 Slot 和狀態 Property 給 QML。
收到 VideoWorker.frame_ready → 更新 image_provider → 遞增 frameCounter。
"""

import os
from datetime import datetime

from PySide6.QtCore import QObject, Property, Signal, Slot

from video_controller import VideoController
from ui.video_worker import VideoWorker
from bridge.video_recorder import VideoRecorder


class VideoBridge(QObject):
    """QML↔VideoController 橋接"""

    # 狀態變更通知
    isProcessingChanged = Signal()
    isPausedChanged = Signal()
    fpsChanged = Signal()
    frameCountChanged = Signal()
    frameCounterChanged = Signal()
    totalFramesChanged = Signal()
    currentFrameChanged = Signal()
    videoSourceChanged = Signal()

    # 幀處理完成（帶完整資料，供 RebaBridge 使用）
    frameProcessed = Signal(object, dict, int, str, float, dict)

    # 處理結束
    processingFinished = Signal()
    errorOccurred = Signal(str)
    imageSaved = Signal(str)

    # 錄影狀態
    isRecordingChanged = Signal()
    recordingStarted = Signal()
    recordingStopped = Signal(str)

    def __init__(self, image_provider, parent=None):
        super().__init__(parent)
        self._image_provider = image_provider
        self._controller = VideoController()
        self._worker = None

        self._fps = 0.0
        self._frame_counter = 0
        self._total_frames = 0
        self._current_frame = 0
        self._video_source = ""
        self._recorder = VideoRecorder()
        self._auto_recording = False  # 全程自動錄影旗標

    # ========== Properties ==========

    @Property(bool, notify=isProcessingChanged)
    def isProcessing(self):
        return self._controller.is_processing

    @Property(bool, notify=isPausedChanged)
    def isPaused(self):
        pipeline = self._controller.pipeline
        return pipeline.paused if pipeline else False

    @Property(float, notify=fpsChanged)
    def fps(self):
        return self._fps

    @Property(int, notify=frameCountChanged)
    def frameCount(self):
        return self._controller.frame_count

    @Property(int, notify=frameCounterChanged)
    def frameCounter(self):
        """每幀遞增，QML Image 綁定此值觸發重繪"""
        return self._frame_counter

    @Property(int, notify=totalFramesChanged)
    def totalFrames(self):
        return self._total_frames

    @Property(int, notify=currentFrameChanged)
    def currentFrame(self):
        return self._current_frame

    @Property(str, notify=videoSourceChanged)
    def videoSource(self):
        return self._video_source

    @Property(bool, notify=isRecordingChanged)
    def isRecording(self):
        return self._recorder.is_recording

    # ========== 暴露 controller 給其他 bridge ==========

    @property
    def controller(self):
        return self._controller

    # ========== Slots ==========

    @Slot()
    def startCamera(self):
        """開啟攝影機"""
        if self._controller.is_processing:
            return
        self._video_source = ""
        self.videoSourceChanged.emit()
        self._start_processing(None)

    @Slot(str)
    def startVideo(self, path):
        """開啟影片檔"""
        if self._controller.is_processing:
            return
        self._video_source = path
        self.videoSourceChanged.emit()
        self._start_processing(path)

    @Slot()
    def pause(self):
        """暫停"""
        if self._controller.pipeline and not self._controller.pipeline.paused:
            self._controller.pause()
            self.isPausedChanged.emit()

    @Slot()
    def resume(self):
        """恢復"""
        if self._controller.pipeline and self._controller.pipeline.paused:
            self._controller.resume()
            self.isPausedChanged.emit()

    @Slot()
    def togglePause(self):
        """切換暫停/恢復"""
        if self._controller.pipeline:
            if self._controller.pipeline.paused:
                self.resume()
            else:
                self.pause()

    @Slot()
    def stop(self):
        """停止處理"""
        if self._worker:
            self._controller.stop()
            self._worker.wait()
            self._worker.cleanup()
            self._worker = None
        self._on_finished()

    @Slot(int)
    def seekFrame(self, frame_number):
        """跳轉到指定幀"""
        self._controller.seek(frame_number)

    @Slot(str, float, str)
    def setParameters(self, side, load_weight, force_coupling):
        """即時更新評估參數"""
        self._controller.set_parameters(side, load_weight, force_coupling)

    @Slot(bool, bool)
    def setDisplayOptions(self, show_lines, show_values):
        """即時更新顯示選項"""
        self._controller.set_display_options(show_lines, show_values)

    @Slot(str)
    def saveImage(self, path):
        """保存當前標註影像"""
        img = self._image_provider.get_current_image()
        if img is None or img.isNull():
            self.errorOccurred.emit("無可保存的影像")
            return
        if img.save(path):
            self.imageSaved.emit(path)
        else:
            self.errorOccurred.emit("影像保存失敗: " + path)

    @Slot(str, result=str)
    def suggestFilePath(self, file_type):
        """根據類型生成建議檔案路徑"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(os.getcwd(), "results")
        os.makedirs(results_dir, exist_ok=True)

        names = {
            "image": f"reba_frame_{timestamp}.png",
            "video": f"reba_video_{timestamp}.mp4",
            "csv": f"reba_analysis_{timestamp}.csv",
            "json": f"reba_stats_{timestamp}.json",
        }
        filename = names.get(file_type, f"reba_{timestamp}.dat")
        return os.path.join(results_dir, filename).replace("\\", "/")

    @Slot()
    def startRecording(self):
        """手動開始錄影片段"""
        if self._recorder.is_recording:
            return
        path = self.suggestFilePath("video")
        fps = self._fps if self._fps > 0 else 30.0
        self._recorder.start(path, fps)
        self._auto_recording = False
        self.isRecordingChanged.emit()
        self.recordingStarted.emit()

    @Slot()
    def stopRecording(self):
        """手動停止錄影"""
        if not self._recorder.is_recording:
            return
        path = self._recorder.stop()
        self._auto_recording = False
        self.isRecordingChanged.emit()
        self.recordingStopped.emit(path)

    # ========== 內部方法 ==========

    def _start_processing(self, video_source,
                          side='right', load_weight=0.0,
                          force_coupling='good',
                          show_lines=True, show_values=True):
        """啟動處理管線"""
        self._controller.start(
            video_source, side, load_weight, force_coupling,
            show_lines, show_values
        )

        self._frame_counter = 0
        self.frameCounterChanged.emit()
        self.isProcessingChanged.emit()

        # 自動開始全程錄影
        auto_path = self.suggestFilePath("video")
        self._recorder.start(auto_path, 30.0)
        self._auto_recording = True
        self.isRecordingChanged.emit()
        self.recordingStarted.emit()

        # 建立 QThread worker（直接複用 reba_tool 的 VideoWorker）
        self._worker = VideoWorker(
            self._controller.pipeline,
            self._controller.event_bus
        )
        self._worker.frame_ready.connect(self._handle_frame)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error_signal.connect(self._on_error)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.start()

    def _handle_frame(self, frame, angles, reba_score, risk_level, fps, details):
        """收到工作線程的幀資料"""
        # 記錄資料
        self._controller.record_frame(frame, angles, reba_score, risk_level, fps, details)

        # 錄影：寫入標註幀
        if self._recorder.is_recording:
            self._recorder.write_frame(frame)

        # 更新影像提供者
        self._image_provider.update_frame(frame)

        # 更新屬性
        self._fps = fps
        self.fpsChanged.emit()
        self.frameCountChanged.emit()

        # 遞增 frameCounter 觸發 QML Image 重繪
        self._frame_counter += 1
        self.frameCounterChanged.emit()

        # 發射幀處理完成信號（供 RebaBridge 等使用）
        self.frameProcessed.emit(frame, angles, reba_score, risk_level, fps, details)

    def _on_finished(self):
        """處理完成"""
        # 自動停止錄影（全程模式）
        if self._recorder.is_recording and self._auto_recording:
            path = self._recorder.stop()
            self._auto_recording = False
            self.isRecordingChanged.emit()
            self.recordingStopped.emit(path)

        self._controller.on_processing_finished()
        self.isProcessingChanged.emit()
        self.isPausedChanged.emit()
        self.processingFinished.emit()

    def _on_error(self, message):
        """錯誤處理"""
        self.errorOccurred.emit(message)
        self._on_finished()

    def _on_progress(self, current_frame, total_frames):
        """進度更新"""
        self._current_frame = current_frame
        self._total_frames = total_frames
        self.currentFrameChanged.emit()
        self.totalFramesChanged.emit()

    def start_with_params(self, video_source, side, load_weight, force_coupling,
                          show_lines, show_values):
        """帶完整參數啟動（由 main.py 或 QML 呼叫）"""
        if self._controller.is_processing:
            return
        self._video_source = video_source or ""
        self.videoSourceChanged.emit()
        self._start_processing(
            video_source, side, load_weight, force_coupling,
            show_lines, show_values
        )

    def cleanup(self):
        """清理資源（視窗關閉時呼叫）"""
        if self._recorder.is_recording:
            self._recorder.stop()
        if self._worker and self._worker.isRunning():
            self._controller.stop()
            self._worker.wait()
            self._worker.cleanup()
            self._worker = None
