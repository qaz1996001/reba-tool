#!/usr/bin/env python3
"""
資料橋接 (Data Bridge)
包裝 DataLogger 的匯出/統計功能。
提供日誌訊息列表給 QML。
"""

from datetime import datetime
from PySide6.QtCore import QObject, Property, Signal, Slot


class DataBridge(QObject):
    """QML↔DataLogger 橋接"""

    recordCountChanged = Signal()
    logMessagesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._controller = None
        self._log_messages = []

    def set_controller(self, controller):
        """設定 VideoController 引用"""
        self._controller = controller

    # ========== Properties ==========

    @Property(int, notify=recordCountChanged)
    def recordCount(self):
        if self._controller:
            return self._controller.data_logger.get_buffer_size()
        return 0

    @Property(list, notify=logMessagesChanged)
    def logMessages(self):
        return self._log_messages

    # ========== Slots ==========

    @Slot(str)
    def log(self, message):
        """添加日誌訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_messages.append(f"[{timestamp}] {message}")
        self.logMessagesChanged.emit()

    @Slot(str, result=str)
    def saveCsv(self, path):
        """保存 CSV 檔案"""
        if not self._controller:
            return ""
        if self._controller.data_logger.get_buffer_size() == 0:
            self.log("沒有資料可保存")
            return ""
        saved = self._controller.save_csv(path)
        if saved:
            self.log(f"已保存CSV: {saved}")
        return saved

    @Slot(str, result=str)
    def saveJson(self, path):
        """保存 JSON 檔案"""
        if not self._controller:
            return ""
        if self._controller.data_logger.get_buffer_size() == 0:
            self.log("沒有資料可保存")
            return ""
        saved = self._controller.save_json(path)
        if saved:
            self.log(f"已保存JSON: {saved}")
        return saved

    @Slot(result=str)
    def getCopyText(self):
        """取得複製用文字"""
        if not self._controller:
            return ""
        return self._controller.get_copy_text()

    def update_record_count(self):
        """通知 QML 記錄數已變更"""
        self.recordCountChanged.emit()
