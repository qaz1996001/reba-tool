#!/usr/bin/env python3
"""
影像繪圖模組 (Frame Renderer)
從 VideoProcessThread 抽出所有 OpenCV/PIL 繪圖邏輯，零 Qt 依賴。
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional, Tuple

from processing_config import ProcessingConfig
from angle_calculator import AngleCalculator


class FrameRenderer:
    """影像繪圖器 - 負責所有 OpenCV/PIL 繪圖"""

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.angle_calc = AngleCalculator()

        # 載入中文字體
        font_path = self.config.FONT_PATH
        if Path(font_path).exists():
            self.font_chinese = ImageFont.truetype(font_path, self.config.OVERLAY_FONT_SIZE)
            self.font_chinese_small = ImageFont.truetype(font_path, self.config.OVERLAY_FONT_SIZE_SMALL)
        else:
            print(f"警告: 找不到字體檔案 {font_path}")
            self.font_chinese = None
            self.font_chinese_small = None

    # MediaPipe landmark 側邊歸屬
    _LEFT_LANDMARKS = {1, 2, 3, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31}
    _RIGHT_LANDMARKS = {4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32}
    _CENTER_LANDMARKS = {0}  # nose
    _CENTER_CONNECTIONS = {(9, 10), (11, 12), (23, 24)}

    def _filter_connections_by_side(self, all_connections, side):
        """根據側邊過濾骨架連線"""
        if side == 'right':
            visible = self._RIGHT_LANDMARKS | self._CENTER_LANDMARKS
        else:
            visible = self._LEFT_LANDMARKS | self._CENTER_LANDMARKS
        filtered = []
        for a, b in all_connections:
            norm = (min(a, b), max(a, b))
            if norm in self._CENTER_CONNECTIONS:
                filtered.append((a, b))
            elif a in visible and b in visible:
                filtered.append((a, b))
        return frozenset(filtered)

    def _get_visible_landmarks(self, side):
        """取得選定側的可見 landmark 索引"""
        if side == 'right':
            return self._RIGHT_LANDMARKS | self._CENTER_LANDMARKS | {9, 10, 11, 12, 23, 24}
        else:
            return self._LEFT_LANDMARKS | self._CENTER_LANDMARKS | {9, 10, 11, 12, 23, 24}

    def draw_pose_landmarks(self, frame, landmarks, mp_drawing, mp_holistic, mp_drawing_styles, side=None):
        """
        繪製姿態關鍵點（支援側邊過濾）

        Args:
            frame: OpenCV 影像
            landmarks: MediaPipe pose landmarks
            mp_drawing: mediapipe.solutions.drawing_utils
            mp_holistic: mediapipe.solutions.holistic
            mp_drawing_styles: mediapipe.solutions.drawing_styles
            side: 'left'/'right' 僅畫該側，None 畫全部
        """
        if side is None:
            mp_drawing.draw_landmarks(
                frame, landmarks, mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
        else:
            filtered_conns = self._filter_connections_by_side(mp_holistic.POSE_CONNECTIONS, side)
            visible_indices = self._get_visible_landmarks(side)
            h, w = frame.shape[:2]
            # 繪製連線
            for a, b in filtered_conns:
                lm_a = landmarks.landmark[a]
                lm_b = landmarks.landmark[b]
                pt_a = (int(lm_a.x * w), int(lm_a.y * h))
                pt_b = (int(lm_b.x * w), int(lm_b.y * h))
                cv2.line(frame, pt_a, pt_b, (0, 255, 0), 2)
            # 繪製關鍵點
            for idx in visible_indices:
                lm = landmarks.landmark[idx]
                pt = (int(lm.x * w), int(lm.y * h))
                cv2.circle(frame, pt, 4, (0, 0, 255), -1)

    def draw_angle_lines(self, frame, landmarks, angles, side, show_lines, show_values):
        """
        繪製角度測量線和角度數值

        Args:
            frame: OpenCV 影像
            landmarks: MediaPipe pose landmarks
            angles: 角度字典
            side: 分析側邊 ('left' / 'right')
            show_lines: 是否顯示角度線
            show_values: 是否顯示角度數值

        Returns:
            (frame, text_items): 影像和文字項目清單
        """
        if landmarks is None:
            return frame, []

        text_items = []
        h, w = frame.shape[:2]
        cfg = self.config
        ac = self.angle_calc

        def get_point(idx):
            lm = landmarks.landmark[idx]
            return (int(lm.x * w), int(lm.y * h))

        # 頸部角度線（紅色）
        if show_lines and angles.get('neck') is not None:
            left_eye = get_point(ac.LEFT_EYE)
            right_eye = get_point(ac.RIGHT_EYE)
            left_shoulder = get_point(ac.LEFT_SHOULDER)
            right_shoulder = get_point(ac.RIGHT_SHOULDER)

            eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
            shoulder_center = ((left_shoulder[0] + right_shoulder[0]) // 2, (left_shoulder[1] + right_shoulder[1]) // 2)

            cv2.line(frame, eye_center, shoulder_center, cfg.COLOR_NECK, cfg.ANGLE_LINE_THICKNESS)

            if show_values:
                mid_point = ((eye_center[0] + shoulder_center[0]) // 2, (eye_center[1] + shoulder_center[1]) // 2)
                text_items.append({
                    'text': f"{angles['neck']:.1f}\u00b0", 'position': mid_point,
                    'font': self.font_chinese_small, 'color': cfg.COLOR_NECK,
                    'bg_style': 'transparent',
                })

        # 軀幹角度線（橙色）
        if show_lines and angles.get('trunk') is not None:
            left_shoulder = get_point(ac.LEFT_SHOULDER)
            right_shoulder = get_point(ac.RIGHT_SHOULDER)
            left_hip = get_point(ac.LEFT_HIP)
            right_hip = get_point(ac.RIGHT_HIP)

            shoulder_center = ((left_shoulder[0] + right_shoulder[0]) // 2, (left_shoulder[1] + right_shoulder[1]) // 2)
            hip_center = ((left_hip[0] + right_hip[0]) // 2, (left_hip[1] + right_hip[1]) // 2)

            cv2.line(frame, shoulder_center, hip_center, cfg.COLOR_TRUNK, cfg.ANGLE_LINE_THICKNESS)

            if show_values:
                mid_point = ((shoulder_center[0] + hip_center[0]) // 2, (shoulder_center[1] + hip_center[1]) // 2)
                text_items.append({
                    'text': f"{angles['trunk']:.1f}\u00b0", 'position': mid_point,
                    'font': self.font_chinese_small, 'color': cfg.COLOR_TRUNK,
                    'bg_style': 'transparent',
                })

        # 上臂角度線（黃色）— vertical_ref→shoulder→elbow（上臂與垂直線夾角）
        if show_lines and angles.get('upper_arm') is not None:
            if side == 'right':
                shoulder = get_point(ac.RIGHT_SHOULDER)
                elbow = get_point(ac.RIGHT_ELBOW)
            else:
                shoulder = get_point(ac.LEFT_SHOULDER)
                elbow = get_point(ac.LEFT_ELBOW)

            # 垂直參考線：從肩膀向下延伸 60 像素
            vertical_ref = (shoulder[0], shoulder[1] + 60)
            cv2.line(frame, vertical_ref, shoulder, cfg.COLOR_UPPER_ARM, cfg.ANGLE_LINE_THICKNESS)
            cv2.line(frame, shoulder, elbow, cfg.COLOR_UPPER_ARM, cfg.ANGLE_LINE_THICKNESS)

            if show_values:
                offset_x = 20 if side == 'right' else -80
                text_pos = (shoulder[0] + offset_x, shoulder[1] - 10)
                text_items.append({
                    'text': f"{angles['upper_arm']:.1f}\u00b0", 'position': text_pos,
                    'font': self.font_chinese_small, 'color': cfg.COLOR_UPPER_ARM,
                    'bg_style': 'transparent',
                })

        # 前臂角度線（青色 Cyan）
        if show_lines and angles.get('forearm') is not None:
            if side == 'right':
                shoulder = get_point(ac.RIGHT_SHOULDER)
                elbow = get_point(ac.RIGHT_ELBOW)
                wrist = get_point(ac.RIGHT_WRIST)
            else:
                shoulder = get_point(ac.LEFT_SHOULDER)
                elbow = get_point(ac.LEFT_ELBOW)
                wrist = get_point(ac.LEFT_WRIST)

            cv2.line(frame, shoulder, elbow, cfg.COLOR_FOREARM, cfg.ANGLE_LINE_THICKNESS)
            cv2.line(frame, elbow, wrist, cfg.COLOR_FOREARM, cfg.ANGLE_LINE_THICKNESS)

            if show_values:
                offset_x = -80 if side == 'right' else 20
                text_pos = (elbow[0] + offset_x, elbow[1] + 20)
                text_items.append({
                    'text': f"{angles['forearm']:.1f}\u00b0", 'position': text_pos,
                    'font': self.font_chinese_small, 'color': cfg.COLOR_FOREARM,
                    'bg_style': 'transparent',
                })

        # 手腕角度線（綠色）
        if show_lines and angles.get('wrist') is not None:
            if side == 'right':
                wrist = get_point(ac.RIGHT_WRIST)
                index = get_point(ac.RIGHT_INDEX)
            else:
                wrist = get_point(ac.LEFT_WRIST)
                index = get_point(ac.LEFT_INDEX)

            cv2.line(frame, wrist, index, cfg.COLOR_WRIST, cfg.ANGLE_LINE_THICKNESS)

            if show_values:
                offset_x = 20 if side == 'right' else -80
                text_pos = (wrist[0] + offset_x, wrist[1] + 20)
                text_items.append({
                    'text': f"{angles['wrist']:.1f}\u00b0", 'position': text_pos,
                    'font': self.font_chinese_small, 'color': cfg.COLOR_WRIST,
                    'bg_style': 'transparent',
                })

        # 腿部角度線（藍色）
        if show_lines and angles.get('leg') is not None:
            if side == 'right':
                hip = get_point(ac.RIGHT_HIP)
                knee = get_point(ac.RIGHT_KNEE)
                ankle = get_point(ac.RIGHT_ANKLE)
            else:
                hip = get_point(ac.LEFT_HIP)
                knee = get_point(ac.LEFT_KNEE)
                ankle = get_point(ac.LEFT_ANKLE)

            cv2.line(frame, hip, knee, cfg.COLOR_LEG, cfg.ANGLE_LINE_THICKNESS)
            cv2.line(frame, knee, ankle, cfg.COLOR_LEG, cfg.ANGLE_LINE_THICKNESS)

            if show_values:
                offset_x = 20 if side == 'right' else -80
                text_pos = (knee[0] + offset_x, knee[1])
                text_items.append({
                    'text': f"{angles['leg']:.1f}\u00b0", 'position': text_pos,
                    'font': self.font_chinese_small, 'color': cfg.COLOR_LEG,
                    'bg_style': 'transparent',
                })

        return frame, text_items

    def build_reba_text_items(self, reba_score, risk_level, color):
        """
        建立 REBA 分數和風險等級的文字項目清單

        Args:
            reba_score: REBA 分數
            risk_level: 風險等級
            color: BGR 顏色

        Returns:
            text_items 清單
        """
        cfg = self.config
        risk_text = self.get_risk_text_chinese(risk_level)

        reba_pos = (cfg.OVERLAY_REBA_SCORE_X, cfg.OVERLAY_REBA_SCORE_Y)
        risk_pos = (cfg.OVERLAY_RISK_LEVEL_X, cfg.OVERLAY_RISK_LEVEL_Y)

        return [
            {'text': f"REBA\u5206\u6578: {reba_score}", 'position': reba_pos,
             'font': self.font_chinese, 'color': color,
             'bg_style': 'solid', 'bg_color': (0, 0, 0)},
            {'text': f"\u98a8\u96aa\u7b49\u7d1a: {risk_text}", 'position': risk_pos,
             'font': self.font_chinese_small, 'color': color,
             'bg_style': 'solid', 'bg_color': (0, 0, 0)},
        ]

    def draw_all_texts(self, frame, text_items):
        """
        批次繪製所有文字覆蓋層（單次 PIL 轉換）

        Args:
            frame: OpenCV 影像 (BGR)
            text_items: 文字項目清單
        """
        if not text_items:
            return frame

        cfg = self.config
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        for item in text_items:
            text = item['text']
            position = item['position']
            font = item['font']
            color_bgr = item['color']
            bg_style = item.get('bg_style', 'none')
            bg_color_bgr = item.get('bg_color', (0, 0, 0))

            pil_color = (color_bgr[2], color_bgr[1], color_bgr[0])

            if bg_style == 'transparent':
                draw_tmp = ImageDraw.Draw(img_pil)
                bbox = draw_tmp.textbbox(position, text, font=font)
                pad = cfg.TEXT_BG_PADDING
                x1 = max(bbox[0] - pad, 0)
                y1 = max(bbox[1] - pad, 0)
                x2 = min(bbox[2] + pad, img_pil.width)
                y2 = min(bbox[3] + pad, img_pil.height)

                region = img_pil.crop((x1, y1, x2, y2)).convert('RGBA')
                overlay = Image.new('RGBA', region.size, (0, 0, 0, cfg.TEXT_BG_ALPHA))
                region = Image.alpha_composite(region, overlay).convert('RGB')
                img_pil.paste(region, (x1, y1))

            elif bg_style == 'solid':
                draw = ImageDraw.Draw(img_pil)
                bbox = draw.textbbox(position, text, font=font)
                pad = cfg.TEXT_BG_PADDING
                pil_bg = (bg_color_bgr[2], bg_color_bgr[1], bg_color_bgr[0])
                draw.rectangle((bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad), fill=pil_bg)

            draw = ImageDraw.Draw(img_pil)
            draw.text(position, text, font=font, fill=pil_color)

        frame[:] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return frame

    def draw_fps(self, frame, fps):
        """繪製 FPS 顯示"""
        cfg = self.config
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, cfg.FPS_FONT_SCALE,
                    (255, 255, 255), cfg.FPS_FONT_THICKNESS)

    @staticmethod
    def get_risk_text_chinese(risk_level):
        """獲取風險等級中文文字"""
        risk_map = {
            'negligible': '\u53ef\u5ffd\u7565',
            'low': '\u4f4e\u98a8\u96aa',
            'medium': '\u4e2d\u7b49\u98a8\u96aa',
            'high': '\u9ad8\u98a8\u96aa',
            'very_high': '\u6975\u9ad8\u98a8\u96aa'
        }
        return risk_map.get(risk_level, risk_level)

    def get_color_for_risk(self, risk_level: str):
        """根據風險等級獲取 BGR 顏色"""
        return self.config.RISK_COLORS.get(risk_level, (255, 255, 255))
