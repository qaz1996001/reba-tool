# REBA Tool iPhone 移植規劃

## 一、現況分析

### 目前技術棧

| 元件 | 現有技術 | iPhone 對應方案 |
|------|----------|----------------|
| GUI 框架 | PySide6 (Qt6) | SwiftUI |
| 姿態偵測 | MediaPipe Holistic (Python) | Apple Vision Framework / MediaPipe iOS SDK |
| 影像處理 | OpenCV (cv2) | AVFoundation + Core Image |
| 角度計算 | NumPy + 自製演算法 | Swift + Accelerate framework |
| REBA 計分 | 純 Python 邏輯 | 純 Swift 邏輯（直接移植） |
| 資料紀錄 | CSV / JSON / Markdown | CSV / JSON + Core Data（本地持久化） |
| 中文字型 | Arial.Unicode.ttf (23MB) | iOS 系統內建中文字型 |

### 可直接移植的模組（純邏輯，無平台依賴）

1. **`reba_scorer.py`** — REBA 計分演算法（Table A/B/C、風險等級判定）
2. **`angle_calculator.py`** — 關節角度計算（向量點積、垂直角度）
3. **`data_logger.py`** — 資料紀錄與統計（Welford 演算法、匯出格式）

### 必須重寫的模組

1. **`MediaPipeApp.py`** — 整個 GUI 與影像擷取流程

---

## 二、關鍵技術決策

### 決策 1：姿態偵測方案

| 方案 | 優點 | 缺點 | 建議 |
|------|------|------|------|
| **Apple Vision Framework** | 原生、免費、無額外依賴、Apple 持續優化、隱私友善（裝置端運算） | 僅支援 19 個身體關節點（vs MediaPipe 33 個）| **優先推薦** |
| **MediaPipe iOS SDK** | 與現有 Python 版本 landmark 一致（33 點）、移植角度計算更直接 | 需額外整合 Google 套件、模型檔案增加 App 大小 | 備選方案 |

**建議選擇 Apple Vision Framework**，理由：
- iOS 14+ 的 `VNDetectHumanBodyPoseRequest` 提供 19 個關節點，涵蓋 REBA 所需的所有關鍵部位（肩、肘、腕、髖、膝、踝、頭部）
- 不需要額外的模型檔案，App 體積更小
- Apple Silicon 硬體加速，效能最佳
- 不依賴第三方套件，長期維護成本低

**Apple Vision 關節點對應 REBA 需求：**

```
REBA 需求          Apple Vision 關節點
─────────────────────────────────────────
頸部角度         → nose / neck / root (torso center)
軀幹角度         → neck / root / hip center
上臂角度         → shoulder → elbow
前臂角度         → elbow → wrist
手腕角度         → wrist（搭配手部偵測補充）
腿部角度         → hip → knee → ankle
```

### 決策 2：開發框架

| 方案 | 優點 | 缺點 | 建議 |
|------|------|------|------|
| **原生 Swift + SwiftUI** | 最佳效能、完整存取 Vision/AVFoundation、App Store 審核最順暢 | 僅限 iOS 平台 | **推薦** |
| **Flutter** | 跨平台（iOS + Android）| Vision API 需要 platform channel 橋接、姿態偵測效能損耗 | 未來擴展可考慮 |
| **React Native** | 跨平台、JavaScript 生態 | 效能瓶頸、原生模組整合複雜 | 不建議 |

**建議選擇原生 Swift + SwiftUI**，專注 iOS 平台先做好。

### 決策 3：最低支援版本

- **建議 iOS 16+**（支援 VNDetectHumanBodyPose3DRequest 進行 3D 姿態偵測）
- iOS 14-15 僅有 2D 姿態，但 REBA 部分角度需要深度資訊
- iOS 16+ 市佔率已超過 90%，向下相容成本不值得

---

## 三、系統架構設計

### 整體架構（MVVM + Clean Architecture）

```
┌─────────────────────────────────────────────────────┐
│                    Presentation Layer                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ CameraView  │  │ ResultsView  │  │HistoryView │ │
│  │ (SwiftUI)   │  │ (SwiftUI)    │  │(SwiftUI)   │ │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘ │
│         └────────────┬───┘                 │        │
│              ┌───────┴────────┐            │        │
│              │  ViewModels    │────────────┘        │
│              └───────┬────────┘                     │
├──────────────────────┼──────────────────────────────┤
│                  Domain Layer                        │
│  ┌───────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │AngleCalculator│ │ REBAScorer   │ │ DataLogger │ │
│  │  (Swift)      │ │  (Swift)     │ │  (Swift)   │ │
│  └───────┬───────┘ └──────┬───────┘ └─────┬──────┘ │
├──────────┼─────────────────┼───────────────┼────────┤
│                Infrastructure Layer                  │
│  ┌───────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │ CameraService │ │ PoseDetector │ │FileExporter│ │
│  │(AVFoundation) │ │(Vision Frmwk)│ │(CSV/JSON)  │ │
│  └───────────────┘ └──────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 資料流

```
AVCaptureSession (相機)
    │
    ▼
