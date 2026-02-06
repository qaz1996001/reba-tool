# REBA 評分流程：從角度計算到風險等級

本文件整理 `reba_scorer.py` 與 `angle_calculator.py` 的完整計算流程。

---

## 總覽流程圖

```
MediaPipe Pose Landmarks (33 個關鍵點)
        │
        ▼
┌─────────────────────────────┐
│  AngleCalculator             │
│  calculate_all_angles()      │
│  計算 6 個關節角度            │
└──────────┬──────────────────┘
           │
           ▼
   angles = { neck, trunk, upper_arm, forearm, wrist, leg }
           │
           ▼
┌─────────────────────────────────────────────────────┐
│  REBAScorer.calculate_reba_score()                   │
│                                                      │
│  ┌────────────────┐    ┌────────────────┐            │
│  │ Group A (軀幹側)│    │ Group B (手臂側)│            │
│  │                │    │                │            │
│  │ score_trunk()  │    │ score_upper_arm│            │
│  │ score_neck()   │    │ score_forearm()│            │
│  │ score_leg()    │    │ score_wrist()  │            │
│  │      │         │    │      │         │            │
│  │      ▼         │    │      ▼         │            │
│  │  Table A 查表  │    │  Table B 查表  │            │
│  │  [5×3×2]       │    │  [6×2×3]       │            │
│  │      │         │    │      │         │            │
│  │      ▼         │    │      ▼         │            │
│  │ + 負荷分數     │    │ + 握持分數     │            │
│  │ = Score A      │    │ = Score B      │            │
│  └───────┬────────┘    └───────┬────────┘            │
│          │                     │                     │
│          └──────────┬──────────┘                     │
│                     ▼                                │
│              Table C 查表 [12×12]                     │
│                     │                                │
│                     ▼                                │
│              + 活動分數                               │
│              = REBA 最終分數                          │
│                     │                                │
│                     ▼                                │
│              風險等級判定 (5 級)                       │
└─────────────────────────────────────────────────────┘
```

---

## 第一階段：角度計算 (`angle_calculator.py`)

`AngleCalculator.calculate_all_angles(landmarks, side)` 從 MediaPipe 的 33 個 Pose Landmarks 中提取 6 個關節角度。每個關鍵點需 visibility > 0.5 才會被使用。

### 6 個角度的計算方式

| 角度 | 方法 | 使用的關鍵點 | 計算邏輯 | 回傳意義 |
|------|------|-------------|---------|---------|
| **neck** | `calculate_neck_angle()` | 左右眼中心、左右肩中心 | 兩中心連線與**垂直線**的夾角 | 頸部前傾角度 (0° = 直立) |
| **trunk** | `calculate_trunk_angle()` | 左右肩中心、左右髖中心 | 兩中心連線與**垂直線**的夾角 | 軀幹前傾角度 (0° = 直立) |
| **upper_arm** | `calculate_upper_arm_angle()` | 肩膀、肘部、手腕 | 三點夾角 (肘部為頂點) | 肘關節角度 (180° = 手臂垂直) |
| **forearm** | `calculate_forearm_angle()` | 同 upper_arm | `180 - upper_arm_angle` | 肘關節屈曲角度 |
| **wrist** | `calculate_wrist_angle()` | 肘部、手腕、食指 | 三點夾角偏離 180° 的程度 | 手腕屈伸偏差角度 (0° = 中性位) |
| **leg** | `calculate_leg_angle()` | 髖部、膝蓋、腳踝 | 三點夾角 (膝蓋為頂點) | 膝關節角度 (180° = 站直) |

### 角度計算的底層工具

- **`calculate_angle(p1, p2, p3)`**: 標準三點向量夾角，使用 `arccos(dot / (|v1|×|v2|))` 計算。
- **`calculate_angle_from_vertical(p1, p2)`**: 兩點連線與垂直向下方向 `[0, -1]` 的夾角，僅使用 x, y 座標 (2D 投影)。

---

## 第二階段：身體部位評分 (`reba_scorer.py`)

`REBAScorer._score_body_parts(angles)` 將 6 個角度轉換為 6 個部位分數。

### 2A. Group A 部位 (軀幹側)

#### 軀幹 `score_trunk(trunk_angle)` → 1~5 分

| 條件 | 基本分數 |
|------|---------|
| 0~20° | 2 |
| 20~60° | 3 |
| > 60° | 4 |
| 有扭轉或側彎 | +1 (上限 5) |

#### 頸部 `score_neck(neck_angle)` → 1~3 分

| 條件 | 基本分數 |
|------|---------|
| 0~20° | 1 |
| > 20° | 2 |
| 有扭轉或側彎 | +1 (上限 3) |

#### 腿部 `score_leg(leg_angle)` → 1~4 分

| 條件 | 基本分數 |
|------|---------|
| 雙腳支撐且角度 ≥ 150° | 1 |
| 其他 | 2 |

膝蓋彎曲調整 (`knee_flexion = 180 - leg_angle`)：

