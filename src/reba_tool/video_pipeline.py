#!/usr/bin/env python3
"""
影片處理管線 (Video Pipeline)
核心處理邏輯，不繼承 QThread，run() 是普通阻塞式方法。
由呼叫端決定在哪個線程執行。
"""

import cv2
import time
import mediapipe as mp
from typing import Optional

from event_bus import EventBus
from processing_config import ProcessingConfig
from frame_renderer import FrameRenderer
from angle_calculator import AngleCalculator
from reba_scorer import REBAScorer


class VideoPipeline:
    """影片處理管線 - 框架無關"""

    def __init__(self, event_bus: EventBus, config: ProcessingConfig = None):
        self._event_bus = event_bus
        self._config = config or ProcessingConfig()
        self._renderer = FrameRenderer(self._config)

        # MediaPipe
        self._mp_holistic = mp.solutions.holistic
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_drawing_styles = mp.solutions.drawing_styles

        # 計算器
        self._angle_calc = AngleCalculator()
        self._reba_scorer = REBAScorer()

        # 來源設定
        self._video_source: Optional[str] = None
        self._camera_id: int = 0

        # 分析參數
        self._side: str = 'right'
        self._load_weight: float = 0.0
        self._force_coupling: str = 'good'

        # 顯示選項
        self._show_angle_lines: bool = True
        self._show_angle_values: bool = True

        # 影片控制
        self._total_frames: int = 0
        self._current_frame_pos: int = 0
        self._seek_to_frame: int = -1

        # 狀態
        self._running: bool = False
        self._paused: bool = False

    # ========== 設定方法 ==========

    def set_source(self, source: Optional[str]):
        """設定影片來源 (None=攝影機)"""
        self._video_source = source

    def set_camera(self, camera_id: int):
        """設定攝影機 ID"""
        self._camera_id = camera_id

    def set_parameters(self, side: str, load_weight: float, force_coupling: str):
        """設定評估參數"""
        self._side = side
        self._load_weight = load_weight
        self._force_coupling = force_coupling

    def set_display_options(self, show_lines: bool, show_values: bool):
        """設定顯示選項"""
        self._show_angle_lines = show_lines
        self._show_angle_values = show_values

    def seek_frame(self, frame_number: int):
        """跳轉到指定幀"""
        self._seek_to_frame = frame_number

    # ========== 控制方法 ==========

    def run(self):
        """
        阻塞式主循環。由呼叫端決定在哪個線程執行：
        - QThread: ui/video_worker.py
        - threading.Thread: CLI 用途
        """
        self._running = True
        cap = self._open_video_source()
        if cap is None:
            return

        self._setup_video_properties(cap)

        with self._create_holistic() as holistic:
            self._process_video_loop(cap, holistic)

        cap.release()
        self._event_bus.emit('processing_finished')

    def stop(self):
        """停止處理"""
        self._running = False

    def pause(self):
        """暫停處理"""
        self._paused = True

    def resume(self):
        """恢復處理"""
        self._paused = False

    # ========== 屬性 ==========

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def total_frames(self) -> int:
        return self._total_frames

    @property
    def video_source(self) -> Optional[str]:
        return self._video_source

    @property
    def paused(self) -> bool:
        return self._paused

    # ========== 內部方法 ==========

    def _open_video_source(self):
        """開啟影片或攝影機"""
        source = self._video_source if self._video_source else self._camera_id
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            self._event_bus.emit('error_occurred', message="無法開啟影片來源")
            return None
        return cap

    def _setup_video_properties(self, cap):
        """設置影片屬性"""
        cfg = self._config
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.VIDEO_CAPTURE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.VIDEO_CAPTURE_HEIGHT)
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if self._video_source else 0

    def _create_holistic(self):
        """建立 MediaPipe Holistic"""
        cfg = self._config
        return self._mp_holistic.Holistic(
            min_detection_confidence=cfg.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=cfg.MIN_TRACKING_CONFIDENCE,
            model_complexity=cfg.MEDIAPIPE_MODEL_COMPLEXITY
        )

    def _process_video_loop(self, cap, holistic):
        """主處理循環"""
        frame_count = 0
        start_time = time.time()

        cached_angles = {}
        cached_reba_score = 0
        cached_risk_level = 'unknown'
        cached_details = {}

        skip_n = self._config.PROCESS_EVERY_N_FRAMES
        delay_ms = self._config.PROCESS_LOOP_DELAY_MS

        while self._running:
            if not self._handle_pause_and_seek(cap):
                break

            ret, frame = cap.read()
            if not ret:
                break

            self._update_progress(cap)

            if skip_n <= 1 or frame_count % skip_n == 0:
                results = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                cached_angles, cached_reba_score, cached_risk_level, cached_details = \
                    self._process_pose_results(frame, results)

            fps = self._calculate_fps(frame_count, start_time)
            frame_count += 1
            if frame_count % 30 == 0:
                start_time = time.time()

            self._renderer.draw_fps(frame, fps)
            self._event_bus.emit(
                'frame_processed',
                frame=frame,
                angles=cached_angles,
                reba_score=cached_reba_score,
                risk_level=cached_risk_level,
                fps=fps,
                details=cached_details
            )

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    def _handle_pause_and_seek(self, cap):
        """處理暫停和跳轉（支援暫停時預覽）"""
        while self._paused and self._running:
            if self._seek_to_frame >= 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, self._seek_to_frame)
                self._current_frame_pos = self._seek_to_frame
                target_frame = self._seek_to_frame
                self._seek_to_frame = -1

                ret, frame = cap.read()
                if ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    self._event_bus.emit(
                        'frame_processed',
                        frame=frame,
                        angles={},
                        reba_score=0,
                        risk_level='unknown',
                        fps=0.0,
                        details={}
                    )

            time.sleep(0.05)

        if not self._running:
            return False

        if self._seek_to_frame >= 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, self._seek_to_frame)
            self._current_frame_pos = self._seek_to_frame
            self._seek_to_frame = -1

        return True

    def _update_progress(self, cap):
        """更新進度"""
        if self._video_source:
            self._current_frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            self._event_bus.emit(
                'progress_updated',
                current_frame=self._current_frame_pos,
                total_frames=self._total_frames
            )

    def _process_pose_results(self, frame, results):
        """處理姿態檢測結果"""
        angles = {}
        reba_score = 0
        risk_level = 'unknown'
        details = {}

        if results.pose_landmarks:
            self._renderer.draw_pose_landmarks(
                frame, results.pose_landmarks,
                self._mp_drawing, self._mp_holistic, self._mp_drawing_styles,
                side=self._side
            )
            angles = self._angle_calc.calculate_all_angles(results.pose_landmarks, self._side)
            frame, angle_text_items = self._renderer.draw_angle_lines(
                frame, results.pose_landmarks, angles,
                self._side, self._show_angle_lines, self._show_angle_values
            )

            reba_score, risk_level, details = self._reba_scorer.calculate_reba_score(
                angles, self._load_weight, self._force_coupling
            )

            color = self._renderer.get_color_for_risk(risk_level)
            reba_text_items = self._renderer.build_reba_text_items(reba_score, risk_level, color)
            all_text_items = reba_text_items + angle_text_items
            self._renderer.draw_all_texts(frame, all_text_items)

        return angles, reba_score, risk_level, details

    @staticmethod
    def _calculate_fps(frame_count, start_time):
        """計算 FPS"""
        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            return 30 / elapsed if elapsed > 0 else 30.0
        return 30.0
