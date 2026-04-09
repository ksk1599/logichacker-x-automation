#!/bin/bash
# 시크릿/연결 검증 스크립트
# 사용법: bash scripts/verify_env.sh
# 토큰 값은 절대 출력하지 않음. OK/FAIL만 보고.

set -a
source .env 2>/dev/null || { echo "❌ .env 파일을 찾을 수 없음. 프로젝트 루트에서 실행하세요."; exit 1; }
set +a

pass=0
fail=0

check() {
  local name="$1"
  local result="$2"
  local detail="$3"
  if [ "$result" = "OK" ]; then
    echo "  ✅ $name${detail:+ — $detail}"
    pass=$((pass+1))
  else
    echo "  ❌ $name — $detail"
    fail=$((fail+1))
  fi
}

echo ""
echo "=========================================="
echo "  로직해커 엑스 — 환경 검증"
echo "=========================================="

# ---------- 1. Supabase ----------
echo ""
echo "[1/4] Supabase (service_role)"

# 7개 테이블 모두 존재 확인
tables=(agent_messages supervisor_audits threads_posts post_insights prompt_versions tokens schedule_runs)
all_ok=true
for t in "${tables[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
    "$SUPABASE_URL/rest/v1/$t?limit=0")
  if [ "$code" != "200" ]; then
    check "$t" "FAIL" "HTTP $code"
    all_ok=false
  fi
done
$all_ok && check "7개 테이블 전체" "OK" "스키마 실행 완료"

# 시드 데이터 확인 (writer v1.0.0)
resp=$(curl -s \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  "$SUPABASE_URL/rest/v1/prompt_versions?agent_name=eq.writer&is_active=eq.true&select=version")
if echo "$resp" | grep -q '"version"'; then
  v=$(echo "$resp" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
  check "writer 초기 프롬프트" "OK" "$v active"
else
  check "writer 초기 프롬프트" "FAIL" "시드 데이터 누락"
fi

# ---------- 2. Threads ----------
echo ""
echo "[2/4] Threads API"
resp=$(curl -s "https://graph.threads.net/v1.0/me?fields=id,username&access_token=$THREADS_ACCESS_TOKEN")
if echo "$resp" | grep -q '"id"'; then
  username=$(echo "$resp" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
  id_returned=$(echo "$resp" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
  check "토큰 유효" "OK" "@$username"
  if [ "$id_returned" = "$THREADS_USER_ID" ]; then
    check "USER_ID 일치" "OK" ""
  else
    check "USER_ID 일치" "FAIL" "토큰의 ID와 .env의 USER_ID가 다름"
  fi
else
  err=$(echo "$resp" | head -c 200)
  check "토큰 유효" "FAIL" "$err"
fi

# 토큰 만료까지 D-day 계산
if [ -n "$THREADS_TOKEN_ISSUED_AT" ]; then
  issued_epoch=$(date -d "$THREADS_TOKEN_ISSUED_AT" +%s 2>/dev/null)
  if [ -n "$issued_epoch" ]; then
    now_epoch=$(date +%s)
    expires_epoch=$((issued_epoch + 60*86400))
    days_left=$(( (expires_epoch - now_epoch) / 86400 ))
    if [ "$days_left" -gt 7 ]; then
      check "토큰 만료" "OK" "D-$days_left"
    elif [ "$days_left" -gt 0 ]; then
      check "토큰 만료" "OK" "⚠️ D-$days_left (곧 갱신 필요)"
    else
      check "토큰 만료" "FAIL" "이미 만료됨"
    fi
  fi
fi

# ---------- 3. Discord ----------
echo ""
echo "[3/4] Discord Webhook"
resp=$(curl -s "$DISCORD_WEBHOOK_URL")
if echo "$resp" | grep -q '"id"'; then
  channel_id=$(echo "$resp" | grep -o '"channel_id":"[^"]*"' | cut -d'"' -f4)
  check "검수용 webhook" "OK" "channel_id=$channel_id"
else
  check "검수용 webhook" "FAIL" "유효하지 않음"
fi

if [ "$DISCORD_ALERT_WEBHOOK_URL" != "$DISCORD_WEBHOOK_URL" ]; then
  resp=$(curl -s "$DISCORD_ALERT_WEBHOOK_URL")
  if echo "$resp" | grep -q '"id"'; then
    check "알림용 webhook" "OK" "별도 채널"
  else
    check "알림용 webhook" "FAIL" "유효하지 않음"
  fi
else
  check "알림용 webhook" "OK" "검수용과 동일 채널"
fi

# ---------- 4. n8n ----------
echo ""
echo "[4/4] n8n"
code=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_BASE_URL/api/v1/workflows?limit=1")
if [ "$code" = "200" ]; then
  check "API 인증" "OK" "$N8N_BASE_URL"
else
  check "API 인증" "FAIL" "HTTP $code"
fi

# ---------- 결과 ----------
echo ""
echo "=========================================="
echo "  결과: $pass 통과 / $fail 실패"
echo "=========================================="
echo ""

[ $fail -eq 0 ] && exit 0 || exit 1
