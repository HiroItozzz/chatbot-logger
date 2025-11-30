@echo off
chcp 65001 >nul

cd /d "%~dp0"

if "%~1"=="" (
    echo ファイルをドラッグ＆ドロップしてください
    timeout /t 3
    exit /b 1
)

echo 処理開始: %~nx1
.venv\Scripts\python.exe "main.py" "%~1"

pause