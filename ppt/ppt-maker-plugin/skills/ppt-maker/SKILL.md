---
name: ppt-maker
description: 순수 HTML, CSS, JavaScript로 웹 프레젠테이션(슬라이드)을 생성합니다. 외부 라이브러리 없이 단일 HTML 파일로 완성되며, GPU 가속 슬라이드 전환, 키보드/터치 네비게이션, 진행 표시바, 반응형 디자인을 포함합니다. 사용자가 프레젠테이션, 슬라이드, 발표자료, PPT 등을 만들어달라고 요청할 때 사용하세요. 'PPT 만들어줘', '슬라이드 생성', '발표자료 만들어줘', 'create a presentation', 'make slides about' 등의 요청에 반응합니다.
---

# PPT Maker

순수 HTML/CSS/JS 단일 파일 웹 프레젠테이션 생성기.

## 워크플로우

1. `references/template.html`을 읽어 전체 구조(CSS/JS)를 파악한다
2. 사용자의 주제, 내용, 슬라이드 수 요구사항을 정리한다
3. 슬라이드 구성을 설계한다 (어떤 타입의 슬라이드를 어떤 순서로)
4. 템플릿의 CSS와 JS를 그대로 유지하면서 슬라이드 HTML 콘텐츠만 교체한다
5. 단일 .html 파일로 출력한다
6. `open` 명령으로 브라우저에서 열어 확인한다

## 핵심 원칙

- **단일 파일**: 모든 CSS, JS가 HTML 안에 인라인
- **외부 의존성 제로**: Google Fonts만 예외 (CDN 링크)
- **GPU 가속**: 전환 애니메이션은 `transform`과 `opacity`만 사용
- **뷰포트 피팅**: 모든 슬라이드가 스크롤 없이 화면에 딱 맞아야 함
- **접근성**: ARIA 속성, prefers-reduced-motion 대응

## 디자인 시스템

### CSS Custom Properties

```css
:root {
  --bg: #0a0a0f;
  --bg-subtle: #111118;
  --accent: #C6A55C;
  --accent-dim: rgba(198, 165, 92, 0.15);
  --accent-glow: rgba(198, 165, 92, 0.3);
  --text-primary: #F0EBE0;
  --text-secondary: #B8B0A0;
  --text-dim: #706858;
  --border: #1e1c18;
  --font-kr: 'Noto Sans KR', sans-serif;
  --font-en: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

사용자가 다른 컬러 테마를 원하면 이 변수들만 교체한다.

### 타이포그래피

| 요소 | 크기 | 비고 |
|------|------|------|
| h1 | `clamp(2rem, 5vw, 4rem)` | 타이틀 슬라이드 |
| h2 | `clamp(1.4rem, 3vw, 2.4rem)` | 섹션 제목 |
| h3 | `clamp(1.1rem, 2vw, 1.6rem)` | 서브 제목 |
| p, li | `clamp(0.85rem, 1.5vw, 1.2rem)` | 본문 |
| code | `clamp(0.65rem, 1.1vw, 0.9rem)` | 코드 블록 |

### 컴포넌트 카탈로그

- **info-card**: 정보 카드 (`background: rgba(255,255,255,0.02)`, `border: 1px solid var(--border)`)
- **split**: 2열 그리드 (`grid-template-columns: 1fr 1fr`)
- **split-card**: split 내부 카드
- **badge**: 태그/라벨 (`border-radius: 100px`, accent 컬러)
- **terminal-badge**: 모노스페이스 라벨 + 깜빡이는 커서 (`> `)
- **accent-line**: 강조선 (`width: 50px; height: 2px; background: var(--accent)`)
- **code-block**: 줄 번호 + 하이라이트 지원 코드 블록

## 슬라이드 타입 카탈로그

### 1. 타이틀 슬라이드 (slide--intro)

```html
<section class="slide slide--intro active" id="slide-1"
  role="region" aria-roledescription="슬라이드" aria-label="슬라이드 1" aria-hidden="false">
  <div class="slide__inner">
    <div class="slide__header">
      <div class="terminal-badge reveal">카테고리</div>
      <h1 class="reveal">메인 타이틀</h1>
    </div>
    <div class="slide__body">
      <p class="reveal" style="font-size: clamp(0.95rem, 1.8vw, 1.3rem);">서브 타이틀</p>
      <div class="accent-line reveal"></div>
      <p class="reveal" style="font-size: clamp(0.7rem, 1vw, 0.85rem); color: var(--text-dim);">
        ← → 키 또는 스와이프로 이동
      </p>
    </div>
    <div class="slide__footer">날짜</div>
  </div>
