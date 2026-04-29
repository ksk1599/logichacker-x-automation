' 로직해커 엑스 웹앱 자동 시작 스크립트
' PC 부팅 시 백그라운드에서 Streamlit 서버를 자동으로 켭니다.

Dim objShell
Set objShell = CreateObject("WScript.Shell")

' streamlit.exe 직접 경로로 실행 (한글 경로 문제 우회)
Dim streamlitPath
Dim appPath
streamlitPath = "C:\Users\yk920\Downloads\로직해커 엑스 자동화 프로젝트\webapp\.venv\Scripts\streamlit.exe"
appPath = "C:\Users\yk920\Downloads\로직해커 엑스 자동화 프로젝트\webapp\app.py"

objShell.Run """" & streamlitPath & """ run """ & appPath & """ --server.headless true", 0, False

' 서버가 뜰 때까지 8초 대기
WScript.Sleep 8000

' 브라우저에서 자동으로 열기
objShell.Run "http://localhost:8501"
