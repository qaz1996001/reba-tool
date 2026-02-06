#!/usr/bin/env python3
"""
角度計算模組
計算REBA評估所需的各關節角度

功能：
1. 計算頸部角度（與垂直線夾角）
2. 計算軀幹角度（與垂直線夾角）
3. 計算上臂角度
4. 計算前臂角度
5. 計算手腕角度
6. 計算腿部角度
"""

import numpy as np
from typing import Dict, Optional, Tuple

class AngleCalculator:
    """角度計算器"""
    
    # MediaPipe Pose關鍵點索引
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32
    
    def __init__(self):
        """初始化"""
        self.min_visibility = 0.5  # 最低可見度閾值
        
    def calculate_angle(self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """
        計算三點形成的角度
        
        Args:
            p1: 第一個點 [x, y, z]
            p2: 頂點 [x, y, z]
            p3: 第三個點 [x, y, z]
            
        Returns:
            角度（度）
        """
        # 創建向量
        v1 = p1 - p2
        v2 = p3 - p2
        
        # 計算角度
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        
        return np.degrees(angle)
    
    def calculate_angle_from_vertical(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """
        計算兩點連線與垂直線的夾角
        
        Args:
            p1: 上方點 [x, y, z]
            p2: 下方點 [x, y, z]
            
        Returns:
            與垂直線的夾角（度）
        """
        # 計算向量
        vector = p1[:2] - p2[:2]  # 只使用x, y座標
        vertical = np.array([0, -1])  # 垂直向下
        
        # 計算角度
        cos_angle = np.dot(vector, vertical) / (np.linalg.norm(vector) * np.linalg.norm(vertical) + 1e-8)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        
        return np.degrees(angle)
    
    def extract_keypoint(self, landmarks, index: int) -> Optional[np.ndarray]:
        """
        提取關鍵點座標
        
        Args:
            landmarks: MediaPipe landmarks
            index: 關鍵點索引
            
        Returns:
            座標 [x, y, z, visibility] 或 None
        """
        if landmarks is None or index >= len(landmarks.landmark):
            return None
        
        landmark = landmarks.landmark[index]
        
        # 檢查可見度
        if landmark.visibility < self.min_visibility:
            return None
        
        return np.array([landmark.x, landmark.y, landmark.z, landmark.visibility])
    
    def calculate_neck_angle(self, landmarks) -> Optional[float]:
        """
        計算頸部角度（肩膀中點與眼睛連線與垂直線的夾角）
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            頸部角度（度）或 None
        """
        # 提取關鍵點
        left_shoulder = self.extract_keypoint(landmarks, self.LEFT_SHOULDER)
        right_shoulder = self.extract_keypoint(landmarks, self.RIGHT_SHOULDER)
        left_eye = self.extract_keypoint(landmarks, self.LEFT_EYE)
        right_eye = self.extract_keypoint(landmarks, self.RIGHT_EYE)
        
        if any(p is None for p in [left_shoulder, right_shoulder, left_eye, right_eye]):
            return None
        
        # 計算中點
        shoulder_center = (left_shoulder + right_shoulder) / 2
        eye_center = (left_eye + right_eye) / 2
        
        # 計算與垂直線的夾角
        angle = self.calculate_angle_from_vertical(eye_center[:3], shoulder_center[:3])
        
        return angle
    
    def calculate_trunk_angle(self, landmarks) -> Optional[float]:
        """
        計算軀幹角度（肩膀中點與臀部中點連線與垂直線的夾角）
        
        Args:
            landmarks: MediaPipe pose landmarks
            
        Returns:
            軀幹角度（度）或 None
        """
        # 提取關鍵點
        left_shoulder = self.extract_keypoint(landmarks, self.LEFT_SHOULDER)
        right_shoulder = self.extract_keypoint(landmarks, self.RIGHT_SHOULDER)
        left_hip = self.extract_keypoint(landmarks, self.LEFT_HIP)
        right_hip = self.extract_keypoint(landmarks, self.RIGHT_HIP)
        
        if any(p is None for p in [left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        # 計算中點
        shoulder_center = (left_shoulder + right_shoulder) / 2
        hip_center = (left_hip + right_hip) / 2
        
        # 計算與垂直線的夾角
        angle = self.calculate_angle_from_vertical(shoulder_center[:3], hip_center[:3])
        
        return angle
    
    def calculate_upper_arm_angle(self, landmarks, side: str = 'right') -> Optional[float]:
        """
        計算上臂角度（肩膀-肘部-手腕）
        
        Args:
            landmarks: MediaPipe pose landmarks
            side: 'left' 或 'right'
            
        Returns:
            上臂角度（度）或 None
        """
        if side == 'left':
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST
        
        # 提取關鍵點
        shoulder = self.extract_keypoint(landmarks, shoulder_idx)
        elbow = self.extract_keypoint(landmarks, elbow_idx)
        wrist = self.extract_keypoint(landmarks, wrist_idx)
        
        if any(p is None for p in [shoulder, elbow, wrist]):
            return None
        
        # 計算角度
        angle = self.calculate_angle(shoulder[:3], elbow[:3], wrist[:3])
        
        return angle
    
    def calculate_forearm_angle(self, landmarks, side: str = 'right') -> Optional[float]:
        """
        計算前臂角度（肘關節屈曲角度）
        
        Args:
            landmarks: MediaPipe pose landmarks
            side: 'left' 或 'right'
            
        Returns:
            前臂角度（度）或 None
        """
        upper_arm_angle = self.calculate_upper_arm_angle(landmarks, side)
        
        if upper_arm_angle is None:
            return None
        
        # 前臂角度 = 180° - 上臂角度
        forearm_angle = 180.0 - upper_arm_angle
        
        return forearm_angle
    
    def calculate_wrist_angle(self, landmarks, side: str = 'right') -> Optional[float]:
        """
        計算手腕角度（手腕屈曲/伸展）
        
        Args:
            landmarks: MediaPipe pose landmarks
            side: 'left' 或 'right'
            
        Returns:
            手腕角度（度）或 None
        """
        if side == 'left':
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
            index_idx = self.LEFT_INDEX
        else:
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST
            index_idx = self.RIGHT_INDEX
        
        # 提取關鍵點
        elbow = self.extract_keypoint(landmarks, elbow_idx)
        wrist = self.extract_keypoint(landmarks, wrist_idx)
        index = self.extract_keypoint(landmarks, index_idx)
        
        if any(p is None for p in [elbow, wrist, index]):
            return None
        
        # 計算角度
        angle = self.calculate_angle(elbow[:3], wrist[:3], index[:3])
        
        # 計算與中性位置（180度）的偏差
        deviation = abs(180.0 - angle)
        
        return deviation
    
    def calculate_leg_angle(self, landmarks, side: str = 'right') -> Optional[float]:
        """
        計算腿部角度（臀部-膝蓋-腳踝）
        
        Args:
            landmarks: MediaPipe pose landmarks
            side: 'left' 或 'right'
            
        Returns:
            腿部角度（度）或 None
        """
        if side == 'left':
            hip_idx = self.LEFT_HIP
            knee_idx = self.LEFT_KNEE
            ankle_idx = self.LEFT_ANKLE
        else:
            hip_idx = self.RIGHT_HIP
            knee_idx = self.RIGHT_KNEE
            ankle_idx = self.RIGHT_ANKLE
        
        # 提取關鍵點
        hip = self.extract_keypoint(landmarks, hip_idx)
        knee = self.extract_keypoint(landmarks, knee_idx)
        ankle = self.extract_keypoint(landmarks, ankle_idx)
        
        if any(p is None for p in [hip, knee, ankle]):
            return None
        
        # 計算角度
        angle = self.calculate_angle(hip[:3], knee[:3], ankle[:3])
        
        return angle
    
    def calculate_all_angles(self, landmarks, side: str = 'right') -> Dict[str, Optional[float]]:
        """
        計算所有REBA所需角度
        
        Args:
            landmarks: MediaPipe pose landmarks
            side: 'left' 或 'right' (用於上肢和下肢)
            
        Returns:
            包含所有角度的字典
        """
        angles = {
            'neck': self.calculate_neck_angle(landmarks),
            'trunk': self.calculate_trunk_angle(landmarks),
            'upper_arm': self.calculate_upper_arm_angle(landmarks, side),
            'forearm': self.calculate_forearm_angle(landmarks, side),
            'wrist': self.calculate_wrist_angle(landmarks, side),
            'leg': self.calculate_leg_angle(landmarks, side)
        }
        
        return angles
    
    def get_angle_summary(self, angles: Dict[str, Optional[float]]) -> str:
        """
        獲取角度摘要文字
        
        Args:
            angles: 角度字典
            
        Returns:
            摘要文字
        """
        summary = []
        
        for name, angle in angles.items():
            if angle is not None:
                summary.append(f"{name}: {angle:.1f}°")
            else:
                summary.append(f"{name}: N/A")
        
        return " | ".join(summary)