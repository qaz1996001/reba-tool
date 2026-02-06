#!/usr/bin/env python3
"""
MediaPipe REBA 分析系統 - PySide6 GUI
基於MediaPipe Holistic進行姿態檢測並計算REBA分數

功能:
1. 即時攝影機分析
2. 影片檔案分析
3. 角度計算與顯示
4. REBA評分與風險評估
5. 結果保存（CSV/JSON）

使用方法:
python main_reba_gui.py
"""

import sys
import cv2
import numpy as np
import mediapipe as mp
from datetime import datetime
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFileDialog,
                               QGroupBox, QGridLayout, QTextEdit, QProgressBar,
                               QComboBox, QSpinBox, QDoubleSpinBox, QSlider, QCheckBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                               QDialog)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont, QColor

# 導入自定義模組
from angle_calculator import AngleCalculator
from reba_scorer import REBAScorer
from data_logger import DataLogger


class TableCDialog(QDialog):
    """Table C 對話框 - 顯示 REBA Score A 與 Score B 的對照表"""

    # REBA Table C 資料 (12x12)
    TABLE_C_DATA = [
        [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],
        [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],
        [2, 3, 3, 4, 5, 5, 6, 7, 7, 8, 8, 9],
        [3, 4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9],
        [4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9, 9],
        [6, 6, 6, 7, 8, 8, 9, 9, 10, 10, 10, 10],
        [7, 7, 7, 8, 9, 9, 9, 10, 10, 11, 11, 11],
        [8, 8, 8, 9, 10, 10, 10, 10, 10, 11, 11, 11],
        [9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12],
        [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],
        [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],
        [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12],
    ]

    def __init__(self, parent=None, score_a=None, score_b=None):
        super().__init__(parent)
        self.score_a = score_a
        self.score_b = score_b
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("REBA Table C - Score A × Score B → Score C")
        self.setMinimumSize(600, 450)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 標題說明
        title_label = QLabel("Table C: 由 Score A (列) 與 Score B (欄) 查詢 Score C")
        title_label.setFont(QFont("Microsoft JhengHei", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 建立表格 (13行 x 13列，包含標題)
        self.table = QTableWidget(13, 13)
        self.table.setFont(QFont("Microsoft JhengHei", 10))
        layout.addWidget(self.table)

        # 設定標題
        self.table.setHorizontalHeaderLabels(
            ['Score B →'] + [str(i) for i in range(1, 13)])
        self.table.setVerticalHeaderLabels(
            ['Score A ↓'] + [str(i) for i in range(1, 13)])

        # 填入第一行（Score B 標題）
        for col in range(13):
            if col == 0:
                item = QTableWidgetItem("Score A \\ B")
            else:
                item = QTableWidgetItem(str(col))
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor('#d0d0d0'))
            item.setFont(QFont("Microsoft JhengHei", 10, QFont.Bold))
            self.table.setItem(0, col, item)

        # 填入第一欄（Score A 標題）和資料
        for row in range(1, 13):
            # Score A 標題欄
            header_item = QTableWidgetItem(str(row))
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setBackground(QColor('#d0d0d0'))
            header_item.setFont(QFont("Microsoft JhengHei", 10, QFont.Bold))
            self.table.setItem(row, 0, header_item)

            # 資料欄
            for col in range(1, 13):
                value = self.TABLE_C_DATA[row - 1][col - 1]
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)

                # 根據分數設定背景色
                color = self._get_score_color(value)
                item.setBackground(QColor(color))

                self.table.setItem(row, col, item)

        # 強調當前 Score A / Score B 對應的儲存格
        if self.score_a is not None and self.score_b is not None:
            self._highlight_current_score()

        # 設定欄寬
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 隱藏原始標題
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)

        # 圖例
        legend_layout = QHBoxLayout()
        layout.addLayout(legend_layout)
        legend_label = QLabel("圖例:")
        legend_label.setFont(QFont("Microsoft JhengHei", 10))
        legend_layout.addWidget(legend_label)

        legend_items = [
            ("#78c850", "1 可忽略"),
            ("#a8d08d", "2-3 低風險"),
            ("#ffeb3b", "4-7 中風險"),
            ("#ff9800", "8-10 高風險"),
            ("#f44336", "11-12 極高風險"),
        ]
        for color, text in legend_items:
            lbl = QLabel(f"  ■ {text}")
            lbl.setFont(QFont("Microsoft JhengHei", 9))
            lbl.setStyleSheet(f"color: {color};")
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()

        # 關閉按鈕
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def _get_score_color(self, score):
        """根據分數取得對應顏色"""
        if score == 1:
            return "#78c850"  # 綠色 - 可忽略
        elif score <= 3:
            return "#a8d08d"  # 淺綠 - 低風險
        elif score <= 7:
            return "#ffeb3b"  # 黃色 - 中風險
        elif score <= 10:
            return "#ff9800"  # 橙色 - 高風險
        else:
            return "#f44336"  # 紅色 - 極高風險

    def _highlight_current_score(self):
        """強調當前 Score A / Score B 對應的儲存格，使用較淺背景色網底"""
        if self.score_a is None or self.score_b is None:
            return

        # 確保範圍有效
        score_a = max(1, min(12, self.score_a))
        score_b = max(1, min(12, self.score_b))

        # 淺色網底顏色 (淺藍色)
        light_highlight = QColor('#b3d9ff')  # 較淺的藍色網底
        header_highlight = QColor('#4a90d9')  # 標題欄的深藍色

        # 強調整行（Score A 對應的那一列）- 使用淺色網底
        for col in range(13):
            item = self.table.item(score_a, col)
            if item:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                if col == 0:
                    # 標題欄使用深藍色
                    item.setBackground(header_highlight)
                    item.setForeground(QColor('white'))
                else:
                    # 資料欄使用淺色網底覆蓋
                    item.setBackground(light_highlight)

        # 強調整欄（Score B 對應的那一行）- 使用淺色網底
        for row in range(13):
            item = self.table.item(row, score_b)
            if item:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                if row == 0:
                    # 標題欄使用深藍色
                    item.setBackground(header_highlight)
                    item.setForeground(QColor('white'))
                elif row != score_a:  # 避免覆蓋交叉點
                    # 資料欄使用淺色網底覆蓋
                    item.setBackground(light_highlight)

        # 交叉點強調（Score A 與 Score B 的交會處）- 使用深色標記
        target_item = self.table.item(score_a, score_b)
        if target_item:
            target_item.setBackground(QColor('#1565c0'))  # 深藍色
            target_item.setForeground(QColor('white'))
            font = target_item.font()
            font.setBold(True)
            font.setPointSize(14)
            target_item.setFont(font)

    def update_scores(self, score_a, score_b):
        """更新分數並重新強調"""
        self.score_a = score_a
        self.score_b = score_b

        # 重設所有儲存格樣式
        for row in range(13):
            for col in range(13):
                item = self.table.item(row, col)
                if item:
                    font = item.font()
                    font.setBold(False)
                    font.setPointSize(10)
                    item.setFont(font)
                    item.setForeground(QColor('black'))

                    if row == 0 or col == 0:
                        item.setBackground(QColor('#d0d0d0'))
                        font.setBold(True)
                        item.setFont(font)
                    elif row > 0 and col > 0:
                        value = self.TABLE_C_DATA[row - 1][col - 1]
                        item.setBackground(
                            QColor(self._get_score_color(value)))

        # 重新強調
        self._highlight_current_score()


