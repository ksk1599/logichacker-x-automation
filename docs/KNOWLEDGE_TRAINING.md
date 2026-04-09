# Knowledge 학습 가이드

> 무료/유료 전자책을 Knowledge Agent에게 학습시키는 절차.
> **유료 콘텐츠가 잠재 고객에게 새지 않도록** 파일을 물리적으로 분리한다.

---

## 학습 원칙 (3가지)

1. **물리적 분리** — 무료는 `free.md`, 유료는 `paid/` 폴더. 같은 파일에 절대 섞지 않는다.
2. **출처 명시** — Knowledge가 답할 때 어느 파일에서 가져왔는지 항상 표시.
3. **추측 금지** — PDF에 없는 내용은 빈칸으로 둔다. LLM이 "보충"하면 사실 오염.

---

## Step 1 — 무료 전자책 학습 (5분)

1. Claude Code 채팅창에 PDF 업로드
2. 명령:

```
무료 전자책 PDF야. 전체를 읽고 skills/knowledge/free.md 의 빈 곳을 채워줘.

규칙:
- 책에 있는 내용만. 추측이나 보강 절대 금지.
- 책에 없으면 빈칸으로 둬.
- 이미지 안의 텍스트도 OCR해서 포함.
- 인용 가능한 문장은 따옴표로 묶어줘.
- 강(章) 단위로 구조 잡되, 무료 전자책은 보통 1강만 있을 거야.
```

3. 결과 검토 → 사실 다른 부분 있으면 직접 수정
4. `skills/knowledge/index.md`의 무료 전자책 메타데이터(분량/학습일) 업데이트

---

## Step 2 — 유료 전자책 학습 (10~20분)

⚠️ **이게 더 중요하다.** 강별로 분리해야 권한 통제가 됨.

1. Claude Code 채팅창에 유료 전자책 PDF 업로드
2. 먼저 목차만 확인:

```
유료 전자책 PDF야. 먼저 목차만 보여줘. 강이 몇 개고 각 강 제목은 뭐야?
파일 분리할 거니까 강별로 식별자(영문 snake_case)도 같이 제안해줘.
```

3. 목차 확인 후 강별 분리 명령:

```
이제 강별로 skills/knowledge/paid/ch01_overview.md, ch02_xxx.md ... 식으로
파일을 만들어서 채워줘.

각 파일 frontmatter:
---
chapter: N
title: "강 제목"
overlap_with_free: false  # 1강은 true
publishable: false        # 항상 false. 노출은 publishable_hints.md에서 따로 관리.
---

규칙:
- 핵심 메시지 / 주요 개념 / 인용 가능 문장 / 사례 4섹션
- 책에 있는 내용만. 추측 절대 금지.
- 1강은 무료 전자책과 겹치니 overlap_with_free: true
- 이미지 텍스트도 포함
```

4. 강별 파일 검토 (특히 1강이 무료와 진짜 겹치는지)
5. `skills/knowledge/index.md` 강 목록 표 업데이트

---

## Step 3 — 노출 가능 힌트 등록 (5분)

유료 전자책 중 **Threads 공개 글에 써도 안전한 부분**을 골라서 등록.
이건 사용자 판단 영역. Knowledge가 마음대로 옮기면 안 됨.

명령 예시:
```
유료 ch03 의 "체급전략" 개념은 일부 노출해도 돼.
publishable_hints.md 에 힌트 #1로 등록해줘.
- 출처: paid/ch03_strategy.md
- 노출 수위: hint
- 구체적 방법론은 노출 금지
```

---

## Step 4 — 학습 검증 (필수)

세 가지 모드로 Knowledge 호출해서 답변이 다른지 확인:

### 4-1. 잠재 고객 모드 (free)
```
@knowledge tier=free 로 답변해줘:
"키워드 3개 중 어떤 게 우선이야?"
```

→ `free.md` 내용으로만 답해야 함. 만약 유료에만 있는 내용이면 "답변 불가"라고 해야 정상.

### 4-2. 유료 고객 모드 (paid)
```
@knowledge tier=paid 로 답변해줘:
같은 질문.
```

→ 유료 내용 포함해서 더 풍부한 답변. 출처에 "(paid ch3)" 명시.

### 4-3. Writer 모드 (publishable)
```
@knowledge tier=publishable 로 답변해줘:
"체급전략 글 쓰려는데 쓸 수 있는 내용 알려줘"
```

→ `free.md` + `publishable_hints.md` 만 보고 답해야 함. ch3 본문 직접 인용 금지.

세 답변이 명확히 달라야 분리가 잘 된 것.
**같으면 ⚠️ 권한 누수.** Knowledge 프롬프트나 파일 분리를 다시 검토.

---

## Step 5 — Supervisor 회귀 테스트 (자동)

학습 끝나면 Supervisor에게 감사 요청:

```
@supervisor knowledge 학습 결과 감사해줘.
- free 모드에서 paid 내용 누출 없는지
- publishable 모드에서 paid/ 폴더 접근 시도 없는지
- 출처 명시 일관적인지
```

→ Supervisor가 `supervisor_audits` 테이블에 결과 기록.

---

## 흔한 실수

| 실수 | 결과 | 방지 |
|---|---|---|
| 무료/유료를 한 파일에 섞음 | LLM이 tier 구분 못함 | 파일 분리 강제 |
| "보충해서 채워줘" 명령 | LLM이 책에 없는 내용 만듦 | "추측 금지" 명시 |
| publishable_hints에 자동 옮김 허용 | 무단 노출 | 사용자만 등록 |
| tier 명시 없이 호출 | 기본값 free → 답변 부족 | CS가 먼저 사용자에 확인 |
| 같은 강 두 파일에 분할 | 검색 시 중복/누락 | 강당 한 파일 원칙 |

---

## 향후 자동화

지금은 너가 캡처 보여주고 "이분 잠재고객이야"라고 말해. 나중에 자동화하려면:

1. Supabase에 `customers` 테이블 추가 (`threads_user_id`, `tier`, `purchased_at`)
2. CS Agent가 메시지 받을 때 발신자 ID로 자동 조회
3. 자동으로 `tier=free` 또는 `tier=paid` 결정

근데 이건 **신뢰성 검증 후에** 옮겨. 처음엔 수동으로 1~2주 돌려보고 누수 없는 거 확인.
