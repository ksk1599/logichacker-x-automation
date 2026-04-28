# 에이전트 사용 가이드

로직해커 엑스 자동화 시스템의 플랫폼별 에이전트 호출 가이드.

---

## 플랫폼별 에이전트 맵

### 🎵 Threads (스마트스토어 콘텐츠 자동화)

| 할 일 | 호출할 에이전트 | 예시 명령 |
|---|---|---|
| 글 발행 시작 | `@orchestrator` | `@orchestrator 오늘 저녁 글 발행해줘` |
| 글 직접 작성 | `@writer` | `@writer 키워드 배열 주제로 글 써줘` |
| 글 검수만 | `@qa` | `@qa 이 글 검수해줘: [글 내용]` |
| 도메인 지식 확인 | `@knowledge` | `@knowledge 배열고정 키워드가 뭐야?` |
| 성과 데이터 분석 | `@analyst` | `@analyst 최근 7일 성과 분석해줘` |
| 팔로워 답변 초안 | `@cs` | `@cs 이 질문에 답변 써줘: [질문]` |
| 스케줄 트리거 | `@scheduler` | `@scheduler 오늘 스케줄 확인해줘` |
| 프롬프트 개선 | `@optimizer` | `@optimizer 최근 성과 기반으로 프롬프트 개선해줘` |
| 산출물 감사 | `@supervisor` | `@supervisor 오늘 발행된 글 검증해줘` |

### 🎬 YouTube (콘텐츠 기획 보조)

| 할 일 | 호출할 에이전트 | 예시 명령 |
|---|---|---|
| 썸네일 문구 + 제목 | `@thumbnail` | `@thumbnail [주제]로 썸네일이랑 제목 만들어줘` |
| 참고 영상 분석 포함 | `@thumbnail` + 이미지 첨부 | `@thumbnail 이 영상 참고해서 [주제] 만들어줘` |
| 첫 30초 원고 생성 | `@script_30s` | `@script_30s [주제]로 첫 30초 원고 써줘` |
| 레퍼런스 원고 학습 | `@script_30s` + 원고 첨부 | `@script_30s 이 원고 학습하고 내 영상에 맞게 써줘` |

---

## 명령 예시 (복사해서 사용)

### Threads 글 1개 즉시 발행
```
@orchestrator 테스트 글 1개 지금 바로 발행해줘
```

### YouTube 썸네일 + 제목 요청
```
@youtube 이번 영상 주제는 [주제]야.
썸네일 문구 3가지랑 유튜브 제목 3가지 만들어줘.
```

### YouTube 참고 영상 포함 요청
```
@youtube 아래 이미지가 요즘 잘 되는 영상이야.
이 패턴 참고해서 [주제]로 썸네일이랑 제목 만들어줘.
[이미지 첨부]
```

---

## 폴더 구조

```
로직해커 엑스 자동화 프로젝트/
│
├── .claude/
│   ├── agents/               ← 모든 에이전트 정의
│   │   ├── [Threads: 9개]    orchestrator, writer, qa, knowledge,
│   │   │                     analyst, cs, scheduler, optimizer, supervisor
│   │   └── youtube.md        ← YouTube 전용
│   └── rules/                ← 자동 로드 규칙 (건드리지 말 것)
│       ├── knowledge/
│       ├── qa/
│       └── writer/
│
├── skills/
│   ├── threads/              ← Threads 에이전트 전용 지식
│   │   ├── knowledge.md
│   │   └── knowledge/
│   │       ├── free.md
│   │       ├── publishable_hints.md
│   │       ├── index.md
│   │       └── paid/
│   └── youtube/              ← YouTube 에이전트 전용 지식
│       └── patterns.md
│
├── agent/                    ← 에이전트 협업 프로토콜
├── n8n/                      ← n8n 워크플로
├── scripts/                  ← 실행 스크립트
├── supabase/                 ← DB 스키마
└── docs/                     ← 운영 문서
```

---

## 간섭 방지 원칙

- **Threads 에이전트**는 `skills/threads/` 폴더만 읽음
- **YouTube 에이전트**는 `skills/youtube/` 폴더만 읽음
- 플랫폼 간 지식 파일 공유 없음
- `@youtube` 호출 시 Threads 에이전트 자동 호출 없음
- `@orchestrator` 호출 시 YouTube 에이전트 자동 호출 없음
