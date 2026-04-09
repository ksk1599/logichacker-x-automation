# 유료 전자책 (paid/)

> ⚠️ **이 폴더는 유료 고객 전용이다.**
> Knowledge Agent는 `tier=paid` 모드일 때만 이 폴더를 읽는다.
> Writer는 절대 이 폴더를 읽지 않는다 (`publishable_hints.md`만 본다).

---

## 강별 파일 규칙

- 파일명: `ch{번호}_{영문_식별자}.md` (예: `ch01_overview.md`)
- 한 강 = 한 파일
- 강 안에서 무료와 겹치는 부분은 frontmatter에 `overlap_with_free: true` 표시

## 학습 절차

사용자 명령 예시:
```
유료 전자책 PDF 올릴게. 강별로 나눠서 skills/knowledge/paid/ch{N}_*.md 파일에 채워줘.
강 제목, 핵심 메시지, 주요 개념, 인용 가능 문장 순서로 정리.
1강은 무료 전자책과 겹치니 frontmatter에 overlap_with_free: true 표시.
이미지 안 텍스트도 포함. 책에 없는 건 추측하지 말고 빈칸.
```

## 강별 파일 템플릿

```markdown
---
chapter: 3
title: "강 제목"
overlap_with_free: false
publishable: false   # Threads 글에 노출 가능?
---

# 3강 — (제목)

## 핵심 메시지
- ___

## 주요 개념
### 개념 A
- ___

### 개념 B
- ___

## 인용 가능한 문장
- "___"

## 사례
- ___
```
