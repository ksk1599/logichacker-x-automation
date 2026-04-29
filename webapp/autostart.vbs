' 로직해커 엑스 웹앱 자동 시작 스크립트
' PC 부팅 시 백그라운드에서 Streamlit 서버를 자동으로 켭니다.

Dim objShell
Set objShell = CreateObject("WScript.Shell")

' Streamlit 서버를 백그라운드(숨김 창)로 실행
' WindowStyle 0 = 창 숨김, bWaitOnReturn False = 비동기 실행
objShell.Run "cmd /c cd /d ""C:\Users\yk920\Downloads\로직해커 엑스 자동화 프로젝트\webapp"" && .venv\Scripts\streamlit run app.py --server.headless true", 0, False

' 서버가 뜰 때까지 6초 대기
WScript.Sleep 6000

' 브라우저에서 자동으로 열기
objShell.Run "http://localhost:8501"
