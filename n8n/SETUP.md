# n8n 워크플로 설정 가이드 (Method B)

## 아키텍처

```
n8n (Railway, PC 꺼져도 돌아감)
  ↓ 08:00, 18:00 KST 매일 / 3일마다 03:00 KST
Supabase agent_messages 테이블 — pending row 삽입
  ↓
[로컬 PC] poll_orchestrator.py 30초마다 체크
  ↓ pending 감지 시
Claude Code 실행 (claude -p "...")
  ↓
orchestrator → writer → qa → Threads 발행
```

> **한계**: PC가 꺼져 있으면 polling script가 멈춤.
> n8n이 트리거를 Supabase에 쌓아두므로 PC 켜지면 밀린 메시지 처리됨.
> Method A(Anthropic API 직접 호출)로 이전하면 PC 없이 가능.

---

## Step 1 — n8n 환경변수 설정

n8n 대시보드 → **Settings > Environment Variables** → 아래 2개 추가:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | `.env`의 `SUPABASE_URL` 값 |
| `SUPABASE_ANON_KEY` | `.env`의 `SUPABASE_ANON_KEY` 값 |

---

## Step 2 — 워크플로 Import

1. n8n 대시보드 → **Workflows > Import from file**
2. 아래 3개 파일 순서대로 임포트:
   - `workflow_morning.json` — 08:00 KST 일반 발행
   - `workflow_evening.json` — 18:00 KST 일반 발행
   - `workflow_optimizer.json` — 3일마다 03:00 KST 자기개선

3. 각 워크플로 열고 → **Active 토글 ON**

---

## Step 3 — 로컬 폴링 스크립트 실행

PC에서 Claude Code 터미널 열고:

```bash
cd "C:\Users\yk920\Downloads\로직해커 엑스 자동화 프로젝트"
python scripts/poll_orchestrator.py
```

PC 꺼지기 전까지 이 터미널 열어둬야 함. 백그라운드 실행:

```bash
# Windows — 백그라운드 실행 (터미널 닫아도 됨)
start /B pythonw scripts/poll_orchestrator.py
```

---

## Step 4 — 동작 테스트

Supabase SQL Editor에서 수동으로 트리거 삽입:

```sql
insert into agent_messages (from_agent, to_agent, message_type, topic, payload, status)
values (
  'scheduler', 'orchestrator', 'request',
  'test_trigger_' || to_char(now(), 'YYYY-MM-DD'),
  '{"loop": "daily_writer", "time_slot": "test"}'::jsonb,
  'pending'
);
```

→ 30초 내 polling script가 감지 → Claude Code 실행 확인.

---

## 크론 시간표 (UTC 기준)

| 워크플로 | Cron (UTC) | KST |
|---------|------------|-----|
| 오전 발행 | `0 23 * * *` | 매일 08:00 |
| 저녁 발행 | `0 9 * * *` | 매일 18:00 |
| 자기개선 | `0 18 */3 * *` | 3일마다 03:00 |

---

## Method A 이전 계획 (PC-off 완전 자동화)

Method B의 한계(로컬 PC 필요)를 해결하려면:

1. n8n 워크플로에서 Supabase 삽입 대신 **Anthropic API 직접 호출** 노드 추가
2. orchestrator 에이전트 프롬프트를 n8n에 붙여넣기
3. 응답을 Supabase에 저장

이 방식으로 전환하면 Railway n8n이 혼자 돌면서 Claude API 호출 → Threads 발행까지 가능.
준비되면 `n8n/workflow_morning_method_a.json` 별도 작성.
