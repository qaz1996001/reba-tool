#!/usr/bin/env python3
"""
ViewModel 協調者 (Video Controller)
UI 層唯一需要互動的對象，零 Qt 依賴。
協調 EventBus, ProcessingConfig, VideoPipeline, DataLogger。
"""

from datetime import datetime
from typing import Optional
from pathlib import Path

from event_bus import EventBus
from processing_config import ProcessingConfig
from video_pipeline import VideoPipeline
from data_logger import DataLogger
from reba_scorer import REBAScorer


class VideoController:
    """ViewModel - 協調管線、資料、事件"""

    def __init__(self):
        self._event_bus = EventBus()
        self._config = ProcessingConfig()
        self._pipeline = VideoPipeline(self._event_bus, self._config)
        self._data_logger = DataLogger()
        self._reba_scorer = REBAScorer()

        self._is_processing = False
        self._frame_count = 0
        self._data_locked = False
        self._locked_data = None

    # ========== 屬性 ==========

    @property
    def event_bus(self) -> EventBus:
        """UI 用來註冊回調"""
        return self._event_bus

    @property
    def pipeline(self) -> VideoPipeline:
        return self._pipeline

    @property
    def data_logger(self) -> DataLogger:
        return self._data_logger

    @property
    def reba_scorer(self) -> REBAScorer:
        return self._reba_scorer

    @property
    def is_processing(self) -> bool:
        return self._is_processing

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def data_locked(self) -> bool:
        return self._data_locked

    @property
    def locked_data(self) -> Optional[dict]:
        return self._locked_data

    # ========== 控制方法 ==========

    def start(self, source, side, load_weight, force_coupling,
              show_lines, show_values, show_skeleton=True):
        """
        準備管線以便啟動。呼叫端負責建立 worker thread 並呼叫 pipeline.run()。

        Args:
            source: 影片路徑或 None (攝影機)
            side: 分析側邊
            load_weight: 負荷重量
            force_coupling: 握持品質
            show_lines: 是否顯示角度線
            show_values: 是否顯示角度數值
            show_skeleton: 是否顯示 MediaPipe 骨架
        """
        self._pipeline = VideoPipeline(self._event_bus, self._config)
        self._pipeline.set_source(source)
        self._pipeline.set_parameters(side, load_weight, force_coupling)
        self._pipeline.set_display_options(show_lines, show_values, show_skeleton)

        self._data_logger.clear_buffer()
        self._frame_count = 0
        self._is_processing = True

    def stop(self):
        """停止管線"""
        if self._pipeline:
            self._pipeline.stop()
        self._is_processing = False

    def pause(self):
        """暫停管線"""
        if self._pipeline:
            self._pipeline.pause()

    def resume(self):
        """恢復管線"""
        if self._pipeline:
            self._pipeline.resume()

    def seek(self, frame_number: int):
        """跳轉到指定幀"""
        if self._pipeline:
            self._pipeline.seek_frame(frame_number)

    def set_parameters(self, side: str, load_weight: float, force_coupling: str):
        """即時更新評估參數"""
        if self._pipeline:
            self._pipeline.set_parameters(side, load_weight, force_coupling)

    def set_display_options(self, show_lines: bool, show_values: bool, show_skeleton: bool = True):
        """即時更新顯示選項"""
        if self._pipeline:
            self._pipeline.set_display_options(show_lines, show_values, show_skeleton)

    # ========== 資料方法 ==========

    def toggle_data_lock(self, locked: bool):
        """切換資料鎖定狀態"""
        self._data_locked = locked

    def record_frame(self, frame, angles, reba_score, risk_level, fps, details):
        """
        記錄幀資料並更新鎖定資料。由 UI 層在收到 frame_processed 時呼叫。
        """
        import time
        self._frame_count += 1

        if not self._data_locked:
            self._locked_data = {
                'frame': frame,
                'angles': angles,
                'reba_score': reba_score,
                'risk_level': risk_level,
                'details': details,
                'fps': fps
            }

        timestamp = time.time()
        self._data_logger.add_frame_data(
            self._frame_count,
            timestamp,
            angles,
            reba_score,
            risk_level
        )

    def get_copy_text(self) -> str:
        """
        格式化剪貼板文字（不碰 Qt clipboard）

        Returns:
            格式化的報告文字
        """
        if self._locked_data is None:
            return ""

        data = self._locked_data
        angles = data['angles']
        details = data.get('details', {})
        reba_score = data['reba_score']
        risk_level = data['risk_level']

        risk_labels = {
            'negligible': '可忽略',
            'low': '低風險',
            'medium': '中等風險',
            'high': '高風險',
            'very_high': '極高風險'
        }
        risk_text = risk_labels.get(risk_level, risk_level)
        risk_desc = self._reba_scorer.get_risk_description(risk_level)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def fmt_angle(key):
            val = angles.get(key)
            return f"{val:.1f}\u00b0" if val is not None else "--"

        return f"""\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
          REBA \u4eba\u56e0\u5de5\u7a0b\u5206\u6790\u5831\u544a
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
\u5206\u6790\u6642\u9593: {timestamp}

\u3010\u95dc\u7bc0\u89d2\u5ea6\u6e2c\u91cf\u5024\u3011
\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502 \u90e8\u4f4d   \u2502 \u89d2\u5ea6     \u2502 \u5206\u6578   \u2502
\u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524
\u2502 \u9838\u90e8   \u2502 {fmt_angle('neck'):>8} \u2502 {details.get('neck_score', '--'):>6} \u2502
\u2502 \u8ec0\u5e79   \u2502 {fmt_angle('trunk'):>8} \u2502 {details.get('trunk_score', '--'):>6} \u2502
\u2502 \u4e0a\u81c2   \u2502 {fmt_angle('upper_arm'):>8} \u2502 {details.get('upper_arm_score', '--'):>6} \u2502
\u2502 \u524d\u81c2   \u2502 {fmt_angle('forearm'):>8} \u2502 {details.get('forearm_score', '--'):>6} \u2502
\u2502 \u624b\u8155   \u2502 {fmt_angle('wrist'):>8} \u2502 {details.get('wrist_score', '--'):>6} \u2502
\u2502 \u8173\u90e8   \u2502 {fmt_angle('leg'):>8} \u2502 {details.get('leg_score', '--'):>6} \u2502
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518

\u3010REBA \u8a55\u5206\u8a08\u7b97\u3011
\u250c\u2500 Group A (\u8eab\u9ad4) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502  \u59ff\u52e2\u5206\u6578 A: {details.get('posture_score_a', '--')}
\u2502  \u8ca0\u8377\u5206\u6578:   {details.get('load_score', '--')}
\u2502  \u25ba Score A:  {details.get('score_a', '--')}
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
\u250c\u2500 Group B (\u624b\u81c2) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502  \u59ff\u52e2\u5206\u6578 B: {details.get('posture_score_b', '--')}
\u2502  \u63e1\u6301\u5206\u6578:   {details.get('coupling_score', '--')}
\u2502  \u25ba Score B:  {details.get('score_b', '--')}
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
\u250c\u2500 \u6700\u7d42\u8a08\u7b97 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502  Score C (A\u00d7B): {details.get('score_c', '--')}
\u2502  \u6d3b\u52d5\u5206\u6578:      {details.get('activity_score', '--')}
\u2502  \u25ba \u6700\u7d42\u5206\u6578:    {details.get('final_score', '--')}
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518

\u3010\u8a55\u4f30\u7d50\u679c\u3011
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
  REBA \u7e3d\u5206: {reba_score}
  \u98a8\u96aa\u7b49\u7d1a: {risk_text}
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
  {risk_desc}
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
"""

    def save_csv(self, filepath: str) -> str:
        """保存 CSV"""
        p = Path(filepath)
        self._data_logger.output_dir = p.parent
        return self._data_logger.save_to_csv(p.stem)

    def save_json(self, filepath: str) -> str:
        """保存 JSON"""
        p = Path(filepath)
        self._data_logger.output_dir = p.parent
        return self._data_logger.save_to_json(p.stem)

    def get_log_summary(self) -> str:
        """取得統計摘要文字"""
        stats = self._data_logger.get_statistics()
        if not stats:
            return "沒有統計資料"
        basic = stats.get('basic', {})
        return f"總幀數: {basic.get('total_frames', 0)}, 有效: {basic.get('valid_frames', 0)}"

    def on_processing_finished(self):
        """處理完成的回調"""
        self._is_processing = False
        if self._data_logger.get_buffer_size() > 0:
            self._data_logger.print_summary()
