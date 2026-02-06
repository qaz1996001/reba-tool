#!/usr/bin/env python3
"""
主視窗 (Main Window)
純 UI 呈現層，所有業務邏輯委派給 VideoController。
"""

import cv2
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QPushButton, QLabel, QFileDialog,
                                QGroupBox, QGridLayout, QTextEdit,
                                QComboBox, QDoubleSpinBox, QSlider, QCheckBox,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QAbstractItemView, QApplication)
from PySide6.QtCore import Qt, QTimer, Signal, QEvent
from PySide6.QtGui import QImage, QPixmap, QColor, QBrush

from ui.qt_config import QtConfig
from ui.video_worker import VideoWorker
from ui.table_c_dialog import TableCDialog
from video_controller import VideoController


class MainWindow(QMainWindow):
    """主視窗 - 純 UI 呈現"""

    table_c_scores_updated = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaPipe REBA \u5206\u6790\u7cfb\u7d71")
        self.setGeometry(QtConfig.WINDOW_X, QtConfig.WINDOW_Y,
                         QtConfig.WINDOW_WIDTH, QtConfig.WINDOW_HEIGHT)

        # ViewModel
        self.controller = VideoController()

        # QThread worker
        self.video_worker = None

        # UI 狀態
        self.is_slider_dragging = False
        self.pending_seek_frame = -1
        self.was_paused_before_drag = False

        # 節流計時器
        self.slider_throttle_timer = QTimer()
        self.slider_throttle_timer.setSingleShot(True)
        self.slider_throttle_timer.timeout.connect(self._execute_throttled_seek)

        # 初始化 UI
        self.init_ui()

    def init_ui(self):
        """初始化使用者介面"""
        cfg = QtConfig

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # ========== 左側：影片顯示區 ==========
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 16)

        self.video_label = QLabel()
        self.video_label.setMinimumSize(cfg.VIDEO_LABEL_MIN_WIDTH, cfg.VIDEO_LABEL_MIN_HEIGHT)
        self.video_label.setStyleSheet(cfg.VIDEO_LABEL_BORDER_STYLE)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("\u8acb\u9078\u64c7\u5f71\u7247\u4f86\u6e90")
        self.video_label.setFont(cfg.get_video_hint_font())
        left_layout.addWidget(self.video_label)

        # 控制按鈕
        control_layout1 = QHBoxLayout()
        left_layout.addLayout(control_layout1)
        button_font = cfg.get_button_font()

        self.btn_camera = QPushButton("\u958b\u555f\u651d\u5f71\u6a5f")
        self.btn_camera.setFont(button_font)
        self.btn_camera.clicked.connect(self.start_camera)
        control_layout1.addWidget(self.btn_camera)

        self.btn_video = QPushButton("\u9078\u64c7\u5f71\u7247")
        self.btn_video.setFont(button_font)
        self.btn_video.clicked.connect(self.select_video)
        control_layout1.addWidget(self.btn_video)

        self.btn_pause = QPushButton("\u66ab\u505c")
        self.btn_pause.setFont(button_font)
        self.btn_pause.clicked.connect(self.pause_processing)
        self.btn_pause.setEnabled(False)
        control_layout1.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("\u505c\u6b62")
        self.btn_stop.setFont(button_font)
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        control_layout1.addWidget(self.btn_stop)

        self.btn_replay = QPushButton("\u91cd\u64ad")

        # 進度條和時間
        progress_layout = QHBoxLayout()
        left_layout.addLayout(progress_layout)
        time_label_font = cfg.get_time_label_font()

        self.label_time_current = QLabel("00:00")
        self.label_time_current.setFont(time_label_font)
        progress_layout.addWidget(self.label_time_current)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderMoved.connect(self.slider_moved)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        progress_layout.addWidget(self.progress_slider)

        self.label_time_total = QLabel("00:00")
        self.label_time_total.setFont(time_label_font)
        progress_layout.addWidget(self.label_time_total)

        # 顯示選項
        display_options_layout = QHBoxLayout()
        left_layout.addLayout(display_options_layout)
        checkbox_font = cfg.get_checkbox_font()

        self.check_angle_lines = QCheckBox("\u986f\u793a\u89d2\u5ea6\u7dda")
        self.check_angle_lines.setFont(checkbox_font)
        self.check_angle_lines.setChecked(True)
        self.check_angle_lines.stateChanged.connect(self.update_display_options)
        display_options_layout.addWidget(self.check_angle_lines)

        self.check_angle_values = QCheckBox("\u986f\u793a\u89d2\u5ea6\u6578\u503c")
        self.check_angle_values.setFont(checkbox_font)
        self.check_angle_values.setChecked(True)
        self.check_angle_values.stateChanged.connect(self.update_display_options)
        display_options_layout.addWidget(self.check_angle_values)
        display_options_layout.addStretch()

        # 保存按鈕
        self.btn_save_csv = QPushButton("\u4fdd\u5b58CSV")
        self.btn_save_csv.setFont(button_font)
        self.btn_save_csv.clicked.connect(self.save_csv)
        display_options_layout.addWidget(self.btn_save_csv)

        self.btn_save_json = QPushButton("\u4fdd\u5b58JSON")
        self.btn_save_json.setFont(button_font)
        self.btn_save_json.clicked.connect(self.save_json)
        display_options_layout.addWidget(self.btn_save_json)

        # 底部資訊區
        bottom_info_layout = QHBoxLayout()
        left_layout.addLayout(bottom_info_layout)

        # 日誌
        log_group = QGroupBox("\u7cfb\u7d71\u65e5\u8a8c")
        log_group.setFont(cfg.get_groupbox_font())
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        bottom_info_layout.addWidget(log_group, 1)

        # 統計
        stats_font = cfg.get_stats_font()
        stats_group = QGroupBox("\u7d71\u8a08\u8cc7\u8a0a")
        stats_group.setFont(cfg.get_groupbox_font())
        stats_layout = QGridLayout()
        stats_group.setLayout(stats_layout)
        bottom_info_layout.addWidget(stats_group)

        fps_prefix_label = QLabel("\u8655\u7406\u5e40\u6578:")
        fps_prefix_label.setFont(stats_font)
        stats_layout.addWidget(fps_prefix_label, 0, 0)
        self.label_frame_count = QLabel("0")
        self.label_frame_count.setFont(stats_font)
        stats_layout.addWidget(self.label_frame_count, 0, 1)

        fps2_prefix_label = QLabel("FPS:")
        fps2_prefix_label.setFont(stats_font)
        stats_layout.addWidget(fps2_prefix_label, 1, 0)
        self.label_fps = QLabel("0")
        self.label_fps.setFont(stats_font)
        stats_layout.addWidget(self.label_fps, 1, 1)

        record_label = QLabel("\u8a18\u9304\u6578:")
        record_label.setFont(stats_font)
        stats_layout.addWidget(record_label, 2, 0)
        self.label_record_count = QLabel("0")
        self.label_record_count.setFont(stats_font)
        stats_layout.addWidget(self.label_record_count, 2, 1)

        self.log_text = QTextEdit()
        self.log_text.setFont(cfg.get_log_text_font())
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(cfg.LOG_TEXT_MAX_HEIGHT)
        log_layout.addWidget(self.log_text)

        # ========== 右側：資料面板 ==========
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 9)

        groupbox_font = cfg.get_groupbox_font()
        param_label_font = cfg.get_param_label_font()
        combobox_font = cfg.get_combobox_font()

        # 參數設置
        param_group = QGroupBox("\u8a55\u4f30\u53c3\u6578")
        param_group.setFont(groupbox_font)
        param_layout = QGridLayout()
        param_group.setLayout(param_layout)
        right_layout.addWidget(param_group)

        label_side = QLabel("\u5206\u6790\u5074\u908a:")
        label_side.setFont(param_label_font)
        param_layout.addWidget(label_side, 0, 0)
        self.combo_side = QComboBox()
        self.combo_side.setFont(combobox_font)
        self.combo_side.addItems(["right", "left"])
        param_layout.addWidget(self.combo_side, 0, 1)

        label_load = QLabel("\u8ca0\u8377\u91cd\u91cf(kg):")
        label_load.setFont(param_label_font)
        param_layout.addWidget(label_load, 1, 0)
        self.spin_load = QDoubleSpinBox()
        self.spin_load.setFont(param_label_font)
        self.spin_load.setRange(0, 100)
        self.spin_load.setValue(0)
        param_layout.addWidget(self.spin_load, 1, 1)

        label_coupling = QLabel("\u63e1\u6301\u54c1\u8cea:")
        label_coupling.setFont(param_label_font)
        param_layout.addWidget(label_coupling, 2, 0)
        self.combo_coupling = QComboBox()
        self.combo_coupling.setFont(combobox_font)
        self.combo_coupling.addItems(["good", "fair", "poor", "unacceptable"])
        param_layout.addWidget(self.combo_coupling, 2, 1)

        self.combo_side.currentTextChanged.connect(self._on_parameters_changed)
        self.spin_load.valueChanged.connect(self._on_parameters_changed)
        self.combo_coupling.currentTextChanged.connect(self._on_parameters_changed)

        # REBA 評估群組
        reba_group = QGroupBox("\u95dc\u7bc0\u89d2\u5ea6\u8207REBA\u5206\u6578")
        reba_group.setFont(groupbox_font)
        reba_layout = QVBoxLayout()
        reba_group.setLayout(reba_layout)
        right_layout.addWidget(reba_group)

        # 總分和風險等級
        score_risk_layout = QHBoxLayout()
        reba_layout.addLayout(score_risk_layout)

        self.label_reba_score = QLabel("\u5206\u6578: --")
        self.label_reba_score.setFont(cfg.get_reba_score_font())
        self.label_reba_score.setAlignment(Qt.AlignCenter)
        score_risk_layout.addWidget(self.label_reba_score)

        self.label_risk_level = QLabel("\u98a8\u96aa\u7b49\u7d1a: --")
        self.label_risk_level.setFont(cfg.get_risk_level_font())
        self.label_risk_level.setAlignment(Qt.AlignCenter)
        score_risk_layout.addWidget(self.label_risk_level)

        # 整合表格
        self.angle_table = QTableWidget()
        self.angle_table.setColumnCount(5)
        self.angle_table.setFont(cfg.get_formula_detail_font())
        self.angle_table.installEventFilter(self)

        self.table_structure = [
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

        self.angle_table.setRowCount(len(self.table_structure))

        self.angle_table.horizontalHeader().setVisible(False)
        self.angle_table.verticalHeader().setVisible(False)
        self.angle_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.angle_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.angle_table.setSelectionBehavior(QAbstractItemView.SelectItems)

        header = self.angle_table.horizontalHeader()
        header.setStretchLastSection(False)
        self.column_ratios = cfg.TABLE_COLUMN_RATIOS

        for col in range(5):
            header.setSectionResizeMode(col, QHeaderView.Interactive)

        self._update_table_column_widths()

        row_h = cfg.TABLE_ROW_HEIGHT
        table_height = row_h * len(self.table_structure) + 4
        self.angle_table.verticalHeader().setDefaultSectionSize(row_h)
        self.angle_table.setFixedHeight(table_height)

        # 建立行映射
        self.angle_row_map = {}
        self.score_row_map = {}

        for row_idx, (left_name, left_key, right_name, right_key, is_header, is_highlight) in enumerate(self.table_structure):
            if row_idx == 0:
                headers = ['部位', '角度', '', '  ', '分數']
                for col, text in enumerate(headers):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QBrush(QColor('#c0c0c0')))
                    item.setFont(cfg.get_formula_header_font())
                    self.angle_table.setItem(row_idx, col, item)
                continue

            if is_header:
                if right_name:
                    left_item = QTableWidgetItem(left_name)
                    left_item.setTextAlignment(Qt.AlignCenter)
                    left_item.setBackground(QBrush(QColor('#e0e0e0')))
                    left_item.setFont(cfg.get_formula_header_font())
                    self.angle_table.setItem(row_idx, 0, left_item)

                    empty1 = QTableWidgetItem('')
                    empty1.setBackground(QBrush(QColor('#e0e0e0')))
                    self.angle_table.setItem(row_idx, 1, empty1)

                    sep_item = QTableWidgetItem('')
                    sep_item.setBackground(QBrush(QColor('#e0e0e0')))
                    self.angle_table.setItem(row_idx, 2, sep_item)

                    right_item = QTableWidgetItem(right_name)
                    right_item.setTextAlignment(Qt.AlignCenter)
                    right_item.setBackground(QBrush(QColor('#e0e0e0')))
                    right_item.setFont(cfg.get_formula_header_font())
                    self.angle_table.setItem(row_idx, 3, right_item)

                    empty2 = QTableWidgetItem('')
                    empty2.setBackground(QBrush(QColor('#e0e0e0')))
                    self.angle_table.setItem(row_idx, 4, empty2)
                else:
                    self.angle_table.setSpan(row_idx, 0, 1, 5)
                    header_item = QTableWidgetItem(left_name)
                    header_item.setTextAlignment(Qt.AlignCenter)
                    header_item.setBackground(QBrush(QColor('#d0d0d0')))
                    header_item.setFont(cfg.get_formula_header_font())
                    self.angle_table.setItem(row_idx, 0, header_item)
                continue

            bg_color = QColor('#d0d0ff') if is_highlight else None
            if left_name == 'REBA總分':
                bg_color = QColor('#ffd0d0')

            left_name_item = QTableWidgetItem(left_name)
            left_name_item.setTextAlignment(Qt.AlignCenter)
            if bg_color:
                left_name_item.setBackground(QBrush(bg_color))
                left_name_item.setFont(cfg.get_formula_total_font())
            self.angle_table.setItem(row_idx, 0, left_name_item)

            left_val_item = QTableWidgetItem('--')
            left_val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if bg_color:
                left_val_item.setBackground(QBrush(bg_color))
                left_val_item.setFont(cfg.get_formula_total_font())
            self.angle_table.setItem(row_idx, 1, left_val_item)

            sep_item = QTableWidgetItem('')
            if bg_color:
                sep_item.setBackground(QBrush(bg_color))
            self.angle_table.setItem(row_idx, 2, sep_item)

            right_name_item = QTableWidgetItem(right_name)
            right_name_item.setTextAlignment(Qt.AlignCenter)
            if bg_color:
                right_name_item.setBackground(QBrush(bg_color))
                right_name_item.setFont(cfg.get_formula_total_font())
            self.angle_table.setItem(row_idx, 3, right_name_item)

            right_val_item = QTableWidgetItem('--' if right_key else '')
            right_val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if bg_color:
                right_val_item.setBackground(QBrush(bg_color))
                right_val_item.setFont(cfg.get_formula_total_font())
            self.angle_table.setItem(row_idx, 4, right_val_item)

            if left_key:
                if left_key in ['neck', 'trunk', 'upper_arm', 'forearm', 'wrist', 'leg']:
                    self.angle_row_map[left_key] = (row_idx, 1)
                else:
                    if left_key not in self.score_row_map:
                        self.score_row_map[left_key] = []
                    self.score_row_map[left_key].append((row_idx, 1))
            if right_key:
                if right_key not in self.score_row_map:
                    self.score_row_map[right_key] = []
                self.score_row_map[right_key].append((row_idx, 4))

        reba_layout.addWidget(self.angle_table)

        self.label_risk_desc = QLabel("")

        self.angle_labels = {}
        self.score_labels = {}

        # 資料操作按鈕
        data_control_layout = QHBoxLayout()
        reba_layout.addLayout(data_control_layout)

        self.checkbox_lock = QCheckBox("\u9396\u5b9a\u8cc7\u6599")
        self.checkbox_lock.setFont(checkbox_font)
        self.checkbox_lock.stateChanged.connect(self.toggle_lock)
        data_control_layout.addWidget(self.checkbox_lock)

        self.btn_table_c = QPushButton("Table C")
        self.btn_table_c.setFont(button_font)
        self.btn_table_c.clicked.connect(self.show_table_c)
        data_control_layout.addWidget(self.btn_table_c)

        self.btn_copy = QPushButton("\u8907\u88fd\u8cc7\u6599")
        self.btn_copy.setFont(button_font)
        self.btn_copy.clicked.connect(self.copy_data)
        data_control_layout.addWidget(self.btn_copy)

        self.table_c_dialog = None

        right_layout.addStretch()

        self.statusBar().showMessage("\u5c31\u7dd2")

        self.log("\u7cfb\u7d71\u555f\u52d5\u5b8c\u6210")
        self.log("\u8acb\u9078\u64c7\u5f71\u7247\u4f86\u6e90\u958b\u59cb\u5206\u6790")

    # ========== 日誌 ==========

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    # ========== 控制方法 ==========

    def start_camera(self):
        if self.controller.is_processing:
            self.log("\u8acb\u5148\u505c\u6b62\u7576\u524d\u8655\u7406")
            return
        self.log("\u6b63\u5728\u958b\u555f\u651d\u5f71\u6a5f...")
        self.start_processing(None)

    def select_video(self):
        if self.controller.is_processing:
            self.log("\u8acb\u5148\u505c\u6b62\u7576\u524d\u8655\u7406")
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "\u9078\u64c7\u5f71\u7247\u6a94\u6848", "",
            "\u5f71\u7247\u6a94\u6848 (*.mp4 *.avi *.mov *.mkv);;\u6240\u6709\u6a94\u6848 (*.*)"
        )
        if file_path:
            self.log(f"\u9078\u64c7\u5f71\u7247: {Path(file_path).name}")
            self.start_processing(file_path)

    def start_processing(self, video_source):
        side = self.combo_side.currentText()
        load_weight = self.spin_load.value()
        force_coupling = self.combo_coupling.currentText()
        show_lines = self.check_angle_lines.isChecked()
        show_values = self.check_angle_values.isChecked()

        self.controller.start(video_source, side, load_weight, force_coupling, show_lines, show_values)

        # 建立 QThread worker
        self.video_worker = VideoWorker(self.controller.pipeline, self.controller.event_bus)
        self.video_worker.frame_ready.connect(self.update_display)
        self.video_worker.finished_signal.connect(self.processing_finished)
        self.video_worker.error_signal.connect(self.handle_error)
        self.video_worker.progress_signal.connect(self.update_progress)
        self.video_worker.start()

        # 更新 UI 狀態
        self.btn_camera.setEnabled(False)
        self.btn_video.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)

        if video_source is not None:
            self.progress_slider.setEnabled(True)
            self.btn_replay.setEnabled(True)
        else:
            self.progress_slider.setEnabled(False)
            self.btn_replay.setEnabled(False)

        source_name = "\u651d\u5f71\u6a5f" if video_source is None else Path(video_source).name
        self.log(f"\u958b\u59cb\u8655\u7406: {source_name}")
        self.statusBar().showMessage("\u8655\u7406\u4e2d...")

    def pause_processing(self):
        pipeline = self.controller.pipeline
        if pipeline:
            if pipeline.paused:
                self.controller.resume()
                self.btn_pause.setText("\u66ab\u505c")
                self.log("\u6062\u5fa9\u8655\u7406")
                self.statusBar().showMessage("\u8655\u7406\u4e2d...")
            else:
                self.controller.pause()
                self.btn_pause.setText("\u6062\u5fa9")
                self.log("\u5df2\u66ab\u505c")
                self.statusBar().showMessage("\u5df2\u66ab\u505c")

    def stop_processing(self):
        if self.video_worker:
            self.log("\u6b63\u5728\u505c\u6b62\u8655\u7406...")
            self.controller.stop()
            self.video_worker.wait()
            self.video_worker.cleanup()
            self.video_worker = None
        self.processing_finished()

    def processing_finished(self):
        self.controller.on_processing_finished()
        self.btn_camera.setEnabled(True)
        self.btn_video.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("\u66ab\u505c")
        self.btn_stop.setEnabled(False)
        self.progress_slider.setEnabled(False)

        self.log(f"\u8655\u7406\u5b8c\u6210\uff0c\u5171\u8655\u7406 {self.controller.frame_count} \u5e40")
        self.statusBar().showMessage("\u8655\u7406\u5b8c\u6210")

    def handle_error(self, error_msg: str):
        self.log(f"\u932f\u8aa4: {error_msg}")
        self.statusBar().showMessage(f"\u932f\u8aa4: {error_msg}")
        self.processing_finished()

    # ========== 顯示更新 ==========

    def update_display(self, frame, angles, reba_score, risk_level, fps, details):
        # 委派給 controller 記錄資料
        self.controller.record_frame(frame, angles, reba_score, risk_level, fps, details)

        self.label_frame_count.setText(str(self.controller.frame_count))
        self.label_fps.setText(f"{fps:.1f}")

        if not self.controller.data_locked:
            # 更新影像
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)

            # 更新角度和分數
            self._update_angles_and_scores(angles, details)
            self._update_reba_display(reba_score, risk_level, details)

        self.label_record_count.setText(str(self.controller.data_logger.get_buffer_size()))

    def _update_table_column_widths(self):
        if not hasattr(self, 'angle_table') or not hasattr(self, 'column_ratios'):
            return
        available_width = self.angle_table.viewport().width()
        if available_width <= 0:
            available_width = self.angle_table.width() - 4
        total_ratio = sum(self.column_ratios)
        for col, ratio in enumerate(self.column_ratios):
            width = int(available_width * ratio / total_ratio)
            self.angle_table.setColumnWidth(col, width)

    def _update_angles_and_scores(self, angles, details):
        for key, (row_idx, col_idx) in self.angle_row_map.items():
            angle_item = self.angle_table.item(row_idx, col_idx)
            if angle_item:
                if angles.get(key) is not None:
                    angle_item.setText(f"{angles[key]:.1f}\u00b0")
                else:
                    angle_item.setText("--")

    def _update_reba_display(self, reba_score, risk_level, details=None):
        if details is None:
            details = {}

        scorer = self.controller.reba_scorer

        if reba_score > 0:
            self.label_reba_score.setText(f"\u5206\u6578: {reba_score}")

            risk_labels = {
                'negligible': '\u53ef\u5ffd\u7565',
                'low': '\u4f4e\u98a8\u96aa',
                'medium': '\u4e2d\u7b49\u98a8\u96aa',
                'high': '\u9ad8\u98a8\u96aa',
                'very_high': '\u6975\u9ad8\u98a8\u96aa'
            }
            risk_text = risk_labels.get(risk_level, risk_level)
            self.label_risk_level.setText(f"\u98a8\u96aa\u7b49\u7d1a: {risk_text}")

            desc = scorer.get_risk_description(risk_level)
            self.label_risk_desc.setText(desc)

            color = scorer.get_risk_color(risk_level)
            self.label_reba_score.setStyleSheet(f"background-color: {color}; padding: 5px;")
            self.label_risk_level.setStyleSheet(f"background-color: {color}; padding: 5px;")

            for key, positions in self.score_row_map.items():
                val = details.get(key)
                text = str(val) if val is not None else '--'
                for (row_idx, col_idx) in positions:
                    score_item = self.angle_table.item(row_idx, col_idx)
                    if score_item:
                        score_item.setText(text)

            score_a = details.get('score_a')
            score_b = details.get('score_b')
            self.table_c_scores_updated.emit(score_a, score_b)
        else:
            self.label_reba_score.setText("\u5206\u6578: --")
            self.label_risk_level.setText("\u98a8\u96aa\u7b49\u7d1a: --")
            self.label_risk_desc.setText("")
            self.label_reba_score.setStyleSheet("")
            self.label_risk_level.setStyleSheet("")

            for key, positions in self.score_row_map.items():
                for (row_idx, col_idx) in positions:
                    score_item = self.angle_table.item(row_idx, col_idx)
                    if score_item:
                        score_item.setText("--")

    # ========== 資料操作 ==========

    def toggle_lock(self, state):
        locked = (state == Qt.Checked)
        self.controller.toggle_data_lock(locked)
        if locked:
            self.log("\u8cc7\u6599\u5df2\u9396\u5b9a - \u986f\u793a\u5c07\u4fdd\u6301\u7576\u524d\u72c0\u614b")
            self.statusBar().showMessage("\u8cc7\u6599\u5df2\u9396\u5b9a")
        else:
            self.log("\u8cc7\u6599\u5df2\u89e3\u9396 - \u6062\u5fa9\u5373\u6642\u66f4\u65b0")
            self.statusBar().showMessage("\u8cc7\u6599\u5df2\u89e3\u9396")

    def show_table_c(self):
        score_a = None
        score_b = None

        if self.controller.locked_data:
            details = self.controller.locked_data.get('details', {})
            score_a = details.get('score_a')
            score_b = details.get('score_b')

        if self.table_c_dialog is None or not self.table_c_dialog.isVisible():
            if self.table_c_dialog is not None:
                try:
                    self.table_c_scores_updated.disconnect(self.table_c_dialog.update_scores)
                except RuntimeError:
                    pass
            self.table_c_dialog = TableCDialog(self, score_a, score_b)
            self.table_c_scores_updated.connect(self.table_c_dialog.update_scores)
            self.table_c_dialog.finished.connect(self._on_table_c_closed)
            self.table_c_dialog.show()
            self._position_table_c_dialog()
        else:
            self.table_c_dialog.update_scores(score_a, score_b)
            self.table_c_dialog.raise_()
            self.table_c_dialog.activateWindow()

    def _on_table_c_closed(self):
        if self.table_c_dialog is not None:
            try:
                self.table_c_scores_updated.disconnect(self.table_c_dialog.update_scores)
            except RuntimeError:
                pass

    def _position_table_c_dialog(self):
        if self.table_c_dialog is None:
            return
        main_geo = self.geometry()
        dialog_width = self.table_c_dialog.width()
        dialog_height = self.table_c_dialog.height()
        new_x = main_geo.x() + main_geo.width() + 10
        new_y = main_geo.y() + (main_geo.height() - dialog_height) // 2

        screen = QApplication.primaryScreen().availableGeometry()
        if new_x + dialog_width > screen.right():
            new_x = main_geo.x() - dialog_width - 10
        if new_y < screen.top():
            new_y = screen.top()
        if new_y + dialog_height > screen.bottom():
            new_y = screen.bottom() - dialog_height

        self.table_c_dialog.move(new_x, new_y)

    def copy_data(self):
        text = self.controller.get_copy_text()
        if not text:
            self.log("\u6c92\u6709\u8cc7\u6599\u53ef\u8907\u88fd")
            return

        # 添加參數設定資訊
        side = self.combo_side.currentText()
        load_weight = self.spin_load.value()
        coupling = self.combo_coupling.currentText()
        coupling_labels = {"good": "\u826f\u597d", "fair": "\u666e\u901a", "poor": "\u5dee", "unacceptable": "\u4e0d\u53ef\u63a5\u53d7"}
        coupling_text = coupling_labels.get(coupling, coupling)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 在報告開頭插入參數設定
        param_section = f"""\u5206\u6790\u6642\u9593: {timestamp}

\u3010\u8a55\u4f30\u53c3\u6578\u8a2d\u5b9a\u3011
\u251c\u2500 \u5206\u6790\u5074: {side}
\u251c\u2500 \u8ca0\u91cd: {load_weight} kg
\u2514\u2500 \u63e1\u6301\u54c1\u8cea: {coupling_text}

"""
        # 找到第一個換行後插入參數
        lines = text.split('\n')
        # 插入到標題行之後
        insert_idx = 3  # 在第3行之後
        final_text = '\n'.join(lines[:insert_idx]) + '\n' + param_section + '\n'.join(lines[insert_idx:])

        clipboard = QApplication.clipboard()
        clipboard.setText(final_text)
        self.log("\u8cc7\u6599\u5df2\u8907\u88fd\u5230\u526a\u8cbc\u7c3f")
        self.statusBar().showMessage("\u8cc7\u6599\u5df2\u8907\u88fd", 2000)

    def save_csv(self):
        if self.controller.data_logger.get_buffer_size() == 0:
            self.log("\u6c92\u6709\u8cc7\u6599\u53ef\u4fdd\u5b58")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "\u4fdd\u5b58CSV\u6a94\u6848",
            f"reba_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV\u6a94\u6848 (*.csv)"
        )
        if file_path:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
            saved_path = self.controller.save_csv(file_path)
            self.log(f"\u5df2\u4fdd\u5b58CSV: {Path(saved_path).name}")

    def save_json(self):
        if self.controller.data_logger.get_buffer_size() == 0:
            self.log("\u6c92\u6709\u8cc7\u6599\u53ef\u4fdd\u5b58")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "\u4fdd\u5b58JSON\u6a94\u6848",
            f"reba_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON\u6a94\u6848 (*.json)"
        )
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            saved_path = self.controller.save_json(file_path)
            self.log(f"\u5df2\u4fdd\u5b58JSON: {Path(saved_path).name}")

    # ========== 進度條操作 ==========

    def update_progress(self, current_frame: int, total_frames: int):
        if total_frames > 0:
            self.progress_slider.blockSignals(True)
            self.progress_slider.setMaximum(total_frames)
            self.progress_slider.setValue(current_frame)
            self.progress_slider.blockSignals(False)

            fps = 30.0
            current_seconds = int(current_frame / fps)
            total_seconds = int(total_frames / fps)
            self.label_time_current.setText(f"{current_seconds // 60:02d}:{current_seconds % 60:02d}")
            self.label_time_total.setText(f"{total_seconds // 60:02d}:{total_seconds % 60:02d}")

    def slider_pressed(self):
        self.is_slider_dragging = True
        pipeline = self.controller.pipeline
        if pipeline:
            self.was_paused_before_drag = pipeline.paused
            if not pipeline.paused:
                self.controller.pause()

    def slider_moved(self, value):
        if not self.is_slider_dragging:
            return
        self.pending_seek_frame = value

        pipeline = self.controller.pipeline
        if pipeline and pipeline.total_frames > 0:
            fps = 30.0
            current_seconds = int(value / fps)
            self.label_time_current.setText(f"{current_seconds // 60:02d}:{current_seconds % 60:02d}")

        if not self.slider_throttle_timer.isActive():
            self.slider_throttle_timer.start(QtConfig.SLIDER_DRAG_THROTTLE_MS)

    def _execute_throttled_seek(self):
        if self.pending_seek_frame >= 0:
            self.controller.seek(self.pending_seek_frame)

    def slider_released(self):
        self.is_slider_dragging = False
        self.slider_throttle_timer.stop()

        target_frame = self.progress_slider.value()
        self.controller.seek(target_frame)
        self.pending_seek_frame = -1

        if not self.was_paused_before_drag:
            self.controller.resume()

    # ========== 顯示選項 ==========

    def update_display_options(self):
        show_lines = self.check_angle_lines.isChecked()
        show_values = self.check_angle_values.isChecked()
        self.controller.set_display_options(show_lines, show_values)

    def _on_parameters_changed(self):
        pipeline = self.controller.pipeline
        if pipeline and pipeline.is_running:
            side = self.combo_side.currentText()
            load_weight = self.spin_load.value()
            force_coupling = self.combo_coupling.currentText()
            self.controller.set_parameters(side, load_weight, force_coupling)

    # ========== 視窗事件 ==========

    def showEvent(self, event):
        super().showEvent(event)
        self._update_table_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_table_column_widths()

    def eventFilter(self, obj, event):
        if obj == self.angle_table and event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                self._copy_table_selection()
                return True
        return super().eventFilter(obj, event)

    def _copy_table_selection(self):
        selection = self.angle_table.selectedRanges()
        if not selection:
            return

        rows_data = {}
        for sel_range in selection:
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                if row not in rows_data:
                    rows_data[row] = {}
                for col in range(sel_range.leftColumn(), sel_range.rightColumn() + 1):
                    item = self.angle_table.item(row, col)
                    text = item.text() if item else ''
                    rows_data[row][col] = text

        lines = []
        for row in sorted(rows_data.keys()):
            cols = rows_data[row]
            min_col = min(cols.keys())
            max_col = max(cols.keys())
            row_texts = []
            for col in range(min_col, max_col + 1):
                row_texts.append(cols.get(col, ''))
            lines.append('\t'.join(row_texts))

        clipboard = QApplication.clipboard()
        clipboard.setText('\n'.join(lines))

    def closeEvent(self, event):
        if self.video_worker and self.video_worker.isRunning():
            self.controller.stop()
            self.video_worker.wait()
            self.video_worker.cleanup()
        event.accept()
