# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**專案名稱**: REBA Tool
**用途**: 使用 MediaPipe 姿態估計與 PySide6 GUI 的 REBA 人因工程分析工具，即時分析攝影機或影片中的關節角度、計算 REBA 分數、評估工作場所人因風險等級
**技術棧**: Python 3.11, PySide6/Qt6, MediaPipe, OpenCV, QML (新版 UI)

---

## Development Commands

### 環境設定
```bash
# 安裝依賴 (使用 uv 套件管理器)
uv sync

# 執行 Widget 版 (原版)
uv run python src/reba_tool/MediaPipeApp.py

# 執行 QML 版 (新版)
uv run src/reba_tool_qml/main.py
```

### 程式碼品質
```bash
black src/         # 格式化
flake8 src/        # Lint
pytest             # 測試
```

### Git 工作流
```bash
git checkout -b feature/[name]
git commit -m "type(scope): description"
```

### Module Import Convention
後端模組使用直接 import（非套件相對路徑）：`from angle_calculator import AngleCalculator`。QML 版透過 `sys.path.insert(0, reba_tool_dir)` 複用所有後端模組。

---

## Verification Commands

**🎯 核心原則**: 每次修改後，Claude 必須執行驗證

### QML 版驗證
```bash
# 1. 執行 QML 版，確認無 QML 載入錯誤
uv run src/reba_tool_qml/main.py 2>&1 | findstr /i "error unavailable TypeError"

# 2. 確認無 style 警告
uv run src/reba_tool_qml/main.py 2>&1 | findstr /i "does not support customization"

# 3. Lint
flake8 src/reba_tool_qml/
```

### 驗證清單
- [ ] QML 載入無錯誤 (無 "unavailable"、"TypeError")
- [ ] 無 native style 自訂化警告
- [ ] 攝影機/影片播放正常
- [ ] REBA 分數即時更新

### 驗證失敗處理
```
驗證失敗 → 檢查錯誤訊息 → 修復問題 → 重新驗證 → 全部通過 ✅
```

---

## Anti-Patterns & Learnings

**📝 活文件規則**: Claude 犯錯時立即新增記錄

### 錯誤行為紀錄

| 日期 | ❌ 錯誤行為 | ✅ 正確做法 |
|------|------------|------------|
| 2026-02-06 | QML 中宣告 `signal showAngleLinesChanged(...)` 同時有 `property bool showAngleLines`，導致 "Duplicate signal name" | QML property 自動生成 `Changed` 信號，自訂信號必須用不同名稱（如 `angleLinesToggled`） |
| 2026-02-06 | 在 Windows native style 下自訂 Button `background` 和 `contentItem`，產生大量警告 | 在 main.py 中設定 `os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"`（須在 QApplication 建立前） |
| 2026-02-06 | ListView delegate 中用 `parent.parent.ListView.view.indexAt(...)` 取得列索引，每行觸發 TypeError | 在 Row delegate 上宣告 `property int rowIndex: index`，Repeater 子元件透過 `rowDelegate.rowIndex` 存取 |
| 2026-02-06 | `QQuickImageProvider.requestImage()` 回傳 `(QImage, QSize)` tuple，PySide6 報 RuntimeWarning 導致影像無法顯示 | PySide6 的 `requestImage` 只需回傳 `QImage`，不需要 tuple（C++ 的 size output parameter 在 Python binding 中不適用） |
| 2026-02-06 | QML RowLayout 中 LeftPanel 用 `Layout.preferredWidth: 16` (ratio值) 但 RightPanel 用 `Layout.preferredWidth: 270` (絕對值)，比例系統失效 | 兩側都用 `Layout.fillWidth: true` + ratio 值作為 `preferredWidth` |
| 2026-02-06 | QML RowLayout 中對 RightPanel 設 `Layout.maximumWidth: 360`，限制右側面板寬度導致左側吸收多餘空間，比例偏離 Widget 版 | 不可用 `maximumWidth` 限制右側面板，改用 `Layout.minimumWidth: 400` 保護不被擠壓，讓 ratio 系統自然分配空間（16:9 ≈ 64%:36%） |

### 禁止事項

