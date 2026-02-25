#!/usr/bin/env python3
"""
處理/渲染配置 (Processing & Rendering Configuration)
從 UIConfig 拆出所有非 Qt 參數，零 Qt 依賴。
"""

from pathlib import Path


class ProcessingConfig:
    """處理與渲染參數集中管理（框架無關）"""

    # ========== 影片擷取設定 ==========
    VIDEO_CAPTURE_WIDTH = 1280
    VIDEO_CAPTURE_HEIGHT = 720

    # ========== MediaPipe 設定 ==========
    MEDIAPIPE_MODEL_COMPLEXITY = 0  # 0=Lite, 1=Full, 2=Heavy
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_TRACKING_CONFIDENCE = 0.5

    # ========== 效能優化設定 ==========
    PROCESS_EVERY_N_FRAMES = 1  # 1=不跳幀
    USE_GPU_BACKEND = False
    PROCESS_LOOP_DELAY_MS = 0  # 0=最快

    # ========== 繪圖參數 ==========
    ANGLE_LINE_THICKNESS = 3

    # 角度線顏色 (BGR)
    COLOR_NECK = (0, 0, 255)        # 紅色
    COLOR_TRUNK = (0, 165, 255)     # 橙色
    COLOR_UPPER_ARM = (0, 255, 255) # 黃色
    COLOR_FOREARM = (255, 255, 0)    # 青色 (Cyan)
    COLOR_WRIST = (0, 255, 0)       # 綠色
    COLOR_LEG = (255, 0, 0)         # 藍色

    # 文字背景設定
    TEXT_BG_PADDING = 5
    TEXT_BG_ALPHA = 153  # 0-255

    # ========== 風險等級顏色 (BGR) ==========
    RISK_COLORS = {
        'negligible': (0, 255, 0),      # 綠色
        'low': (144, 238, 144),          # 淡綠色
        'medium': (0, 255, 255),         # 黃色
        'high': (0, 165, 255),           # 橙色
        'very_high': (0, 0, 255)         # 紅色
    }

    # ========== 影片覆蓋層文字位置 ==========
    OVERLAY_REBA_SCORE_X = 10
    OVERLAY_REBA_SCORE_Y = 10
    OVERLAY_RISK_LEVEL_X = 10
    OVERLAY_RISK_LEVEL_Y = 60

    # ========== PIL 字體設定 ==========
    OVERLAY_FONT_SIZE = 48
    OVERLAY_FONT_SIZE_SMALL = 48

    # ========== FPS 顯示 (OpenCV) ==========
    FPS_FONT_SCALE = 0.6
    FPS_FONT_THICKNESS = 2

    # ========== 字體路徑 ==========
    FONT_PATH = str(Path(__file__).parent / "Arial.Unicode.ttf")