class UIConfig:
    """UI 配置類別 - 所有 UI 參數集中管理"""

    # ========== 視窗設定 ==========
    WINDOW_X = 100
    WINDOW_Y = 100
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900

    # ========== 影片顯示區設定 ==========
    VIDEO_LABEL_MIN_WIDTH = 600
    VIDEO_LABEL_MIN_HEIGHT = 450
    VIDEO_LABEL_BORDER_STYLE = "border: 2px solid black; background-color: #2b2b2b;"

    # ========== 影片處理設定 ==========
    VIDEO_CAPTURE_WIDTH = 1280
    VIDEO_CAPTURE_HEIGHT = 720

    # ========== 效能優化設定 ==========
    # MediaPipe 模型複雜度: 0=Lite(最快), 1=Full(中等), 2=Heavy(最精確)
    MEDIAPIPE_MODEL_COMPLEXITY = 0  # 降低可提升 FPS

    # 跳幀處理: 每 N 幀才進行一次完整的姿態分析 (1=不跳幀, 2=處理一半幀數)
    PROCESS_EVERY_N_FRAMES = 1

    # 是否啟用 GPU 加速 (需要支援 CUDA 的顯卡)
    USE_GPU_BACKEND = False

    # 處理循環延遲 (毫秒)，0=最快但 CPU 使用率最高
    PROCESS_LOOP_DELAY_MS = 0

    # ========== 字體設定 ==========
    # Qt 字體設定 - 通用
    FONT_FAMILY = "Microsoft YaHei"

    # 影片覆蓋層中文字體（PIL）
    OVERLAY_FONT_SIZE = 48
    OVERLAY_FONT_SIZE_SMALL = 48

    # --- 按鈕字體 ---
    BUTTON_FONT_SIZE = 18
    BUTTON_FONT_BOLD = False

    # --- 群組框標題字體 ---
    GROUPBOX_FONT_SIZE = 18
    GROUPBOX_FONT_BOLD = True

    # --- 下拉框字體 ---
    COMBOBOX_FONT_SIZE = 16
    COMBOBOX_FONT_BOLD = False

    # --- 複選框字體 ---
    CHECKBOX_FONT_SIZE = 16
    CHECKBOX_FONT_BOLD = False

    # --- 參數標籤字體 ---
    PARAM_LABEL_FONT_SIZE = 16
    PARAM_LABEL_FONT_BOLD = False

    # --- 角度標籤字體 ---
    ANGLE_LABEL_FONT_SIZE = 24
    ANGLE_LABEL_FONT_BOLD = True

    # --- REBA 分數字體 ---
    REBA_SCORE_FONT_SIZE = 28
    REBA_SCORE_FONT_BOLD = True

    # --- 風險等級字體 ---
    RISK_LEVEL_FONT_SIZE = 24
    RISK_LEVEL_FONT_BOLD = False

    # --- 風險描述字體 ---
    RISK_DESC_FONT_SIZE = 12
    RISK_DESC_FONT_BOLD = False

    # --- REBA 公式顯示字體 ---
    FORMULA_HEADER_FONT_SIZE = 14
    FORMULA_HEADER_FONT_BOLD = True
    FORMULA_DETAIL_FONT_SIZE = 11
    FORMULA_DETAIL_FONT_BOLD = False
    FORMULA_TOTAL_FONT_SIZE = 18
    FORMULA_TOTAL_FONT_BOLD = True

    # --- 表格設定 ---
    TABLE_ROW_HEIGHT = 28  # 表格每行高度
    TABLE_HEADER_HEIGHT = 32  # 表格標題高度
    # 欄位寬度比例: [部位, 角度, 分隔, 部位, 分數]（自動依比例分配寬度）
    TABLE_COLUMN_RATIOS = [3, 2, 1, 3, 2]

    # --- 統計資訊字體 ---
    STATS_FONT_SIZE = 24
    STATS_FONT_BOLD = True

    # --- 時間標籤字體 ---
    TIME_LABEL_FONT_SIZE = 12
    TIME_LABEL_FONT_BOLD = False

    # --- 影片提示文字字體 ---
    VIDEO_HINT_FONT_SIZE = 16
    VIDEO_HINT_FONT_BOLD = False

    # --- 日誌框字體 ---
    LOG_TEXT_FONT_SIZE = 10
    LOG_TEXT_FONT_BOLD = False

    # FPS 顯示字體（OpenCV）
    FPS_FONT_SCALE = 0.6
    FPS_FONT_THICKNESS = 2

    # ========== 繪圖參數 ==========
    # 角度線粗細
    ANGLE_LINE_THICKNESS = 3

    # 角度線顏色 (BGR)
    COLOR_NECK = (0, 0, 255)        # 紅色
    COLOR_TRUNK = (0, 165, 255)     # 橙色
    COLOR_UPPER_ARM = (0, 255, 255)  # 黃色
    COLOR_WRIST = (0, 255, 0)       # 綠色
    COLOR_LEG = (255, 0, 0)         # 藍色

    # 文字背景設定
    TEXT_BG_PADDING = 5
    TEXT_BG_ALPHA = 153  # 0-255，透明度

    # ========== 元件尺寸 ==========
    LOG_TEXT_MAX_HEIGHT = 150

    # ========== 進度條拖曳設定 ==========
    # 拖曳時預覽的節流間隔（毫秒），值越大越省效能但反應較慢
    SLIDER_DRAG_THROTTLE_MS = 150

    # ========== 風險等級顏色 (BGR) ==========
    RISK_COLORS = {
        'negligible': (0, 255, 0),      # 綠色
        'low': (144, 238, 144),          # 淡綠色
        'medium': (0, 255, 255),         # 黃色
        'high': (0, 165, 255),           # 橙色
        'very_high': (0, 0, 255)         # 紅色
    }

    # ========== 影片覆蓋層文字位置 ==========
    # REBA 分數位置 (x, y)
    OVERLAY_REBA_SCORE_X = 10
    OVERLAY_REBA_SCORE_Y = 10

    # 風險等級位置 (x, y)
    OVERLAY_RISK_LEVEL_X = 10
    OVERLAY_RISK_LEVEL_Y = 60

    # ========== 字體取得方法 ==========
    @classmethod
    def get_button_font(cls) -> QFont:
        """取得按鈕字體"""
        weight = QFont.Bold if cls.BUTTON_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.BUTTON_FONT_SIZE, weight)

    @classmethod
    def get_groupbox_font(cls) -> QFont:
        """取得群組框標題字體"""
        weight = QFont.Bold if cls.GROUPBOX_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.GROUPBOX_FONT_SIZE, weight)

    @classmethod
    def get_combobox_font(cls) -> QFont:
        """取得下拉框字體"""
        weight = QFont.Bold if cls.COMBOBOX_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.COMBOBOX_FONT_SIZE, weight)

    @classmethod
    def get_checkbox_font(cls) -> QFont:
        """取得複選框字體"""
        weight = QFont.Bold if cls.CHECKBOX_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.CHECKBOX_FONT_SIZE, weight)

    @classmethod
    def get_param_label_font(cls) -> QFont:
        """取得參數標籤字體"""
        weight = QFont.Bold if cls.PARAM_LABEL_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.PARAM_LABEL_FONT_SIZE, weight)

    @classmethod
    def get_angle_label_font(cls) -> QFont:
        """取得角度標籤字體"""
        weight = QFont.Bold if cls.ANGLE_LABEL_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.ANGLE_LABEL_FONT_SIZE, weight)

    @classmethod
    def get_reba_score_font(cls) -> QFont:
        """取得 REBA 分數字體"""
        weight = QFont.Bold if cls.REBA_SCORE_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.REBA_SCORE_FONT_SIZE, weight)

    @classmethod
    def get_risk_level_font(cls) -> QFont:
        """取得風險等級字體"""
        weight = QFont.Bold if cls.RISK_LEVEL_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.RISK_LEVEL_FONT_SIZE, weight)

    @classmethod
    def get_risk_desc_font(cls) -> QFont:
        """取得風險描述字體"""
        weight = QFont.Bold if cls.RISK_DESC_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.RISK_DESC_FONT_SIZE, weight)

    @classmethod
    def get_formula_header_font(cls) -> QFont:
        """取得公式標題字體"""
        weight = QFont.Bold if cls.FORMULA_HEADER_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.FORMULA_HEADER_FONT_SIZE, weight)

    @classmethod
    def get_formula_detail_font(cls) -> QFont:
        """取得公式細節字體"""
        weight = QFont.Bold if cls.FORMULA_DETAIL_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.FORMULA_DETAIL_FONT_SIZE, weight)

    @classmethod
    def get_formula_total_font(cls) -> QFont:
        """取得公式總分字體"""
        weight = QFont.Bold if cls.FORMULA_TOTAL_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.FORMULA_TOTAL_FONT_SIZE, weight)

    @classmethod
    def get_stats_font(cls) -> QFont:
        """取得統計資訊字體"""
        weight = QFont.Bold if cls.STATS_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.STATS_FONT_SIZE, weight)

    @classmethod
    def get_time_label_font(cls) -> QFont:
        """取得時間標籤字體"""
        weight = QFont.Bold if cls.TIME_LABEL_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.TIME_LABEL_FONT_SIZE, weight)

    @classmethod
    def get_video_hint_font(cls) -> QFont:
        """取得影片提示文字字體"""
        weight = QFont.Bold if cls.VIDEO_HINT_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.VIDEO_HINT_FONT_SIZE, weight)

    @classmethod
    def get_log_text_font(cls) -> QFont:
        """取得日誌框字體"""
        weight = QFont.Bold if cls.LOG_TEXT_FONT_BOLD else QFont.Normal
        return QFont(cls.FONT_FAMILY, cls.LOG_TEXT_FONT_SIZE, weight)