CMSampleBuffer (每一幀影像)
    │
    ▼
VNDetectHumanBodyPose3DRequest (Apple Vision)
    │
    ▼
VNHumanBodyPose3DObservation (3D 關節點)
    │
    ▼
AngleCalculator.calculateAllAngles(joints:) → [String: Double]
    │
    ▼
REBAScorer.calculateREBA(angles:) → REBAResult
    │
    ▼
ViewModel → SwiftUI View 更新
    │
    ▼
DataLogger.addFrame(result:) → 累積統計
```

### 專案目錄結構

```
REBATool-iOS/
├── REBATool.xcodeproj
├── REBATool/
│   ├── App/
│   │   ├── REBAToolApp.swift              # App 進入點
│   │   └── ContentView.swift              # 主頁面路由
│   │
│   ├── Models/
│   │   ├── JointAngles.swift              # 角度資料模型
│   │   ├── REBAResult.swift               # REBA 結果模型
│   │   ├── RiskLevel.swift                # 風險等級列舉
│   │   └── FrameRecord.swift              # 單幀紀錄模型
│   │
│   ├── Core/
│   │   ├── AngleCalculator.swift          # ← 移植自 angle_calculator.py
│   │   ├── REBAScorer.swift               # ← 移植自 reba_scorer.py
│   │   └── REBATables.swift               # Table A/B/C 資料
│   │
│   ├── Services/
│   │   ├── CameraService.swift            # AVFoundation 相機管理
│   │   ├── PoseDetectionService.swift     # Vision Framework 姿態偵測
│   │   ├── DataLogger.swift               # ← 移植自 data_logger.py
│   │   └── FileExportService.swift        # CSV/JSON 匯出
│   │
│   ├── ViewModels/
│   │   ├── CameraViewModel.swift          # 相機頁面邏輯
│   │   ├── AnalysisViewModel.swift        # 分析結果邏輯
│   │   └── HistoryViewModel.swift         # 歷史紀錄邏輯
│   │
│   ├── Views/
│   │   ├── Camera/
│   │   │   ├── CameraPreviewView.swift    # 相機即時預覽
│   │   │   ├── PoseOverlayView.swift      # 骨架繪製疊加層
│   │   │   └── ScoreOverlayView.swift     # REBA 分數即時顯示
│   │   │
│   │   ├── Analysis/
│   │   │   ├── AngleDetailView.swift      # 各關節角度顯示
│   │   │   ├── REBAScoreView.swift        # REBA 分數與公式
│   │   │   ├── RiskLevelBadge.swift       # 風險等級標示
│   │   │   └── TableCView.swift           # Table C 對照表
│   │   │
│   │   ├── History/
│   │   │   ├── SessionListView.swift      # 分析歷程列表
│   │   │   ├── SessionDetailView.swift    # 單次分析詳情
│   │   │   └── StatisticsView.swift       # 統計圖表
│   │   │
│   │   └── Common/
│   │       ├── ColorScheme.swift          # 風險等級色彩定義
│   │       └── ChartView.swift            # 趨勢圖表元件
│   │
│   ├── Resources/
│   │   └── Assets.xcassets                # 圖示與色彩資源
│   │
│   └── Extensions/
│       ├── VNHumanBodyPose+REBA.swift     # Vision 關節點轉換擴展
│       └── simd+Angle.swift               # SIMD 向量角度計算
│
├── REBAToolTests/
│   ├── AngleCalculatorTests.swift         # 角度計算單元測試
│   ├── REBAScorerTests.swift              # REBA 計分單元測試
│   └── DataLoggerTests.swift              # 資料紀錄單元測試
│
└── REBAToolUITests/
    └── CameraFlowTests.swift              # UI 自動化測試
