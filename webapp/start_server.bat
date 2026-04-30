@echo off
cd /d "C:\Users\yk920\Downloads\로직해커 엑스 자동화 프로젝트\webapp"
start "" ".venv\Scripts\streamlit.exe" run "app.py" --server.headless true
timeout /t 10 /nobreak >nul
start "" "http://localhost:8501"
