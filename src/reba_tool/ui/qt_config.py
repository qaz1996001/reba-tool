#!/usr/bin/env python3
"""
Qt 專用 UI 配置 (Qt-Specific UI Configuration)
只含依賴 PySide6 的參數：視窗幾何、Widget 字體、樣式等。
"""

from PySide6.QtGui import QFont


class QtConfig:
    """Qt 專用 UI 參數"""

    # ========== 視窗設定 ==========
    WINDOW_X = 100
    WINDOW_Y = 100
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900

    # ========== 影片顯示區設定 ==========
    VIDEO_LABEL_MIN_WIDTH = 600
    VIDEO_LABEL_MIN_HEIGHT = 450
    VIDEO_LABEL_BORDER_STYLE = "border: 2px solid black; background-color: #2b2b2b;"

    # ========== 字體設定 ==========
    FONT_FAMILY = "Microsoft YaHei"

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
    TABLE_ROW_HEIGHT = 28
    TABLE_HEADER_HEIGHT = 32
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

    # ========== 元件尺寸 ==========
    LOG_TEXT_MAX_HEIGHT = 150

    # ========== 進度條拖曳設定 ==========
    SLIDER_DRAG_THROTTLE_MS = 150

    # ========== 字體取得方法 ==========

    @classmethod
    def _make_font(cls, size, bold):
        weight = QFont.Bold if bold else QFont.Normal
        return QFont(cls.FONT_FAMILY, size, weight)

    @classmethod
    def get_button_font(cls) -> QFont:
        return cls._make_font(cls.BUTTON_FONT_SIZE, cls.BUTTON_FONT_BOLD)

    @classmethod
    def get_groupbox_font(cls) -> QFont:
        return cls._make_font(cls.GROUPBOX_FONT_SIZE, cls.GROUPBOX_FONT_BOLD)

    @classmethod
    def get_combobox_font(cls) -> QFont:
        return cls._make_font(cls.COMBOBOX_FONT_SIZE, cls.COMBOBOX_FONT_BOLD)

    @classmethod
    def get_checkbox_font(cls) -> QFont:
        return cls._make_font(cls.CHECKBOX_FONT_SIZE, cls.CHECKBOX_FONT_BOLD)

    @classmethod
    def get_param_label_font(cls) -> QFont:
        return cls._make_font(cls.PARAM_LABEL_FONT_SIZE, cls.PARAM_LABEL_FONT_BOLD)

    @classmethod
    def get_angle_label_font(cls) -> QFont:
        return cls._make_font(cls.ANGLE_LABEL_FONT_SIZE, cls.ANGLE_LABEL_FONT_BOLD)

    @classmethod
    def get_reba_score_font(cls) -> QFont:
        return cls._make_font(cls.REBA_SCORE_FONT_SIZE, cls.REBA_SCORE_FONT_BOLD)

    @classmethod
    def get_risk_level_font(cls) -> QFont:
        return cls._make_font(cls.RISK_LEVEL_FONT_SIZE, cls.RISK_LEVEL_FONT_BOLD)

    @classmethod
    def get_risk_desc_font(cls) -> QFont:
        return cls._make_font(cls.RISK_DESC_FONT_SIZE, cls.RISK_DESC_FONT_BOLD)

    @classmethod
    def get_formula_header_font(cls) -> QFont:
        return cls._make_font(cls.FORMULA_HEADER_FONT_SIZE, cls.FORMULA_HEADER_FONT_BOLD)

    @classmethod
    def get_formula_detail_font(cls) -> QFont:
        return cls._make_font(cls.FORMULA_DETAIL_FONT_SIZE, cls.FORMULA_DETAIL_FONT_BOLD)

    @classmethod
    def get_formula_total_font(cls) -> QFont:
        return cls._make_font(cls.FORMULA_TOTAL_FONT_SIZE, cls.FORMULA_TOTAL_FONT_BOLD)

    @classmethod
    def get_stats_font(cls) -> QFont:
        return cls._make_font(cls.STATS_FONT_SIZE, cls.STATS_FONT_BOLD)

    @classmethod
    def get_time_label_font(cls) -> QFont:
        return cls._make_font(cls.TIME_LABEL_FONT_SIZE, cls.TIME_LABEL_FONT_BOLD)

    @classmethod
    def get_video_hint_font(cls) -> QFont:
        return cls._make_font(cls.VIDEO_HINT_FONT_SIZE, cls.VIDEO_HINT_FONT_BOLD)

    @classmethod
    def get_log_text_font(cls) -> QFont:
        return cls._make_font(cls.LOG_TEXT_FONT_SIZE, cls.LOG_TEXT_FONT_BOLD)