```

---

## 四、分階段實作計畫

### 第一階段：核心演算法移植與驗證

**目標**：將純邏輯模組移植至 Swift，確保計算結果與 Python 版本一致

**工作項目**：

1. **建立 Xcode 專案**
   - 建立 iOS App 專案（SwiftUI, iOS 16+）
   - 設定專案結構與 Target

2. **移植 `AngleCalculator`**
   - 將 `calculate_angle()` 移植為 Swift（使用 `simd` 向量運算）
   - 將 `calculate_angle_from_vertical()` 移植
   - 移植所有關節角度計算方法
   - 處理 Apple Vision 關節點索引對應（不同於 MediaPipe 的 33 點）

3. **移植 `REBAScorer`**
   - 移植 Table A (5×3×2), Table B (6×2×3), Table C (12×12)
   - 移植所有身體部位計分函式
   - 移植調整因子計算
   - 移植風險等級判定

4. **撰寫單元測試**
   - 使用 Python 版本產生測試案例（輸入角度→預期分數）
   - 確保 Swift 版本輸出與 Python 版本完全一致
   - 邊界條件測試（角度閾值、極端值）

**驗證方式**：
```
Python: calculate_all_angles(test_landmarks) → angles
        calculate_reba(angles) → score
Swift:  calculateAllAngles(testJoints) → angles
        calculateREBA(angles) → score
結果必須完全一致
```

### 第二階段：相機與姿態偵測

**目標**：實現即時相機畫面與 Apple Vision 姿態偵測

**工作項目**：

1. **`CameraService`**
   - 使用 `AVCaptureSession` 設定相機輸入
   - 設定 `AVCaptureVideoDataOutput` 擷取影像幀
   - 處理前後鏡頭切換
   - 處理相機權限請求

2. **`PoseDetectionService`**
   - 整合 `VNDetectHumanBodyPose3DRequest`（iOS 16+，3D 姿態）
   - 將 `VNHumanBodyPose3DObservation` 轉換為 AngleCalculator 可用的格式
   - 處理偵測失敗與低信心度的情況

3. **`CameraPreviewView`**
   - SwiftUI 相機預覽（使用 `UIViewRepresentable` 包裝 `AVCaptureVideoPreviewLayer`）
   - 即時顯示相機畫面

4. **`PoseOverlayView`**
   - 在相機畫面上繪製骨架連線
   - 關節點以彩色圓點標示
   - 使用 `Canvas` 或 `Path` 繪製

5. **效能優化**
   - 使用 `CMSampleBuffer` 直接傳入 Vision 請求（零拷貝）
   - 控制偵測頻率（例如每 2 幀偵測一次）
   - 在背景佇列執行姿態偵測，避免阻塞 UI

### 第三階段：即時分析 UI

**目標**：完成即時 REBA 分析的完整介面

**工作項目**：

1. **`ScoreOverlayView`**
   - 在相機畫面右上角顯示即時 REBA 分數
   - 風險等級色彩標示（與桌面版一致）
   - 動態更新（帶平滑過渡動畫）

2. **`AngleDetailView`**
   - 各關節角度的即時數值顯示
   - 類似桌面版右側面板的資訊
   - 可折疊/展開

3. **`REBAScoreView`**
   - REBA 計分公式分解顯示
   - Score A、Score B、Score C 的來源
   - 各身體部位單項分數

4. **分析控制**
   - 開始/暫停/停止分析
   - 左右側切換（分析左側或右側身體）
   - 負荷重量、握持品質等參數設定

5. **`TableCView`**
   - Table C 對照表顯示（類似桌面版的 `TableCDialog`）
   - 當前分數高亮標示

### 第四階段：資料紀錄與匯出

**目標**：完成資料持久化與分享功能

**工作項目**：

1. **`DataLogger` (Swift 版)**
   - 移植 Welford 串流統計演算法
   - 使用 Core Data 或 SwiftData 儲存分析歷程
   - 每幀紀錄：時間戳、角度、REBA 分數、風險等級

2. **`FileExportService`**
   - CSV 匯出（與桌面版格式相容）
   - JSON 匯出（含完整統計資料）
   - 使用 `UIActivityViewController` 分享檔案

3. **`HistoryView` 系列**
   - 分析歷程列表（日期、時長、平均分數）
   - 單次分析詳情（時間序列圖表、統計摘要）
   - 支援搜尋與篩選

4. **影片回放分析**
   - 從相簿選取影片進行離線分析
   - 使用 `AVAssetReader` 逐幀讀取
   - 進度條與時間軸控制

### 第五階段：打磨與上架

**目標**：UI 優化、測試、App Store 上架

**工作項目**：

1. **UI/UX 打磨**
   - 深色/淺色模式支援
   - iPad 適配（Split View）
   - Dynamic Type（字型大小輔助功能）
   - VoiceOver 無障礙支援

2. **效能調校**
   - Instruments 效能分析（CPU、記憶體、GPU）
   - 電池消耗優化
   - 發熱控制（長時間分析時降低偵測頻率）

3. **測試**
   - 單元測試覆蓋率 > 80%（核心演算法 100%）
   - UI 自動化測試
   - 不同 iPhone 型號實機測試（iPhone 12 ~ 16 系列）
   - 不同光線、角度、距離的姿態偵測準確度測試

4. **App Store 上架準備**
   - App Icon 與 Launch Screen
   - App Store 截圖與預覽影片
   - 隱私權說明（相機權限、照片權限）
   - App Review 指南合規檢查

---

## 五、關節點對應表（MediaPipe → Apple Vision）

以下為 REBA 計算所需的關節點在兩個平台之間的對應關係：

```
REBA 角度          MediaPipe 點位              Apple Vision 點位
─────────────────────────────────────────────────────────────────
頸部 (Neck)       NOSE(0), EYE(2,5)          .topHead, .centerHead
                   SHOULDER(11,12)             .leftShoulder, .rightShoulder