class VideoProcessThread(QThread):
    """影片處理執行緒"""

    # 信號定義
    # 影像, 角度, REBA分數, 風險等級, FPS, 詳細分數
    frame_processed = Signal(object, dict, int, str, float, dict)
    processing_finished = Signal()
    error_occurred = Signal(str)
    progress_updated = Signal(int, int)  # 當前幀, 總幀數

    def __init__(self):
        super().__init__()
        self.running = False
        self.paused = False
        self.video_source = None  # None表示攝影機, 否則為影片路徑
        self.camera_id = 0

        # 初始化MediaPipe
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # 初始化角度計算器和評分器
        self.angle_calc = AngleCalculator()
        self.reba_scorer = REBAScorer()

        # 設置參數
        self.side = 'right'  # 分析的身體側邊
        self.load_weight = 0.0  # 負荷重量
        self.force_coupling = 'good'  # 握持品質

        # 顯示選項
        self.show_angle_lines = True  # 顯示角度線
        self.show_angle_values = True  # 顯示角度數值

        # 影片控制
        self.total_frames = 0
        self.current_frame_pos = 0
        self.seek_to_frame = -1  # 跳轉到指定幀（-1表示不跳轉）

        # 載入中文字體（使用 UIConfig 配置）
        font_path = Path(__file__).parent / "Arial.Unicode.ttf"
        if font_path.exists():
            self.font_chinese = ImageFont.truetype(
                str(font_path), UIConfig.OVERLAY_FONT_SIZE)
            self.font_chinese_small = ImageFont.truetype(
                str(font_path), UIConfig.OVERLAY_FONT_SIZE_SMALL)
        else:
            print(f"警告: 找不到字體檔案 {font_path}")
            self.font_chinese = None
            self.font_chinese_small = None

    def set_source(self, source):
        """設置影片來源"""
        self.video_source = source

    def set_camera(self, camera_id: int):
        """設置攝影機ID"""
        self.camera_id = camera_id

    def set_parameters(self, side: str, load_weight: float, force_coupling: str):
        """設置評估參數"""
        self.side = side
        self.load_weight = load_weight
        self.force_coupling = force_coupling

    def set_display_options(self, show_angle_lines: bool, show_angle_values: bool):
        """設置顯示選項"""
        self.show_angle_lines = show_angle_lines
        self.show_angle_values = show_angle_values

    def seek_frame(self, frame_number: int):
        """跳轉到指定幀"""
        self.seek_to_frame = frame_number

    def draw_angle_lines(self, frame, landmarks, angles):
        """繪製角度測量線和角度數值"""
        if landmarks is None:
            return frame

        h, w = frame.shape[:2]

        # 定義關鍵點提取函數
        def get_point(idx):
            lm = landmarks.landmark[idx]
            return (int(lm.x * w), int(lm.y * h))

        # 頸部角度線（紅色）
        if self.show_angle_lines and angles.get('neck') is not None:
            # 計算眼睛中心和肩膀中心
            left_eye = get_point(self.angle_calc.LEFT_EYE)
            right_eye = get_point(self.angle_calc.RIGHT_EYE)
            left_shoulder = get_point(self.angle_calc.LEFT_SHOULDER)
            right_shoulder = get_point(self.angle_calc.RIGHT_SHOULDER)

            eye_center = ((left_eye[0] + right_eye[0]) //
                          2, (left_eye[1] + right_eye[1]) // 2)
            shoulder_center = (
                (left_shoulder[0] + right_shoulder[0]) // 2, (left_shoulder[1] + right_shoulder[1]) // 2)

            cv2.line(frame, eye_center, shoulder_center,
                     UIConfig.COLOR_NECK, UIConfig.ANGLE_LINE_THICKNESS)

            if self.show_angle_values:
                mid_point = ((eye_center[0] + shoulder_center[0]) //
                             2, (eye_center[1] + shoulder_center[1]) // 2)
                self._draw_angle_text(
                    frame, f"{angles['neck']:.1f}°", mid_point, UIConfig.COLOR_NECK)

        # 軀幹角度線（橙色）
        if self.show_angle_lines and angles.get('trunk') is not None:
            left_shoulder = get_point(self.angle_calc.LEFT_SHOULDER)
            right_shoulder = get_point(self.angle_calc.RIGHT_SHOULDER)
            left_hip = get_point(self.angle_calc.LEFT_HIP)
            right_hip = get_point(self.angle_calc.RIGHT_HIP)

            shoulder_center = (
                (left_shoulder[0] + right_shoulder[0]) // 2, (left_shoulder[1] + right_shoulder[1]) // 2)
            hip_center = ((left_hip[0] + right_hip[0]) //
                          2, (left_hip[1] + right_hip[1]) // 2)

            cv2.line(frame, shoulder_center, hip_center,
                     UIConfig.COLOR_TRUNK, UIConfig.ANGLE_LINE_THICKNESS)

            if self.show_angle_values:
                mid_point = (
                    (shoulder_center[0] + hip_center[0]) // 2, (shoulder_center[1] + hip_center[1]) // 2)
                self._draw_angle_text(
                    frame, f"{angles['trunk']:.1f}°", mid_point, UIConfig.COLOR_TRUNK)

        # 上臂角度線（黃色）
        if self.show_angle_lines and angles.get('upper_arm') is not None:
            if self.side == 'right':
                shoulder = get_point(self.angle_calc.RIGHT_SHOULDER)
                elbow = get_point(self.angle_calc.RIGHT_ELBOW)
                wrist = get_point(self.angle_calc.RIGHT_WRIST)
            else:
                shoulder = get_point(self.angle_calc.LEFT_SHOULDER)
                elbow = get_point(self.angle_calc.LEFT_ELBOW)
                wrist = get_point(self.angle_calc.LEFT_WRIST)

            cv2.line(frame, shoulder, elbow, UIConfig.COLOR_UPPER_ARM,
                     UIConfig.ANGLE_LINE_THICKNESS)
            cv2.line(frame, elbow, wrist, UIConfig.COLOR_UPPER_ARM,
                     UIConfig.ANGLE_LINE_THICKNESS)

            if self.show_angle_values:
                offset_x = 20 if self.side == 'right' else -80
                text_pos = (elbow[0] + offset_x, elbow[1] - 10)
                self._draw_angle_text(
                    frame, f"{angles['upper_arm']:.1f}°", text_pos, UIConfig.COLOR_UPPER_ARM)

        # 手腕角度線（綠色）
        if self.show_angle_lines and angles.get('wrist') is not None:
            if self.side == 'right':
                elbow = get_point(self.angle_calc.RIGHT_ELBOW)
                wrist = get_point(self.angle_calc.RIGHT_WRIST)
                index = get_point(self.angle_calc.RIGHT_INDEX)
            else:
                elbow = get_point(self.angle_calc.LEFT_ELBOW)
                wrist = get_point(self.angle_calc.LEFT_WRIST)
                index = get_point(self.angle_calc.LEFT_INDEX)

            cv2.line(frame, wrist, index, UIConfig.COLOR_WRIST,
                     UIConfig.ANGLE_LINE_THICKNESS)

            if self.show_angle_values:
                offset_x = 20 if self.side == 'right' else -80
                text_pos = (wrist[0] + offset_x, wrist[1] + 20)
                self._draw_angle_text(
                    frame, f"{angles['wrist']:.1f}°", text_pos, UIConfig.COLOR_WRIST)

        # 腿部角度線（藍色）
        if self.show_angle_lines and angles.get('leg') is not None:
            if self.side == 'right':
                hip = get_point(self.angle_calc.RIGHT_HIP)
                knee = get_point(self.angle_calc.RIGHT_KNEE)
                ankle = get_point(self.angle_calc.RIGHT_ANKLE)
            else:
                hip = get_point(self.angle_calc.LEFT_HIP)
                knee = get_point(self.angle_calc.LEFT_KNEE)
                ankle = get_point(self.angle_calc.LEFT_ANKLE)

            cv2.line(frame, hip, knee, UIConfig.COLOR_LEG,
                     UIConfig.ANGLE_LINE_THICKNESS)
            cv2.line(frame, knee, ankle, UIConfig.COLOR_LEG,
                     UIConfig.ANGLE_LINE_THICKNESS)

            if self.show_angle_values:
                offset_x = 20 if self.side == 'right' else -80
                text_pos = (knee[0] + offset_x, knee[1])
                self._draw_angle_text(
                    frame, f"{angles['leg']:.1f}°", text_pos, UIConfig.COLOR_LEG)

        return frame

    def _draw_text_with_pil(self, frame, text, position, font, color, bg_style='none', bg_color=(0, 0, 0)):
        """
        統一的PIL文字繪製方法（Template Method Pattern）

        Args:
            frame: OpenCV影像（BGR格式）
            text: 要顯示的文字
            position: 文字位置 (x, y)
            font: PIL ImageFont物件
            color: 文字顏色 (B, G, R)
            bg_style: 背景樣式 ('none', 'solid', 'transparent')
            bg_color: 背景顏色 (B, G, R)
        """
        if font is None:
            cv2.putText(frame, text, position,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            return frame

        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        pil_color = (color[2], color[1], color[0])

        if bg_style != 'none':
            bbox = draw.textbbox(position, text, font=font)
            padding = UIConfig.TEXT_BG_PADDING
            bg_bbox = (bbox[0] - padding, bbox[1] - padding,
                       bbox[2] + padding, bbox[3] + padding)

            if bg_style == 'solid':
                pil_bg_color = (bg_color[2], bg_color[1], bg_color[0])
                draw.rectangle(bg_bbox, fill=pil_bg_color)
            elif bg_style == 'transparent':
                overlay = Image.new('RGBA', img_pil.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle(bg_bbox, fill=(
                    0, 0, 0, UIConfig.TEXT_BG_ALPHA))
                img_pil_rgba = img_pil.convert('RGBA')
                img_pil_rgba = Image.alpha_composite(img_pil_rgba, overlay)
                img_pil = img_pil_rgba.convert('RGB')
                draw = ImageDraw.Draw(img_pil)

        draw.text(position, text, font=font, fill=pil_color)
        frame[:] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return frame

    def _draw_angle_text(self, frame, text, position, color):
        """在影像上繪製角度文字（帶半透明背景）"""
        return self._draw_text_with_pil(frame, text, position, self.font_chinese_small,
                                        color, bg_style='transparent')

    def _put_chinese_text(self, frame, text, position, font, color=(255, 255, 255), bg_color=None):
        """使用PIL在OpenCV影像上繪製中文文字"""
        bg_style = 'solid' if bg_color is not None else 'none'
        return self._draw_text_with_pil(frame, text, position, font, color,
                                        bg_style=bg_style, bg_color=bg_color if bg_color else (0, 0, 0))

    def run(self):
        """執行緒主循環（重構為小函式）"""
        self.running = True
        cap = self._open_video_source()
        if cap is None:
            return

        self._setup_video_properties(cap)

        with self._create_holistic() as holistic:
            self._process_video_loop(cap, holistic)

        cap.release()
        self.processing_finished.emit()

    def _open_video_source(self):
        """開啟影片或攝影機"""
        cap = cv2.VideoCapture(
            self.video_source if self.video_source else self.camera_id)
        if not cap.isOpened():
            self.error_occurred.emit("無法開啟影片來源")
            return None
        return cap

    def _setup_video_properties(self, cap):
        """設置影片屬性"""
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, UIConfig.VIDEO_CAPTURE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, UIConfig.VIDEO_CAPTURE_HEIGHT)
        self.total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)) if self.video_source else 0

    def _create_holistic(self):
        """創建 MediaPipe Holistic 實例"""
        return self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=UIConfig.MEDIAPIPE_MODEL_COMPLEXITY
        )

    def _process_video_loop(self, cap, holistic):
        """主處理循環（含效能優化）"""
        frame_count = 0
        start_time = time.time()

        # 快取上一次的分析結果（用於跳幀時）
        cached_angles = {}
        cached_reba_score = 0
        cached_risk_level = 'unknown'
        cached_details = {}

        skip_n = UIConfig.PROCESS_EVERY_N_FRAMES
        delay_ms = UIConfig.PROCESS_LOOP_DELAY_MS

        while self.running:
            if not self._handle_pause_and_seek(cap):
                break

            ret, frame = cap.read()
            if not ret:
                break

            self._update_progress(cap)

            # 跳幀優化：只有每 N 幀才進行完整姿態分析
            if skip_n <= 1 or frame_count % skip_n == 0:
                results = holistic.process(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                cached_angles, cached_reba_score, cached_risk_level, cached_details = \
                    self._process_pose_results(frame, results)
            else:
                # 使用快取的結果，只繪製骨架（如果有的話）
                pass

            fps = self._calculate_fps(frame_count, start_time)
            frame_count += 1
            if frame_count % 30 == 0:
                start_time = time.time()

            self._draw_fps(frame, fps)
            self.frame_processed.emit(frame, cached_angles, cached_reba_score,
                                      cached_risk_level, fps, cached_details)

            # 可配置的延遲
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    def _handle_pause_and_seek(self, cap):
        """處理暫停和跳轉（支援暫停時預覽）"""
        while self.paused and self.running:
            # 暫停時也檢查是否有跳轉請求（用於拖曳預覽）
            if self.seek_to_frame >= 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, self.seek_to_frame)
                self.current_frame_pos = self.seek_to_frame
                target_frame = self.seek_to_frame
                self.seek_to_frame = -1

                # 讀取並處理單一幀以更新顯示
                ret, frame = cap.read()
                if ret:
                    # 重新定位到該幀（因為 read() 會前進一幀）
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    self._process_single_frame_for_preview(frame)

            time.sleep(0.05)  # 縮短檢查間隔以提高響應速度

        if not self.running:
            return False

        if self.seek_to_frame >= 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, self.seek_to_frame)
            self.current_frame_pos = self.seek_to_frame
            self.seek_to_frame = -1

        return True

    def _process_single_frame_for_preview(self, frame):
        """處理單一幀用於拖曳預覽（簡化版，不含完整分析）"""
        # 發送基本幀顯示，不進行完整的姿態分析以節省效能
        self.frame_processed.emit(frame, {}, 0, 'unknown', 0.0, {})

    def _update_progress(self, cap):
        """更新進度條"""
        if self.video_source:
            self.current_frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.progress_updated.emit(
                self.current_frame_pos, self.total_frames)

    def _process_pose_results(self, frame, results):
        """處理姿態檢測結果"""
        angles = {}
        reba_score = 0
        risk_level = 'unknown'
        details = {}

        if results.pose_landmarks:
            # self._draw_pose_landmarks(frame, results.pose_landmarks)
            angles = self.angle_calc.calculate_all_angles(
                results.pose_landmarks, self.side)
            # frame = self.draw_angle_lines(frame, results.pose_landmarks, angles)
            reba_score, risk_level, details = self._calculate_and_draw_reba(
                frame, angles)

        return angles, reba_score, risk_level, details

    def _draw_pose_landmarks(self, frame, landmarks):
        """繪製姿態關鍵點"""
        self.mp_drawing.draw_landmarks(
            frame, landmarks, self.mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )

    def _calculate_and_draw_reba(self, frame, angles):
        """計算並繪製 REBA 分數"""
        reba_score, risk_level, details = self.reba_scorer.calculate_reba_score(
            angles, self.load_weight, self.force_coupling
        )

        color = self._get_color_for_risk(risk_level)
        risk_text = self._get_risk_text_chinese(risk_level)

        # 使用 UIConfig 配置的位置
        reba_pos = (UIConfig.OVERLAY_REBA_SCORE_X,
                    UIConfig.OVERLAY_REBA_SCORE_Y)
        risk_pos = (UIConfig.OVERLAY_RISK_LEVEL_X,
                    UIConfig.OVERLAY_RISK_LEVEL_Y)

        # frame = self._put_chinese_text(frame, f"REBA分數: {reba_score}", reba_pos,
        #                                self.font_chinese, color, bg_color=(0, 0, 0))
        # frame = self._put_chinese_text(frame, f"風險等級: {risk_text}", risk_pos,
        #                                self.font_chinese_small, color, bg_color=(0, 0, 0))

        return reba_score, risk_level, details

    def _get_risk_text_chinese(self, risk_level):
        """獲取風險等級中文文字"""
        risk_map = {
            'negligible': '可忽略',
            'low': '低風險',
            'medium': '中等風險',
            'high': '高風險',
            'very_high': '極高風險'
        }
        return risk_map.get(risk_level, risk_level)

    def _calculate_fps(self, frame_count, start_time):
        """計算 FPS"""
        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            return 30 / elapsed if elapsed > 0 else 30.0
        return 30.0

    def _draw_fps(self, frame, fps):
        """繪製 FPS"""
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, UIConfig.FPS_FONT_SCALE, (255, 255, 255), UIConfig.FPS_FONT_THICKNESS)

    def _get_color_for_risk(self, risk_level: str):
        """根據風險等級獲取顏色"""
        return UIConfig.RISK_COLORS.get(risk_level, (255, 255, 255))

    def stop(self):
        """停止處理"""
        self.running = False

    def pause(self):
        """暫停處理"""
        self.paused = True

    def resume(self):
        """恢復處理"""
        self.paused = False


class MainWindow(QMainWindow):
    """主視窗"""

    # 定義 Signal：Table C 分數更新
    table_c_scores_updated = Signal(object, object)  # score_a, score_b

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaPipe REBA 分析系統")
        self.setGeometry(UIConfig.WINDOW_X, UIConfig.WINDOW_Y,
                         UIConfig.WINDOW_WIDTH, UIConfig.WINDOW_HEIGHT)

        # 初始化變數
        self.video_thread = None
        self.data_logger = DataLogger()
        self.frame_count = 0
        self.is_processing = False
        self.data_locked = False  # 資料鎖定狀態
        self.locked_data = None  # 鎖定的資料
        self.reba_scorer = REBAScorer()

        # 進度條拖曳相關
        self.is_slider_dragging = False  # 是否正在拖曳
        self.pending_seek_frame = -1  # 待執行的跳轉幀
        self.was_paused_before_drag = False  # 拖曳前是否已暫停

        # 節流計時器（用於拖曳時的預覽）
        self.slider_throttle_timer = QTimer()
        self.slider_throttle_timer.setSingleShot(True)
        self.slider_throttle_timer.timeout.connect(
            self._execute_throttled_seek)

        # 初始化UI
        self.init_ui()

    def init_ui(self):
        """初始化使用者介面"""
        # 主Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主佈局
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # 左側: 影片顯示區
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 16)

        # 影片顯示標籤
        self.video_label = QLabel()
        self.video_label.setMinimumSize(
            UIConfig.VIDEO_LABEL_MIN_WIDTH, UIConfig.VIDEO_LABEL_MIN_HEIGHT)
        self.video_label.setStyleSheet(UIConfig.VIDEO_LABEL_BORDER_STYLE)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("請選擇影片來源")
        self.video_label.setFont(UIConfig.get_video_hint_font())
        left_layout.addWidget(self.video_label)

        # 控制按鈕區（第一行）
        control_layout1 = QHBoxLayout()
        left_layout.addLayout(control_layout1)
        button_font = UIConfig.get_button_font()

        self.btn_camera = QPushButton("開啟攝影機")
        self.btn_camera.setFont(button_font)
        self.btn_camera.clicked.connect(self.start_camera)
        control_layout1.addWidget(self.btn_camera)

        self.btn_video = QPushButton("選擇影片")
        self.btn_video.setFont(button_font)
        self.btn_video.clicked.connect(self.select_video)
        control_layout1.addWidget(self.btn_video)

        self.btn_pause = QPushButton("暫停")
        self.btn_pause.setFont(button_font)
        self.btn_pause.clicked.connect(self.pause_processing)
        self.btn_pause.setEnabled(False)
        control_layout1.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setFont(button_font)
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        control_layout1.addWidget(self.btn_stop)

        self.btn_replay = QPushButton("重播")
        # self.btn_replay.setFont(button_font)
        # self.btn_replay.clicked.connect(self.replay_video)
        # self.btn_replay.setEnabled(False)
        # control_layout1.addWidget(self.btn_replay)

        # 進度條和時間顯示
        progress_layout = QHBoxLayout()
        left_layout.addLayout(progress_layout)
        time_label_font = UIConfig.get_time_label_font()

        self.label_time_current = QLabel("00:00")
        self.label_time_current.setFont(time_label_font)
        progress_layout.addWidget(self.label_time_current)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderMoved.connect(self.slider_moved)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        progress_layout.addWidget(self.progress_slider)

        self.label_time_total = QLabel("00:00")
        self.label_time_total.setFont(time_label_font)
        progress_layout.addWidget(self.label_time_total)

        # 顯示選項（複選框）
        display_options_layout = QHBoxLayout()
        left_layout.addLayout(display_options_layout)
        checkbox_font = UIConfig.get_checkbox_font()

        self.check_angle_lines = QCheckBox("顯示角度線")
        self.check_angle_lines.setFont(checkbox_font)
        self.check_angle_lines.setChecked(True)
        self.check_angle_lines.stateChanged.connect(
            self.update_display_options)
        display_options_layout.addWidget(self.check_angle_lines)

        self.check_angle_values = QCheckBox("顯示角度數值")
        self.check_angle_values.setFont(checkbox_font)
        self.check_angle_values.setChecked(True)
        self.check_angle_values.stateChanged.connect(
            self.update_display_options)

        display_options_layout.addWidget(self.check_angle_values)
        display_options_layout.addStretch()

        # 保存按鈕
        save_layout = QHBoxLayout()
        self.btn_save_csv = QPushButton("保存CSV")
        self.btn_save_csv.setFont(button_font)
        self.btn_save_csv.clicked.connect(self.save_csv)
        # save_layout.addWidget(self.btn_save_csv)
        display_options_layout.addWidget(self.btn_save_csv)

        self.btn_save_json = QPushButton("保存JSON")
        self.btn_save_json.setFont(button_font)
        self.btn_save_json.clicked.connect(self.save_json)
        # save_layout.addWidget(self.btn_save_json)
        display_options_layout.addWidget(self.btn_save_json)

        # display_options_layout.addLayout(save_layout)

        # 統計資訊和日誌區塊（水平排列）
        bottom_info_layout = QHBoxLayout()
        left_layout.addLayout(bottom_info_layout)

        # 日誌顯示
        log_group = QGroupBox("系統日誌")
        log_group.setFont(UIConfig.get_groupbox_font())
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        bottom_info_layout.addWidget(log_group, 1)  # stretch=1 讓日誌區塊佔更多空間

        # 統計資訊群組
        stats_font = UIConfig.get_stats_font()
        stats_group = QGroupBox("統計資訊")
        stats_group.setFont(UIConfig.get_groupbox_font())
        stats_layout = QGridLayout()
        stats_group.setLayout(stats_layout)
        bottom_info_layout.addWidget(stats_group)

        fps_prefix_label = QLabel("處理幀數:")
        fps_prefix_label.setFont(stats_font)
        stats_layout.addWidget(fps_prefix_label, 0, 0)
        self.label_frame_count = QLabel("0")
        self.label_frame_count.setFont(stats_font)
        stats_layout.addWidget(self.label_frame_count, 0, 1)

        fps2_prefix_label = QLabel("FPS:")
        fps2_prefix_label.setFont(stats_font)
        stats_layout.addWidget(fps2_prefix_label, 1, 0)
        self.label_fps = QLabel("0")
        self.label_fps.setFont(stats_font)
        stats_layout.addWidget(self.label_fps, 1, 1)

        record_label = QLabel("記錄數:")
        record_label.setFont(stats_font)
        stats_layout.addWidget(record_label, 2, 0)
        self.label_record_count = QLabel("0")
        self.label_record_count.setFont(stats_font)
        stats_layout.addWidget(self.label_record_count, 2, 1)

        self.log_text = QTextEdit()
        self.log_text.setFont(UIConfig.get_log_text_font())
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(UIConfig.LOG_TEXT_MAX_HEIGHT)
        log_layout.addWidget(self.log_text)

        # 右側: 資料面板
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 9)

        # 取得各種字體
        groupbox_font = UIConfig.get_groupbox_font()
        param_label_font = UIConfig.get_param_label_font()
        combobox_font = UIConfig.get_combobox_font()

        # 參數設置群組
        param_group = QGroupBox("評估參數")
        param_group.setFont(groupbox_font)
        param_layout = QGridLayout()
        param_group.setLayout(param_layout)
        right_layout.addWidget(param_group)

        label_side = QLabel("分析側邊:")
        label_side.setFont(param_label_font)
        param_layout.addWidget(label_side, 0, 0)
        self.combo_side = QComboBox()
        self.combo_side.setFont(combobox_font)
        self.combo_side.addItems(["right", "left"])
        param_layout.addWidget(self.combo_side, 0, 1)

        label_load = QLabel("負荷重量(kg):")
        label_load.setFont(param_label_font)
        param_layout.addWidget(label_load, 1, 0)
        self.spin_load = QDoubleSpinBox()
        self.spin_load.setFont(param_label_font)
        self.spin_load.setRange(0, 100)
        self.spin_load.setValue(0)
        param_layout.addWidget(self.spin_load, 1, 1)

        label_coupling = QLabel("握持品質:")
        label_coupling.setFont(param_label_font)
        param_layout.addWidget(label_coupling, 2, 0)
        self.combo_coupling = QComboBox()
        self.combo_coupling.setFont(combobox_font)
        self.combo_coupling.addItems(["good", "fair", "poor", "unacceptable"])
        param_layout.addWidget(self.combo_coupling, 2, 1)

        # 連接參數變更信號
        self.combo_side.currentTextChanged.connect(self._on_parameters_changed)
        self.spin_load.valueChanged.connect(self._on_parameters_changed)
        self.combo_coupling.currentTextChanged.connect(
            self._on_parameters_changed)

        # REBA 評估群組 - 整合關節角度與所有分數為單一表格
        reba_group = QGroupBox("關節角度與REBA分數")

        reba_group.setFont(groupbox_font)
        reba_layout = QVBoxLayout()
        reba_group.setLayout(reba_layout)
        right_layout.addWidget(reba_group)

        # 第一行：總分和風險等級
        score_risk_layout = QHBoxLayout()
        reba_layout.addLayout(score_risk_layout)

        self.label_reba_score = QLabel("分數: --")
        self.label_reba_score.setFont(UIConfig.get_reba_score_font())
        self.label_reba_score.setAlignment(Qt.AlignCenter)
        score_risk_layout.addWidget(self.label_reba_score)

        self.label_risk_level = QLabel("風險等級: --")
        self.label_risk_level.setFont(UIConfig.get_risk_level_font())
        self.label_risk_level.setAlignment(Qt.AlignCenter)
        score_risk_layout.addWidget(self.label_risk_level)

        # 創建整合表格 - 5列設計（左右並列），表頭作為第一行可複製
        from PySide6.QtGui import QColor, QBrush

        self.angle_table = QTableWidget()
        self.angle_table.setColumnCount(5)
        self.angle_table.setFont(UIConfig.get_formula_detail_font())
        self.angle_table.installEventFilter(self)  # 安裝事件過濾器處理複製

        # 定義表格行結構（第一行是表頭）
        # (左側部位, 左側key, 右側部位, 右側key, is_section_header, is_highlight)
        self.table_structure = [
            # 表頭行（可複製）
            ('部位', '', '角度', '', True, False),
            # 關節角度區塊（左側角度，右側分數）
            ('頸部', 'neck', '', 'neck_score', False, False),
            ('軀幹', 'trunk', '', 'trunk_score', False, False),
            ('上臂', 'upper_arm', '', 'upper_arm_score', False, False),
            ('前臂', 'forearm', '', 'forearm_score', False, False),
            ('手腕', 'wrist', '', 'wrist_score', False, False),
            ('腿部', 'leg', '', 'leg_score', False, False),
            # REBA評分區塊標題
            ('REBA評分', '', '', '', True, False),
            # GroupA / GroupB 標題
            ('GroupA', '', 'GroupB', '', True, False),
            # 分數明細
            ('頸部', 'neck_score', '上臂', 'upper_arm_score', False, False),
            ('軀幹', 'trunk_score', '前臂', 'forearm_score', False, False),
            ('腿部', 'leg_score', '手腕', 'wrist_score', False, False),
            ('負荷', 'load_score', '握持', 'coupling_score', False, False),
            ('姿勢A', 'posture_score_a', '姿勢B', 'posture_score_b', False, False),
            ('Score A', 'score_a', 'Score B', 'score_b', False, True),
            # 總分區塊
            ('Score C', 'score_c', '活動', 'activity_score', False, False),
            ('REBA總分', 'final_score', '', '', False, True),
        ]

        self.angle_table.setRowCount(len(self.table_structure))

        # 設定表格樣式 - 隱藏水平表頭（改用第一行）
        self.angle_table.horizontalHeader().setVisible(False)
        self.angle_table.verticalHeader().setVisible(False)
        self.angle_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.angle_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.angle_table.setSelectionBehavior(QAbstractItemView.SelectItems)

        # 設定每欄寬度（使用比例自適應 RWD）
        header = self.angle_table.horizontalHeader()
        header.setStretchLastSection(False)
        self.column_ratios = UIConfig.TABLE_COLUMN_RATIOS

        # 設定欄位為 Interactive 模式，允許動態調整
        for col in range(5):
            header.setSectionResizeMode(col, QHeaderView.Interactive)

        # 初始化欄位寬度
        self._update_table_column_widths()

        # 自動調整行高
        row_h = UIConfig.TABLE_ROW_HEIGHT
        table_height = row_h * len(self.table_structure) + 4
        self.angle_table.verticalHeader().setDefaultSectionSize(row_h)
        self.angle_table.setFixedHeight(table_height)

        # 建立行映射
        self.angle_row_map = {}
        self.score_row_map = {}

        for row_idx, (left_name, left_key, right_name, right_key, is_header, is_highlight) in enumerate(self.table_structure):
            # 第一行表頭（部位/角度）
            if row_idx == 0:
                headers = ['部位', '角度', '', '  ', '分數']
                for col, text in enumerate(headers):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QBrush(QColor('#c0c0c0')))
                    item.setFont(UIConfig.get_formula_header_font())
                    self.angle_table.setItem(row_idx, col, item)
                continue

            # 區塊標題行（合併儲存格）
            if is_header:
                if right_name:  # GroupA / GroupB 標題
                    left_item = QTableWidgetItem(left_name)
                    left_item.setTextAlignment(Qt.AlignCenter)
                    left_item.setBackground(QBrush(QColor('#e0e0e0')))
                    left_item.setFont(UIConfig.get_formula_header_font())
                    self.angle_table.setItem(row_idx, 0, left_item)

                    empty1 = QTableWidgetItem('')
                    empty1.setBackground(QBrush(QColor('#e0e0e0')))
                    self.angle_table.setItem(row_idx, 1, empty1)

                    sep_item = QTableWidgetItem('')
                    sep_item.setBackground(QBrush(QColor('#e0e0e0')))
                    self.angle_table.setItem(row_idx, 2, sep_item)

                    right_item = QTableWidgetItem(right_name)
                    right_item.setTextAlignment(Qt.AlignCenter)
                    right_item.setBackground(QBrush(QColor('#e0e0e0')))
                    right_item.setFont(UIConfig.get_formula_header_font())
                    self.angle_table.setItem(row_idx, 3, right_item)

                    empty2 = QTableWidgetItem('')
                    empty2.setBackground(QBrush(QColor('#e0e0e0')))
                    self.angle_table.setItem(row_idx, 4, empty2)
                else:  # REBA評分 標題
                    self.angle_table.setSpan(row_idx, 0, 1, 5)
                    header_item = QTableWidgetItem(left_name)
                    header_item.setTextAlignment(Qt.AlignCenter)
                    header_item.setBackground(QBrush(QColor('#d0d0d0')))
                    header_item.setFont(UIConfig.get_formula_header_font())
                    self.angle_table.setItem(row_idx, 0, header_item)
                continue

            # 設定背景顏色
            bg_color = QColor('#d0d0ff') if is_highlight else None
            if left_name == 'REBA總分':
                bg_color = QColor('#ffd0d0')

            # 左側部位名稱
            left_name_item = QTableWidgetItem(left_name)
            left_name_item.setTextAlignment(Qt.AlignCenter)
            if bg_color:
                left_name_item.setBackground(QBrush(bg_color))
                left_name_item.setFont(UIConfig.get_formula_total_font())
            self.angle_table.setItem(row_idx, 0, left_name_item)

            # 左側數值（角度或分數）
            left_val_item = QTableWidgetItem('--')
            left_val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if bg_color:
                left_val_item.setBackground(QBrush(bg_color))
                left_val_item.setFont(UIConfig.get_formula_total_font())
            self.angle_table.setItem(row_idx, 1, left_val_item)

            # 中間分隔欄
            sep_item = QTableWidgetItem('')
            if bg_color:
                sep_item.setBackground(QBrush(bg_color))
            self.angle_table.setItem(row_idx, 2, sep_item)

            # 右側部位名稱
            right_name_item = QTableWidgetItem(right_name)
            right_name_item.setTextAlignment(Qt.AlignCenter)
            if bg_color:
                right_name_item.setBackground(QBrush(bg_color))
                right_name_item.setFont(UIConfig.get_formula_total_font())
            self.angle_table.setItem(row_idx, 3, right_name_item)

            # 右側數值（REBA分數）
            right_val_item = QTableWidgetItem('--' if right_key else '')
            right_val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if bg_color:
                right_val_item.setBackground(QBrush(bg_color))
                right_val_item.setFont(UIConfig.get_formula_total_font())
            self.angle_table.setItem(row_idx, 4, right_val_item)

            # 建立映射 (用於更新數值) - 使用 list 支援同一 key 多個位置
            if left_key:
                if left_key in ['neck', 'trunk', 'upper_arm', 'forearm', 'wrist', 'leg']:
                    self.angle_row_map[left_key] = (row_idx, 1)  # 角度值在 col 1
                else:
                    if left_key not in self.score_row_map:
                        self.score_row_map[left_key] = []
                    self.score_row_map[left_key].append(
                        (row_idx, 1))  # 分數值在 col 1
            if right_key:
                if right_key not in self.score_row_map:
                    self.score_row_map[right_key] = []
                self.score_row_map[right_key].append(
                    (row_idx, 4))  # 分數值在 col 4

        reba_layout.addWidget(self.angle_table)

        # # 風險描述
        self.label_risk_desc = QLabel("")
        # self.label_risk_desc.setFont(UIConfig.get_risk_desc_font())
        # self.label_risk_desc.setWordWrap(True)
        # self.label_risk_desc.setAlignment(Qt.AlignCenter)
        # reba_layout.addWidget(self.label_risk_desc)

        # 保留舊的字典結構以相容現有程式碼
        self.angle_labels = {}
        self.score_labels = {}

        # 資料操作按鈕
        data_control_layout = QHBoxLayout()
        reba_layout.addLayout(data_control_layout)

        self.checkbox_lock = QCheckBox("鎖定資料")
        self.checkbox_lock.setFont(checkbox_font)
        self.checkbox_lock.stateChanged.connect(self.toggle_lock)
        data_control_layout.addWidget(self.checkbox_lock)

        self.btn_table_c = QPushButton("Table C")
        self.btn_table_c.setFont(button_font)
        self.btn_table_c.clicked.connect(self.show_table_c)
        data_control_layout.addWidget(self.btn_table_c)

        self.btn_copy = QPushButton("複製資料")
        self.btn_copy.setFont(button_font)
        self.btn_copy.clicked.connect(self.copy_data)
        data_control_layout.addWidget(self.btn_copy)

        # Table C 對話框實例
        self.table_c_dialog = None

        # 添加彈性空間
        right_layout.addStretch()

        # 狀態列
        self.statusBar().showMessage("就緒")

        # 日誌歡迎訊息
        self.log("系統啟動完成")
        self.log("請選擇影片來源開始分析")

    def log(self, message: str):
        """添加日誌訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def start_camera(self):
        """開啟攝影機"""
        if self.is_processing:
            self.log("請先停止當前處理")
            return

        self.log("正在開啟攝影機...")
        self.start_processing(None)

    def select_video(self):
        """選擇影片檔案"""
        if self.is_processing:
            self.log("請先停止當前處理")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇影片檔案",
            "",
            "影片檔案 (*.mp4 *.avi *.mov *.mkv);;所有檔案 (*.*)"
        )

        if file_path:
            self.log(f"選擇影片: {Path(file_path).name}")
            self.start_processing(file_path)

    def start_processing(self, video_source):
        """開始處理"""
        # 創建並啟動執行緒
        self.video_thread = VideoProcessThread()
        self.video_thread.set_source(video_source)

        # 設置參數
        side = self.combo_side.currentText()
        load_weight = self.spin_load.value()
        force_coupling = self.combo_coupling.currentText()
        self.video_thread.set_parameters(side, load_weight, force_coupling)

        # 設置顯示選項
        show_lines = self.check_angle_lines.isChecked()
        show_values = self.check_angle_values.isChecked()
        self.video_thread.set_display_options(show_lines, show_values)

        # 連接信號
        self.video_thread.frame_processed.connect(self.update_display)
        self.video_thread.processing_finished.connect(self.processing_finished)
        self.video_thread.error_occurred.connect(self.handle_error)
        self.video_thread.progress_updated.connect(self.update_progress)

        # 啟動執行緒
        self.video_thread.start()

        # 更新UI狀態
        self.is_processing = True
        self.btn_camera.setEnabled(False)
        self.btn_video.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)

        # 如果是影片文件，啟用進度條和重播按鈕
        if video_source is not None:
            self.progress_slider.setEnabled(True)
            self.btn_replay.setEnabled(True)
        else:
            self.progress_slider.setEnabled(False)
            self.btn_replay.setEnabled(False)

        # 清空資料記錄器
        self.data_logger.clear_buffer()
        self.frame_count = 0

        source_name = "攝影機" if video_source is None else Path(
            video_source).name
        self.log(f"開始處理: {source_name}")
        self.statusBar().showMessage("處理中...")

    def pause_processing(self):
        """暫停/恢復處理"""
        if self.video_thread:
            if self.video_thread.paused:
                self.video_thread.resume()
                self.btn_pause.setText("暫停")
                self.log("恢復處理")
                self.statusBar().showMessage("處理中...")
            else:
                self.video_thread.pause()
                self.btn_pause.setText("恢復")
                self.log("已暫停")
                self.statusBar().showMessage("已暫停")

    def stop_processing(self):
        """停止處理"""
        if self.video_thread:
            self.log("正在停止處理...")
            self.video_thread.stop()
            self.video_thread.wait()
            self.video_thread = None

        self.processing_finished()

    def processing_finished(self):
        """處理完成"""
        self.is_processing = False
        self.btn_camera.setEnabled(True)
        self.btn_video.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("暫停")
        self.btn_stop.setEnabled(False)
        self.progress_slider.setEnabled(False)

        self.log(f"處理完成，共處理 {self.frame_count} 幀")
        self.statusBar().showMessage("處理完成")

        # 顯示統計摘要
        if self.data_logger.get_buffer_size() > 0:
            self.data_logger.print_summary()

    def handle_error(self, error_msg: str):
        """處理錯誤"""
        self.log(f"錯誤: {error_msg}")
        self.statusBar().showMessage(f"錯誤: {error_msg}")
        self.processing_finished()

    def update_display(self, frame, angles, reba_score, risk_level, fps, details):
        """更新顯示（支援資料鎖定）"""
        # 更新幀計數（始終更新）
        self.frame_count += 1
        self.label_frame_count.setText(str(self.frame_count))
        self.label_fps.setText(f"{fps:.1f}")

        # 如果資料被鎖定，使用鎖定的資料，否則使用當前資料
        if not self.data_locked:
            # 保存當前資料供複製使用
            self.locked_data = {
                'frame': frame,
                'angles': angles,
                'reba_score': reba_score,
                'risk_level': risk_level,
                'details': details,
                'fps': fps
            }

            # 更新影像顯示
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h,
                              bytes_per_line, QImage.Format_RGB888)

            # 縮放到適合視窗大小
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)

            # 更新角度和分數顯示
            self._update_angles_and_scores(angles, details)

            # 更新REBA總分和公式顯示
            self._update_reba_display(reba_score, risk_level, details)

        # 記錄資料
        timestamp = time.time()
        self.data_logger.add_frame_data(
            self.frame_count,
            timestamp,
            angles,
            reba_score,
            risk_level
        )

        self.label_record_count.setText(
            str(self.data_logger.get_buffer_size()))

    def _update_table_column_widths(self):
        """根據比例更新表格欄位寬度（RWD 支援）"""
        if not hasattr(self, 'angle_table') or not hasattr(self, 'column_ratios'):
            return

        # 取得表格可用寬度（扣除垂直滾動條和邊框）
        available_width = self.angle_table.viewport().width()
        if available_width <= 0:
            available_width = self.angle_table.width() - 4

        # 計算總比例
        total_ratio = sum(self.column_ratios)

        # 根據比例分配寬度
        for col, ratio in enumerate(self.column_ratios):
            width = int(available_width * ratio / total_ratio)
            self.angle_table.setColumnWidth(col, width)

    def _update_angles_and_scores(self, angles, details):
        """更新角度表格顯示（新版5列表格）"""
        # 更新角度值
        for key, (row_idx, col_idx) in self.angle_row_map.items():
            angle_item = self.angle_table.item(row_idx, col_idx)
            if angle_item:
                if angles.get(key) is not None:
                    angle_item.setText(f"{angles[key]:.1f}°")
                else:
                    angle_item.setText("--")

    def _update_reba_display(self, reba_score, risk_level, details=None):
        """更新REBA總分、風險等級和分數表格顯示（新版5列表格）"""
        if details is None:
            details = {}

        if reba_score > 0:
            self.label_reba_score.setText(f"分數: {reba_score}")

            # 風險等級
            risk_labels = {
                'negligible': '可忽略',
                'low': '低風險',
                'medium': '中等風險',
                'high': '高風險',
                'very_high': '極高風險'
            }
            risk_text = risk_labels.get(risk_level, risk_level)
            self.label_risk_level.setText(f"風險等級: {risk_text}")

            # 風險描述
            # reba_scorer = REBAScorer()
            desc = self.reba_scorer.get_risk_description(risk_level)
            self.label_risk_desc.setText(desc)

            # 設置顏色
            color = self.reba_scorer.get_risk_color(risk_level)
            self.label_reba_score.setStyleSheet(
                f"background-color: {color}; padding: 5px;")
            self.label_risk_level.setStyleSheet(
                f"background-color: {color}; padding: 5px;")

            # ===== 更新分數表格 =====
            # 使用 score_row_map 更新所有分數值（每個 key 可能有多個位置）
            for key, positions in self.score_row_map.items():
                val = details.get(key)
                text = str(val) if val is not None else '--'
                for (row_idx, col_idx) in positions:
                    score_item = self.angle_table.item(row_idx, col_idx)
                    if score_item:
                        score_item.setText(text)

            # ===== 即時更新 Table C 對話框 (透過 Signal) =====
            score_a = details.get('score_a')
            score_b = details.get('score_b')
            self.table_c_scores_updated.emit(score_a, score_b)

        else:
            # 重置所有顯示
            self.label_reba_score.setText("分數: --")
            self.label_risk_level.setText("風險等級: --")
            self.label_risk_desc.setText("")
            self.label_reba_score.setStyleSheet("")
            self.label_risk_level.setStyleSheet("")

            # 重置分數表格
            for key, positions in self.score_row_map.items():
                for (row_idx, col_idx) in positions:
                    score_item = self.angle_table.item(row_idx, col_idx)
                    if score_item:
                        score_item.setText("--")

    def toggle_lock(self, state):
        """切換資料鎖定狀態"""
        self.data_locked = (state == Qt.Checked)
        if self.data_locked:
            self.log("資料已鎖定 - 顯示將保持當前狀態")
            self.statusBar().showMessage("資料已鎖定")
        else:
            self.log("資料已解鎖 - 恢復即時更新")
            self.statusBar().showMessage("資料已解鎖")

    def show_table_c(self):
        """顯示 Table C 對話框"""
        # 取得當前 Score A 和 Score B
        score_a = None
        score_b = None

        if self.locked_data:
            details = self.locked_data.get('details', {})
            score_a = details.get('score_a')
            score_b = details.get('score_b')

        # 如果對話框不存在或已關閉，建立新的
        if self.table_c_dialog is None or not self.table_c_dialog.isVisible():
            # 如果之前有對話框，先斷開舊的 Signal 連接
            if self.table_c_dialog is not None:
                try:
                    self.table_c_scores_updated.disconnect(
                        self.table_c_dialog.update_scores)
                except RuntimeError:
                    pass  # 已經斷開連接

            self.table_c_dialog = TableCDialog(self, score_a, score_b)
            # 連接 Signal 到對話框的更新方法
            self.table_c_scores_updated.connect(
                self.table_c_dialog.update_scores)
            # 當對話框關閉時斷開 Signal
            self.table_c_dialog.finished.connect(self._on_table_c_closed)
            self.table_c_dialog.show()
            # 定位視窗：主視窗右邊、垂直置中
            self._position_table_c_dialog()
        else:
            # 更新現有對話框的分數
            self.table_c_dialog.update_scores(score_a, score_b)
            self.table_c_dialog.raise_()
            self.table_c_dialog.activateWindow()

    def _on_table_c_closed(self):
        """Table C 對話框關閉時的處理"""
        if self.table_c_dialog is not None:
            try:
                self.table_c_scores_updated.disconnect(
                    self.table_c_dialog.update_scores)
            except RuntimeError:
                pass  # 已經斷開連接

    def _position_table_c_dialog(self):
        """將 Table C 對話框定位在主視窗右邊，垂直置中"""
        if self.table_c_dialog is None:
            return

        # 取得主視窗的位置和大小
        main_geo = self.geometry()
        main_x = main_geo.x()
        main_y = main_geo.y()
        main_width = main_geo.width()
        main_height = main_geo.height()

        # 取得對話框大小
        dialog_width = self.table_c_dialog.width()
        dialog_height = self.table_c_dialog.height()

        # 計算新位置：主視窗右邊、垂直置中
        new_x = main_x + main_width + 10  # 右邊間隔 10 像素
        new_y = main_y + (main_height - dialog_height) // 2  # 垂直置中

        # 確保不超出螢幕邊界
        screen = QApplication.primaryScreen().availableGeometry()
        if new_x + dialog_width > screen.right():
            # 如果超出右邊，放到主視窗左邊
            new_x = main_x - dialog_width - 10
        if new_y < screen.top():
            new_y = screen.top()
        if new_y + dialog_height > screen.bottom():
            new_y = screen.bottom() - dialog_height

        self.table_c_dialog.move(new_x, new_y)

    def copy_data(self):
        """複製當前資料到剪貼板"""
        if self.locked_data is None:
            self.log("沒有資料可複製")
            return

        data = self.locked_data
        angles = data['angles']
        details = data.get('details', {})
        reba_score = data['reba_score']
        risk_level = data['risk_level']

        # 風險等級中文
        risk_labels = {
            'negligible': '可忽略',
            'low': '低風險',
            'medium': '中等風險',
            'high': '高風險',
            'very_high': '極高風險'
        }
        risk_text = risk_labels.get(risk_level, risk_level)

        # 取得風險描述
        risk_desc = self.reba_scorer.get_risk_description(risk_level)

        # 取得當前參數設定
        side = self.combo_side.currentText()
        load_weight = self.spin_load.value()
        coupling = self.combo_coupling.currentText()
        coupling_labels = {"good": "良好", "fair": "普通",
                           "poor": "差", "unacceptable": "不可接受"}
        coupling_text = coupling_labels.get(coupling, coupling)

        # 時間戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 格式化角度值（處理可能的 None）
        def fmt_angle(key):
            val = angles.get(key)
            return f"{val:.1f}°" if val is not None else "--"

        # 格式化資料為文字
        text_data = f"""════════════════════════════════════════
          REBA 人因工程分析報告
