#!/usr/bin/env python3
"""
REBA 分數橋接 (REBA Bridge)
暴露 REBA 分數、風險等級、顏色等為 QML Property。
由 VideoBridge.frameProcessed 觸發更新。
"""

from PySide6.QtCore import QObject, Property, Signal

from reba_scorer import REBAScorer


class RebaBridge(QObject):
    """QML↔REBA 分數橋接"""

    scoreChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scorer = REBAScorer()

        # 當前分數資料
        self._reba_score = 0
        self._risk_level = ""
        self._risk_level_zh = ""
        self._risk_color = "#FFFFFF"
        self._risk_description = ""

        # 各部位分數
        self._neck_score = 0
        self._trunk_score = 0
        self._leg_score = 0
        self._upper_arm_score = 0
        self._forearm_score = 0
        self._wrist_score = 0

        # 表格分數
        self._posture_score_a = 0
        self._posture_score_b = 0
        self._load_score = 0
        self._coupling_score = 0
        self._score_a = 0
        self._score_b = 0
        self._score_c = 0
        self._activity_score = 0
        self._final_score = 0

        # 角度
        self._angles = {}

    # ========== 分數 Properties ==========

    @Property(int, notify=scoreChanged)
    def rebaScore(self):
        return self._reba_score

    @Property(str, notify=scoreChanged)
    def riskLevel(self):
        return self._risk_level

    @Property(str, notify=scoreChanged)
    def riskLevelZh(self):
        return self._risk_level_zh

    @Property(str, notify=scoreChanged)
    def riskColor(self):
        return self._risk_color

    @Property(str, notify=scoreChanged)
    def riskDescription(self):
        return self._risk_description

    # 各部位分數
    @Property(int, notify=scoreChanged)
    def neckScore(self):
        return self._neck_score

    @Property(int, notify=scoreChanged)
    def trunkScore(self):
        return self._trunk_score

    @Property(int, notify=scoreChanged)
    def legScore(self):
        return self._leg_score

    @Property(int, notify=scoreChanged)
    def upperArmScore(self):
        return self._upper_arm_score

    @Property(int, notify=scoreChanged)
    def forearmScore(self):
        return self._forearm_score

    @Property(int, notify=scoreChanged)
    def wristScore(self):
        return self._wrist_score

    # 表格分數
    @Property(int, notify=scoreChanged)
    def postureScoreA(self):
        return self._posture_score_a

    @Property(int, notify=scoreChanged)
    def postureScoreB(self):
        return self._posture_score_b

    @Property(int, notify=scoreChanged)
    def loadScore(self):
        return self._load_score

    @Property(int, notify=scoreChanged)
    def couplingScore(self):
        return self._coupling_score

    @Property(int, notify=scoreChanged)
    def scoreA(self):
        return self._score_a

    @Property(int, notify=scoreChanged)
    def scoreB(self):
        return self._score_b

    @Property(int, notify=scoreChanged)
    def scoreC(self):
        return self._score_c

    @Property(int, notify=scoreChanged)
    def activityScore(self):
        return self._activity_score

    @Property(int, notify=scoreChanged)
    def finalScore(self):
        return self._final_score

    # 角度
    @Property(float, notify=scoreChanged)
    def neckAngle(self):
        return self._angles.get('neck', 0.0)

    @Property(float, notify=scoreChanged)
    def trunkAngle(self):
        return self._angles.get('trunk', 0.0)

    @Property(float, notify=scoreChanged)
    def upperArmAngle(self):
        return self._angles.get('upper_arm', 0.0)

    @Property(float, notify=scoreChanged)
    def forearmAngle(self):
        return self._angles.get('forearm', 0.0)

    @Property(float, notify=scoreChanged)
    def wristAngle(self):
        return self._angles.get('wrist', 0.0)

    @Property(float, notify=scoreChanged)
    def legAngle(self):
        return self._angles.get('leg', 0.0)

    # ========== 更新方法 ==========

    def update_from_frame(self, frame, angles, reba_score, risk_level, fps, details):
        """
        由 VideoBridge.frameProcessed 信號呼叫

        Args:
            frame: OpenCV frame (不使用)
            angles: 角度字典
            reba_score: REBA 分數
            risk_level: 風險等級字串
            fps: FPS (不使用)
            details: 詳細分數字典
        """
        self._angles = angles or {}
        self._reba_score = reba_score
        self._risk_level = risk_level
        self._risk_level_zh = self._scorer.get_risk_name_zh(risk_level) if risk_level else ""
        self._risk_color = self._scorer.get_risk_color(risk_level) if risk_level else "#FFFFFF"
        self._risk_description = self._scorer.get_risk_description(risk_level) if risk_level else ""

        if details:
            self._neck_score = details.get('neck_score', 0)
            self._trunk_score = details.get('trunk_score', 0)
            self._leg_score = details.get('leg_score', 0)
            self._upper_arm_score = details.get('upper_arm_score', 0)
            self._forearm_score = details.get('forearm_score', 0)
            self._wrist_score = details.get('wrist_score', 0)
            self._posture_score_a = details.get('posture_score_a', 0)
            self._posture_score_b = details.get('posture_score_b', 0)
            self._load_score = details.get('load_score', 0)
            self._coupling_score = details.get('coupling_score', 0)
            self._score_a = details.get('score_a', 0)
            self._score_b = details.get('score_b', 0)
            self._score_c = details.get('score_c', 0)
            self._activity_score = details.get('activity_score', 0)
            self._final_score = details.get('final_score', 0)

        self.scoreChanged.emit()
