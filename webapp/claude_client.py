"""
claude_client.py — Anthropic API 호출 + 프롬프트 조립
에이전트 .md를 시스템 프롬프트로, skills/.md를 컨텍스트로 사용.
"""

import base64
import re
from datetime import date
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent  # 프로젝트 루트


# ── .env 파싱 (stdlib-only) ────────────────────────────────────────────
def load_api_key() -> str:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f".env 파일 없음: {env_path}")
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "ANTHROPIC_API_KEY":
                return val.strip()
    raise ValueError("ANTHROPIC_API_KEY를 .env에서 찾을 수 없습니다")


# ── .md 파일 유틸 ─────────────────────────────────────────────────────
def _strip_frontmatter(text: str) -> str:
    """YAML frontmatter (--- ... ---) 제거"""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text


def _read_agent_prompt(agent_name: str) -> str:
    path = BASE_DIR / ".claude" / "agents" / f"{agent_name}.md"
    return _strip_frontmatter(path.read_text(encoding="utf-8"))


def _read_knowledge(filename: str) -> str:
    path = BASE_DIR / "skills" / "youtube" / filename
    return path.read_text(encoding="utf-8")


# ── 웹앱 환경 추가 지침 (Claude가 응답에 저장 블록을 마커로 출력하도록 유도) ──
_THUMBNAIL_SUFFIX = """\n
## 웹앱 환경 추가 지침
Write 도구 없이 실행 중입니다. 레퍼런스 이미지가 제공된 경우,
응답 안에 반드시 아래 마커 사이에 저장 블록을 정확한 형식으로 포함하세요.
마커는 한 글자도 바꾸지 말고 그대로 출력하세요:

<!-- SAVE_START -->
### 레퍼런스 {letter} — [영상 주제] ({today} 학습)
- **채널**: [채널명] (구독자 [N]명 → 조회수 [N])
- **썸네일**: "[문구]"
- **제목**: "[제목]"
- **핵심 공식**: `[추출한 일반화 공식]`
- **감정 훅**: [감정] + [감정]
- **스마트스토어 변형 카피**: [이번 작업에서 생성한 카피 중 채택 가능한 것]
<!-- SAVE_END -->

레퍼런스 이미지가 제공되지 않은 경우에는 마커를 절대 출력하지 마세요.
"""

_SCRIPT_SUFFIX = """\n
## 웹앱 환경 추가 지침
Write 도구 없이 실행 중입니다. 레퍼런스 원고가 제공된 경우,
응답 안에 반드시 아래 마커 사이에 저장 블록을 정확한 형식으로 포함하세요.
마커는 한 글자도 바꾸지 말고 그대로 출력하세요:

<!-- SAVE_START -->
### 레퍼런스 #{number} — [영상 주제/채널] ({today} 학습)
**원본 원고:**
> [원고 전문]

**구조 분석:**
- 후킹 (0~5초): [분석]
- 공감 (5~15초): [분석]
- 예고 (15~25초): [분석]
- 신뢰 (25~30초): [분석]

**핵심 공식:** [일반화된 공식]
**감정 흐름:** [감정A] → [감정B] → [감정C]
<!-- SAVE_END -->

레퍼런스 원고가 제공되지 않은 경우에는 마커를 절대 출력하지 마세요.
"""


# ── API 호출 ──────────────────────────────────────────────────────────
def _get_client():
    import anthropic  # 런타임 import (streamlit 환경에서 에러 메시지 개선 목적)
    return anthropic.Anthropic(api_key=load_api_key())


def call_thumbnail(
    topic: str,
    image_bytes: Optional[bytes],
    note: str,
    next_letter: str,
) -> str:
    today = date.today().strftime("%Y-%m-%d")
    knowledge = _read_knowledge("patterns.md")
    system = _read_agent_prompt("thumbnail") + _THUMBNAIL_SUFFIX.format(
        letter=next_letter, today=today
    )

    # user 메시지 조립
    preamble = (
        f"## 현재까지 학습된 패턴 지식베이스\n{knowledge}\n\n---\n\n"
        f"영상 주제: {topic}\n"
    )
    if note.strip():
        preamble += f"특별 요청: {note}\n"

    if image_bytes:
        mime = "image/png" if image_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        user_content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": b64},
            },
            {
                "type": "text",
                "text": preamble + "위 이미지가 레퍼런스 영상입니다. 분석 후 카피라이팅해주세요.",
            },
        ]
    else:
        user_content = preamble + "참고 이미지 없이 기존 패턴 기반으로 카피라이팅해주세요."

    resp = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return resp.content[0].text


def call_script(
    topic: str,
    ref_script: str,
    next_number: int,
) -> str:
    today = date.today().strftime("%Y-%m-%d")
    knowledge = _read_knowledge("hook_patterns.md")
    system = _read_agent_prompt("script_30s") + _SCRIPT_SUFFIX.format(
        number=next_number, today=today
    )

    preamble = (
        f"## 현재까지 학습된 후킹 패턴 지식베이스\n{knowledge}\n\n---\n\n"
        f"영상 주제: {topic}\n"
    )
    if ref_script.strip():
        user_content = (
            preamble
            + f"\n레퍼런스 30초 원고:\n{ref_script}\n\n"
            + "위 원고를 학습하고 제 채널 주제에 맞게 첫 30초 원고를 작성해주세요."
        )
    else:
        user_content = preamble + "\n레퍼런스 원고 없이 기존 패턴 기반으로 첫 30초 원고를 작성해주세요."

    resp = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return resp.content[0].text


def call_ppt_content(title: str, script: str) -> str:
    system = """당신은 강의용 PPT 슬라이드 설계 전문가입니다.
유튜브 원고를 받아 강의 슬라이드에 최적화된 구조로 변환합니다.

## 규칙
- 슬라이드 1장 = 핵심 개념 1개
- 불릿 포인트: 슬라이드당 최대 4개, 각 항목 15자 이내
- 전체 문장 금지 — 핵심어/구 중심으로 압축
- 강조할 핵심어는 ** ** 로 표시
- 원고의 흐름과 순서를 유지

## 출력 형식 (정확히 이 형식으로만 출력)

[TITLE]
제목: {title}
부제: (한 줄 부제목)

[SECTION]
섹션명: 도입부
슬라이드제목: (섹션 소개 제목)

[BULLETS]
슬라이드제목: (이 슬라이드의 핵심 질문이나 주제)
• (핵심어/구 1)
• (핵심어/구 2)
• (핵심어/구 3)

[HIGHLIGHT]
강조문구: (임팩트 있는 한 줄, 20자 이내)
설명: (한 줄 보충 설명)

[SECTION]
섹션명: 본문
...

각 섹션마다 위 형식의 슬라이드를 2~5장 생성하세요.
도입부·본문·개인가치·결론 순서를 유지하세요."""

    user_content = f"강의 제목: {title}\n\n원고:\n{script}"

    resp = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return resp.content[0].text


def call_full_script(
    topic: str,
    script_draft: str,
    title_ref: str = "",
) -> str:
    system = _read_agent_prompt("full_script")

    title_block = f"## 유튜브 제목 (방향 참고용)\n{title_ref.strip()}\n\n" if title_ref.strip() else ""

    user_content = (
        f"영상 주제: {topic}\n\n"
        f"{title_block}"
        f"## 원고 초안 (도입부+본문 전체)\n{script_draft}\n\n"
        "원고에서 도입부와 본문을 구분하고, 각각 채널 스타일에 맞게 다듬은 후 개인가치와 결론을 추가해주세요."
    )

    resp = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    return resp.content[0].text
