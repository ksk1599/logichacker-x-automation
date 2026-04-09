# 에이전트 협업 프로토콜

이 문서는 9개 에이전트가 **서로 직접 대화**하며 협업하는 방식을 정의한다.
사용자 개입 없이 팀 내부 루프로 검수까지 끝내는 것이 목표.

---

## 통신 방식: Supabase `agent_messages` 메시지 버스

모든 에이전트간 통신은 **Supabase `agent_messages` 테이블** 경유. 직접 호출 금지.

### 왜 이 방식인가
- **비동기**: 한 에이전트가 막혀도 다른 에이전트가 안 멈춤
- **감시 가능**: Supervisor가 모든 메시지를 독립 감사 가능
- **재시도 가능**: status 필드로 실패 추적
- **Realtime 구독**: Supabase Realtime으로 즉시 수신 (폴링 불필요)

### 메시지 스키마

```json
{
  "from_agent": "writer",
  "to_agent": "qa",
  "message_type": "request",
  "topic": "post_2026-04-09_morning",
  "payload": { ... },
  "parent_id": null,
  "status": "pending"
}
```

| 필드 | 의미 |
|---|---|
| `from_agent` | 발신자 (소문자, 하이픈 없음) |
| `to_agent` | 수신자. `*`는 broadcast |
| `message_type` | `request` / `response` / `feedback` / `alert` |
| `topic` | 작업 컨텍스트 — 같은 topic으로 스레드 추적 |
| `payload` | 자유 JSON. 에이전트별 페이로드 스키마는 각 agent.md 참고 |
| `parent_id` | 답변 체인 추적 (response/feedback일 때) |
| `status` | `pending` / `read` / `done` / `failed` |

---

## 협업 흐름 (3가지)

### Loop 1 — 일반 발행 (매일 2회)
```
[Scheduler]
   │ trigger
   ▼
[Orchestrator]
   │ request: generate_post
   ▼
[Writer] ──── 도메인 질의 ───▶ [Knowledge]
   │                           │ response
   │ ◀─────────────────────────┘
   │ submit for review
   ▼
[QA] ──── 도메인 재확인 ──▶ [Knowledge]
   │
   ├─ pass ─▶ Discord webhook ─▶ Threads 발행
   │            │
   │            ▼
   │         [Supervisor] (사후 감사)
   │
   └─ fail ─▶ [Writer] 재작성 (최대 3회)
                 │
              4회 이상 ─▶ [Supervisor] ─▶ [Orchestrator] 에스컬레이션
```

### Loop 2 — 자기개선 (3일마다)
```
[Scheduler]
   │
   ▼
[Analyst] ── 성과 수집 ──▶ Threads Insights API
   │
   │ 데이터 패스
   ▼
[Optimizer]
   │ 새 프롬프트 제안
   ▼
[Supervisor] (회귀 검증, 가장 중요)
   │
   ├─ reject ─▶ Optimizer 재작업
   └─ pass   ─▶ [Orchestrator]
                  │
                  ├─ approve ─▶ prompt_versions.is_active 토글
                  └─ reject  ─▶ 변경 폐기
```

### Loop 3 — 토큰 관리 (매일)
```
[Scheduler] ─▶ tokens 테이블 조회
                  │
                  └─ expires_at - now() < 2일 ─▶ Discord 알림
```

---

## 병렬 처리 규칙

토큰 효율을 위해 **다음 작업은 반드시 병렬 실행**:

| 병렬 가능 | 이유 |
|---|---|
| Analyst 수집 + Writer 글 생성 | 의존성 없음 |
| Writer 인스턴스 N개 (다중 글 생성) | 각 글 독립 |
| Supervisor 감사 + 일반 루프 | Supervisor는 사후, 비동기 |
| Knowledge 다중 질의 | 읽기 전용 |

병렬화는 Orchestrator가 Task 도구로 여러 서브에이전트를 동시 호출해서 구현.

---

## 에이전트 권한 매트릭스

| 에이전트 | DB 쓰기 | 외부 API | 다른 에이전트 직접 호출 |
|---|---|---|---|
| Orchestrator | ⭕ all | ❌ | ⭕ all |
| Knowledge | ❌ | ❌ | ❌ (응답만) |
| Writer | threads_posts, agent_messages | ❌ | knowledge, qa |
| QA | threads_posts(status), agent_messages | Discord | writer, knowledge, supervisor |
| Analyst | post_insights | Threads Insights | optimizer, supervisor |
| CS | agent_messages | ❌ | knowledge |
| Scheduler | schedule_runs, agent_messages | Discord | orchestrator, analyst |
| Optimizer | prompt_versions | ❌ | supervisor, orchestrator |
| Supervisor | supervisor_audits, agent_messages | Discord | **모두** (재작업 명령) |

---

## 시크릿 접근

**모든 에이전트는 `.env`에서 시크릿을 읽되, 절대 출력/로그/메시지 페이로드에 포함하지 않는다.**

- `SUPABASE_SERVICE_ROLE_KEY` — 백엔드 작업용. 클라이언트 코드에 노출 금지
- `THREADS_ACCESS_TOKEN` — 60일 만료. Scheduler가 58일째 알림
- `DISCORD_WEBHOOK_URL` — 외부에 유출되면 누구나 채널 도배 가능

> 시크릿 노출 의심 시: 즉시 Supabase 대시보드/Meta/Discord에서 rotate.

---

## 에러 처리 표준

1. **에이전트는 자기 실패를 숨기지 않는다.** 실패 시 `agent_messages.status='failed'` + `payload.error`에 사유.
2. **3회 재시도 후에도 실패** → Supervisor에 alert + Discord 알림 채널.
3. **Orchestrator는 5분 내 응답 없는 에이전트를 dead로 간주** → 다른 경로 모색 또는 Discord 에러 발송.
