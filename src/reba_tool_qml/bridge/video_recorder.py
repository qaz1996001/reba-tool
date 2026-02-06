#!/usr/bin/env python3
"""
影片錄製器 (Video Recorder)
使用 cv2.VideoWriter 將標註幀寫入 MP4 檔案。
支援延遲建立（第一幀到達時根據實際尺寸建立 VideoWriter）。
"""

import os
import cv2
import numpy as np


class VideoRecorder:
    """cv2.VideoWriter 包裝器，支援延遲建立"""

    def __init__(self):
        self._writer = None
        self._output_path = ""
        self._fps = 30.0
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self, output_path: str, fps: float = 30.0):
        """開始錄影。VideoWriter 延遲到第一幀到達時建立（取得實際尺寸）"""
        if self._recording:
            self.stop()

        # 確保輸出目錄存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        self._output_path = output_path
        self._fps = fps if fps > 0 else 30.0
        self._recording = True
        self._writer = None  # 延遲建立

    def write_frame(self, frame: np.ndarray):
        """寫入一幀。若 VideoWriter 尚未建立則根據幀尺寸建立"""
        if not self._recording:
            return

        if self._writer is None:
            h, w = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self._writer = cv2.VideoWriter(
                self._output_path, fourcc, self._fps, (w, h)
            )
            if not self._writer.isOpened():
                self._recording = False
                self._writer = None
                return

        # 確保是 BGR 格式（cv2.VideoWriter 預期 BGR）
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        self._writer.write(frame)

    def stop(self) -> str:
        """停止錄影，釋放 VideoWriter，返回檔案路徑"""
        path = self._output_path
        self._recording = False
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        return path