軀幹 (Trunk)      SHOULDER(11,12)             .leftShoulder, .rightShoulder
                   HIP(23,24)                  .leftHip, .rightHip

上臂 (Upper Arm)  SHOULDER(11/12)             .leftShoulder / .rightShoulder
                   ELBOW(13/14)                .leftElbow / .rightElbow

前臂 (Forearm)    SHOULDER(11/12)             .leftShoulder / .rightShoulder
                   ELBOW(13/14)                .leftElbow / .rightElbow
                   WRIST(15/16)                .leftWrist / .rightWrist

手腕 (Wrist)      ELBOW(13/14)                .leftElbow / .rightElbow
                   WRIST(15/16)                .leftWrist / .rightWrist
                   INDEX(19/20)                (需搭配 Hand Pose 偵測)

腿部 (Leg)        HIP(23/24)                  .leftHip / .rightHip
                   KNEE(25/26)                 .leftKnee / .rightKnee
                   ANKLE(27/28)                .leftAnkle / .rightAnkle
```

**注意事項**：
- Apple Vision 的手腕偵測不含手指方向，手腕角度計算需搭配 `VNDetectHumanHandPoseRequest` 取得手指關節點
- Apple Vision 3D 姿態的座標系統與 MediaPipe 不同，需要轉換

---

## 六、iPhone 特有功能建議

### 可利用的 iPhone 硬體優勢

| 功能 | 說明 | 適用場景 |
|------|------|----------|
| **LiDAR 掃描器** | iPhone 12 Pro+ 內建深度感測器 | 更精確的 3D 姿態與距離估測 |
| **TrueDepth 前鏡頭** | 結構光深度感測 | 自拍模式的精確姿態偵測 |
| **超廣角鏡頭** | 更寬廣的拍攝範圍 | 全身入鏡更容易 |
| **Apple Watch 整合** | 手腕加速度計 / 陀螺儀 | 更精確的手腕活動資料 |
| **ARKit** | 空間追蹤 + 場景理解 | 與環境結合的進階分析 |
| **Core ML** | 裝置端機器學習推論 | 自訂姿態模型部署 |
| **HealthKit** | 健康資料整合 | 紀錄人體工學資料到健康 App |

### 建議加入的 iPhone 專屬功能

1. **拍照模式**：除了即時影片，支援拍攝單張照片進行靜態姿勢分析
2. **通知提醒**：設定工作時間，定時提醒使用者進行姿勢檢測
3. **Widget**：桌面小工具顯示今日平均 REBA 分數
4. **Shortcuts 整合**：支援 iOS 捷徑自動化（例如到達辦公室自動開始分析）
5. **分享報告**：透過 AirDrop、LINE、Email 等分享分析報告（PDF 格式）

---

## 七、風險評估與對策

| 風險 | 影響程度 | 對策 |
|------|---------|------|
| Apple Vision 3D 姿態精度不足 | 高 | 準備 MediaPipe iOS SDK 作為備案；比對兩者精度後決定 |
| 手腕角度偵測困難 | 中 | 整合 Hand Pose Detection 補充手指方向資料 |
| 長時間使用發熱 | 中 | 動態調整偵測頻率；低電量模式降級為每 3 幀偵測一次 |
| 不同 iPhone 型號效能差異 | 中 | 自動偵測裝置效能，調整模型複雜度與幀率 |
| App Store 審核被拒 | 低 | 確保隱私政策完善；相機用途說明清楚 |
| 角度計算因座標系差異導致誤差 | 高 | 第一階段就建立完整的交叉驗證測試 |

---

## 八、開發工具與環境需求

- **Xcode 15+**（支援 iOS 17 SDK，向下相容 iOS 16）
- **macOS Sonoma 14+**（Xcode 15 要求）
- **實機測試裝置**：至少一台 iPhone 12+ 以上（支援 3D 姿態偵測）
- **Apple Developer Program**：年費 US$99（App Store 上架必須）
- **Swift 5.9+** / **SwiftUI**
- **版本控制**：Git（延續現有 repository）

---

## 九、核心程式碼移植範例

### AngleCalculator（Python → Swift）

**Python 原始碼：**
```python
def calculate_angle(self, p1, p2, p3):
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
    return angle
