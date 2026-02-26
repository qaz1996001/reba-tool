#!/usr/bin/env python3
"""
設定橋接 (Settings Bridge)
雙向綁定評估參數（side, loadWeight, coupling, 顯示選項）。
setter 變更時通知 VideoBridge 更新 VideoController。
"""

from PySide6.QtCore import QObject, Property, Signal, Slot


class SettingsBridge(QObject):
    """QML↔設定參數橋接"""

    sideChanged = Signal()
    loadWeightChanged = Signal()
    couplingChanged = Signal()
    showAngleLinesChanged = Signal()
    showAngleValuesChanged = Signal()
    showSkeletonChanged = Signal()
    dataLockedChanged = Signal()

    # 參數變更通知（VideoBridge 監聽此信號）
    parametersChanged = Signal(str, float, str)
    displayOptionsChanged = Signal(bool, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._side = "right"
        self._load_weight = 0.0
        self._coupling = "good"
        self._show_angle_lines = True
        self._show_angle_values = True
        self._show_skeleton = True
        self._data_locked = False

    # ========== Properties ==========

    @Property(str, notify=sideChanged)
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        if self._side != value:
            self._side = value
            self.sideChanged.emit()
            self.parametersChanged.emit(self._side, self._load_weight, self._coupling)

    @Property(float, notify=loadWeightChanged)
    def loadWeight(self):
        return self._load_weight

    @loadWeight.setter
    def loadWeight(self, value):
        if self._load_weight != value:
            self._load_weight = value
            self.loadWeightChanged.emit()
            self.parametersChanged.emit(self._side, self._load_weight, self._coupling)

    @Property(str, notify=couplingChanged)
    def coupling(self):
        return self._coupling

    @coupling.setter
    def coupling(self, value):
        if self._coupling != value:
            self._coupling = value
            self.couplingChanged.emit()
            self.parametersChanged.emit(self._side, self._load_weight, self._coupling)

    @Property(bool, notify=showAngleLinesChanged)
    def showAngleLines(self):
        return self._show_angle_lines

    @showAngleLines.setter
    def showAngleLines(self, value):
        if self._show_angle_lines != value:
            self._show_angle_lines = value
            self.showAngleLinesChanged.emit()
            self.displayOptionsChanged.emit(
                self._show_angle_lines, self._show_angle_values, self._show_skeleton)

    @Property(bool, notify=showAngleValuesChanged)
    def showAngleValues(self):
        return self._show_angle_values

    @showAngleValues.setter
    def showAngleValues(self, value):
        if self._show_angle_values != value:
            self._show_angle_values = value
            self.showAngleValuesChanged.emit()
            self.displayOptionsChanged.emit(
                self._show_angle_lines, self._show_angle_values, self._show_skeleton)

    @Property(bool, notify=showSkeletonChanged)
    def showSkeleton(self):
        return self._show_skeleton

    @showSkeleton.setter
    def showSkeleton(self, value):
        if self._show_skeleton != value:
            self._show_skeleton = value
            self.showSkeletonChanged.emit()
            self.displayOptionsChanged.emit(
                self._show_angle_lines, self._show_angle_values, self._show_skeleton)

    @Property(bool, notify=dataLockedChanged)
    def dataLocked(self):
        return self._data_locked

    @dataLocked.setter
    def dataLocked(self, value):
        if self._data_locked != value:
            self._data_locked = value
            self.dataLockedChanged.emit()

    # ========== Slots ==========

    @Slot(str)
    def setSide(self, value):
        self.side = value

    @Slot(float)
    def setLoadWeight(self, value):
        self.loadWeight = value

    @Slot(str)
    def setCoupling(self, value):
        self.coupling = value

    @Slot(bool)
    def setShowAngleLines(self, value):
        self.showAngleLines = value

    @Slot(bool)
    def setShowAngleValues(self, value):
        self.showAngleValues = value

    @Slot(bool)
    def setShowSkeleton(self, value):
        self.showSkeleton = value

    @Slot(bool)
    def setDataLocked(self, value):
        self.dataLocked = value