</section>
```

### 2. 리스트 콘텐츠 (slide--content / slide--content-alt)

```html
<section class="slide slide--content" id="slide-N"
  role="region" aria-roledescription="슬라이드" aria-label="슬라이드 N" aria-hidden="true">
  <div class="slide__inner">
    <div class="slide__header">
      <div class="terminal-badge reveal">영문 키워드</div>
      <h2 class="reveal">섹션 제목</h2>
    </div>
    <div class="slide__body">
      <ul>
        <li class="reveal">항목 1</li>
        <li class="reveal">항목 2</li>
        <li class="reveal">항목 3</li>
      </ul>
    </div>
  </div>
</section>
```

`slide--content`와 `slide--content-alt`를 번갈아 사용하면 배경 그라데이션 방향이 달라져 시각적 변화를 준다.

### 3. 코드 슬라이드 (slide--code)

```html
<section class="slide slide--code" id="slide-N"
  role="region" aria-roledescription="슬라이드" aria-label="슬라이드 N" aria-hidden="true">
  <div class="slide__inner">
    <div class="slide__header">
      <h2 class="reveal" style="color: var(--accent);">코드 제목</h2>
    </div>
    <div class="slide__body">
      <pre class="code-block reveal" data-language="javascript" data-highlight-lines="2,4-6"><code><span class="line"><span class="kw">const</span> <span class="var">x</span> = <span class="str">42</span>;</span>
<span class="line"><span class="cmt">// 강조될 줄</span></span></code></pre>
    </div>
  </div>
</section>
```

**신택스 클래스**: `kw`(키워드), `fn`(함수), `str`(문자열/숫자), `cmt`(주석), `var`(변수), `op`(연산자), `tag`(태그), `attr`(속성), `val`(값)

`data-highlight-lines`에 강조할 줄 번호를 지정한다 (예: "2,4-6").

### 4. 분할 레이아웃 (slide--diagram)

```html
<section class="slide slide--diagram" id="slide-N"
  role="region" aria-roledescription="슬라이드" aria-label="슬라이드 N" aria-hidden="true">
  <div class="slide__inner">
    <div class="slide__header">
      <div class="terminal-badge reveal">키워드</div>
      <h2 class="reveal">제목</h2>
    </div>
    <div class="slide__body">
      <div class="split">
        <div class="split-card reveal">
          <p><strong style="color: var(--accent);">왼쪽 제목</strong><br>설명</p>
        </div>
        <div class="split-card reveal">
          <p><strong style="color: #D4B87A;">오른쪽 제목</strong><br>설명</p>
        </div>
      </div>
    </div>
  </div>
</section>
```

### 5. 정보 카드 슬라이드

```html
<div class="slide__body">
  <div class="info-card reveal">
    <div class="card-title">// 카드 라벨</div>
    <p>카드 내용</p>
  </div>
  <div class="info-card reveal">
    <div class="card-title">// 카드 라벨 2</div>
    <p>카드 내용 2</p>
  </div>
