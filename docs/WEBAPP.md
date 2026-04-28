# 로컬 웹앱 — 로직해커 엑스 콘텐츠 도구

## 개요
CLI 없이 브라우저에서 바로 쓸 수 있는 유튜브 콘텐츠 생성 도구.
Streamlit 기반, 로컬 전용 (외부 배포 없음).

## 실행 방법

### 처음 한 번만 (환경 구성)
```
cd webapp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 매번 실행
```
cd webapp
.venv\Scripts\streamlit run app.py
```
→ 브라우저 `http://localhost:8501` 자동으로 열림

또는 `webapp\run.bat` 더블클릭.

---

## 탭 구성

### 탭 1 — 썸네일 만들기
| 입력 | 설명 |
|---|---|
| 영상 주제 | 필수. 이번 영상 핵심 내용 |
| 참고 이미지 | 선택. png/jpg — 다른 채널 터진 영상 캡처 |
| 특별 요청 | 선택. "Before→After 패턴으로" 등 |

출력: 썸네일 문구 3개 + 유튜브 제목 3개 + 추천 조합

### 탭 2 — 30초 원고
| 입력 | 설명 |
|---|---|
| 영상 주제 | 필수 |
| 레퍼런스 원고 | 선택. 터진 영상의 30초 원고 붙여넣기 |

출력: 후킹(0~5초) → 공감(5~15초) → 예고(15~25초) → 신뢰(25~30초) 구간별 원고

---

## 자동 학습 (핵심)

레퍼런스를 주면 **별도 명령 없이** 자동으로 학습·저장됩니다.

```
참고 이미지 업로드 → [생성하기]
      ↓
Claude가 분석 블록 포함해서 응답
      ↓
앱이 자동으로 patterns.md에 append
      ↓
✅ "레퍼런스 G 저장됨" 알림
      ↓
PC 재시작 후에도 G까지 학습된 상태 유지
```

- 이미지 학습 → `skills/youtube/patterns.md` 에 누적
- 원고 학습 → `skills/youtube/hook_patterns.md` 에 누적
- 저장 위치가 `.md` 파일이라 Claude Code 재시작 시에도 컨텍스트로 자동 로드됨

---

## 주요 파일

| 파일 | 역할 |
|---|---|
| `webapp/app.py` | Streamlit UI (탭 2개) |
| `webapp/claude_client.py` | 에이전트 .md 시스템 프롬프트 + API 호출 |
| `webapp/auto_save.py` | 응답 파싱 → `.md` append |
| `webapp/requirements.txt` | streamlit, anthropic |
| `webapp/run.bat` | 윈도우 더블클릭 런처 |
| `webapp/.venv/` | 가상환경 (git 제외) |

에이전트 프롬프트 위치:
- `.claude/agents/thumbnail.md` — 썸네일 탭 시스템 프롬프트
- `.claude/agents/script_30s.md` — 30초 원고 탭 시스템 프롬프트

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `ModuleNotFoundError: streamlit` | 가상환경 미설치 | `pip install -r requirements.txt` |
| `ANTHROPIC_API_KEY 없음` | `.env` 파일 누락 | 루트의 `.env`에 키 입력 |
| "저장 블록을 찾지 못했습니다" | Claude 응답에 마커 없음 | 재시도 또는 주제를 더 구체적으로 입력 |
| 포트 충돌 | 8501 이미 사용 중 | `streamlit run app.py --server.port 8502` |
