@echo off
chcp 950 >nul

echo 當前目錄：%cd%

REM === 目錄檢查 ===
if not exist "src\reba_tool\MediaPipeApp.py" (
    echo [錯誤] 找不到 src\reba_tool\MediaPipeApp.py
    echo 請在專案根目錄執行此腳本
    pause
    exit /b 1
)

REM === UV 檢查 ===
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未安裝 uv，開始自動安裝...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo [錯誤] uv 安裝失敗，請手動安裝: https://docs.astral.sh/uv/
        pause
        exit /b 1
    )
    echo uv 安裝完成
)

REM === 安裝依賴 ===
if not exist ".venv" (
    echo [提示] 首次執行，安裝依賴套件...
    uv sync
    if %errorlevel% neq 0 (
        echo [錯誤] 依賴安裝失敗
        pause
        exit /b 1
    )
    echo 依賴安裝完成
)

REM === 啟動應用 ===
echo 啟動 REBA 分析系統...
uv run .\src\reba_tool\MediaPipeApp.py
pause
