# ViewTrap 썸네일·제목 생성기 — 이식 가이드

## 파일 구성

| 파일 | 용도 |
|---|---|
| `1_SYSTEM_PROMPT.md` | Claude에게 주입할 역할·지침 (System Prompt) |
| `2_API_CALL.py` | 백엔드에 붙여넣을 Python 코드 |
| `3_README.md` | 이 파일 |

---

## 로직해커 엑스 버전과 달라진 점

| 항목 | 로직해커 엑스 (기존) | ViewTrap (이식 버전) |
|---|---|---|
| 채널 정보 | 스마트스토어 채널 고정 | 채널 주제/타겟 동적 입력 |
| 지식베이스 | patterns.md 파일 필요 | 파일 없이 패턴을 System Prompt에 내장 |
| 저장 기능 | patterns.md에 자동 저장 | 없음 (ViewTrap DB에 저장하면 됨) |
| 호출 방식 | Streamlit 앱 내부 | 독립 함수 — 어디서든 import 가능 |

---

## 사용 방법 (ViewTrap 백엔드에서)

```python
from thumbnail_generator import generate_thumbnail

# 기본 사용 (이미지 없음)
result = generate_thumbnail(
    api_key="sk-ant-...",
    topic="다이어트 3개월 만에 10kg 빼는 법",
    channel_topic="다이어트·헬스",
    target_audience="다이어트 초보, 20~40대 직장인",
)

# 참고 이미지 포함
with open("reference.jpg", "rb") as f:
    image = f.read()

result = generate_thumbnail(
    api_key="sk-ant-...",
    topic="다이어트 3개월 만에 10kg 빼는 법",
    channel_topic="다이어트·헬스",
    target_audience="다이어트 초보, 20~40대 직장인",
    image_bytes=image,
    note="경고 어조로 만들어주세요",
)

print(result)  # 썸네일 3가지 + 제목 3가지 + 추천 조합
```

---

## UI에 필요한 입력 필드

| 필드 | 필수 여부 | 설명 |
|---|---|---|
| `topic` | 필수 | "이번 영상 주제" 텍스트 입력 |
| `channel_topic` | 필수 | "채널 주제" (한 번만 설정 or 매번 입력) |
| `target_audience` | 필수 | "타겟 시청자" (한 번만 설정 or 매번 입력) |
| `image_bytes` | 선택 | 참고 이미지 업로드 |
| `note` | 선택 | 특별 요청 |

> 💡 `channel_topic`, `target_audience`는 ViewTrap의 "채널 설정" 페이지에서
> 한 번 저장해두고 매 요청마다 자동으로 주입하면 사용자 경험이 좋아집니다.

---

## 출력 형식 예시

```
**레퍼런스 분석** (이미지 있을 때)
- 채널 정보: OOO채널 (구독자 1만 → 조회수 50만)
- 사용된 패턴: 패턴 4 (퍼센트 + 충격 현실)
- 핵심 공식: [높은 %]가 놓치는 [주제의 핵심]
- ...

---

### 썸네일 문구 3가지

**옵션 A**
다이어트 포기했다면
이것 때문입니다
- 패턴: 원인 제시 프레임
- 감정 훅: 두려움 + 공감

**옵션 B**
90%는 모르는
살 안 빠지는 진짜 이유
- 패턴: 퍼센트 + 충격 현실
- 감정 훅: 호기심 + 두려움

...

### 유튜브 제목 3가지

**제목 A**: 다이어트 포기하는 진짜 이유 알려드립니다 | 다이어트 방법 체중감량 식단 운동
- 35자 기준 앞: "다이어트 포기하는 진짜 이유 알려드립니다"
- 35자 기준 뒤: "다이어트 방법 체중감량 식단 운동"
...

### 추천 조합
썸네일 옵션 B + 제목 A
이유: 퍼센트 패턴이 클릭 심리 가장 강하게 자극, 제목은 검색 최적화됨
```

---

## 비용 참고 (Claude Sonnet 4.6 기준)

| 조건 | 예상 토큰 | 예상 비용 |
|---|---|---|
| 이미지 없음 | ~2,000 토큰 | ~$0.006 |
| 이미지 포함 | ~3,500 토큰 | ~$0.011 |

월 1,000회 요청 기준: 약 $6~11 수준
