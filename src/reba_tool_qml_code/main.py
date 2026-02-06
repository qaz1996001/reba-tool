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

from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

HERE = Path(__file__).resolve().parent
QML_DIR = HERE / "qml"
CONFIG_DIR = HERE / "config"


def main():
    app = QApplication(sys.argv)

    engine = QQmlApplicationEngine()

    # 載入主題配置注入 QML context
    theme_path = CONFIG_DIR / "theme_dark_neon.json"
    with open(theme_path, "r", encoding="utf-8") as f:
        theme_data = json.load(f)
    engine.rootContext().setContextProperty("themeConfig", theme_data)

    # 加入 QML import path（讓 style/ 的 qmldir 可被找到）
    engine.addImportPath(str(QML_DIR))

    # 載入主 QML
    qml_file = QML_DIR / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("QML 載入失敗，請檢查 QML 檔案")
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
