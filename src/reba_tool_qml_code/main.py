"""
REBA Tool QML Code 版入口
深色霓虹主題 Dashboard，後端複用 reba_tool_qml 的 bridge 層
"""
import sys
import os
import json
from pathlib import Path

# 必須在 QApplication 建立前設定 Fusion style，避免 Windows native style 警告
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

# 將 reba_tool 後端模組加入 Python 路徑（複用所有後端）
_this_dir = Path(__file__).resolve().parent
_reba_tool_dir = _this_dir.parent / "reba_tool"
sys.path.insert(0, str(_reba_tool_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl
from PySide6.QtGui import QPalette, QColor

from bridge.image_provider import VideoImageProvider
from bridge.video_bridge import VideoBridge
from bridge.reba_bridge import RebaBridge
from bridge.settings_bridge import SettingsBridge
from bridge.data_bridge import DataBridge
from bridge.table_c_model import TableCModel
from bridge.score_table_model import ScoreTableModel

HERE = Path(__file__).resolve().parent
QML_DIR = HERE / "qml"
CONFIG_DIR = HERE / "config"


def main():
    app = QApplication(sys.argv)

    # 設定 Fusion style 深色調色盤（讓 ComboBox/SpinBox 配合深色霓虹主題）
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

    # VideoBridge.frameProcessed → ScoreTableModel + TableCModel 更新
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

    # SettingsBridge → VideoBridge
    settings_bridge.parametersChanged.connect(video_bridge.setParameters)
    settings_bridge.displayOptionsChanged.connect(video_bridge.setDisplayOptions)

    # SettingsBridge.dataLockedChanged → VideoController
    def _on_data_lock_changed():
        video_bridge.controller.toggle_data_lock(settings_bridge.dataLocked)
    settings_bridge.dataLockedChanged.connect(_on_data_lock_changed)

    # VideoBridge 事件日誌
    video_bridge.processingFinished.connect(
        lambda: data_bridge.log(
            f"處理完成，共處理 {video_bridge.controller.frame_count} 幀"
        )
    )
    video_bridge.errorOccurred.connect(
        lambda msg: data_bridge.log(f"錯誤: {msg}")
    )

    # ========== 載入主題配置 ==========
    theme_path = CONFIG_DIR / "theme_dark_neon.json"
    with open(theme_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)

    # ========== 註冊到 QML Context ==========
    ctx = engine.rootContext()
    ctx.setContextProperty("themeConfig", theme_data)
    ctx.setContextProperty("videoBridge", video_bridge)
    ctx.setContextProperty("rebaBridge", reba_bridge)
    ctx.setContextProperty("settingsBridge", settings_bridge)
    ctx.setContextProperty("dataBridge", data_bridge)
    ctx.setContextProperty("tableCModel", table_c_model)
    ctx.setContextProperty("scoreTableModel", score_table_model)

    # ========== 載入 QML ==========

    # 加入 QML import path（讓 style/ 的 qmldir 可被找到）
    engine.addImportPath(str(QML_DIR))

    # 載入主 QML
    qml_file = QML_DIR / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("QML 載入失敗，請檢查 QML 檔案")
        sys.exit(-1)

    # ========== 執行 + 清理 ==========
    ret = app.exec()
    video_bridge.cleanup()
    sys.exit(ret)


if __name__ == "__main__":
    main()
