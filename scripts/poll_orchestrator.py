#!/usr/bin/env python3
"""
poll_orchestrator.py — Method B 로컬 폴링 스크립트

Supabase agent_messages 테이블을 30초마다 체크.
pending 메시지가 있으면 Claude Code를 실행해 처리.

실행 방법:
  python scripts/poll_orchestrator.py

종료:
  Ctrl+C
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Windows cp949 터미널 인코딩 문제 방지
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── 환경변수 로드 ──────────────────────────────────────────────
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_path = os.path.abspath(env_path)
    if not os.path.exists(env_path):
        print(f"[ERROR] .env 파일 없음: {env_path}")
        sys.exit(1)

    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


# ── Supabase REST 헬퍼 ────────────────────────────────────────
def supabase_request(method, path, body=None):
    url = os.environ['SUPABASE_URL'].rstrip('/') + path
    data = json.dumps(body).encode('utf-8') if body else None

    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            'apikey': os.environ['SUPABASE_ANON_KEY'],
            'Authorization': 'Bearer ' + os.environ['SUPABASE_ANON_KEY'],
            'Content-Type': 'application/json',
            'Prefer': 'return=representation',
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode('utf-8', errors='replace')
        print(f"[HTTP {e.code}] {path}: {body_text[:200]}")
        return None
    except Exception as e:
        print(f"[ERROR] Supabase 요청 실패: {e}")
        return None


def fetch_pending_messages():
    """orchestrator 또는 analyst로 가는 pending 메시지 조회"""
    path = (
        '/rest/v1/agent_messages'
        '?status=eq.pending'
        '&to_agent=in.(orchestrator,analyst)'
        '&order=created_at.asc'
        '&limit=5'
    )
    return supabase_request('GET', path) or []


def mark_processing(msg_id):
    path = f'/rest/v1/agent_messages?id=eq.{msg_id}'
    supabase_request('PATCH', path, {'status': 'read', 'read_at': utcnow()})


def mark_done(msg_id):
    path = f'/rest/v1/agent_messages?id=eq.{msg_id}'
    supabase_request('PATCH', path, {'status': 'done', 'done_at': utcnow()})


def mark_failed(msg_id, error_msg):
    path = f'/rest/v1/agent_messages?id=eq.{msg_id}'
    supabase_request('PATCH', path, {
        'status': 'failed',
        'done_at': utcnow(),
        'payload': {'error': error_msg[:500]}
    })


def utcnow():
    return datetime.now(timezone.utc).isoformat()


# ── Claude Code 실행 ──────────────────────────────────────────
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

AGENT_PROMPTS = {
    'orchestrator': (
        "너는 orchestrator 에이전트다. "
        "agent/PROTOCOL.md와 .claude/agents/orchestrator.md를 읽고 아래 트리거를 처리해:\n\n"
        "{payload}"
    ),
    'analyst': (
        "너는 analyst 에이전트다. "
        ".claude/agents/analyst.md를 읽고 아래 자기개선 루프 트리거를 처리해:\n\n"
        "{payload}"
    ),
}


def run_claude(msg):
    to_agent = msg.get('to_agent', 'orchestrator')
    topic = msg.get('topic', '')
    payload = msg.get('payload', {})

    prompt_template = AGENT_PROMPTS.get(to_agent, AGENT_PROMPTS['orchestrator'])
    prompt = prompt_template.format(
        payload=json.dumps({'topic': topic, **payload}, ensure_ascii=False, indent=2)
    )

    print(f"  → claude 실행 중 (agent: {to_agent}, topic: {topic})")

    result = subprocess.run(
        ['claude', '-p', prompt],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=600  # 10분 타임아웃
    )

    if result.returncode == 0:
        print(f"  ✓ 완료 (exit 0)")
        return True, result.stdout[:200]
    else:
        err = result.stderr[:300] or result.stdout[:300]
        print(f"  ✗ 실패 (exit {result.returncode}): {err}")
        return False, err


# ── 중복 방지: 최근 5분 내 같은 topic 처리 여부 체크 ─────────
_recently_processed = {}  # topic → timestamp

def already_processed_recently(topic):
    if topic in _recently_processed:
        elapsed = time.time() - _recently_processed[topic]
        if elapsed < 300:  # 5분
            return True
    return False

def mark_recently_processed(topic):
    _recently_processed[topic] = time.time()
    # 오래된 항목 정리
    cutoff = time.time() - 600
    for k in list(_recently_processed):
        if _recently_processed[k] < cutoff:
            del _recently_processed[k]


# ── 메인 루프 ─────────────────────────────────────────────────
POLL_INTERVAL = 30  # 초

def main():
    load_env()
    print("=" * 50)
    print("로직해커 엑스 - Orchestrator Polling Script")
    print(f"프로젝트: {PROJECT_DIR}")
    print(f"폴링 간격: {POLL_INTERVAL}초")
    print("종료: Ctrl+C")
    print("=" * 50)

    while True:
        try:
            messages = fetch_pending_messages()

            if messages:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] pending {len(messages)}개 발견")

                for msg in messages:
                    msg_id = msg['id']
                    topic = msg.get('topic', f'msg_{msg_id}')

                    if already_processed_recently(topic):
                        print(f"  SKIP (5분 내 처리됨): {topic}")
                        continue

                    mark_processing(msg_id)
                    mark_recently_processed(topic)

                    success, detail = run_claude(msg)

                    if success:
                        mark_done(msg_id)
                    else:
                        mark_failed(msg_id, detail)

            else:
                # 대기 중 — 조용히
                pass

        except KeyboardInterrupt:
            print("\n\n폴링 종료.")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 루프 오류: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
