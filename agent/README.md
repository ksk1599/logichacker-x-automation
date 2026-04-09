# 에이전트 팀 명세

이 폴더는 **에이전트 팀의 협업 규칙**을 담는다.
실제 에이전트 정의는 [`.claude/agents/`](../.claude/agents/) 에 있다 (Claude Code 서브에이전트 표준 위치).

## 구성

| 파일 | 용도 |
|---|---|
| [PROTOCOL.md](PROTOCOL.md) | 통신 방식, 협업 흐름, 권한 매트릭스 |
| [README.md](README.md) | 이 파일 |

## 9개 에이전트 한눈에

| # | 에이전트 | 모델 | 역할 | 정의 |
|---|---|---|---|---|
| 1 | **Orchestrator** | sonnet | 팀장. 작업 분배, 흐름 제어 | [orchestrator.md](../.claude/agents/orchestrator.md) |
| 2 | **Knowledge** | sonnet | 도메인 두뇌. 즉답 | [knowledge.md](../.claude/agents/knowledge.md) |
| 3 | **Writer** | sonnet | Threads 글 4줄 작성 | [writer.md](../.claude/agents/writer.md) |
| 4 | **QA** | sonnet | 글 검수, Discord 발송 | [qa.md](../.claude/agents/qa.md) |
| 5 | **Analyst** | haiku | 성과 수집 (반복 작업) | [analyst.md](../.claude/agents/analyst.md) |
| 6 | **CS** | haiku | 팔로워 답변 초안 | [cs.md](../.claude/agents/cs.md) |
| 7 | **Scheduler** | haiku | 스케줄 트리거 | [scheduler.md](../.claude/agents/scheduler.md) |
| 8 | **Optimizer** | sonnet | Writer 프롬프트 진화 | [optimizer.md](../.claude/agents/optimizer.md) |
| 9 | **Supervisor** | sonnet | 전체 감시 (반편향) | [supervisor.md](../.claude/agents/supervisor.md) |

## 모델 할당 원칙
- **Sonnet (6개)**: 추론, 판단, 글쓰기, 감시 — 품질이 토큰비보다 중요한 곳
- **Haiku (3개)**: 데이터 수집, 트리거, 초안 — 단순 반복

## 다음 단계
1. [supabase/schema.sql](../supabase/schema.sql)을 Supabase SQL Editor에 실행
2. [.env](../.env) 값 검증 완료
3. n8n에서 cron 워크플로 3개 생성 (08:00, 18:00, 03:00 KST)
4. 사용자가 전자책 PDF 업로드 → `skills/knowledge.md` 채우기
5. Orchestrator 첫 부팅 테스트
