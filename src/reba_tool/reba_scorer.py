#!/usr/bin/env python3
"""
REBA評分模組 (Rapid Entire Body Assessment Scoring Module)
完整實現REBA人因工程評估方法

功能：
1. 根據關節角度計算各部位評分
2. 實現完整的REBA評分表（表A、表B、表C）
3. 判定風險等級（5個等級）
4. 提供風險描述和顏色編碼
5. 考慮負荷、握持品質、活動等調整因子

REBA評分標準:
- 分數1: 可忽略風險 (Negligible risk)
- 分數2-3: 低風險 (Low risk)
- 分數4-7: 中等風險 (Medium risk)
- 分數8-10: 高風險 (High risk)
- 分數11+: 極高風險 (Very high risk)

參考文獻:
Hignett, S., & McAtamney, L. (2000). Rapid entire body assessment (REBA). 
Applied ergonomics, 31(2), 201-205.

作者：人因工程研究團隊
日期：2025年1月
版本：1.0
"""

from typing import Dict, Optional, Tuple, List
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class REBAScorer:
    """
    REBA評分計算器
    
    提供完整的REBA評估功能，包括：
    - 各身體部位評分
    - 查表計算
    - 風險等級判定
    - 視覺化支援
    """
    
    # ==================== 風險等級定義 ====================
    
    RISK_LEVELS = {
        'negligible': (1, 1),      # 可忽略風險
        'low': (2, 3),             # 低風險
        'medium': (4, 7),          # 中等風險
        'high': (8, 10),           # 高風險
        'very_high': (11, 15)      # 極高風險
    }
    
    # 風險等級對應顏色（用於視覺化）
    RISK_COLORS = {
        'negligible': '#00FF00',   # 綠色
        'low': '#90EE90',          # 淺綠色
        'medium': '#FFFF00',       # 黃色
        'high': '#FFA500',         # 橙色
        'very_high': '#FF0000'     # 紅色
    }
    
    # 風險等級中文名稱
    RISK_NAMES_ZH = {
        'negligible': '可忽略風險',
        'low': '低風險',
        'medium': '中等風險',
        'high': '高風險',
        'very_high': '極高風險'
    }
    
    # ==================== REBA評分表（多維陣列，直接索引）====================

    # 表A：軀幹、頸部、腿部組合評分表
    # 維度: [軀幹(1-5)][頸部(1-3)][腿部(1-2)]
    # 使用方式: TABLE_A[trunk-1][neck-1][leg-1]
    TABLE_A = [
        # 軀幹分數 = 1
        [[1, 2],  # 頸部=1, 腿部=1-2
         [2, 3],  # 頸部=2, 腿部=1-2
         [3, 4]], # 頸部=3, 腿部=1-2

        # 軀幹分數 = 2
        [[2, 3],  # 頸部=1
         [3, 4],  # 頸部=2
         [4, 5]], # 頸部=3

        # 軀幹分數 = 3
        [[3, 4],  # 頸部=1
         [4, 5],  # 頸部=2
         [4, 5]], # 頸部=3

        # 軀幹分數 = 4
        [[4, 5],  # 頸部=1
         [5, 6],  # 頸部=2
         [5, 6]], # 頸部=3

        # 軀幹分數 = 5
        [[5, 6],  # 頸部=1
         [6, 7],  # 頸部=2
         [6, 7]], # 頸部=3
    ]

    # 表B：上臂、前臂、手腕組合評分表
    # 維度: [上臂(1-6)][前臂(1-2)][手腕(1-3)]
    # 使用方式: TABLE_B[upper_arm-1][forearm-1][wrist-1]
    TABLE_B = [
        # 上臂分數 = 1
        [[1, 2, 2],  # 前臂=1, 手腕=1-3
         [1, 2, 3]], # 前臂=2, 手腕=1-3

        # 上臂分數 = 2
        [[1, 2, 3],  # 前臂=1
         [2, 3, 4]], # 前臂=2

        # 上臂分數 = 3
        [[3, 4, 5],  # 前臂=1
         [4, 5, 5]], # 前臂=2

        # 上臂分數 = 4
        [[4, 5, 5],  # 前臂=1
         [5, 6, 7]], # 前臂=2

        # 上臂分數 = 5
        [[7, 8, 8],  # 前臂=1
         [8, 9, 9]], # 前臂=2

        # 上臂分數 = 6
        [[8, 9, 9],  # 前臂=1
         [9, 9, 9]], # 前臂=2
    ]

    # 表C：表A和表B組合的最終評分表
    # 維度: [表A分數(1-12)][表B分數(1-9)]
    # 使用方式: TABLE_C[score_a-1][score_b-1]
    # TABLE_C = [
    #     # 表A分數 = 1
    #     [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7],  # 表B=1-9
    #     # 表A分數 = 2
    #     [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],  # 表B=1-9
    #     # [1, 2, 3, 4, 5, 6, 7, 8, 9],  # 表B=1-9

    #     # 表A分數 = 3
    #     [2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 8, 8],
    #     # [2, 3, 4, 5, 6, 7, 8, 9, 9],  # 表B=1-9

    #     # 表A分數 = 4
    #     [3, 4, 5, 6, 7, 8, 9, 9, 9],  # 表B=1-9

    #     # 表A分數 = 5
    #     [4, 5, 6, 7, 8, 9, 9, 9, 9],  # 表B=1-9

    #     # 表A分數 = 6
    #     [5, 6, 7, 8, 9, 10, 10, 10, 10],  # 表B=1-9

    #     # 表A分數 = 7
    #     [5, 6, 7, 8, 9, 10, 10, 10, 10],  # 表B=1-9

    #     # 表A分數 = 8
    #     [6, 7, 8, 9, 10, 11, 11, 11, 11],  # 表B=1-9

    #     # 表A分數 = 9
    #     [7, 8, 9, 10, 11, 11, 11, 12, 12],  # 表B=1-9

    #     # 表A分數 = 10
    #     [7, 8, 9, 10, 11, 11, 11, 12, 12],  # 表B=1-9

    #     # 表A分數 = 11
    #     [8, 9, 10, 11, 11, 12, 12, 12, 12],  # 表B=1-9

    #     # 表A分數 = 12
    #     [8, 9, 10, 11, 11, 12, 12, 12, 12],  # 表B=1-9
    # ]
  
    TABLE_C = [[1,  1,  1,  2,  3,  3,  4,  5,  6,  7,  7,  7],
               [1,  2,  2,  3,  4,  4,  5,  6,  6,  7,  7,  8],
               [2,  3,  3,  3,  4,  5,  6,  7,  7,  8,  8,  8],
               [3,  4,  4,  4,  5,  6,  7,  8,  8,  9,  9,  9],
               [4,  4,  4,  5,  6,  7,  8,  8,  9,  9,  9,  9],
               [6,  6,  6,  7,  8,  8,  9,  9,  10, 10, 10, 10],
               [7,  7,  7,  8,  9,  9,  9,  10, 10, 11, 11, 11],
               [8,  8,  8,  9,  10, 10, 10, 10, 10, 11, 11, 11],
               [9,  9,  9,  10, 10, 10, 11, 11, 11, 12, 12, 12],
               [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],
               [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],
               [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]]


    
    def __init__(self):
        """初始化REBA評分器"""
        logger.info("REBA評分器初始化完成")
    
    # ==================== 身體部位評分方法 ====================
    
    def score_trunk(self, trunk_angle: float, has_twist: bool = False, 
                   has_side_flex: bool = False) -> int:
        """
        軀幹評分
        
        Args:
            trunk_angle: 軀幹角度（度），與垂直線的夾角
            has_twist: 是否有扭轉
            has_side_flex: 是否有側向彎曲
            
        Returns:
            軀幹分數 (1-5)
            
        評分標準：
        - 1分: 近乎直立 (≤5°)
        - 2分: 屈曲或伸展 5-20°
        - 3分: 屈曲 20-60° 或 伸展 >20°
        - 4分: 屈曲 >60°
        - 加分: 扭轉或側向彎曲 +1
        """
        # 基本分數
        if trunk_angle <= 5:
            base_score = 1  # 近乎直立（REBA Step 2: erect）
        elif trunk_angle <= 20:
            base_score = 2  # 0-20度屈曲/伸展
        elif trunk_angle <= 60:
            base_score = 3  # 20-60度屈曲
        else:
            base_score = 4  # >60度屈曲
        
        # 調整分數
        adjustment = 0
        if has_twist or has_side_flex:
            adjustment += 1
        
        final_score = min(base_score + adjustment, 5)  # 最高5分
        
        logger.debug(f"軀幹評分: 角度={trunk_angle:.1f}°, 基本分數={base_score}, "
                    f"調整={adjustment}, 最終分數={final_score}")
        
        return final_score
    
    def score_neck(self, neck_angle: float, has_twist: bool = False,
                  has_side_flex: bool = False) -> int:
        """
        頸部評分
        
        Args:
            neck_angle: 頸部角度（度），與垂直線的夾角
            has_twist: 是否有扭轉
            has_side_flex: 是否有側向傾斜
            
        Returns:
            頸部分數 (1-3)
            
        評分標準：
        - 1分: 屈曲 0-20°
        - 2分: 屈曲 >20° 或任何伸展
        - 加分: 扭轉或側向傾斜 +1
        """
        # 基本分數
        if neck_angle <= 20:
            base_score = 1
        else:
            base_score = 2
        
        # 調整分數
        adjustment = 0
        if has_twist or has_side_flex:
            adjustment += 1
        
        final_score = min(base_score + adjustment, 3)  # 最高3分
        
        logger.debug(f"頸部評分: 角度={neck_angle:.1f}°, 基本分數={base_score}, "
                    f"調整={adjustment}, 最終分數={final_score}")
        
        return final_score
    
    def score_leg(self, leg_angle: float, bilateral_support: bool = True) -> int:
        """
        腿部評分

        Args:
            leg_angle: 膝關節屈曲角度（度），0°=伸直, 90°=直角彎曲
            bilateral_support: 是否雙腳支撐

        Returns:
            腿部分數 (1-4)

        評分標準：
        - 1分: 雙腳支撐，行走或坐姿
        - 2分: 單腳站立或膝蓋彎曲
        - 加分: 膝蓋彎曲30-60° +1
        - 加分: 膝蓋彎曲>60° +2
        """
        # 基本分數（屈曲角度 ≤30° 視為「幾乎站直」）
        if bilateral_support and leg_angle <= 30:
            base_score = 1  # 雙腳支撐，幾乎站直
        else:
            base_score = 2  # 單腳或膝蓋彎曲

        # 膝蓋彎曲調整（直接使用屈曲角度）
        knee_flexion = leg_angle
        adjustment = 0
        if 30 <= knee_flexion <= 60:
            adjustment += 1
        elif knee_flexion > 60:
            adjustment += 2

        final_score = min(base_score + adjustment, 4)  # 最高4分

        logger.debug(f"腿部評分: 屈曲={knee_flexion:.1f}°, "
                    f"基本分數={base_score}, 調整={adjustment}, 最終分數={final_score}")
        
        return final_score
    
    def score_upper_arm(self, upper_arm_angle: float, is_abducted: bool = False,
                       is_raised: bool = False, has_support: bool = False) -> int:
        """
        上臂評分

        Args:
            upper_arm_angle: 上臂與垂直線的夾角（度），0°=自然下垂, 90°=水平抬起
                gravity-relative 的 unsigned angle (0-180°)
            is_abducted: 手臂是否外展或旋轉
            is_raised: 肩膀是否抬高
            has_support: 是否有支撐點或姿勢順應重力

        Returns:
            上臂分數 (1-6)

        評分標準（gravity-relative unsigned angle）：
        - 1分: ≤20°（近乎下垂，含 extension 和 minor flexion）
        - 2分: 20-45°（輕度抬起）
        - 3分: 45-90°（中度抬起）
        - 4分: >90°（超過水平）
        - 加分: 外展或旋轉 +1
        - 加分: 肩膀抬高 +1
        - 減分: 有支撐點 -1
        """
        # gravity-relative angle: 0°=下垂, 90°=水平, 180°=過頭
        flexion = upper_arm_angle

        # 基本分數
        if flexion <= 20:
            base_score = 1    # 近乎下垂（±20°）
        elif flexion <= 45:
            base_score = 2    # 輕度抬起
        elif flexion <= 90:
            base_score = 3    # 中度抬起
        else:
            base_score = 4    # 超過水平
        
        # 調整分數
        adjustment = 0
        if is_abducted:
            adjustment += 1
        if is_raised:
            adjustment += 1
        if has_support:
            adjustment -= 1
        
        final_score = max(1, min(base_score + adjustment, 6))  # 1-6分
        
        logger.debug(f"上臂評分: 角度={upper_arm_angle:.1f}°, 屈曲={flexion:.1f}°, "
                    f"基本分數={base_score}, 調整={adjustment}, 最終分數={final_score}")
        
        return final_score
    
    def score_forearm(self, forearm_angle: float) -> int:
        """
        前臂評分

        Args:
            forearm_angle: 前臂屈曲角度（度）
                0° = 完全伸直, 90° = 直角彎曲

        Returns:
            前臂分數 (1-2)

        評分標準：
        - 1分: 屈曲60-100°
        - 2分: 屈曲<60° 或 >100°
        """
        # 傳入的已是屈曲角度，直接使用
        flexion = forearm_angle

        if 60 <= flexion <= 100:
            score = 1
        else:
            score = 2

        logger.debug(f"前臂評分: 屈曲={flexion:.1f}°, 分數={score}")

        return score
    
    def score_wrist(self, wrist_angle: float, has_twist: bool = False) -> int:
        """
        手腕評分
        
        Args:
            wrist_angle: 手腕偏差角度（度），與中性位置的偏差
            has_twist: 是否有扭轉或橈尺偏
            
        Returns:
            手腕分數 (1-3)
            
        評分標準：
        - 1分: 中性位置或屈伸0-15°
        - 2分: 屈曲或伸展>15°
        - 加分: 扭轉或橈尺偏 +1
        """
        # 基本分數
        if wrist_angle <= 15:
            base_score = 1
        else:
            base_score = 2
        
        # 調整分數
        adjustment = 0
        if has_twist:
            adjustment += 1
        
        final_score = min(base_score + adjustment, 3)  # 最高3分
        
        logger.debug(f"手腕評分: 偏差={wrist_angle:.1f}°, 基本分數={base_score}, "
                    f"調整={adjustment}, 最終分數={final_score}")
        
        return final_score
    
    # ==================== REBA表格查詢方法 ====================
    
    def calculate_table_a(self, trunk_score: int, neck_score: int, 
                         leg_score: int) -> int:
        """
        查詢表A：軀幹、頸部、腿部組合評分
        
        Args:
            trunk_score: 軀幹分數 (1-5)
            neck_score: 頸部分數 (1-3)
            leg_score: 腿部分數 (1-4)
            
        Returns:
            表A分數 (1-9)
        """
        # 限制輸入範圍並轉換為陣列索引（0-based）
        trunk_idx = max(0, min(trunk_score - 1, 4))  # 0-4 for trunk 1-5
        neck_idx = max(0, min(neck_score - 1, 2))    # 0-2 for neck 1-3
        leg_idx = max(0, min(leg_score - 1, 1))      # 0-1 for leg 1-2

        # 直接陣列索引（無 .get()，無預設值）
        score = self.TABLE_A[trunk_idx][neck_idx][leg_idx]

        logger.debug(f"表A查詢: 軀幹={trunk_score}, 頸部={neck_score}, "
                    f"腿部={leg_score} → 分數={score}")

        return score
    
    def calculate_table_b(self, upper_arm_score: int, forearm_score: int,
                         wrist_score: int) -> int:
        """
        查詢表B：上臂、前臂、手腕組合評分
        
        Args:
            upper_arm_score: 上臂分數 (1-6)
            forearm_score: 前臂分數 (1-2)
            wrist_score: 手腕分數 (1-3)
            
        Returns:
            表B分數 (1-9)
        """
        # 限制輸入範圍並轉換為陣列索引（0-based）
        upper_arm_idx = max(0, min(upper_arm_score - 1, 5))  # 0-5 for upper_arm 1-6
        forearm_idx = max(0, min(forearm_score - 1, 1))      # 0-1 for forearm 1-2
        wrist_idx = max(0, min(wrist_score - 1, 2))          # 0-2 for wrist 1-3

        # 直接陣列索引（無 .get()，無預設值）
        score = self.TABLE_B[upper_arm_idx][forearm_idx][wrist_idx]

        logger.debug(f"表B查詢: 上臂={upper_arm_score}, 前臂={forearm_score}, "
                    f"手腕={wrist_score} → 分數={score}")

        return score
    
    def calculate_table_c(self, score_a: int, score_b: int) -> int:
        """
        查詢表C：表A和表B組合的最終評分
        
        Args:
            score_a: 表A分數 (1-12)
            score_b: 表B分數 (1-12)
            
        Returns:
            表C分數 (1-12)
        """
        # 限制輸入範圍並轉換為陣列索引（0-based）
        score_a_idx = max(0, min(score_a - 1, 11))  # 0-11 for score_a 1-12
        score_b_idx = max(0, min(score_b - 1, 11))  # 0-11 for score_b 1-12

        # 直接陣列索引（無 .get()，無預設值）
        score = self.TABLE_C[score_a_idx][score_b_idx]

        logger.debug(f"表C查詢: 表A={score_a}, 表B={score_b} → 分數={score}")

        return score
    
    # ==================== 負荷與握持評分 ====================
    
    def calculate_load_score(self, load_weight: float, 
                            is_static: bool = False,
                            is_repetitive: bool = False,
                            is_shock: bool = False) -> int:
        """
        計算負荷/力量評分
        
        Args:
            load_weight: 負荷重量（kg）
            is_static: 是否為靜態負荷或持續>10分鐘
            is_repetitive: 是否為重複性負荷
            is_shock: 是否有突然或震動力量
            
        Returns:
            負荷分數 (0-3)
            
        評分標準：
        - 0分: <5kg 間歇性
        - +1分: 5-10kg 間歇性
        - +2分: >10kg 或 靜態/重複>10分鐘
        - +1分: 突然或震動力量
        """
        score = 0
        
        if load_weight < 5:
            score = 0
        elif load_weight < 10:
            score = 1
        else:
            score = 2
        
        # 靜態或重複性調整
        if is_static or is_repetitive:
            score = max(score, 2)
        
        # 突然或震動力量
        if is_shock:
            score += 1
        
        score = min(score, 3)  # 最高3分
        
        logger.debug(f"負荷評分: 重量={load_weight}kg, 靜態={is_static}, "
                    f"重複={is_repetitive}, 震動={is_shock} → 分數={score}")
        
        return score
    
    def calculate_coupling_score(self, coupling_quality: str) -> int:
        """
        計算握持品質評分
        
        Args:
            coupling_quality: 握持品質
                - 'good': 良好握持，合適把手
                - 'fair': 可接受但非理想
                - 'poor': 握持不可接受但可能
                - 'unacceptable': 無把手、笨拙、不安全
                
        Returns:
            握持分數 (0-3)
        """
        coupling_scores = {
            'good': 0,
            'fair': 1,
            'poor': 2,
            'unacceptable': 3
        }
        
        score = coupling_scores.get(coupling_quality.lower(), 0)
        
        logger.debug(f"握持評分: 品質={coupling_quality} → 分數={score}")
        
        return score
    
    def calculate_activity_score(self, is_static: bool = False,
                                is_repetitive: bool = False,
                                has_large_changes: bool = False) -> int:
        """
        計算活動評分
        
        Args:
            is_static: 是否為靜態姿勢（持續>1分鐘）
            is_repetitive: 是否為高重複動作（>4次/分鐘）
            has_large_changes: 是否有大範圍快速動作改變
            
        Returns:
            活動分數 (0-3)
        """
        score = 0
        
        if is_static:
            score += 1
        if is_repetitive:
            score += 1
        if has_large_changes:
            score += 1
        
        logger.info(f"活動評分: 靜態={is_static}, 重複={is_repetitive}, "
                    f"大範圍={has_large_changes} → 分數={score}")
        
        return score
    
    # ==================== 完整REBA計算 ====================

    def _validate_angles(self, angles: Dict[str, Optional[float]]) -> bool:
        """驗證必要的角度數據"""
        required_angles = ['trunk', 'neck', 'leg', 'upper_arm', 'forearm', 'wrist']
        if not all(angles.get(key) is not None for key in required_angles):
            logger.warning("缺少必要的角度數據")
            return False
        return True

    def _score_body_parts(self, angles: Dict[str, Optional[float]]) -> Dict[str, int]:
        """計算各身體部位分數"""
        return {
            'trunk': self.score_trunk(angles['trunk']),
            'neck': self.score_neck(angles['neck']),
            'leg': self.score_leg(angles['leg']),
            'upper_arm': self.score_upper_arm(angles['upper_arm']),
            'forearm': self.score_forearm(angles['forearm']),
            'wrist': self.score_wrist(angles['wrist'])
        }

    def _calculate_group_a_score(self, scores: Dict[str, int], load_weight: float,
                                 is_static: bool, is_repetitive: bool) -> Dict[str, int]:
        """計算Group A分數（軀幹、頸部、腿部 + 負荷）"""
        posture_score_a = self.calculate_table_a(scores['trunk'], scores['neck'], scores['leg'])
        load_score = self.calculate_load_score(load_weight, is_static, is_repetitive)
        return {
            'posture_score_a': posture_score_a,
            'load_score': load_score,
            'score_a': posture_score_a + load_score
        }

    def _calculate_group_b_score(self, scores: Dict[str, int],
                                 force_coupling: str) -> Dict[str, int]:
        """計算Group B分數（上臂、前臂、手腕 + 握持）"""
        posture_score_b = self.calculate_table_b(scores['upper_arm'], scores['forearm'], scores['wrist'])
        coupling_score = self.calculate_coupling_score(force_coupling)
        return {
            'posture_score_b': posture_score_b,
            'coupling_score': coupling_score,
            'score_b': posture_score_b + coupling_score
        }

    def _calculate_final_score(self, score_a: int, score_b: int,
                               is_static: bool, is_repetitive: bool,
                               has_large_changes: bool) -> Dict[str, int]:
        """計算最終分數（Table C + 活動）"""
        score_c = self.calculate_table_c(score_a, score_b)
        activity_score = self.calculate_activity_score(is_static, is_repetitive, has_large_changes)
        return {
            'score_c': score_c,
            'activity_score': activity_score,
            'final_score': score_c + activity_score
        }

    def _build_details_dict(self, body_scores: Dict[str, int],
                           group_a: Dict[str, int], group_b: Dict[str, int],
                           final: Dict[str, int], risk_level: str) -> Dict:
        """構建詳細分數字典"""
        return {
            # 各部位分數
            'trunk_score': body_scores['trunk'],
            'neck_score': body_scores['neck'],
            'leg_score': body_scores['leg'],
            'upper_arm_score': body_scores['upper_arm'],
            'forearm_score': body_scores['forearm'],
            'wrist_score': body_scores['wrist'],
            # 表格分數
            'posture_score_a': group_a['posture_score_a'],
            'load_score': group_a['load_score'],
            'score_a': group_a['score_a'],
            'posture_score_b': group_b['posture_score_b'],
            'coupling_score': group_b['coupling_score'],
            'score_b': group_b['score_b'],
            'score_c': final['score_c'],
            # 調整分數
            'activity_score': final['activity_score'],
            # 最終結果
            'final_score': final['final_score'],
            'risk_level': risk_level
        }

    def calculate_reba_score(self, angles: Dict[str, Optional[float]],
                            load_weight: float = 0.0,
                            force_coupling: str = 'good',
                            is_static: bool = False,
                            is_repetitive: bool = False,
                            has_large_changes: bool = False) -> Tuple[int, str, Dict]:
        """
        計算完整REBA分數（重構為pipeline模式）

        Args:
            angles: 各關節角度字典，包含：
                - 'neck': 頸部角度
                - 'trunk': 軀幹角度
                - 'leg': 腿部角度
                - 'upper_arm': 上臂角度
                - 'forearm': 前臂角度
                - 'wrist': 手腕角度
            load_weight: 負荷重量（kg）
            force_coupling: 握持品質 ('good'/'fair'/'poor'/'unacceptable')
            is_static: 是否為靜態姿勢
            is_repetitive: 是否為重複動作
            has_large_changes: 是否有大範圍動作改變

        Returns:
            (REBA分數, 風險等級, 詳細分數字典)
        """
        if not self._validate_angles(angles):
            return 0, 'unknown', {}

        try:
            body_scores = self._score_body_parts(angles)
            group_a = self._calculate_group_a_score(body_scores, load_weight, is_static, is_repetitive)
            group_b = self._calculate_group_b_score(body_scores, force_coupling)
            final = self._calculate_final_score(group_a['score_a'], group_b['score_b'],
                                               is_static, is_repetitive, has_large_changes)
            risk_level = self.get_risk_level(final['final_score'])
            details = self._build_details_dict(body_scores, group_a, group_b, final, risk_level)

            # logger.info(f"REBA計算完成: 分數={final['final_score']}, 風險等級={risk_level} , group_b={group_b}")
            return final['final_score'], risk_level, details

        except Exception as e:
            logger.error(f"REBA計算錯誤: {e}")
            return 0, 'unknown', {}
    
    # ==================== 風險等級相關方法 ====================
    
    def get_risk_level(self, reba_score: int) -> str:
        """
        根據REBA分數獲取風險等級
        
        Args:
            reba_score: REBA分數
            
        Returns:
            風險等級名稱
        """
        for level, (min_score, max_score) in self.RISK_LEVELS.items():
            if min_score <= reba_score <= max_score:
                return level
        
        return 'very_high'  # 超過11分視為極高風險
    
    def get_risk_color(self, risk_level: str) -> str:
        """
        獲取風險等級對應顏色（十六進制）
        
        Args:
            risk_level: 風險等級
            
        Returns:
            顏色代碼
        """
        return self.RISK_COLORS.get(risk_level, '#FFFFFF')
    
    def get_risk_color_rgb(self, risk_level: str) -> Tuple[int, int, int]:
        """
        獲取風險等級對應顏色（RGB格式）
        
        Args:
            risk_level: 風險等級
            
        Returns:
            (R, G, B) 元組
        """
        hex_color = self.get_risk_color(risk_level)
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def get_risk_name_zh(self, risk_level: str) -> str:
        """
        獲取風險等級中文名稱
        
        Args:
            risk_level: 風險等級
            
        Returns:
            中文名稱
        """
        return self.RISK_NAMES_ZH.get(risk_level, '未知風險')
    
    def get_risk_description(self, risk_level: str) -> str:
        """
        獲取風險等級描述
        
        Args:
            risk_level: 風險等級
            
        Returns:
            描述文字
        """
        descriptions = {
            'negligible': '可忽略風險 - 不需要處理',
            'low': '低風險 - 有需要時再進行改善',
            'medium': '中等風險 - 需要進一步調查並適時改善',
            'high': '高風險 - 近日內需要進行調查及改善',
            'very_high': '極高風險 - 必須立即進行調查及改善'
        }
        
        return descriptions.get(risk_level, '未知風險')
    
    def get_action_level(self, reba_score: int) -> Tuple[str, str]:
        """
        獲取行動等級和建議
        
        Args:
            reba_score: REBA分數
            
        Returns:
            (行動等級, 建議)
        """
        risk_level = self.get_risk_level(reba_score)
        
        action_levels = {
            'negligible': ('AL1', '不需要處理'),
            'low': ('AL2', '有需要時再進行改善'),
            'medium': ('AL3', '進一步調查及必要時進行改善'),
            'high': ('AL4', '近日內需要進行進一步調查及改善'),
            'very_high': ('AL5', '必須立即進行調查及改善')
        }
        
        return action_levels.get(risk_level, ('Unknown', '未知'))


