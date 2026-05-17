@echo off
REM ============================================================
REM  내 자산 관리자 - Windows .exe 빌드 스크립트
REM  이 파일을 Windows 환경에서 더블클릭하거나
REM  cmd에서 build.bat 으로 실행하세요.
REM ============================================================

echo [1/3] 의존성 설치 중...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo 의존성 설치에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [2/3] PyInstaller로 .exe 빌드 중...
pyinstaller --noconfirm --onefile --windowed ^
    --name "MyAssetManager" ^
    --hidden-import="yfinance" ^
    app.py

if errorlevel 1 (
    echo .exe 빌드에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [3/3] 빌드 완료!
echo 생성된 파일: dist\MyAssetManager.exe
echo.
pause
