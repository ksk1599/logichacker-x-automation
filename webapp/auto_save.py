"""
auto_save.py — Claude 응답에서 레퍼런스 블록을 추출해 .md 파일에 영구 저장.
PC를 껐다 켜도 skills/youtube/*.md 파일에 누적 학습 내용이 남습니다.
"""

import re
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent

PATTERNS_MD = BASE_DIR / "skills" / "youtube" / "patterns.md"
HOOKS_MD = BASE_DIR / "skills" / "youtube" / "hook_patterns.md"

# Claude 응답에서 저장 블록을 감싸는 마커
_MARKER_RE = re.compile(
    r"<!--\s*SAVE_START\s*-->(.*?)<!--\s*SAVE_END\s*-->",
    re.DOTALL,
)


def _extract_save_block(response: str) -> Optional[str]:
    """응답 텍스트에서 <!-- SAVE_START --> ... <!-- SAVE_END --> 사이 내용 추출"""
    m = _MARKER_RE.search(response)
    return m.group(1).strip() if m else None


# ── 다음 알파벳/번호 계산 ─────────────────────────────────────────────
def get_next_thumbnail_letter() -> str:
    """patterns.md에 저장된 마지막 레퍼런스 알파벳 + 1 반환 (없으면 'A')"""
    text = PATTERNS_MD.read_text(encoding="utf-8")
    matches = re.findall(r"###\s*레퍼런스\s+([A-Z])\s+—", text)
    if not matches:
        return "A"
    last = matches[-1]
    return chr(ord(last) + 1) if ord(last) < ord("Z") else "A"


def get_next_script_number() -> int:
    """hook_patterns.md에 저장된 마지막 레퍼런스 번호 + 1 반환 (없으면 1)"""
    text = HOOKS_MD.read_text(encoding="utf-8")
    matches = re.findall(r"###\s*레퍼런스\s+#(\d+)\s+—", text)
    if not matches:
        return 1
    return max(int(n) for n in matches) + 1


# ── 파일 append ───────────────────────────────────────────────────────
def save_thumbnail_reference(response: str) -> Optional[str]:
    """
    응답에 저장 블록이 있으면 patterns.md에 append.
    저장된 레퍼런스 알파벳 반환, 없으면 None.
    """
    block = _extract_save_block(response)
    if not block:
        return None

    with open(PATTERNS_MD, "a", encoding="utf-8") as f:
        f.write("\n\n---\n\n" + block + "\n")

    m = re.search(r"###\s*레퍼런스\s+([A-Z])\s+—", block)
    return m.group(1) if m else "?"


def save_script_reference(response: str) -> Optional[int]:
    """
    응답에 저장 블록이 있으면 hook_patterns.md에 append.
    저장된 레퍼런스 번호 반환, 없으면 None.
    """
    block = _extract_save_block(response)
    if not block:
        return None

    with open(HOOKS_MD, "a", encoding="utf-8") as f:
        f.write("\n\n---\n\n" + block + "\n")

    m = re.search(r"###\s*레퍼런스\s+#(\d+)\s+—", block)
    return int(m.group(1)) if m else None