# ==================== 測試代碼 ====================

if __name__ == "__main__":
    # 創建評分器
    scorer = REBAScorer()
    
    # 測試角度（使用 REBA 圖表定義的屈曲角度）
    test_angles = {
        'neck': 25.0,        # 頸部前傾25度
        'trunk': 30.0,       # 軀幹前傾30度
        'upper_arm': 45.0,   # 上臂抬起45度
        'forearm': 90.0,     # 肘關節屈曲90度（直角彎曲）
        'wrist': 10.0,       # 手腕偏差10度
        'leg': 5.0           # 膝關節屈曲5度（幾乎站直）
    }
    
    # 計算REBA分數
    score, risk, details = scorer.calculate_reba_score(
        test_angles,
        load_weight=5.0,
        force_coupling='fair'
    )
    
    # 顯示結果
    print("\n" + "="*50)
    print("REBA評分測試結果")
    print("="*50)
    print(f"REBA分數: {score}")
    print(f"風險等級: {scorer.get_risk_name_zh(risk)}")
    print(f"顏色: {scorer.get_risk_color(risk)}")
    print(f"描述: {scorer.get_risk_description(risk)}")
    
    action_level, action = scorer.get_action_level(score)
    print(f"行動等級: {action_level}")
    print(f"建議: {action}")
    
    print("\n詳細分數:")
    for key, value in details.items():
        print(f"  {key}: {value}")
    print("="*50)