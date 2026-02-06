#!/usr/bin/env python3
"""
影像提供者 (Video Image Provider)
將 OpenCV BGR numpy frame 轉為 QML Image 可用的 QImage。
QML 端用 Image { source: "image://video/frame?" + frameCounter; cache: false }
"""

import threading
import numpy as np
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class VideoImageProvider(QQuickImageProvider):
    """QQuickImageProvider - OpenCV frame → QML Image"""

    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self._image = QImage()
        self._lock = threading.Lock()

    def update_frame(self, cv_frame: np.ndarray):
        """
        更新當前影像幀（由 VideoBridge 在主線程呼叫）

        Args:
            cv_frame: OpenCV BGR numpy 陣列
        """
        if cv_frame is None or cv_frame.size == 0:
            return

        # BGR → RGB
        import cv2
        rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        with self._lock:
            self._image = QImage(
                rgb_frame.data.tobytes(),
                w, h, bytes_per_line,
                QImage.Format_RGB888
            )

    def requestImage(self, id_str, size, requested_size):
        """
        QML 請求影像時呼叫

        Args:
            id_str: 影像 ID（忽略，只有一個影像源）
            size: 回傳實際尺寸（PySide6 不使用）
            requested_size: 請求尺寸

        Returns:
            QImage
        """
        with self._lock:
            if self._image.isNull():
                # 回傳空白影像
                img = QImage(640, 480, QImage.Format_RGB888)
                img.fill(0)
                return img

            img = self._image.copy()

        if (requested_size.isValid()
                and requested_size.width() > 0
                and requested_size.height() > 0):
            img = img.scaled(
                requested_size,
                mode=1  # Qt.KeepAspectRatio
            )

        return img
