#!/usr/bin/env python3
"""
Table C 對話框 (Table C Dialog)
顯示 REBA Score A 與 Score B 的對照表。
使用 REBAScorer.TABLE_C 取代重複的 TABLE_C_DATA。
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from reba_scorer import REBAScorer


class TableCDialog(QDialog):
    """Table C 對話框 - 顯示 REBA Score A 與 Score B 的對照表"""

    # 直接使用 REBAScorer 的 TABLE_C
    TABLE_C_DATA = REBAScorer.TABLE_C

    def __init__(self, parent=None, score_a=None, score_b=None):
        super().__init__(parent)
        self.score_a = score_a
        self.score_b = score_b
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("REBA Table C - Score A \u00d7 Score B \u2192 Score C")
        self.setMinimumSize(600, 450)

        layout = QVBoxLayout()
        self.setLayout(layout)

        title_label = QLabel("Table C: \u7531 Score A (\u5217) \u8207 Score B (\u6b04) \u67e5\u8a62 Score C")
        title_label.setFont(QFont("Microsoft JhengHei", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 建立表格 (13行 x 13列，包含標題)
        self.table = QTableWidget(13, 13)
        self.table.setFont(QFont("Microsoft JhengHei", 10))
        layout.addWidget(self.table)

        # 設定標題
        self.table.setHorizontalHeaderLabels(['Score B \u2192'] + [str(i) for i in range(1, 13)])
        self.table.setVerticalHeaderLabels(['Score A \u2193'] + [str(i) for i in range(1, 13)])

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
            header_item = QTableWidgetItem(str(row))
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setBackground(QColor('#d0d0d0'))
            header_item.setFont(QFont("Microsoft JhengHei", 10, QFont.Bold))
            self.table.setItem(row, 0, header_item)

            for col in range(1, 13):
                value = self.TABLE_C_DATA[row - 1][col - 1]
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                color = self._get_score_color(value)
                item.setBackground(QColor(color))
                self.table.setItem(row, col, item)

        if self.score_a is not None and self.score_b is not None:
            self._highlight_current_score()

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)

        # 圖例
        legend_layout = QHBoxLayout()
        layout.addLayout(legend_layout)
        legend_label = QLabel("\u5716\u4f8b:")
        legend_label.setFont(QFont("Microsoft JhengHei", 10))
        legend_layout.addWidget(legend_label)

        legend_items = [
            ("#78c850", "1 \u53ef\u5ffd\u7565"),
            ("#a8d08d", "2-3 \u4f4e\u98a8\u96aa"),
            ("#ffeb3b", "4-7 \u4e2d\u98a8\u96aa"),
            ("#ff9800", "8-10 \u9ad8\u98a8\u96aa"),
            ("#f44336", "11-12 \u6975\u9ad8\u98a8\u96aa"),
        ]
        for color, text in legend_items:
            lbl = QLabel(f"  \u25a0 {text}")
            lbl.setFont(QFont("Microsoft JhengHei", 9))
            lbl.setStyleSheet(f"color: {color};")
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()

        btn_close = QPushButton("\u95dc\u9589")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def _get_score_color(self, score):
        """根據分數取得對應顏色"""
        if score == 1:
            return "#78c850"
        elif score <= 3:
            return "#a8d08d"
        elif score <= 7:
            return "#ffeb3b"
        elif score <= 10:
            return "#ff9800"
        else:
            return "#f44336"

    def _highlight_current_score(self):
        """強調當前 Score A / Score B 對應的儲存格"""
        if self.score_a is None or self.score_b is None:
            return

        score_a = max(1, min(12, self.score_a))
        score_b = max(1, min(12, self.score_b))

        light_highlight = QColor('#b3d9ff')
        header_highlight = QColor('#4a90d9')

        # 強調整行
        for col in range(13):
            item = self.table.item(score_a, col)
            if item:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                if col == 0:
                    item.setBackground(header_highlight)
                    item.setForeground(QColor('white'))
                else:
                    item.setBackground(light_highlight)

        # 強調整欄
        for row in range(13):
            item = self.table.item(row, score_b)
            if item:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                if row == 0:
                    item.setBackground(header_highlight)
                    item.setForeground(QColor('white'))
                elif row != score_a:
                    item.setBackground(light_highlight)

        # 交叉點
        target_item = self.table.item(score_a, score_b)
        if target_item:
            target_item.setBackground(QColor('#1565c0'))
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
                        item.setBackground(QColor(self._get_score_color(value)))

        self._highlight_current_score()
