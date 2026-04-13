-- =====================================================
-- Threads 토큰을 DB에 등록 (최초 1회만)
-- =====================================================
-- ⚠️ 이 파일은 .env 값을 참조해야 함.
-- 실행 전에 아래 두 줄의 PLACEHOLDER를 실제 .env 값으로 바꾸세요:
--
--   1. <THREADS_ACCESS_TOKEN_THAASoy7pLlZCBBUVRzY3FDT2gzZAnUtMFRVX1pkMlFzVjhTSW5KSGd2bTZA6UjJtQzRfUjR0UU14X3dLNThMeUJ1N3BDN3BZAYjBsdHJCTjlraVB3cUo1eG0xM25UZAFI1dlBGMWhfekhmamxNYU1iZAWNpZAmlYeUFzcmlydExYNDlDbzN2UQZDZD>
--   2. <THREADS_TOKEN_ISSUED_AT_여기에_2026-04-08>
--
-- 그 다음 Supabase SQL Editor에 붙여넣고 Run.
-- =====================================================

insert into tokens (service, access_token, issued_at, expires_at)
values (
  'threads',
  '<THREADS_ACCESS_TOKEN_여기에_붙여넣기>',
  '<THREADS_TOKEN_ISSUED_AT_여기에_YYYY-MM-DD>'::timestamptz,
  '<THREADS_TOKEN_ISSUED_AT_여기에_YYYY-MM-DD>'::timestamptz + interval '60 days'
)
on conflict (service) do update
set access_token = excluded.access_token,
    issued_at    = excluded.issued_at,
    expires_at   = excluded.expires_at,
    last_refresh_alert_at = null;

-- 확인
select service, issued_at, expires_at, expires_at - now() as remaining
from tokens where service = 'threads';
