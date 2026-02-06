#!/usr/bin/env python3
"""
MediaPipe REBA 分析系統 - 入口點
"""

import sys
import os

# 確保 src/reba_tool/ 在 Python 路徑中（支援 ui/ 子目錄 import 上層模組）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
