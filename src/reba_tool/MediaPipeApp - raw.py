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
                              QComboBox, QSpinBox, QDoubleSpinBox, QSlider, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont

# 導入自定義模組
from angle_calculator import AngleCalculator
from reba_scorer import REBAScorer
from data_logger import DataLogger


class VideoProcessThread(QThread):
    """影片處理執行緒"""

    # 信號定義
    frame_processed = Signal(object, dict, int, str, float, dict)  # 影像, 角度, REBA分數, 風險等級, FPS, 詳細分數
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

        # 載入中文字體
        font_path = Path(__file__).parent / "Arial.Unicode.ttf"
        if font_path.exists():
            self.font_chinese = ImageFont.truetype(str(font_path), 48)
            self.font_chinese_small = ImageFont.truetype(str(font_path), 48)
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

            eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
            shoulder_center = ((left_shoulder[0] + right_shoulder[0]) // 2, (left_shoulder[1] + right_shoulder[1]) // 2)

            cv2.line(frame, eye_center, shoulder_center, (0, 0, 255), 3)

            if self.show_angle_values:
                mid_point = ((eye_center[0] + shoulder_center[0]) // 2, (eye_center[1] + shoulder_center[1]) // 2)
                self._draw_angle_text(frame, f"{angles['neck']:.1f}°", mid_point, (0, 0, 255))

        # 軀幹角度線（橙色）
        if self.show_angle_lines and angles.get('trunk') is not None:
            left_shoulder = get_point(self.angle_calc.LEFT_SHOULDER)
            right_shoulder = get_point(self.angle_calc.RIGHT_SHOULDER)
            left_hip = get_point(self.angle_calc.LEFT_HIP)
            right_hip = get_point(self.angle_calc.RIGHT_HIP)

            shoulder_center = ((left_shoulder[0] + right_shoulder[0]) // 2, (left_shoulder[1] + right_shoulder[1]) // 2)
            hip_center = ((left_hip[0] + right_hip[0]) // 2, (left_hip[1] + right_hip[1]) // 2)

            cv2.line(frame, shoulder_center, hip_center, (0, 165, 255), 3)

            if self.show_angle_values:
                mid_point = ((shoulder_center[0] + hip_center[0]) // 2, (shoulder_center[1] + hip_center[1]) // 2)
                self._draw_angle_text(frame, f"{angles['trunk']:.1f}°", mid_point, (0, 165, 255))

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

            cv2.line(frame, shoulder, elbow, (0, 255, 255), 3)
            cv2.line(frame, elbow, wrist, (0, 255, 255), 3)

            if self.show_angle_values:
                offset_x = 20 if self.side == 'right' else -80
                text_pos = (elbow[0] + offset_x, elbow[1] - 10)
                self._draw_angle_text(frame, f"{angles['upper_arm']:.1f}°", text_pos, (0, 255, 255))

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

            cv2.line(frame, wrist, index, (0, 255, 0), 3)

            if self.show_angle_values:
                offset_x = 20 if self.side == 'right' else -80
                text_pos = (wrist[0] + offset_x, wrist[1] + 20)
                self._draw_angle_text(frame, f"{angles['wrist']:.1f}°", text_pos, (0, 255, 0))

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

            cv2.line(frame, hip, knee, (255, 0, 0), 3)
            cv2.line(frame, knee, ankle, (255, 0, 0), 3)

            if self.show_angle_values:
                offset_x = 20 if self.side == 'right' else -80
                text_pos = (knee[0] + offset_x, knee[1])
                self._draw_angle_text(frame, f"{angles['leg']:.1f}°", text_pos, (255, 0, 0))

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
            cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            return frame

        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        pil_color = (color[2], color[1], color[0])

        if bg_style != 'none':
            bbox = draw.textbbox(position, text, font=font)
            padding = 5
            bg_bbox = (bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding)

            if bg_style == 'solid':
                pil_bg_color = (bg_color[2], bg_color[1], bg_color[0])
                draw.rectangle(bg_bbox, fill=pil_bg_color)
            elif bg_style == 'transparent':
                overlay = Image.new('RGBA', img_pil.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle(bg_bbox, fill=(0, 0, 0, 153))
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
        cap = cv2.VideoCapture(self.video_source if self.video_source else self.camera_id)
        if not cap.isOpened():
            self.error_occurred.emit("無法開啟影片來源")
            return None
        return cap

    def _setup_video_properties(self, cap):
        """設置影片屬性"""
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if self.video_source else 0

    def _create_holistic(self):
        """創建 MediaPipe Holistic 實例"""
        return self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )

    def _process_video_loop(self, cap, holistic):
        """主處理循環"""
        frame_count = 0
        start_time = time.time()

        while self.running:
            if not self._handle_pause_and_seek(cap):
                break

            ret, frame = cap.read()
            if not ret:
                break

            self._update_progress(cap)

            results = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            angles, reba_score, risk_level, details = self._process_pose_results(frame, results)

            fps = self._calculate_fps(frame_count, start_time)
            frame_count += 1
            if frame_count % 30 == 0:
                start_time = time.time()

            self._draw_fps(frame, fps)
            self.frame_processed.emit(frame, angles, reba_score, risk_level, fps, details)
            time.sleep(0.001)

    def _handle_pause_and_seek(self, cap):
        """處理暫停和跳轉"""
        while self.paused and self.running:
            time.sleep(0.1)

        if not self.running:
            return False

        if self.seek_to_frame >= 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, self.seek_to_frame)
            self.current_frame_pos = self.seek_to_frame
            self.seek_to_frame = -1

        return True

    def _update_progress(self, cap):
        """更新進度條"""
        if self.video_source:
            self.current_frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.progress_updated.emit(self.current_frame_pos, self.total_frames)

    def _process_pose_results(self, frame, results):
        """處理姿態檢測結果"""
        angles = {}
        reba_score = 0
        risk_level = 'unknown'
        details = {}

        if results.pose_landmarks:
            self._draw_pose_landmarks(frame, results.pose_landmarks)
            angles = self.angle_calc.calculate_all_angles(results.pose_landmarks, self.side)
            frame = self.draw_angle_lines(frame, results.pose_landmarks, angles)
            reba_score, risk_level, details = self._calculate_and_draw_reba(frame, angles)

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

        frame = self._put_chinese_text(frame, f"REBA分數: {reba_score}", (10, 10),
                                       self.font_chinese, color, bg_color=(0, 0, 0))
        frame = self._put_chinese_text(frame, f"風險等級: {risk_text}", (10, 45),
                                       self.font_chinese_small, color, bg_color=(0, 0, 0))

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
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def _get_color_for_risk(self, risk_level: str):
        """根據風險等級獲取顏色"""
        colors = {
            'negligible': (0, 255, 0),
            'low': (144, 238, 144),
            'medium': (0, 255, 255),
            'high': (0, 165, 255),
            'very_high': (0, 0, 255)
        }
        return colors.get(risk_level, (255, 255, 255))
    
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
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaPipe REBA 分析系統")
        self.setGeometry(100, 100, 1400, 800)
        
        # 初始化變數
        self.video_thread = None
        self.data_logger = DataLogger()
        self.frame_count = 0
        self.is_processing = False
        self.data_locked = False  # 資料鎖定狀態
        self.locked_data = None  # 鎖定的資料
        
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
        main_layout.addLayout(left_layout, 2)
        
        # 影片顯示標籤
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("border: 2px solid black; background-color: #2b2b2b;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("請選擇影片來源")
        left_layout.addWidget(self.video_label)
        
        # 控制按鈕區（第一行）
        control_layout1 = QHBoxLayout()
        left_layout.addLayout(control_layout1)

        self.btn_camera = QPushButton("開啟攝影機")
        self.btn_camera.clicked.connect(self.start_camera)
        control_layout1.addWidget(self.btn_camera)

        self.btn_video = QPushButton("選擇影片")
        self.btn_video.clicked.connect(self.select_video)
        control_layout1.addWidget(self.btn_video)

        self.btn_pause = QPushButton("暫停")
        self.btn_pause.clicked.connect(self.pause_processing)
        self.btn_pause.setEnabled(False)
        control_layout1.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        control_layout1.addWidget(self.btn_stop)

        self.btn_replay = QPushButton("重播")
        self.btn_replay.clicked.connect(self.replay_video)
        self.btn_replay.setEnabled(False)
        control_layout1.addWidget(self.btn_replay)

        # 進度條和時間顯示
        progress_layout = QHBoxLayout()
        left_layout.addLayout(progress_layout)

        self.label_time_current = QLabel("00:00")
        progress_layout.addWidget(self.label_time_current)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        progress_layout.addWidget(self.progress_slider)

        self.label_time_total = QLabel("00:00")
        progress_layout.addWidget(self.label_time_total)

        # 顯示選項（複選框）
        display_options_layout = QHBoxLayout()
        left_layout.addLayout(display_options_layout)

        self.check_angle_lines = QCheckBox("顯示角度線")
        self.check_angle_lines.setChecked(True)
        self.check_angle_lines.stateChanged.connect(self.update_display_options)
        display_options_layout.addWidget(self.check_angle_lines)

        self.check_angle_values = QCheckBox("顯示角度數值")
        self.check_angle_values.setChecked(True)
        self.check_angle_values.stateChanged.connect(self.update_display_options)
        display_options_layout.addWidget(self.check_angle_values)

        display_options_layout.addStretch()
        
        # 右側: 資料面板
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)
        
        # 參數設置群組
        param_group = QGroupBox("評估參數")
        param_layout = QGridLayout()
        param_group.setLayout(param_layout)
        right_layout.addWidget(param_group)
        
        param_layout.addWidget(QLabel("分析側邊:"), 0, 0)
        self.combo_side = QComboBox()
        self.combo_side.addItems(["right", "left"])
        param_layout.addWidget(self.combo_side, 0, 1)
        
        param_layout.addWidget(QLabel("負荷重量(kg):"), 1, 0)
        self.spin_load = QDoubleSpinBox()
        self.spin_load.setRange(0, 100)
        self.spin_load.setValue(0)
        param_layout.addWidget(self.spin_load, 1, 1)
        
        param_layout.addWidget(QLabel("握持品質:"), 2, 0)
        self.combo_coupling = QComboBox()
        self.combo_coupling.addItems(["good", "fair", "poor", "unacceptable"])
        param_layout.addWidget(self.combo_coupling, 2, 1)
        
        # 角度顯示群組
        angle_group = QGroupBox("關節角度與分數")
        angle_layout = QGridLayout()
        angle_group.setLayout(angle_layout)
        right_layout.addWidget(angle_group)

        # 創建角度標籤和分數標籤
        self.angle_labels = {}
        self.score_labels = {}
        angle_names = [
            ('neck', '頸部'),
            ('trunk', '軀幹'),
            ('upper_arm', '上臂'),
            ('forearm', '前臂'),
            ('wrist', '手腕'),
            ('leg', '腿部')
        ]
        angle_label_qfont = QFont("Arial", 28, QFont.Bold)
        for i, (key, name) in enumerate(angle_names):
            angle_label_prefix = QLabel(f"{name}:")
            angle_label_prefix.setFont(angle_label_qfont)
            angle_layout.addWidget(angle_label_prefix, i, 0)

            # 角度標籤
            angle_label = QLabel("--")
            angle_label.setFont(angle_label_qfont)
            self.angle_labels[key] = angle_label
            angle_layout.addWidget(angle_label, i, 1)

            # REBA分數標籤
            score_label = QLabel("")
            score_label.setFont(angle_label_qfont)
            score_label.setStyleSheet("color: #666;")
            self.score_labels[key] = score_label
            angle_layout.addWidget(score_label, i, 2)
        
        # REBA分數顯示群組
        reba_group = QGroupBox("REBA評估")
        reba_layout = QVBoxLayout()
        reba_group.setLayout(reba_layout)
        right_layout.addWidget(reba_group)
        
        self.label_reba_score = QLabel("分數: --")
        self.label_reba_score.setFont(QFont("Arial", 32, QFont.Bold))
        self.label_reba_score.setAlignment(Qt.AlignCenter)
        reba_layout.addWidget(self.label_reba_score)
        
        self.label_risk_level = QLabel("風險等級: --")
        self.label_risk_level.setFont(QFont("Arial", 24))
        self.label_risk_level.setAlignment(Qt.AlignCenter)
        reba_layout.addWidget(self.label_risk_level)
        
        self.label_risk_desc = QLabel("")
        self.label_risk_desc.setWordWrap(True)
        self.label_risk_desc.setAlignment(Qt.AlignCenter)
        reba_layout.addWidget(self.label_risk_desc)

        # 資料操作按鈕
        data_control_layout = QHBoxLayout()
        reba_layout.addLayout(data_control_layout)

        self.checkbox_lock = QCheckBox("鎖定資料")
        self.checkbox_lock.stateChanged.connect(self.toggle_lock)
        data_control_layout.addWidget(self.checkbox_lock)

        self.btn_copy = QPushButton("複製資料")
        self.btn_copy.clicked.connect(self.copy_data)
        data_control_layout.addWidget(self.btn_copy)

        # 統計資訊群組
        prefix_qfont = QFont("Arial", 28, QFont.Bold)

        stats_group = QGroupBox("統計資訊")
        stats_layout = QGridLayout()
        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)
        fps_prefix_label = QLabel("處理幀數:")
        fps_prefix_label.setFont(prefix_qfont)

        stats_layout.addWidget(fps_prefix_label, 0, 0)
        self.label_frame_count = QLabel("0")
        self.label_frame_count.setFont(prefix_qfont)
        stats_layout.addWidget(self.label_frame_count, 0, 1)
        
        fps2_prefix_label = QLabel("FPS:")
        fps2_prefix_label.setFont(prefix_qfont)
        stats_layout.addWidget(fps2_prefix_label, 1, 0)

        self.label_fps = QLabel("0")
        self.label_fps.setFont(prefix_qfont)
        stats_layout.addWidget(self.label_fps, 1, 1)
        
        stats_layout.addWidget(QLabel("記錄數:"), 2, 0)
        self.label_record_count = QLabel("0")
        stats_layout.addWidget(self.label_record_count, 2, 1)
        
        # 保存按鈕
        save_layout = QHBoxLayout()
        right_layout.addLayout(save_layout)
        
        self.btn_save_csv = QPushButton("保存CSV")
        self.btn_save_csv.clicked.connect(self.save_csv)
        save_layout.addWidget(self.btn_save_csv)
        
        self.btn_save_json = QPushButton("保存JSON")
        self.btn_save_json.clicked.connect(self.save_json)
        save_layout.addWidget(self.btn_save_json)
        
        # 日誌顯示
        log_group = QGroupBox("系統日誌")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
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

        source_name = "攝影機" if video_source is None else Path(video_source).name
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
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # 縮放到適合視窗大小
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)

            # 更新角度和分數顯示
            self._update_angles_and_scores(angles, details)

            # 更新REBA總分顯示
            self._update_reba_display(reba_score, risk_level)
        
        # 記錄資料
        timestamp = time.time()
        self.data_logger.add_frame_data(
            self.frame_count,
            timestamp,
            angles,
            reba_score,
            risk_level
        )
        
        self.label_record_count.setText(str(self.data_logger.get_buffer_size()))

    def _update_angles_and_scores(self, angles, details):
        """更新角度和個別REBA分數顯示"""
        # 分數映射（從details字典的key映射到angle key）
        score_mapping = {
            'neck': 'neck_score',
            'trunk': 'trunk_score',
            'upper_arm': 'upper_arm_score',
            'forearm': 'forearm_score',
            'wrist': 'wrist_score',
            'leg': 'leg_score'
        }

        for key, angle_label in self.angle_labels.items():
            # 更新角度
            if angles.get(key) is not None:
                angle_label.setText(f"{angles[key]:.1f}°")
            else:
                angle_label.setText("--")

            # 更新對應的REBA分數
            score_label = self.score_labels[key]
            score_key = score_mapping.get(key)
            if score_key and details.get(score_key) is not None:
                score = details[score_key]
                score_label.setText(f"[分數: {score}]")
            else:
                score_label.setText("")

    def _update_reba_display(self, reba_score, risk_level):
        """更新REBA總分和風險等級顯示"""
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
            reba_scorer = REBAScorer()
            desc = reba_scorer.get_risk_description(risk_level)
            self.label_risk_desc.setText(desc)

            # 設置顏色
            color = reba_scorer.get_risk_color(risk_level)
            self.label_reba_score.setStyleSheet(f"background-color: {color}; padding: 5px;")
            self.label_risk_level.setStyleSheet(f"background-color: {color}; padding: 5px;")
        else:
            self.label_reba_score.setText("分數: --")
            self.label_risk_level.setText("風險等級: --")
            self.label_risk_desc.setText("")
            self.label_reba_score.setStyleSheet("")
            self.label_risk_level.setStyleSheet("")

    def toggle_lock(self, state):
        """切換資料鎖定狀態"""
        self.data_locked = (state == Qt.Checked)
        if self.data_locked:
            self.log("資料已鎖定 - 顯示將保持當前狀態")
            self.statusBar().showMessage("資料已鎖定")
        else:
            self.log("資料已解鎖 - 恢復即時更新")
            self.statusBar().showMessage("資料已解鎖")

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

        # 格式化資料為文字
        text_data = f"""REBA 分析資料
============

【關節角度與分數】
頸部: {angles.get('neck', '--'):.1f}° [分數: {details.get('neck_score', '--')}]
軀幹: {angles.get('trunk', '--'):.1f}° [分數: {details.get('trunk_score', '--')}]
上臂: {angles.get('upper_arm', '--'):.1f}° [分數: {details.get('upper_arm_score', '--')}]
前臂: {angles.get('forearm', '--'):.1f}° [分數: {details.get('forearm_score', '--')}]
手腕: {angles.get('wrist', '--'):.1f}° [分數: {details.get('wrist_score', '--')}]
腿部: {angles.get('leg', '--'):.1f}° [分數: {details.get('leg_score', '--')}]

【REBA 評估】
總分: {reba_score}
風險等級: {risk_text}

【詳細分數】
Group A 姿勢分數: {details.get('posture_score_a', '--')}
負荷分數: {details.get('load_score', '--')}
Score A: {details.get('score_a', '--')}
Group B 姿勢分數: {details.get('posture_score_b', '--')}
握持分數: {details.get('coupling_score', '--')}
Score B: {details.get('score_b', '--')}
Score C: {details.get('score_c', '--')}
活動分數: {details.get('activity_score', '--')}
最終分數: {details.get('final_score', '--')}
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
        """進度條按下時暫停影片"""
        if self.video_thread and not self.video_thread.paused:
            self.video_thread.pause()

    def slider_released(self):
        """進度條釋放時跳轉到指定幀"""
        if self.video_thread:
            target_frame = self.progress_slider.value()
            self.video_thread.seek_frame(target_frame)
            if self.video_thread.paused and self.btn_pause.text() == "暫停":
                self.video_thread.resume()

    def update_display_options(self):
        """更新顯示選項"""
        if self.video_thread:
            show_lines = self.check_angle_lines.isChecked()
            show_values = self.check_angle_values.isChecked()
            self.video_thread.set_display_options(show_lines, show_values)

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