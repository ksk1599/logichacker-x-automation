# 로직해커 엑스 멀티에이전트 시스템

## 프로젝트 개요
스마트스토어 상위노출 전문가 '로직해커 엑스'(secretmovev) 계정의
Threads 콘텐츠 자동 생성, 성과 분석, 자기개선 루프 시스템

## 인프라
- n8n: https://n8n-production-9b1b.up.railway.app
- Supabase: 모든 데이터 저장 (토큰, 성과, 프롬프트 버전)
- Threads API: secretmovev 계정
- Discord: 글 검수용 웹훅
- 모델: claude-sonnet-4-6 / claude-haiku-4-5

## 에이전트 팀
| 에이전트 | 모델 | 역할 |
|---|---|---|
| Orchestrator | Sonnet | 전체 지휘, 작업 분배, 최종 판단 |
| Knowledge | Sonnet | 도메인 지식 저장소 (tier 접근 통제) |
| Writer | Sonnet | Threads 글 생성 (4줄 포맷) |
| QA | Sonnet | 글 검수 → Discord/Threads 발송 |
| Analyst | Haiku | 성과 데이터 수집·분석 |
| CS | Haiku | 팔로워 질문 답변 초안 |
| Scheduler | Haiku | 08:00/18:00 트리거, 3일마다 Optimizer |
| Optimizer | Sonnet | 프롬프트 자동 개선 (3일 주기) |
| Supervisor | Sonnet | 전체 산출물 독립 재검증 |

## 협업 흐름

### 일반 루프 (매일 2회: 08:00, 18:00 KST)
```
n8n cron → Supabase agent_messages → poll_orchestrator.py
→ Orchestrator → Writer → QA → Discord + Threads 발송
```

### 자기개선 루프 (3일마다 03:00 KST)
```
Scheduler → Analyst → Prompt Optimizer → Orchestrator 승인 → Writer 프롬프트 업데이트
```

## 에이전트 협업 규칙
1. 에이전트 간 직접 소통 가능. Orchestrator 경유 불필요.
2. QA는 Writer에게 직접 재작성 요청.
3. 사용자는 최종 결과만 확인. 중간 개입 불필요.
4. 루프 실패 시 Orchestrator가 Discord로 알림 발송.

## Supabase 테이블
- `threads_posts`: 글 ID, 내용, 발송시간, 상태
- `post_insights`: 좋아요, 조회수, 댓글, 리포스트
- `prompt_versions`: 프롬프트 버전, 날짜, 성과 점수
- `tokens`: Threads 토큰, 갱신일
- `agent_messages`: 에이전트 간 메시지 큐
- `schedule_runs`: 스케줄 실행 로그

---

## 유튜브 콘텐츠 도구 (로컬 웹앱)

브라우저에서 썸네일·제목·30초 원고를 생성하는 Streamlit 앱.

- 실행: `cd webapp && .venv\Scripts\streamlit run app.py`
- 또는 `webapp\run.bat` 더블클릭
- 상세: @docs/WEBAPP.md

**에이전트:**
- `@thumbnail` — 썸네일 문구 + 제목 (`.claude/agents/thumbnail.md`)
- `@script_30s` — 첫 30초 후킹 원고 (`.claude/agents/script_30s.md`)

**자동 학습:** 참고 이미지/원고를 웹앱에 업로드하면 별도 명령 없이
`skills/youtube/patterns.md` · `hook_patterns.md`에 자동 저장됨.
PC 재시작 후에도 학습 상태 유지.

---

## 도메인 규칙 (반드시 준수)

> 세부 규칙은 `.claude/rules/` 폴더에서 에이전트별로 관리.
> 아래는 **전체 에이전트 공통 절대 규칙**이다.

### ❌ 키워드 위치 가점 — 낭설, 절대 금지

**상품명에서 키워드가 앞에 올수록 가점이 높다는 말은 완전히 틀렸다.**

- 실제: 키워드 위치(앞/뒤)는 검색 순위와 무관
- 중요한 것은 **배열 관계** (키워드끼리 얼마나 가까이, 순서대로 붙어있는지)
- 근거: `skills/knowledge/free.md` 위치(앞/뒤)의 진실 섹션

**금지 표현:**
- "앞에 올수록 가점 N배"
- "앞에 온 키워드에 N배 이상 가점"
- "중요 키워드는 맨 앞에 써야 유리하다"

### 용어 규칙
- 스마트스토어 랭킹 문맥에서 **"가중치" 대신 "가점"** 표현
- ML/알고리즘 기술 설명 시는 예외 허용
