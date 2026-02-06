#!/usr/bin/env python3
"""
分數表格模型 (Score Table Model)
對應現有 main_window.py 的 17x5 表格結構。
QAbstractTableModel 讓 QML TableView 直接使用。
"""

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Property, Signal
from PySide6.QtGui import QColor


class ScoreTableModel(QAbstractTableModel):
    """17 行 x 5 欄角度/分數明細表"""

    # Custom roles
    DisplayRole = Qt.DisplayRole
    BackgroundColorRole = Qt.UserRole + 1
    FontBoldRole = Qt.UserRole + 2
    SectionRole = Qt.UserRole + 3
    TextAlignRole = Qt.UserRole + 4

    scoreDataChanged = Signal()

    # 表格結構定義（與 main_window.py 一致）
    TABLE_STRUCTURE = [
        # (left_name, left_key, right_name, right_key, is_header, is_highlight)
        ('部位', '', '角度', '', True, False),
        ('頸部', 'neck', '', 'neck_score', False, False),
        ('軀幹', 'trunk', '', 'trunk_score', False, False),
        ('上臂', 'upper_arm', '', 'upper_arm_score', False, False),
        ('前臂', 'forearm', '', 'forearm_score', False, False),
        ('手腕', 'wrist', '', 'wrist_score', False, False),
        ('腿部', 'leg', '', 'leg_score', False, False),
        ('REBA評分', '', '', '', True, False),
        ('GroupA', '', 'GroupB', '', True, False),
        ('頸部', 'neck_score', '上臂', 'upper_arm_score', False, False),
        ('軀幹', 'trunk_score', '前臂', 'forearm_score', False, False),
        ('腿部', 'leg_score', '手腕', 'wrist_score', False, False),
        ('負荷', 'load_score', '握持', 'coupling_score', False, False),
        ('姿勢A', 'posture_score_a', '姿勢B', 'posture_score_b', False, False),
        ('Score A', 'score_a', 'Score B', 'score_b', False, True),
        ('Score C', 'score_c', '活動', 'activity_score', False, False),
        ('REBA總分', 'final_score', '', '', False, True),
    ]

    # 角度 key 集合
    ANGLE_KEYS = {'neck', 'trunk', 'upper_arm', 'forearm', 'wrist', 'leg'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angles = {}
        self._details = {}

    def roleNames(self):
        return {
            Qt.DisplayRole: b"display",
            self.BackgroundColorRole: b"bgColor",
            self.FontBoldRole: b"fontBold",
            self.SectionRole: b"section",
            self.TextAlignRole: b"textAlign",
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self.TABLE_STRUCTURE)

    def columnCount(self, parent=QModelIndex()):
        return 5

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        left_name, left_key, right_name, right_key, is_header, is_highlight = self.TABLE_STRUCTURE[row]

        # === 第一行標題 ===
        if row == 0:
            headers = ['部位', '角度', '', '  ', '分數']
            if role == Qt.DisplayRole:
                return headers[col] if col < len(headers) else ""
            if role == self.BackgroundColorRole:
                return "#1a2235"
            if role == self.FontBoldRole:
                return True
            if role == self.TextAlignRole:
                return "center"
            return None

        # === 區段標題行 ===
        if is_header:
            if role == self.BackgroundColorRole:
                return "#1a2235" if right_name else "#151b2c"
            if role == self.FontBoldRole:
                return True
            if role == self.TextAlignRole:
                return "center"
            if role == Qt.DisplayRole:
                if right_name:
                    # 雙標題行: GroupA | | | GroupB |
                    return [left_name, '', '', right_name, ''][col] if col < 5 else ""
                else:
                    # 全跨行標題
                    return left_name if col == 0 else ""
            if role == self.SectionRole:
                return "span" if not right_name else "split"
            return None

        # === 資料行 ===
        bg_color = None
        if is_highlight:
            bg_color = "#0a2a3a"
        if left_name == 'REBA總分':
            bg_color = "#2a1525"

        if role == self.BackgroundColorRole:
            return bg_color or ""

        if role == self.FontBoldRole:
            return is_highlight or (left_name == 'REBA總分')

        if role == self.TextAlignRole:
            if col in (0, 2, 3):
                return "center"
            return "right"

        if role == Qt.DisplayRole:
            if col == 0:
                return left_name
            elif col == 1:
                return self._get_value(left_key)
            elif col == 2:
                return ""
            elif col == 3:
                return right_name
            elif col == 4:
                return self._get_value(right_key) if right_key else ""

        return None

    def _get_value(self, key):
        """取得角度或分數值的顯示文字"""
        if not key:
            return ""

        if key in self.ANGLE_KEYS:
            val = self._angles.get(key)
            if val is not None:
                return f"{val:.1f}\u00b0"
            return "--"
        else:
            val = self._details.get(key)
            if val is not None:
                return str(val)
            return "--"

    def update_data(self, angles, details):
        """更新角度和分數資料"""
        self._angles = angles or {}
        self._details = details or {}
        self.beginResetModel()
        self.endResetModel()
        self.scoreDataChanged.emit()
