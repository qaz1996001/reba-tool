#!/usr/bin/env python3
"""
REBA Tool QML 版 - 入口程式
建立 QApplication + QQmlApplicationEngine，
註冊所有 bridge 和 image_provider 到 QML context。
"""

import sys
import os
import json
from pathlib import Path

# 設定 QML 控件樣式為 Fusion（支援 background/contentItem 自訂）
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

# 將 reba_tool 後端模組加入 Python 路徑（複用所有後端）
_this_dir = Path(__file__).resolve().parent
_reba_tool_dir = _this_dir.parent / "reba_tool"
sys.path.insert(0, str(_reba_tool_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
from PySide6.QtCore import QUrl, QObject
from PySide6.QtGui import QPalette, QColor

from bridge.image_provider import VideoImageProvider
from bridge.video_bridge import VideoBridge
from bridge.reba_bridge import RebaBridge
from bridge.settings_bridge import SettingsBridge
from bridge.data_bridge import DataBridge
from bridge.table_c_model import TableCModel
from bridge.score_table_model import ScoreTableModel


def load_theme_json(theme_path: Path) -> dict:
    """載入主題 JSON 配置"""
    if theme_path.exists():
        with open(theme_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def main():
    app = QApplication(sys.argv)

    # 設定 Fusion style 深色調色盤（讓 ComboBox/SpinBox 也呈現深色）
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0a0f1d"))
    palette.setColor(QPalette.WindowText, QColor("#e2e8f0"))
    palette.setColor(QPalette.Base, QColor("#1e2539"))
    palette.setColor(QPalette.AlternateBase, QColor("#161c2d"))
    palette.setColor(QPalette.Text, QColor("#e2e8f0"))
    palette.setColor(QPalette.Button, QColor("#1e2539"))
    palette.setColor(QPalette.ButtonText, QColor("#00f2ff"))
    palette.setColor(QPalette.Highlight, QColor("#00f2ff"))
    palette.setColor(QPalette.HighlightedText, QColor("#0a0f1d"))
    palette.setColor(QPalette.Mid, QColor("#2d3748"))
    app.setPalette(palette)

    engine = QQmlApplicationEngine()

    # ========== 建立 Bridge 實例 ==========

    # 影像提供者
    image_provider = VideoImageProvider()
    engine.addImageProvider("video", image_provider)

    # 影片橋接（持有 VideoController）
    video_bridge = VideoBridge(image_provider)

    # REBA 分數橋接
    reba_bridge = RebaBridge()

    # 設定橋接
    settings_bridge = SettingsBridge()

    # 資料橋接
    data_bridge = DataBridge()
    data_bridge.set_controller(video_bridge.controller)

    # Table C 模型
    table_c_model = TableCModel()

    # 分數表格模型
    score_table_model = ScoreTableModel()

    # ========== 連接信號 ==========

    # VideoBridge.frameProcessed → RebaBridge 更新分數
    video_bridge.frameProcessed.connect(reba_bridge.update_from_frame)

    # VideoBridge.frameProcessed → ScoreTableModel 更新表格
    def _on_frame_for_table(frame, angles, reba_score, risk_level, fps, details):
        score_table_model.update_data(angles, details)
        data_bridge.update_record_count()
        # 更新 Table C 高亮（無有效分數時清除）
        sa = details.get('score_a') if details else None
        sb = details.get('score_b') if details else None
        if sa and sb:
            table_c_model.updateScores(sa, sb)
        else:
            table_c_model.updateScores(0, 0)

    video_bridge.frameProcessed.connect(_on_frame_for_table)

    # SettingsBridge.parametersChanged → VideoBridge
    settings_bridge.parametersChanged.connect(video_bridge.setParameters)
    settings_bridge.displayOptionsChanged.connect(video_bridge.setDisplayOptions)

    # SettingsBridge.dataLockedChanged → VideoController
    def _on_data_lock_changed():
        video_bridge.controller.toggle_data_lock(settings_bridge.dataLocked)
    settings_bridge.dataLockedChanged.connect(_on_data_lock_changed)

    # VideoBridge 事件日誌
    video_bridge.processingFinished.connect(
        lambda: data_bridge.log(f"處理完成，共處理 {video_bridge.controller.frame_count} 幀")
    )
    video_bridge.errorOccurred.connect(
        lambda msg: data_bridge.log(f"錯誤: {msg}")
    )

    # ========== 載入主題 ==========
    config_dir = _this_dir / "config"
    theme_json = load_theme_json(config_dir / "theme_neon_navy.json")

    # 將主題 JSON 注入 QML context（QML Theme.qml 可在 Component.onCompleted 呼叫 loadTheme）
    ctx = engine.rootContext()
    ctx.setContextProperty("themeJson", theme_json)

    # ========== 註冊到 QML Context ==========
    ctx.setContextProperty("videoBridge", video_bridge)
    ctx.setContextProperty("rebaBridge", reba_bridge)
    ctx.setContextProperty("settingsBridge", settings_bridge)
    ctx.setContextProperty("dataBridge", data_bridge)
    ctx.setContextProperty("tableCModel", table_c_model)
    ctx.setContextProperty("scoreTableModel", score_table_model)

    # ========== 載入 QML ==========
    qml_dir = _this_dir / "qml"

    # 加入 QML 模組搜尋路徑（讓 import "style" 生效）
    engine.addImportPath(str(qml_dir))

    qml_file = qml_dir / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("錯誤: 無法載入 QML 檔案")
        sys.exit(-1)

    # ========== 清理 ==========
    ret = app.exec()
    video_bridge.cleanup()
    sys.exit(ret)


if __name__ == "__main__":
    main()
