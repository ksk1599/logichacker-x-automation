# Threads 토큰 갱신 가이드

> Threads 장기 토큰은 **60일 유효**.
> Scheduler가 D-7, D-3, D-1, D-Day에 Discord로 알림을 보낸다.
> 알림 받으면 이 문서대로 5분 안에 갱신.

---

## 사전 체크 (10초)

- ✅ 현재 토큰이 **발급 24시간 이상** 됐는가? (당일 발급은 refresh 불가)
- ✅ 현재 토큰이 **아직 만료 안 됐는가**? (만료된 후엔 OAuth 재시작)
- ✅ `.env` 파일을 열 수 있는가?
- ✅ Supabase 대시보드 접근 가능?

---

## Step 1 — 새 토큰 받기 (1분)

### 방법 A — 브라우저 (제일 쉬움)

1. `.env`에서 현재 `THREADS_ACCESS_TOKEN` 값 복사
2. 아래 URL의 `{CURRENT_TOKEN}` 부분 붙여넣기 후 브라우저 주소창에 입력:

```
https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token={CURRENT_TOKEN}
```

3. 응답에서 `access_token` 값이 **새 토큰**:

```json
{
  "access_token": "THAA...새토큰...",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

### 방법 B — curl

```bash
curl -i -X GET "https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token=$THREADS_ACCESS_TOKEN"
```

---

## Step 2 — `.env` 업데이트 (1분)

[.env](../.env) 파일 열어서:

```env
THREADS_ACCESS_TOKEN=<새 토큰>
THREADS_TOKEN_ISSUED_AT=<오늘 YYYY-MM-DD>
```

저장.

---

## Step 3 — Supabase `tokens` 테이블 UPDATE (1분)

[Supabase Dashboard](https://supabase.com/dashboard) → 프로젝트 → SQL Editor → 아래 실행:

```sql
update tokens
set access_token          = '<새 토큰>',
    issued_at             = now(),
    expires_at            = now() + interval '60 days',
    last_refresh_alert_at = null
where service = 'threads';
```

`last_refresh_alert_at = null`로 리셋해야 다음 사이클 알림이 정상 동작.

---

## Step 4 — 검증 (1분)

확인 SQL:
```sql
select service, issued_at, expires_at, expires_at - now() as remaining
from tokens where service = 'threads';
```

`remaining`이 약 60일이면 OK.

---

## Step 5 — 다음 일반 루프 모니터링

다음 08:00 또는 18:00 KST에 Writer→QA→Discord 흐름이 정상 작동하는지 확인.
실패하면 토큰 갱신이 잘못된 거니 Step 1부터 재시도.

---

## 트러블슈팅

### "Invalid OAuth access token"
- 옛 토큰이 이미 만료됨 → Meta for Developers 앱에서 OAuth 재시작 필요
- https://developers.facebook.com/apps → 본인 앱 → Threads API → User Token Generator

### "This authorization code has been used"
- refresh 엔드포인트를 두 번 호출함. 두 번째 호출 결과가 진짜 새 토큰
- 그래도 안 되면 OAuth 재시작

### refresh 했는데 60일이 아니라 며칠만 나옴
- 원래 토큰이 거의 만료 직전이었음 → 정상. 다음 알림 사이클에서 다시 갱신

### 토큰 발급일을 잊어버림
- Meta for Developers → 본인 앱 → Threads API → User Token에서 발급일 확인 가능

---

## 자동화 가능성 (선택)

n8n에서 cron으로 D-7에 자동 refresh 워크플로 만들 수 있음:
1. cron 노드 → 매일 00:00
2. Supabase 노드 → tokens에서 expires_at 조회
3. IF 노드 → D-7 이내?
4. HTTP Request 노드 → refresh_access_token API
5. Supabase UPDATE 노드 → 새 토큰 저장
6. Discord 노드 → "자동 갱신 완료" 알림

→ 단, **자동 갱신은 Supervisor가 검증할 수 없는 작업**이라 처음 1~2 사이클은 수동으로 하는 걸 권장.
