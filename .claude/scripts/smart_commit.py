"""
smart_commit.py — 변경 내용을 Claude API로 분석해 의미 있는 커밋 메시지 자동 생성
세션 종료 훅에서 호출됨
"""

import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent  # 프로젝트 루트


def load_api_key() -> str:
    env_path = BASE_DIR / ".env"
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "ANTHROPIC_API_KEY":
                return val.strip()
    raise ValueError("ANTHROPIC_API_KEY를 .env에서 찾을 수 없습니다")


def get_diff_stat() -> str:
    """변경된 파일 목록과 간략한 통계 반환"""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    stat = result.stdout.strip()

    # 새 파일(untracked) 목록도 포함
    new_files = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, cwd=BASE_DIR
    ).stdout.strip()

    if new_files:
        stat += "\n새 파일:\n" + new_files

    return stat or "변경사항 없음"


def generate_commit_message(diff_stat: str) -> str:
    """Claude API로 커밋 메시지 생성"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=load_api_key())

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # 빠르고 저렴한 모델로 충분
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"""아래 git 변경 내용을 보고 한국어로 커밋 메시지를 한 줄로 작성해줘.
규칙:
- 30자 이내
- 무엇을 했는지 명확하게
- "자동 저장" 같은 말 쓰지 말 것
- 예시: "썸네일 에이전트 추가", "웹앱 UI 버그 수정", "hook_patterns 학습 데이터 추가"

변경 내용:
{diff_stat}

커밋 메시지만 출력해. 다른 말 하지 마."""
            }]
        )
        return response.content[0].text.strip()

    except Exception as e:
        # API 실패 시 파일 목록 기반 기본 메시지 생성
        lines = diff_stat.split("\n")
        files = [l.strip().split()[0] for l in lines if "|" in l or l.startswith(" ")][:3]
        if files:
            return f"업데이트: {', '.join(files)}"
        return "코드 업데이트"


def has_changes() -> bool:
    """커밋할 변경사항이 있는지 확인"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    return bool(result.stdout.strip())


def main():
    os.chdir(BASE_DIR)

    if not has_changes():
        sys.exit(0)  # 변경사항 없으면 조용히 종료

    diff_stat = get_diff_stat()
    message = generate_commit_message(diff_stat)

    # git add + commit + push
    subprocess.run(["git", "add", "."], cwd=BASE_DIR)
    subprocess.run(["git", "commit", "-m", message], cwd=BASE_DIR)
    subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR)

    print(f"[smart_commit] 커밋 완료: {message}")


if __name__ == "__main__":
    main()
