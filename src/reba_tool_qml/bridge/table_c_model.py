#!/usr/bin/env python3
"""
Table C 模型 (Table C Model)
12x12 Table C 資料 + 顏色 + highlight。
QAbstractTableModel 讓 QML TableView 直接使用。
"""

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Property, Signal, Slot
from PySide6.QtGui import QColor

from reba_scorer import REBAScorer


class TableCModel(QAbstractTableModel):
    """12x12 REBA Table C 查詢表"""

    BackgroundColorRole = Qt.UserRole + 1
    FontBoldRole = Qt.UserRole + 2
    FontSizeRole = Qt.UserRole + 3
    ForegroundColorRole = Qt.UserRole + 4

    scoreAChanged = Signal()
    scoreBChanged = Signal()

    # 直接使用 REBAScorer 的 TABLE_C
    TABLE_C_DATA = REBAScorer.TABLE_C

    def __init__(self, parent=None):
        super().__init__(parent)
        self._score_a = None
        self._score_b = None

    def roleNames(self):
        return {
            Qt.DisplayRole: b"display",
            self.BackgroundColorRole: b"bgColor",
            self.FontBoldRole: b"fontBold",
            self.FontSizeRole: b"fontSize",
            self.ForegroundColorRole: b"fgColor",
        }

    def rowCount(self, parent=QModelIndex()):
        return 13  # 1 header + 12 data

    def columnCount(self, parent=QModelIndex()):
        return 13  # 1 header + 12 data

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        is_header_row = (row == 0)
        is_header_col = (col == 0)
        is_highlighted_row = (self._score_a is not None and row == self._score_a)
        is_highlighted_col = (self._score_b is not None and col == self._score_b)
        is_intersection = is_highlighted_row and is_highlighted_col

        # === Display ===
        if role == Qt.DisplayRole:
            if row == 0 and col == 0:
                return "Score A \\ B"
            if row == 0:
                return str(col)
            if col == 0:
                return str(row)
            return str(self.TABLE_C_DATA[row - 1][col - 1])

        # === Background Color ===
        if role == self.BackgroundColorRole:
            if is_intersection and not is_header_row and not is_header_col:
                return "#00f2ff"
            if is_header_row or is_header_col:
                if is_intersection:
                    return "#0a3d42"
                if (is_header_row and is_highlighted_col) or (is_header_col and is_highlighted_row):
                    return "#0a3d42"
                return "#1a2235"
            if is_highlighted_row or is_highlighted_col:
                return "#0a2a3a"
            # 一般資料格顏色
            value = self.TABLE_C_DATA[row - 1][col - 1]
            return self._get_score_color(value)

        # === Foreground Color ===
        if role == self.ForegroundColorRole:
            if is_intersection and not is_header_row and not is_header_col:
                return "#0a0f1d"
            if (is_header_row and is_highlighted_col) or (is_header_col and is_highlighted_row):
                return "#00f2ff"
            return "#e2e8f0"

        # === Font Bold ===
        if role == self.FontBoldRole:
            if is_header_row or is_header_col:
                return True
            return is_highlighted_row or is_highlighted_col

        # === Font Size ===
        if role == self.FontSizeRole:
            if is_intersection and not is_header_row and not is_header_col:
                return 14
            return 10

        return None

    @staticmethod
    def _get_score_color(score):
        """根據分數取得對應顏色"""
        if score == 1:
            return "#10b981"
        elif score <= 3:
            return "#34d399"
        elif score <= 7:
            return "#fbbf24"
        elif score <= 10:
            return "#f43f5e"
        else:
            return "#ff0000"

    # ========== QML 可呼叫的 Cell 資料 Slots ==========

    @Slot(int, int, result=str)
    def cellText(self, row, col):
        """QML 用：取得 cell 顯示文字"""
        idx = self.index(row, col)
        v = self.data(idx, Qt.DisplayRole)
        return v if v else ""

    @Slot(int, int, result=str)
    def cellBgColor(self, row, col):
        """QML 用：取得 cell 背景色"""
        idx = self.index(row, col)
        v = self.data(idx, self.BackgroundColorRole)
        return v if v else ""

    @Slot(int, int, result=str)
    def cellFgColor(self, row, col):
        """QML 用：取得 cell 文字色"""
        idx = self.index(row, col)
        v = self.data(idx, self.ForegroundColorRole)
        return v if v else ""

    @Slot(int, int, result=bool)
    def cellBold(self, row, col):
        """QML 用：取得 cell 是否粗體"""
        idx = self.index(row, col)
        v = self.data(idx, self.FontBoldRole)
        return bool(v) if v else False

    @Slot(int, int, result=int)
    def cellFontSize(self, row, col):
        """QML 用：取得 cell 字號"""
        idx = self.index(row, col)
        v = self.data(idx, self.FontSizeRole)
        return v if v else 10

    # ========== Score Properties ==========

    @Property(int, notify=scoreAChanged)
    def scoreA(self):
        return self._score_a if self._score_a is not None else 0

    @Property(int, notify=scoreBChanged)
    def scoreB(self):
        return self._score_b if self._score_b is not None else 0

    # ========== Slots ==========

    @Slot(int, int)
    def updateScores(self, score_a, score_b):
        """更新分數並重新高亮"""
        sa = max(1, min(12, score_a)) if score_a else None
        sb = max(1, min(12, score_b)) if score_b else None
        self._score_a = sa
        self._score_b = sb
        self.beginResetModel()
        self.endResetModel()
        self.scoreAChanged.emit()
        self.scoreBChanged.emit()
