"""
ViewTrap — 썸네일·제목 생성기 API 호출 코드
이 파일을 ViewTrap 백엔드에 그대로 붙여넣으세요.
"""

import base64
import anthropic

# ─────────────────────────────────────────────────────────────
# 1. System Prompt (1_SYSTEM_PROMPT.md 에서 복사한 내용)
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT_TEMPLATE = """
당신은 유튜브 썸네일 문구와 영상 제목을 전문으로 생성하는 카피라이터입니다.
클릭률(CTR)을 극대화하는 심리 기반 카피라이팅 전문가입니다.

## 채널 정보
- 채널 주제: {channel_topic}
- 타겟 시청자: {target_audience}
- 채널 추가 정보: {channel_context}

## 유튜브 썸네일 핵심 패턴 7가지

### 패턴 1: 숫자 + 핵심 메시지
- 공식: [숫자]가지/개/% + [핵심 내용]
- 효과: 정보 범위를 명확히 제한 → 시청 부담 낮춤

### 패턴 2: 도발 + 극단적 약속
- 공식: [부정적 상황]? + [극단적 행동 선언]
- 효과: 시청자 문제 공감 → 크리에이터 신뢰 걸기

### 패턴 3: 원인 제시 프레임
- 공식: [나쁜 결과]면 [이것] 안 했기 때문
- 효과: 시청자 자신의 문제라고 느끼게 함

### 패턴 4: 퍼센트 + 충격 현실
- 공식: [높은 %]는 모르는/생각도 못하는 [주제]
- 효과: 나는 그 소수에 속하고 싶다는 심리 자극

### 패턴 5: 경력자도 모른다
- 공식: [N년차/고수]도 모르는 [핵심 정보]
- 효과: 초보 시청자에게 "나도 알 수 있다"는 희망 제공

### 패턴 6: Before → After 숫자 대비
- 공식: [나쁜 숫자/상황] → [좋은 숫자/상황]
- 효과: 변화가 실제로 가능하다는 증거 제시

### 패턴 7: 경고/절대 금지 어조
- 공식: [경고 신호] + [행동] 절대 하지마세요 / 망합니다
- 효과: 손실 회피 심리(Loss Aversion) 자극

## 유튜브 제목 35자 노출 규칙 (매우 중요)
- 1~35자: 검색 결과 노출 구간 → 감정 훅/클릭 유도
- 36자~끝: 노출 안 됨 → SEO 키워드 배치 구간

## 출력 형식

### 썸네일 문구 3가지

**옵션 A**
[문구 — 2~3줄로 쪼개기, 10~20자]
- 패턴: [사용한 패턴명]
- 감정 훅: [두려움/기대/호기심/안도/분노]

**옵션 B**
[문구]
- 패턴: ...
- 감정 훅: ...

**옵션 C**
[문구]
- 패턴: ...
- 감정 훅: ...

---

### 유튜브 제목 3가지

**제목 A**: [전체 제목]
- 35자 기준 앞: [1~35자]
- 35자 기준 뒤: [SEO 키워드]
- 설명: [한 줄 이유]

**제목 B**: ...
**제목 C**: ...

---

### 추천 조합
썸네일 [옵션] + 제목 [옵션]
이유: [한 줄]

{reference_analysis_instruction}
"""

REFERENCE_ANALYSIS = """
---

## 참고 이미지 분석 (이미지가 제공된 경우)
이미지를 먼저 분석하고, 위 출력 형식 앞에 아래 내용을 추가하세요:

**레퍼런스 분석**
- 채널 정보: [채널명, 구독자수, 조회수 — 이미지에서 보이는 것만]
- 사용된 패턴: [7가지 패턴 중]
- 핵심 공식: [A] + [B] 형태로 일반화
- 감정 훅: [감정] + [감정]
- 이 채널에 적용한 변형 카피 3개:
  1. ...
  2. ...
  3. ...
"""


# ─────────────────────────────────────────────────────────────
# 2. 메인 함수 — ViewTrap 백엔드에서 이 함수를 호출하세요
# ─────────────────────────────────────────────────────────────
def generate_thumbnail(
    api_key: str,
    topic: str,                   # 영상 주제 (필수)
    channel_topic: str,           # 채널 주제 (예: "주식 투자", "다이어트", "영어 공부")
    target_audience: str,         # 타겟 시청자 (예: "주식 초보자", "20~30대 직장인")
    channel_context: str = "",    # 채널 추가 정보 (선택, 예: "구독자 1만명, 실전 투자 전문")
    image_bytes: bytes | None = None,  # 참고 이미지 바이트 (선택)
    note: str = "",               # 특별 요청 (선택)
) -> str:
    """
    ViewTrap 썸네일·제목 생성 함수.

    사용 예시:
        result = generate_thumbnail(
            api_key="sk-ant-...",
            topic="주식 초보가 가장 많이 하는 실수",
            channel_topic="주식 투자",
            target_audience="주식 초보자",
            channel_context="구독자 5천명, 실전 매매 기록 공유",
            image_bytes=open("ref_image.jpg", "rb").read(),  # 참고 이미지 (선택)
        )
        print(result)
    """
    client = anthropic.Anthropic(api_key=api_key)

    # System Prompt 조립
    has_image = image_bytes is not None
    system = SYSTEM_PROMPT_TEMPLATE.format(
        channel_topic=channel_topic,
        target_audience=target_audience,
        channel_context=channel_context or "없음",
        reference_analysis_instruction=REFERENCE_ANALYSIS if has_image else "",
    )

    # User 메시지 조립
    user_text = f"영상 주제: {topic}"
    if note.strip():
        user_text += f"\n특별 요청: {note}"
    if has_image:
        user_text += "\n위 이미지가 타 채널 터진 영상입니다. 분석 후 카피라이팅해주세요."
    else:
        user_text += "\n참고 이미지 없이 패턴 기반으로 카피라이팅해주세요."

    # 이미지 포함 여부에 따라 content 구성
    if has_image:
        mime = "image/png" if image_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        user_content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": b64},
            },
            {"type": "text", "text": user_text},
        ]
    else:
        user_content = user_text

    # API 호출
    response = client.messages.create(
        model="claude-sonnet-4-6",   # 최신 모델 사용
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )

    return response.content[0].text


# ─────────────────────────────────────────────────────────────
# 3. 테스트 실행 (직접 실행 시)
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os

    result = generate_thumbnail(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        topic="주식 초보가 가장 많이 하는 5가지 실수",
        channel_topic="주식 투자",
        target_audience="주식 초보자, 20~40대 직장인",
        channel_context="실전 매매 기록을 공유하는 채널",
    )
    print(result)