════════════════════════════════════════
分析時間: {timestamp}

【評估參數設定】
├─ 分析側: {side}
├─ 負重: {load_weight} kg
└─ 握持品質: {coupling_text}

【關節角度測量值】
┌────────┬──────────┬────────┐
│ 部位   │ 角度     │ 分數   │
├────────┼──────────┼────────┤
│ 頸部   │ {fmt_angle('neck'):>8} │ {details.get('neck_score', '--'):>6} │
│ 軀幹   │ {fmt_angle('trunk'):>8} │ {details.get('trunk_score', '--'):>6} │
│ 上臂   │ {fmt_angle('upper_arm'):>8} │ {details.get('upper_arm_score', '--'):>6} │
│ 前臂   │ {fmt_angle('forearm'):>8} │ {details.get('forearm_score', '--'):>6} │
│ 手腕   │ {fmt_angle('wrist'):>8} │ {details.get('wrist_score', '--'):>6} │
│ 腿部   │ {fmt_angle('leg'):>8} │ {details.get('leg_score', '--'):>6} │
└────────┴──────────┴────────┘

【REBA 評分計算】
┌─ Group A (身體) ─────────────────────┐
│  姿勢分數 A: {details.get('posture_score_a', '--')}
│  負荷分數:   {details.get('load_score', '--')}
│  ► Score A:  {details.get('score_a', '--')}
└──────────────────────────────────────┘
┌─ Group B (手臂) ─────────────────────┐
│  姿勢分數 B: {details.get('posture_score_b', '--')}
│  握持分數:   {details.get('coupling_score', '--')}
│  ► Score B:  {details.get('score_b', '--')}
└──────────────────────────────────────┘
┌─ 最終計算 ───────────────────────────┐
│  Score C (A×B): {details.get('score_c', '--')}
│  活動分數:      {details.get('activity_score', '--')}
│  ► 最終分數:    {details.get('final_score', '--')}
└──────────────────────────────────────┘

