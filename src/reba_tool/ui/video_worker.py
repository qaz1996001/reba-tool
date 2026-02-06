#!/usr/bin/env python3
"""
QThread 橋接 (Video Worker)
唯一的線程相關 Qt 程式碼。
將 EventBus callback 轉為 Qt Signal（自動跨線程到主線程）。
"""

from PySide6.QtCore import QThread, Signal

from event_bus import EventBus
from video_pipeline import VideoPipeline


class VideoWorker(QThread):
    """QThread 薄包裝 - 在 worker thread 中執行 VideoPipeline"""

    # Qt Signals（自動跨線程 queue 到主線程）
    frame_ready = Signal(object, dict, int, str, float, dict)
    finished_signal = Signal()
    error_signal = Signal(str)
    progress_signal = Signal(int, int)

    def __init__(self, pipeline: VideoPipeline, event_bus: EventBus):
        super().__init__()
        self._pipeline = pipeline
        self._event_bus = event_bus

        # 註冊 EventBus 回調 → 轉為 Qt Signal
        self._event_bus.on('frame_processed', self._on_frame_processed)
        self._event_bus.on('processing_finished', self._on_finished)
        self._event_bus.on('error_occurred', self._on_error)
        self._event_bus.on('progress_updated', self._on_progress)

    def run(self):
        """在 QThread 中執行管線"""
        self._pipeline.run()

    def cleanup(self):
        """清理 EventBus 回調"""
        self._event_bus.off('frame_processed', self._on_frame_processed)
        self._event_bus.off('processing_finished', self._on_finished)
        self._event_bus.off('error_occurred', self._on_error)
        self._event_bus.off('progress_updated', self._on_progress)

    # ========== EventBus → Qt Signal 橋接 ==========

    def _on_frame_processed(self, frame, angles, reba_score, risk_level, fps, details):
        self.frame_ready.emit(frame, angles, reba_score, risk_level, fps, details)

    def _on_finished(self):
        self.finished_signal.emit()

    def _on_error(self, message):
        self.error_signal.emit(message)

    def _on_progress(self, current_frame, total_frames):
        self.progress_signal.emit(current_frame, total_frames)
