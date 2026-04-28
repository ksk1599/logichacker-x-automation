@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 로직해커 엑스 콘텐츠 도구 시작 중...

:: 가상환경이 있으면 사용, 없으면 시스템 Python 사용
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [알림] 가상환경 없음. 시스템 Python으로 실행합니다.
    echo [알림] 처음 실행이라면 아래 명령어로 환경을 먼저 구성하세요:
    echo.
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
)

streamlit run app.py --server.headless false
pause