- ❌ QML 中不可宣告與 property 同名的 `Changed` 信號（property `xxx` 自動生成 `xxxChanged`）
- ❌ 不可在未指定 non-native style (Fusion/Material/Basic) 的情況下自訂 Button/GroupBox 的 `background`/`contentItem`/`label`
- ❌ 不可在 Repeater delegate 中用 `parent.parent.ListView.view.indexAt()` 取列索引（parent chain 不可靠）
- ❌ `QQuickImageProvider.requestImage()` 不可回傳 tuple `(QImage, QSize)`，PySide6 只接受 `QImage`
- ❌ QML RowLayout 比例布局中，不可一側用 ratio 值、另一側用絕對值作為 `preferredWidth`（兩側都須 `fillWidth: true` + ratio）
- ❌ QML RowLayout 比例布局中，不可對右側面板設 `Layout.maximumWidth`（會導致左側吸收多餘空間），應改用 `Layout.minimumWidth` 保護右側不被擠壓
- ❌ 不可修改 `src/reba_tool/` 下的後端模組（QML 版只替換 UI 層）

### 更新時機

- Claude 產生錯誤輸出時 → 立即新增記錄
- PR 審查發現問題時 → 使用 @.claude 標籤更新
- 每週審視 → 精簡過時記錄

---

## Architecture

### 雙版本架構
```
src/reba_tool/           ← Widget 版 (原版, PySide6 Widgets)
  ├── MediaPipeApp.py    ← Widget 版入口
  ├── angle_calculator.py, reba_scorer.py, data_logger.py  ← 後端 (零 Qt 依賴)
  ├── video_controller.py, video_pipeline.py, event_bus.py  ← ViewModel + 管線
  ├── frame_renderer.py, processing_config.py               ← 渲染/配置
  └── ui/                ← 薄 Qt 層 (video_worker.py, qt_config.py)

src/reba_tool_qml/       ← QML 版 (新版, QtQuick/QML)
  ├── main.py            ← QML 版入口
  ├── bridge/            ← Python↔QML 橋接 (QObject 子類)
  │   ├── image_provider.py   ← QQuickImageProvider
  │   ├── video_bridge.py     ← 包裝 VideoController
  │   ├── reba_bridge.py      ← REBA 分數 Property
  │   ├── settings_bridge.py  ← 參數雙向綁定
  │   ├── data_bridge.py      ← 匯出/日誌
  │   ├── score_table_model.py ← 17x5 分數表
  │   └── table_c_model.py    ← 12x12 Table C
  ├── qml/               ← QML UI 檔案
  │   ├── main.qml, components/, panels/
  │   └── style/Theme.qml     ← 主題 Singleton
  └── config/            ← 主題 JSON (default, dark, high_contrast)
```

### Data Flow (QML 版)
```
[Worker Thread]                    [Main Thread]              [QML Render]
VideoPipeline.run()
  → EventBus.emit('frame_processed')
    → VideoWorker.frame_ready Signal → VideoBridge._handle_frame()
                                        → image_provider.update_frame()
                                        → frameCounter += 1
                                        → reba_bridge.update_from_frame()
                                                                → Image source 綁定
                                                                  frameCounter 觸發重繪
```

### Key Technical Details

| 項目 | 說明 |
|------|------|
| REBA Tables | Table A 5x3x2, Table B 6x2x3, Table C 12x12，皆在 `reba_scorer.py` 中 |
| Risk Levels | 1=Negligible, 2-3=Low, 4-7=Medium, 8-10=High, 11-15=Very High |
| QML Style | 必須使用 Fusion style (`QT_QUICK_CONTROLS_STYLE=Fusion`) |
| QML Image Provider | `image://video/frame?{frameCounter}` 觸發重繪，`cache: false` |
| 中文渲染 | Widget 版用 `Arial.Unicode.ttf` via PIL；QML 版用 `Microsoft YaHei` |
| 文件語言 | Docstrings and comments are in Traditional Chinese (繁體中文) |

---

## Error Handling

### 常見 QML 錯誤

| 錯誤 | 原因 | 解決 |
|------|------|------|
| `Duplicate signal name` | property 自動生成 `xxxChanged`，又手動宣告同名 signal | 自訂 signal 用不同名稱 |
| `does not support customization` | Windows native style 不支援自訂 background/contentItem | 設定 `QT_QUICK_CONTROLS_STYLE=Fusion` |
| `Failed to get image from provider` | `requestImage()` 回傳 tuple 而非 QImage | 只回傳 `QImage`，不要 tuple |
| 左右面板比例失衡 | `maximumWidth` 限制面板或 `preferredWidth` 混用 ratio/絕對值 | 兩側 `fillWidth: true` + ratio，用 `minimumWidth` 保護 |

---

## References

| 文件 | 說明 |
|------|------|
| `README.md` | 專案總覽 |
| `docs/` | 詳細文件 |
| `src/reba_tool/reba_scorer.py` | REBA 計分核心邏輯 |
| `src/reba_tool_qml/qml/style/Theme.qml` | QML 主題設定 (含 leftRatio/rightRatio) |

---

**最後更新**: 2026-02-06