| 膝蓋彎曲 | 調整 |
|----------|------|
| 30~60° | +1 |
| > 60° | +2 |
| 上限 | 4 |

### 2B. Group B 部位 (手臂側)

#### 上臂 `score_upper_arm(upper_arm_angle)` → 1~6 分

先轉換為屈曲角度：`flexion = 180 - upper_arm_angle`

| 條件 | 基本分數 |
|------|---------|
| -20° ~ 20° | 1 |
| < -20° (伸展 > 20°) | 2 |
| 20° ~ 45° | 2 |
| 45° ~ 90° | 3 |
| > 90° | 4 |

調整因子：

| 條件 | 調整 |
|------|------|
| 外展或旋轉 | +1 |
| 肩膀抬高 | +1 |
| 有支撐 | -1 |
| 範圍 | 1~6 |

#### 前臂 `score_forearm(forearm_angle)` → 1~2 分

| 條件 | 分數 |
|------|------|
| 60° ~ 100° | 1 |
| 其他 | 2 |

#### 手腕 `score_wrist(wrist_angle)` → 1~3 分

| 條件 | 基本分數 |
|------|---------|
| ≤ 15° | 1 |
| > 15° | 2 |
| 有扭轉 | +1 (上限 3) |

> **注意**: 目前程式中 `has_twist`、`has_side_flex`、`is_abducted`、`is_raised`、`has_support` 等調整參數均使用預設值 (`False`)，因為 MediaPipe 2D/3D pose 難以可靠偵測這些細微姿態。

---

## 第三階段：查表計算

### 3A. Table A — 軀幹 × 頸部 × 腿部

維度：`[trunk(1~5)][neck(1~3)][leg(1~2)]`，索引方式：`TABLE_A[trunk-1][neck-1][leg-1]`

```
                  腿部=1  腿部=2
軀幹=1, 頸部=1 :   1       2
軀幹=1, 頸部=2 :   2       3
軀幹=1, 頸部=3 :   3       4
軀幹=2, 頸部=1 :   2       3
軀幹=2, 頸部=2 :   3       4
軀幹=2, 頸部=3 :   4       5
軀幹=3, 頸部=1 :   3       4
軀幹=3, 頸部=2 :   4       5
軀幹=3, 頸部=3 :   4       5
軀幹=4, 頸部=1 :   4       5
軀幹=4, 頸部=2 :   5       6
軀幹=4, 頸部=3 :   5       6
軀幹=5, 頸部=1 :   5       6
軀幹=5, 頸部=2 :   6       7
軀幹=5, 頸部=3 :   6       7
```

查表結果 + **負荷分數** = **Score A**

### 負荷分數 `calculate_load_score(load_weight)`

| 條件 | 分數 |
|------|------|
| < 5 kg | 0 |
| 5~10 kg | 1 |
| ≥ 10 kg | 2 |
| 靜態/重複性 | 至少 2 |
| 突然/震動力量 | +1 |
| 上限 | 3 |

---

### 3B. Table B — 上臂 × 前臂 × 手腕

維度：`[upper_arm(1~6)][forearm(1~2)][wrist(1~3)]`，索引方式：`TABLE_B[upper_arm-1][forearm-1][wrist-1]`

```
                        手腕=1  手腕=2  手腕=3
上臂=1, 前臂=1 :         1       2       2
上臂=1, 前臂=2 :         1       2       3
上臂=2, 前臂=1 :         1       2       3
上臂=2, 前臂=2 :         2       3       4
上臂=3, 前臂=1 :         3       4       5
上臂=3, 前臂=2 :         4       5       5
上臂=4, 前臂=1 :         4       5       5
上臂=4, 前臂=2 :         5       6       7
上臂=5, 前臂=1 :         7       8       8
上臂=5, 前臂=2 :         8       9       9
上臂=6, 前臂=1 :         8       9       9
上臂=6, 前臂=2 :         9       9       9
```

查表結果 + **握持分數** = **Score B**

### 握持分數 `calculate_coupling_score(coupling_quality)`

| 握持品質 | 分數 |
|---------|------|
| good | 0 |
| fair | 1 |
| poor | 2 |
| unacceptable | 3 |

---

### 3C. Table C — Score A × Score B → Score C

維度：`[Score A (1~12)][Score B (1~12)]`，索引方式：`TABLE_C[score_a-1][score_b-1]`

```
      ScoreB: 1   2   3   4   5   6   7   8   9  10  11  12
ScoreA=1  :   1   2   2   3   4   4   5   6   6   7   7   8
ScoreA=2  :   1   2   2   3   4   4   5   6   6   7   7   8
ScoreA=3  :   2   3   3   4   5   5   6   7   7   8   8   9
ScoreA=4  :   3   4   4   4   5   6   7   8   8   9   9   9
ScoreA=5  :   4   4   4   5   6   7   8   8   9   9   9   9
ScoreA=6  :   6   6   6   7   8   8   9   9  10  10  10  10
ScoreA=7  :   7   7   7   8   9   9   9  10  10  11  11  11
ScoreA=8  :   8   8   8   9  10  10  10  10  10  11  11  11
ScoreA=9  :   9   9   9  10  10  10  11  11  11  12  12  12
ScoreA=10 :  10  10  10  11  11  11  11  12  12  12  12  12
ScoreA=11 :  11  11  11  11  12  12  12  12  12  12  12  12
ScoreA=12 :  12  12  12  12  12  12  12  12  12  12  12  12
```

