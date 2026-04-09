# 로직해커 엑스 멀티에이전트 시스템

스마트스토어 상위노출 전문가 **로직해커 엑스(secretmovev)** 의 Threads 운영 자동화.
9개 에이전트가 사용자 개입 없이 협업해서 콘텐츠 생성 → 검수 → 발행 → 분석 → 자기개선까지 수행.

## 핵심 컨셉

- **에이전트간 직접 협업** — 사용자는 결과만 본다
- **Supervisor가 모든 산출물 독립 검증** — LLM의 자가 만족 견제
- **3일마다 자기 프롬프트 진화** — Optimizer 루프
- **Sonnet/Haiku 혼합** — 토큰 효율

## 폴더 구조

```
로직해커 엑스 자동화 프로젝트/
├── .env                      # 시크릿 (git 제외)
├── .env.example              # 템플릿
├── .gitignore
├── README.md                 # 이 파일
├── CLAUDE_1.md               # 원본 명세
│
├── .claude/
│   └── agents/               # ⭐ Claude Code 서브에이전트 정의 (9개)
│       ├── orchestrator.md   # 팀장 (sonnet)
│       ├── knowledge.md      # 도메인 두뇌 (sonnet)
│       ├── writer.md         # 글 작성 (sonnet)
│       ├── qa.md             # 검수 (sonnet)
│       ├── analyst.md        # 성과 분석 (haiku)
│       ├── cs.md             # 답변 초안 (haiku)
│       ├── scheduler.md      # 트리거 (haiku)
│       ├── optimizer.md      # 프롬프트 진화 (sonnet)
│       └── supervisor.md     # 전체 감시 (sonnet)
│
├── agent/                    # ⭐ 협업 규칙 / 프로토콜
│   ├── README.md             # 에이전트 팀 개요
│   └── PROTOCOL.md           # 메시지 스키마, 흐름, 권한
│
├── supabase/
│   └── schema.sql            # ⭐ DB 스키마 (한 번 실행)
│
└── skills/
    └── knowledge.md          # Knowledge Agent 소스 (전자책 학습 후 채움)
```

## 첫 부팅 절차

### 1단계 — Supabase 스키마 생성
1. https://supabase.com/dashboard → 프로젝트 → **SQL Editor**
2. [supabase/schema.sql](supabase/schema.sql) 전체 복사 → 붙여넣기 → **Run**
3. 7개 테이블 생성 확인 (`agent_messages`, `supervisor_audits`, `threads_posts`, `post_insights`, `prompt_versions`, `tokens`, `schedule_runs`)

### 2단계 — Threads 토큰 DB에 등록
Supabase SQL Editor에서 한 번만 실행 (값은 .env에서 복사):
```sql
insert into tokens (service, access_token, issued_at, expires_at)
values (
  'threads',
  '<.env의 THREADS_ACCESS_TOKEN>',
  '2026-04-08'::timestamptz,
  '2026-04-08'::timestamptz + interval '60 days'
);
```

### 3단계 — 전자책 학습
Claude Code에서:
```
전자책 PDF 올릴게요. 전체 내용을 읽고
skills/knowledge.md 의 빈 곳을 채워주세요. 이미지 안의 텍스트도 포함해서.
```

### 4단계 — n8n 워크플로 3개 생성
| 워크플로 | Cron | 호출 대상 |
|---|---|---|
| 일반 발행 (오전) | `0 8 * * *` KST | scheduler agent |
| 일반 발행 (저녁) | `0 18 * * *` KST | scheduler agent |
| 자기개선 루프 | `0 3 */3 * *` KST | scheduler agent |

n8n에서 webhook 노드 → Claude API 호출 → scheduler 에이전트에 트리거 메시지 발송.

### 5단계 — 첫 테스트
Claude Code에서:
```
@orchestrator 테스트 글 1개 발행해
```
→ Writer→QA→Discord 흐름 확인.

## 협업 흐름 요약

자세한 건 [agent/PROTOCOL.md](agent/PROTOCOL.md) 참고.

```
일반 루프 (매일 2회)
  Scheduler → Orchestrator → Writer ⇄ Knowledge
                              ↓
                              QA ⇄ Knowledge
                              ↓
                          Discord → Threads
                              ↓
                          Supervisor (사후 감사)

자기개선 (3일마다)
  Scheduler → Analyst → Optimizer → Supervisor → Orchestrator → 적용
```

## 보안

- `.env`는 절대 git에 올리지 마라 (`.gitignore` 처리됨)
- `SUPABASE_SERVICE_ROLE_KEY`, `THREADS_APP_SECRET`은 백엔드 전용
- 토큰 노출 의심 시 즉시 rotate

## 운영 가이드

- 📄 [docs/TOKEN_REFRESH.md](docs/TOKEN_REFRESH.md) — Threads 토큰 갱신 (58일마다)
- 📄 [docs/KNOWLEDGE_TRAINING.md](docs/KNOWLEDGE_TRAINING.md) — 무료/유료 전자책 학습 절차

## 다음 진화 방향

- [ ] Knowledge Agent 학습 (전자책)
- [ ] Optimizer 첫 루프 후 v1.0.1 생성 확인
- [ ] Supervisor가 실제로 fail 잡는지 회귀 테스트
- [ ] n8n 워크플로에 에러 알림 추가
