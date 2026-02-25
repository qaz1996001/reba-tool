#!/usr/bin/env python3
"""
輸出錄製器 (Video Recorder)
將標註幀寫入輸出目錄，包含 MP4 影片、每幀 JPG 圖片、CSV 資料。
所有磁碟 I/O 在背景線程執行，避免阻塞主線程 (GUI thread)。

輸出目錄結構：
  {output_dir}/
    ├── video.mp4
    ├── image/
    │   ├── frame_000001.jpg
    │   ├── frame_000002.jpg
    │   └── ...
    └── reba_data.csv
"""

import csv
import os
import threading
from datetime import datetime
from queue import Queue

import cv2
import numpy as np

_SENTINEL = None  # 停止信號

# CSV 欄位定義
_CSV_FIELDS = [
    'frame_id', 'timestamp', 'datetime',
    'neck_angle', 'trunk_angle', 'upper_arm_angle',
    'forearm_angle', 'wrist_angle', 'leg_angle',
    'reba_score', 'risk_level',
]


class VideoRecorder:
    """輸出目錄管理器，背景線程寫入 MP4 + JPG + CSV"""

    def __init__(self):
        self._writer = None
        self._output_dir = ""
        self._video_path = ""
        self._image_dir = ""
        self._csv_path = ""
        self._fps = 30.0
        self._recording = False
        self._frame_id = 0
        self._queue: Queue = Queue(maxsize=120)
        self._thread: threading.Thread | None = None
        self._csv_file = None
        self._csv_writer = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def output_dir(self) -> str:
        return self._output_dir

    def start(self, output_dir: str, fps: float = 30.0):
        """
        開始錄製到指定目錄。

        Args:
            output_dir: 輸出目錄路徑（完整路徑）
            fps: 影片 FPS
        """
        if self._recording:
            self.stop()

        self._output_dir = output_dir
        self._video_path = os.path.join(output_dir, "video.mp4")
        self._image_dir = os.path.join(output_dir, "image")
        self._csv_path = os.path.join(output_dir, "reba_data.csv")
        self._fps = fps if fps > 0 else 30.0
        self._frame_id = 0
        self._recording = True
        self._writer = None  # 延遲建立

        # 建立目錄結構
        os.makedirs(self._image_dir, exist_ok=True)

        # 開啟 CSV 串流寫入
        self._csv_file = open(self._csv_path, 'w', newline='', encoding='utf-8-sig')
        self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=_CSV_FIELDS)
        self._csv_writer.writeheader()

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

    def write_frame(self, frame: np.ndarray, frame_data: dict = None):
        """
        將幀送入佇列（非阻塞），由背景線程寫入磁碟。

        Args:
            frame: OpenCV BGR 影像
            frame_data: 該幀的分析資料 dict，包含 angles, reba_score, risk_level 等
        """
        if not self._recording:
            return
        self._frame_id += 1
        item = {
            'frame': frame.copy(),
            'frame_id': self._frame_id,
            'frame_data': frame_data,
        }
        # 佇列滿時丟棄最舊的項目，避免阻塞主線程
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except Exception:
                pass
        self._queue.put(item)

    def stop(self) -> str:
        """停止錄製，等待背景線程完成，釋放資源，返回輸出目錄路徑"""
        out_dir = self._output_dir
        self._recording = False

        # 送入停止信號並等待線程結束
        if self._thread is not None and self._thread.is_alive():
            self._queue.put(_SENTINEL)
            self._thread.join(timeout=30)
        self._thread = None

        if self._writer is not None:
            self._writer.release()
            self._writer = None

        if self._csv_file is not None:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None

        return out_dir

    # ========== 背景線程 ==========

    def _write_loop(self):
        """背景線程：持續從佇列取項目並寫入 MP4 + JPG + CSV"""
        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                break

            frame = item['frame']
            frame_id = item['frame_id']
            frame_data = item.get('frame_data')

            # 確保是 BGR 格式
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            # 1. 寫入 MP4
            if self._writer is None:
                h, w = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self._writer = cv2.VideoWriter(
                    self._video_path, fourcc, self._fps, (w, h)
                )
                if not self._writer.isOpened():
                    self._recording = False
                    self._writer = None
                    break
            self._writer.write(frame)

            # 2. 寫入 JPG 圖片
            img_filename = f"frame_{frame_id:06d}.jpg"
            img_path = os.path.join(self._image_dir, img_filename)
            cv2.imwrite(img_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # 3. 寫入 CSV 行
            if frame_data and self._csv_writer:
                import time
                ts = frame_data.get('timestamp', time.time())
                angles = frame_data.get('angles', {})
                row = {
                    'frame_id': frame_id,
                    'timestamp': f"{ts:.3f}",
                    'datetime': datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'neck_angle': self._fmt_angle(angles.get('neck')),
                    'trunk_angle': self._fmt_angle(angles.get('trunk')),
                    'upper_arm_angle': self._fmt_angle(angles.get('upper_arm')),
                    'forearm_angle': self._fmt_angle(angles.get('forearm')),
                    'wrist_angle': self._fmt_angle(angles.get('wrist')),
                    'leg_angle': self._fmt_angle(angles.get('leg')),
                    'reba_score': frame_data.get('reba_score', ''),
                    'risk_level': frame_data.get('risk_level', ''),
                }
                try:
                    self._csv_writer.writerow(row)
                    self._csv_file.flush()
                except Exception:
                    pass

    @staticmethod
    def _fmt_angle(val):
        """格式化角度值"""
        return f"{val:.1f}" if val is not None else ""