---

## 第四階段：活動調整與最終分數

### 活動分數 `calculate_activity_score()`

| 條件 | 加分 |
|------|------|
| 靜態姿勢 > 1 分鐘 | +1 |
| 高重複動作 > 4 次/分鐘 | +1 |
| 大範圍快速動作改變 | +1 |
| 上限 | 3 |

### 最終公式

```
REBA 最終分數 = Score C + 活動分數
```

---

## 第五階段：風險等級判定

| REBA 分數 | 風險等級 | 中文名稱 | 顏色 | 行動等級 | 建議 |
|-----------|---------|---------|------|---------|------|
| 1 | negligible | 可忽略風險 | 綠色 #00FF00 | AL1 | 不需要處理 |
| 2~3 | low | 低風險 | 淺綠 #90EE90 | AL2 | 有需要時再進行改善 |
| 4~7 | medium | 中等風險 | 黃色 #FFFF00 | AL3 | 進一步調查及必要時改善 |
| 8~10 | high | 高風險 | 橙色 #FFA500 | AL4 | 近日內需調查及改善 |
| 11~15 | very_high | 極高風險 | 紅色 #FF0000 | AL5 | 必須立即調查及改善 |

---

## 完整範例

以下用 `reba_scorer.py` 內建測試數據走一遍：

```
輸入角度:
  neck=25°, trunk=30°, upper_arm=135°, forearm=80°, wrist=10°, leg=175°
  load_weight=5.0 kg, force_coupling='fair'
```

**部位評分:**

| 部位 | 角度 | 評分邏輯 | 分數 |
|------|------|---------|------|
| 軀幹 | 30° | 20~60° → 3 | 3 |
| 頸部 | 25° | > 20° → 2 | 2 |
| 腿部 | 175° | 雙腳支撐且 ≥150° → 1, 膝彎曲 5° < 30° → +0 | 1 |
| 上臂 | 135° | flexion = 180-135 = 45°, 20~45° → 2 | 2 |
| 前臂 | 80° | 60~100° → 1 | 1 |
| 手腕 | 10° | ≤ 15° → 1 | 1 |

**查表:**

| 步驟 | 計算 | 結果 |
|------|------|------|
| Table A | A[3-1][2-1][1-1] = A[2][1][0] | 4 |
| 負荷分數 | 5 kg → 1 | 1 |
| **Score A** | 4 + 1 | **5** |
| Table B | B[2-1][1-1][1-1] = B[1][0][0] | 1 |
| 握持分數 | fair → 1 | 1 |
| **Score B** | 1 + 1 | **2** |
| Table C | C[5-1][2-1] = C[4][1] | 4 |
| 活動分數 | 全 False → 0 | 0 |
| **REBA 最終分數** | 4 + 0 | **4** |
| **風險等級** | 4~7 → medium | **中等風險** |

---

## 程式呼叫鏈

```python
# MediaPipeApp.py 中的呼叫順序
angles = self.angle_calc.calculate_all_angles(landmarks, side)
#  └→ calculate_neck_angle()
#  └→ calculate_trunk_angle()
#  └→ calculate_upper_arm_angle()
#  └→ calculate_forearm_angle()
#  └→ calculate_wrist_angle()
#  └→ calculate_leg_angle()

reba_score, risk_level, details = self.reba_scorer.calculate_reba_score(angles, load_weight, force_coupling)
#  └→ _validate_angles()
#  └→ _score_body_parts()
#       └→ score_trunk() / score_neck() / score_leg()
#       └→ score_upper_arm() / score_forearm() / score_wrist()
#  └→ _calculate_group_a_score()
#       └→ calculate_table_a()    → posture_score_a
#       └→ calculate_load_score() → load_score
#       └→ score_a = posture_score_a + load_score
#  └→ _calculate_group_b_score()
#       └→ calculate_table_b()       → posture_score_b
#       └→ calculate_coupling_score() → coupling_score
#       └→ score_b = posture_score_b + coupling_score
#  └→ _calculate_final_score()
#       └→ calculate_table_c(score_a, score_b) → score_c
#       └→ calculate_activity_score()          → activity_score
#       └→ final_score = score_c + activity_score
#  └→ get_risk_level(final_score) → 'negligible'|'low'|'medium'|'high'|'very_high'
```

---

## 參考文獻

Hignett, S., & McAtamney, L. (2000). Rapid entire body assessment (REBA). *Applied Ergonomics*, 31(2), 201-205.
