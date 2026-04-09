-- =====================================================
-- 로직해커 엑스 멀티에이전트 시스템 - Supabase Schema
-- =====================================================
-- 실행 방법:
--   1. Supabase Dashboard > SQL Editor 열기
--   2. 이 파일 전체 복사해서 붙여넣기
--   3. Run 클릭
-- =====================================================

-- ========== 1. 에이전트 메시지 버스 ==========
-- 에이전트들이 서로 실시간으로 대화하는 채널
-- Realtime 구독으로 즉시 수신 가능
create table if not exists agent_messages (
  id           bigserial primary key,
  created_at   timestamptz not null default now(),
  from_agent   text not null,           -- 보낸 에이전트 (예: 'qa', 'writer')
  to_agent     text not null,           -- 받는 에이전트 ('*'는 broadcast)
  message_type text not null,           -- 'request' | 'response' | 'feedback' | 'alert'
  topic        text,                    -- 작업 컨텍스트 (예: 'post_2026-04-09_morning')
  payload      jsonb not null,          -- 실제 내용 (자유 구조)
  status       text not null default 'pending', -- 'pending' | 'read' | 'done' | 'failed'
  parent_id    bigint references agent_messages(id), -- 답변 체인 추적
  read_at      timestamptz,
  done_at      timestamptz
);

create index if not exists idx_agent_messages_to_status
  on agent_messages(to_agent, status, created_at);
create index if not exists idx_agent_messages_topic
  on agent_messages(topic);

-- Realtime 활성화 (에이전트가 구독 가능)
alter publication supabase_realtime add table agent_messages;


-- ========== 2. Supervisor 감사 로그 ==========
-- 감시 에이전트가 발견한 문제와 조치를 모두 기록
create table if not exists supervisor_audits (
  id           bigserial primary key,
  created_at   timestamptz not null default now(),
  target_agent text not null,           -- 감사 대상 에이전트
  target_message_id bigint references agent_messages(id),
  verdict      text not null,           -- 'pass' | 'fail' | 'warning'
  reason       text,                    -- 실패 이유
  action_taken text,                    -- 'rerun_requested' | 'logged' | 'escalated'
  details      jsonb
);

create index if not exists idx_supervisor_audits_target
  on supervisor_audits(target_agent, created_at desc);


-- ========== 3. Threads 게시물 ==========
create table if not exists threads_posts (
  id              bigserial primary key,
  threads_post_id text unique,           -- Threads API가 반환하는 ID
  content         text not null,         -- 본문 (4줄)
  status          text not null default 'draft', -- 'draft' | 'qa_pending' | 'qa_passed' | 'published' | 'rejected'
  qa_feedback     text,                  -- QA 피드백 (재작성 시 참고)
  retry_count     integer not null default 0,
  prompt_version  text,                  -- 어떤 프롬프트 버전으로 생성됐는지
  created_at      timestamptz not null default now(),
  published_at    timestamptz
);

create index if not exists idx_threads_posts_status on threads_posts(status, created_at desc);


-- ========== 4. 게시물 성과 ==========
create table if not exists post_insights (
  id              bigserial primary key,
  post_id         bigint references threads_posts(id) on delete cascade,
  threads_post_id text,
  likes           integer default 0,
  views           integer default 0,
  replies         integer default 0,
  reposts         integer default 0,
  collected_at    timestamptz not null default now(),
  -- 잘 된 글 판별용 (조회수 상위 20%)
  is_top_performer boolean default false
);

create index if not exists idx_post_insights_post_id on post_insights(post_id, collected_at desc);
create index if not exists idx_post_insights_top on post_insights(is_top_performer) where is_top_performer = true;


-- ========== 5. 프롬프트 버전 ==========
create table if not exists prompt_versions (
  id            bigserial primary key,
  agent_name    text not null,           -- 'writer' | 'qa' | 'cs' 등
  version       text not null,           -- 'v1.0.3' 또는 timestamp 기반
  prompt        text not null,           -- 실제 프롬프트
  parent_version text,                   -- 이전 버전
  diff_summary  text,                    -- Optimizer가 작성한 변경 요약
  performance_score numeric,             -- 적용 후 평균 성과
  is_active     boolean default false,
  approved_by   text,                    -- 'orchestrator' | 'user'
  created_at    timestamptz not null default now(),
  activated_at  timestamptz,
  unique(agent_name, version)
);

create index if not exists idx_prompt_versions_active
  on prompt_versions(agent_name, is_active) where is_active = true;


-- ========== 6. 토큰 관리 ==========
create table if not exists tokens (
  id           bigserial primary key,
  service      text not null unique,    -- 'threads' | 'meta'
  access_token text not null,
  issued_at    timestamptz not null,
  expires_at   timestamptz not null,    -- issued_at + 60일
  last_refresh_alert_at timestamptz,    -- 중복 알림 방지
  meta         jsonb
);


-- ========== 7. 스케줄 로그 ==========
-- Scheduler가 실행한 루프 기록 (디버깅 + Supervisor 감시용)
create table if not exists schedule_runs (
  id           bigserial primary key,
  loop_name    text not null,           -- 'daily_writer' | 'optimizer_3day' | 'token_check'
  started_at   timestamptz not null default now(),
  ended_at     timestamptz,
  status       text not null default 'running', -- 'running' | 'success' | 'failed'
  error        text,
  meta         jsonb
);

create index if not exists idx_schedule_runs_loop on schedule_runs(loop_name, started_at desc);


-- =====================================================
-- 초기 시드 데이터
-- =====================================================

-- Threads 토큰 초기값 (.env에서도 읽을 수 있지만 DB에도 저장)
-- ⚠️ 실제 값은 .env에서 읽어서 별도 스크립트로 insert. 여기엔 안 박음.

-- Writer 초기 프롬프트 버전
insert into prompt_versions (agent_name, version, prompt, is_active, approved_by, activated_at)
values (
  'writer',
  'v1.0.0',
  '딱 4줄로 써라. 한 줄 최대 15자. 1줄: 내가 한 행동(숫자 포함). 2줄: 결과(숫자 포함). 3줄: 반전 또는 이유. 4줄: 핵심 한 줄. 제목 금지. 번호 목록 금지. 👇 금지.',
  true,
  'system',
  now()
) on conflict (agent_name, version) do nothing;
