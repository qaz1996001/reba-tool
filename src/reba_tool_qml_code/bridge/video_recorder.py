#!/usr/bin/env python3
"""
影片錄製器 (Video Recorder)
使用 cv2.VideoWriter 將標註幀寫入 MP4 檔案。
寫入操作在背景線程執行，避免阻塞主線程 (GUI thread)。
"""

import os
import threading
from queue import Queue

import cv2
import numpy as np

_SENTINEL = None  # 停止信號


class VideoRecorder:
    """cv2.VideoWriter 包裝器，背景線程寫入避免 UI 卡頓"""

    def __init__(self):
        self._writer = None
        self._output_path = ""
        self._fps = 30.0
        self._recording = False
        self._queue: Queue = Queue(maxsize=120)
        self._thread: threading.Thread | None = None

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

        # 清空佇列後啟動寫入線程
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Exception:
                break
        self._thread = threading.Thread(
            target=self._write_loop, daemon=True
        )
        self._thread.start()

    def write_frame(self, frame: np.ndarray):
        """將幀送入佇列（非阻塞），由背景線程寫入磁碟"""
        if not self._recording:
            return
        # 佇列滿時丟棄最舊的幀，避免阻塞主線程
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except Exception:
                pass
        self._queue.put(frame)

    def stop(self) -> str:
        """停止錄影，等待背景線程完成，釋放 VideoWriter，返回檔案路徑"""
        path = self._output_path
        self._recording = False

        # 送入停止信號並等待線程結束
        if self._thread is not None and self._thread.is_alive():
            self._queue.put(_SENTINEL)
            self._thread.join(timeout=10)
        self._thread = None

        if self._writer is not None:
            self._writer.release()
            self._writer = None
        return path

    # ========== 背景線程 ==========

    def _write_loop(self):
        """背景線程：持續從佇列取幀並寫入 VideoWriter"""
        while True:
            frame = self._queue.get()
            if frame is _SENTINEL:
                break

            # 延遲建立 VideoWriter（取得第一幀的實際尺寸）
            if self._writer is None:
                h, w = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self._writer = cv2.VideoWriter(
                    self._output_path, fourcc, self._fps, (w, h)
                )
                if not self._writer.isOpened():
                    self._recording = False
                    self._writer = None
                    break

            # 確保是 BGR 格式（cv2.VideoWriter 預期 BGR）
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            self._writer.write(frame)