```

**Swift 移植版：**
```swift
import simd

struct AngleCalculator {
    /// 計算三點之間的夾角（度）
    static func calculateAngle(
        p1: SIMD3<Float>,
        p2: SIMD3<Float>,  // 頂點
        p3: SIMD3<Float>
    ) -> Float {
        let v1 = p1 - p2
        let v2 = p3 - p2
        let cosAngle = dot(v1, v2) / (length(v1) * length(v2))
        let clampedCos = min(max(cosAngle, -1.0), 1.0)
        return acos(clampedCos) * 180.0 / .pi
    }

    /// 計算線段與垂直方向的夾角（度）
    static func calculateAngleFromVertical(
        p1: SIMD3<Float>,
        p2: SIMD3<Float>
    ) -> Float {
        let direction = SIMD2<Float>(p1.x - p2.x, p1.y - p2.y)
        let vertical = SIMD2<Float>(0, -1)  // 螢幕座標系 Y 軸向下
        let cosAngle = dot(direction, vertical)
            / (length(direction) * length(vertical))
        let clampedCos = min(max(cosAngle, -1.0), 1.0)
        return acos(clampedCos) * 180.0 / .pi
    }
}
```

### REBAScorer（Python → Swift）

```swift
struct REBAScorer {
    // REBA Table A: [trunk-1][neck-1][leg-1]
    static let tableA: [[[Int]]] = [
        [[1,2],[2,3]],   // trunk=1
        [[2,3],[3,4]],   // trunk=2
        [[3,4],[5,5]],   // trunk=3
        [[5,6],[6,7]],   // trunk=4
        [[7,7],[8,8]],   // trunk=5
    ]
    // ... Table B, Table C 同理

    /// 計算軀幹分數
    static func scoreTrunk(angle: Float, hasTwist: Bool = false, hasSideFlex: Bool = false) -> Int {
        var score: Int
        if angle >= 0 && angle <= 5 {
            score = 1
        } else if angle <= 20 {
            score = 2
        } else if angle <= 60 {
            score = 3
        } else {
            score = 4
        }
        if hasTwist || hasSideFlex { score += 1 }
        return min(score, 5)
    }

    /// 完整 REBA 計算
    static func calculateREBA(angles: JointAngles, loadWeight: Float = 0, couplingQuality: CouplingQuality = .good) -> REBAResult {
        // 1. 計算各部位分數
        // 2. 查表 A, B
        // 3. 查表 C
        // 4. 加上調整因子
        // 5. 判定風險等級
        // ...
    }
}
```

---

## 十、總結

### 可行性評估：**高度可行**

- REBA 核心演算法是純數學運算，可無縫移植至 Swift
- Apple Vision Framework 提供足夠的關節點支援 REBA 分析
- iPhone 的相機與運算效能足以支援即時姿態偵測與分析
- SwiftUI 可以快速建構現代化的 iOS 介面

### 預計產出

| 階段 | 產出 |
|------|------|
| 第一階段 | Swift 核心演算法 + 單元測試通過 |
| 第二階段 | 即時相機姿態偵測可運作 |
| 第三階段 | 完整即時分析 UI |
| 第四階段 | 資料紀錄、匯出、歷史回顧 |
| 第五階段 | App Store 上架就緒 |

### 建議執行順序

```
第一階段 ──→ 第二階段 ──→ 第三階段 ──→ 第四階段 ──→ 第五階段
(核心邏輯)   (相機偵測)   (完整 UI)    (資料功能)   (上架打磨)
```

每完成一個階段都可以進行一次完整的驗證與回顧，確保品質再進入下一階段。