【評估結果】
═══════════════════════════════════════
  REBA 總分: {reba_score}
  風險等級: {risk_text}
═══════════════════════════════════════
  {risk_desc}
════════════════════════════════════════
"""

        # 複製到剪貼板
        clipboard = QApplication.clipboard()
        clipboard.setText(text_data)

        self.log("資料已複製到剪貼板")
        self.statusBar().showMessage("資料已複製", 2000)

    def save_csv(self):
        """保存CSV檔案"""
        if self.data_logger.get_buffer_size() == 0:
            self.log("沒有資料可保存")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存CSV檔案",
            f"reba_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV檔案 (*.csv)"
        )

        if file_path:
            # 確保有.csv副檔名
            if not file_path.endswith('.csv'):
                file_path += '.csv'

            # 使用指定的檔案名稱
            filename = Path(file_path).stem
            self.data_logger.output_dir = Path(file_path).parent
            saved_path = self.data_logger.save_to_csv(filename)

            self.log(f"已保存CSV: {Path(saved_path).name}")

    def save_json(self):
        """保存JSON檔案"""
        if self.data_logger.get_buffer_size() == 0:
            self.log("沒有資料可保存")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存JSON檔案",
            f"reba_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON檔案 (*.json)"
        )

        if file_path:
            # 確保有.json副檔名
            if not file_path.endswith('.json'):
                file_path += '.json'

            # 使用指定的檔案名稱
            filename = Path(file_path).stem
            self.data_logger.output_dir = Path(file_path).parent
            saved_path = self.data_logger.save_to_json(filename)

            self.log(f"已保存JSON: {Path(saved_path).name}")

    def replay_video(self):
        """重播影片"""
        if self.video_thread and self.video_thread.video_source is not None:
            self.video_thread.seek_frame(0)
            if self.video_thread.paused:
                self.video_thread.resume()
                self.btn_pause.setText("暫停")
            self.log("重播影片")

    def update_progress(self, current_frame: int, total_frames: int):
        """更新進度條和時間顯示"""
        if total_frames > 0:
            # 更新進度條（避免觸發信號）
            self.progress_slider.blockSignals(True)
            self.progress_slider.setMaximum(total_frames)
            self.progress_slider.setValue(current_frame)
            self.progress_slider.blockSignals(False)

            # 假設影片為30fps，計算時間
            fps = 30.0
            current_seconds = int(current_frame / fps)
            total_seconds = int(total_frames / fps)

            # 格式化時間顯示
            current_time = f"{current_seconds // 60:02d}:{current_seconds % 60:02d}"
            total_time = f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"

            self.label_time_current.setText(current_time)
            self.label_time_total.setText(total_time)

    def slider_pressed(self):
        """進度條按下時暫停影片並記錄狀態"""
        self.is_slider_dragging = True
        if self.video_thread:
            # 記錄拖曳前的暫停狀態
            self.was_paused_before_drag = self.video_thread.paused
            if not self.video_thread.paused:
                self.video_thread.pause()

    def slider_moved(self, value):
        """進度條拖曳時的節流預覽"""
        if not self.is_slider_dragging:
            return

        # 記錄待執行的幀位置
        self.pending_seek_frame = value

        # 更新時間顯示（即時響應）
        if self.video_thread and self.video_thread.total_frames > 0:
            fps = 30.0
            current_seconds = int(value / fps)
            self.label_time_current.setText(
                f"{current_seconds // 60:02d}:{current_seconds % 60:02d}")

        # 節流：如果計時器未運行，啟動它
        if not self.slider_throttle_timer.isActive():
            self.slider_throttle_timer.start(UIConfig.SLIDER_DRAG_THROTTLE_MS)

    def _execute_throttled_seek(self):
        """執行節流後的跳轉"""
        if self.video_thread and self.pending_seek_frame >= 0:
            self.video_thread.seek_frame(self.pending_seek_frame)

    def slider_released(self):
        """進度條釋放時跳轉到最終位置"""
        self.is_slider_dragging = False
        self.slider_throttle_timer.stop()  # 停止節流計時器

        if self.video_thread:
            # 跳轉到最終位置
            target_frame = self.progress_slider.value()
            self.video_thread.seek_frame(target_frame)
            self.pending_seek_frame = -1

            # 如果拖曳前不是暫停狀態，恢復播放
            if not self.was_paused_before_drag:
                self.video_thread.resume()

    def update_display_options(self):
        """更新顯示選項"""
        if self.video_thread:
            show_lines = self.check_angle_lines.isChecked()
            show_values = self.check_angle_values.isChecked()
            self.video_thread.set_display_options(show_lines, show_values)

    def _on_parameters_changed(self):
        """參數變更時更新 video thread"""
        if self.video_thread and self.video_thread.isRunning():
            side = self.combo_side.currentText()
            load_weight = self.spin_load.value()
            force_coupling = self.combo_coupling.currentText()
            self.video_thread.set_parameters(side, load_weight, force_coupling)

    def showEvent(self, event):
        """視窗顯示事件 - 初始化欄位寬度"""
        super().showEvent(event)
        # 視窗顯示後更新欄位寬度（此時 viewport 有正確寬度）
        self._update_table_column_widths()

    def resizeEvent(self, event):
        """視窗調整大小事件 - 更新欄位寬度"""
        super().resizeEvent(event)
        # 視窗大小改變時重新計算欄位寬度
        self._update_table_column_widths()

    def eventFilter(self, obj, event):
        """事件過濾器 - 處理表格複製"""
        from PySide6.QtCore import QEvent
        if obj == self.angle_table and event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                self._copy_table_selection()
                return True  # 事件已處理
        return super().eventFilter(obj, event)

    def _copy_table_selection(self):
        """複製表格選取的儲存格（支援多欄位）"""
        selection = self.angle_table.selectedRanges()
        if not selection:
            return

        # 收集所有選取的儲存格
        rows_data = {}
        for sel_range in selection:
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                if row not in rows_data:
                    rows_data[row] = {}
                for col in range(sel_range.leftColumn(), sel_range.rightColumn() + 1):
                    item = self.angle_table.item(row, col)
                    text = item.text() if item else ''
                    rows_data[row][col] = text

        # 組合成 TSV 格式（Tab 分隔，可直接貼到 Excel）
        lines = []
        for row in sorted(rows_data.keys()):
            cols = rows_data[row]
            min_col = min(cols.keys())
            max_col = max(cols.keys())
            row_texts = []
            for col in range(min_col, max_col + 1):
                row_texts.append(cols.get(col, ''))
            lines.append('\t'.join(row_texts))

        # 複製到剪貼簿
        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(lines))

    def closeEvent(self, event):
        """視窗關閉事件"""
        # 停止處理
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop()
            self.video_thread.wait()

        event.accept()


def main():
    """主程式入口"""
    app = QApplication(sys.argv)

    # 設置應用程式樣式
    app.setStyle('Fusion')

    # 創建主視窗
    window = MainWindow()
    window.show()

    # 執行應用程式
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
