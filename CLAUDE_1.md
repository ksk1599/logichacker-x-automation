# 로직해커 엑스 멀티에이전트 시스템

## 프로젝트 개요
스마트스토어 상위노출 전문가 '로직해커 엑스'(secretmovev) 계정의
Threads 콘텐츠 자동 생성, 성과 분석, 자기개선 루프 시스템

## 인프라
- n8n: https://n8n-production-9b1b.up.railway.app
- Supabase: 모든 데이터 저장 (토큰, 성과, 프롬프트 버전)
- Threads API: secretmovev 계정
- Discord: 글 검수용 웹훅
- 모델: claude-sonnet-4-5 / claude-haiku-4-5

## 에이전트 팀 구성

### 1. Orchestrator (팀장) - Sonnet
- 역할: 전체 지휘, 작업 분배, 최종 판단
- 규칙: 에이전트간 직접 소통 허용. 사용자 개입 최소화
- 3일마다 Prompt Optimizer 루프 실행

### 2. Knowledge Agent - Sonnet
- 역할: 로직해커 엑스의 두뇌. 전자책+글 학습
- 핵심 지식:
  - 상위노출 = 적합도 × 인기도 × 신뢰도
  - 배열고정 키워드: 순서 고정 (삼양라면)
  - 붙박이 키워드: 반드시 붙여쓰기
  - 조립형 키워드: 자유 배치 (꽃게라면)
  - 체급전략: 검색량 낮은 키워드로 1위 먼저
  - 인기도: 최근 30일만 반영, 7일 가중치 높음
  - 네이버/인스타 외부유입 인기도 0점
  - 키워드 많으면 점수 분산 → 집중이 답
- 다른 에이전트 질문에 즉시 답변

### 3. Writer Agent - Sonnet
- 역할: Threads 글 생성
- Knowledge Agent 참고 필수
- 글쓰기 규칙:
  - 딱 4줄. 한 줄 최대 15자
  - 1줄: 내가 한 행동 (숫자 포함)
  - 2줄: 결과 (숫자 포함)
  - 3줄: 반전 또는 이유
  - 4줄: 핵심 한 줄
  - 제목 금지. 번호 목록 금지. 👇 금지
- QA 불합격시 즉시 재작성

### 4. Analyst Agent - Haiku
- 역할: 성과 데이터 수집 및 분석
- Threads insights API로 좋아요/조회수/댓글/리포스트 수집
- 구글 시트 + Supabase 저장
- 3일마다 Prompt Optimizer에 데이터 전달
- 잘 된 글 기준: 조회수 상위 20%

### 5. QA Agent - Sonnet
- 역할: Writer 글 검수
- 체크리스트:
  - 4줄 이내인가?
  - 숫자 2개 대비 있는가?
  - 인과관계가 맞는가?
  - 제목/목록/홍보 없는가?
- 불합격시 구체적 피드백과 함께 Writer에 재요청
- 합격시 Discord → Threads 발송

### 6. CS Agent - Haiku
- 역할: 팔로워 질문 답변 초안
- Knowledge Agent 참고해서 순관 씨 말투로 작성
- 말투: 친근하고 짧게. 전문가지만 어렵지 않게

### 7. Scheduler Agent - Haiku
- 역할: 스케줄 관리
- 매일 08:00, 18:00 Writer 루프 실행
- 3일마다 Prompt Optimizer 루프 실행
- 58일마다 토큰 갱신 알림 Discord 발송

### 8. Prompt Optimizer - Sonnet
- 역할: 프롬프트 자동 개선
- 3일마다 실행
- Analyst 데이터 받아서 잘 된 글 패턴 추출
- Writer 프롬프트 개선안 생성
- 개선 전/후 Supabase에 버전 저장
- Orchestrator 승인 후 적용

## 협업 흐름

### 일반 루프 (매일 2회)
```
Scheduler → Orchestrator → Writer
Writer → QA
QA 불합격 → Writer 재작성
QA 합격 → Discord → Threads 발송
```

### 자기개선 루프 (3일마다)
```
Scheduler → Analyst (성과 수집)
Analyst → Prompt Optimizer (데이터 전달)
Prompt Optimizer → 패턴 분석 → 프롬프트 개선안
Orchestrator → 승인 → Writer 프롬프트 업데이트
```

### 병렬 처리
- Analyst 데이터 수집 + Writer 글 생성 → 동시 실행
- 여러 글 생성시 Writer 인스턴스 병렬 실행

## 에이전트 협업 규칙
1. 에이전트간 직접 소통 가능. Orchestrator 경유 불필요
2. QA는 Writer에게 직접 재작성 요청
3. Analyst는 Prompt Optimizer에게 직접 데이터 전달
4. 사용자는 최종 결과만 확인. 중간 개입 불필요
5. 루프 실패시 Orchestrator가 Discord로 알림 발송

## Supabase 테이블
- threads_posts: 글 ID, 내용, 발송시간
- post_insights: 좋아요, 조회수, 댓글, 리포스트
- prompt_versions: 프롬프트 버전, 날짜, 성과 점수
- tokens: Threads 토큰, 갱신일

## 전자책 학습 방법
Claude Code 실행 후:
"전자책 PDF 올릴게요. 전체 내용을 읽고
Knowledge Agent용 지식베이스를 skills/knowledge.md에 정리해줘.
이미지 안의 내용도 포함해서."