</div>
```

### 6. 마무리 슬라이드 (slide--end)

```html
<section class="slide slide--end" id="slide-N"
  role="region" aria-roledescription="슬라이드" aria-label="슬라이드 N" aria-hidden="true">
  <div class="slide__inner" style="text-align: center; align-items: center;">
    <div class="slide__body" style="align-items: center;">
      <h1 class="reveal">감사합니다</h1>
      <div class="accent-line reveal" style="margin: 0.8rem auto;"></div>
      <p class="reveal">마무리 메시지</p>
      <div class="reveal" style="display: flex; gap: 0.5rem; margin-top: 1rem;">
        <span class="badge">태그1</span>
        <span class="badge">태그2</span>
      </div>
    </div>
  </div>
</section>
```

## 콘텐츠 작성 규칙

### reveal 순차 등장

- 모든 콘텐츠 요소에 `class="reveal"` 추가
- CSS `transition-delay`로 nth-child 기반 순차 등장이 자동 적용됨
- 최대 8단계까지 지원 (0.08s 간격)

### 슬라이드 구조 필수 규칙

- 첫 번째 슬라이드만 `class="slide ... active"`, `aria-hidden="false"`
- 나머지는 `aria-hidden="true"`, active 클래스 없음
- 모든 슬라이드에 고유 `id="slide-N"` (1부터 시작)
- `role="region"`, `aria-roledescription="슬라이드"`, `aria-label="슬라이드 N"` 필수

### 슬라이드 수 가이드

- 사용자가 지정하면 그대로 따름
- 지정하지 않으면 주제에 맞게 7~12장 구성
- 기본 구성: 타이틀(1) + 개요(1) + 본론(3~8) + 마무리(1)

### 콘텐츠 밀도

- 리스트: 슬라이드당 최대 5개 항목
- 텍스트: 한 단락 2~3줄 이내
- 코드: 최대 10줄
- **뷰포트에 딱 맞아야 함 — 스크롤이 발생하면 안 된다**

## 기술 요구사항

### 네비게이션

- **키보드**: ← → / ↑ ↓ / Space / PageUp·Down / Home·End / F(전체화면)
- **터치**: 스와이프 (threshold 50px, `passive:false`로 `preventDefault`)
- **버튼**: 좌하단 이전/다음 버튼
- **URL hash**: `#slide-N` 동기화 + 뒤로가기 지원

### 전환 애니메이션

- `transform: translateX(±100%)` + `opacity` (GPU 가속, Composite 전용)
- duration: 400~450ms
- `isAnimating` 잠금 + `transitionend` + `setTimeout(duration+150)` fallback
- `will-change`는 전환 직전 설정, 완료 후 `auto`로 해제

### UI 요소

- **진행 표시바**: 상단 2px, accent 컬러
- **슬라이드 카운터**: 우하단 `01 / 10` 형식 (2자리 zero-pad)
- **네비게이션 버튼**: 좌하단 ‹ › 버튼

### 접근성

- `prefers-reduced-motion: reduce`에서 transition-duration 최소화
- 모바일 터치 타겟 최소 44px (`@media (hover: none)`)
- `100dvh` 사용 (모바일 주소창 동적 대응)

## 주의사항

- `display:none` 사용 금지 — transition 불가
- 초기 위치: `transition:none` → 위치 설정 → `void el.offsetWidth` → `transition` 복원
- Space 키는 반드시 `preventDefault()` (페이지 스크롤 방지)
- `will-change`를 모든 슬라이드에 정적 적용하면 GPU 메모리 낭비
- 애니메이션 duration 500ms 초과 금지 (사용자 지루함 유발)
- `e.repeat` 체크로 키 반복 이벤트 차단

## 슬라이드 카운터 업데이트

JS에서 슬라이드 총 개수를 반드시 실제 슬라이드 수와 일치시킨다. `slideCounter` 초기 텍스트도 `01 / {총 슬라이드 수}`로 설정한다.

## 참고 템플릿

`references/template.html`에 10장짜리 완전한 동작 예시가 있다.
이 파일의 **CSS와 JS를 기반으로** 슬라이드 HTML 콘텐츠만 교체하여 새 프레젠테이션을 만든다.
