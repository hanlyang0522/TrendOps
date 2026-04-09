# Research: 자소서 작성 자동화 서비스

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-09
**Status**: Complete — 모든 NEEDS CLARIFICATION 해소됨 (결정 8개)

---

## 결정 1: 사용자 정보 입력 방식

**Decision**: Streamlit 텍스트 영역 직접 붙여넣기 + TXT 파일 업로드(`st.file_uploader`). UTF-8 decode 후 내장 `str` 처리.

**Rationale**:
- PDF·DOCX 파싱은 MVP 범위 외로 제외 (Clarify Session 2026-04-09 Q1)
- TXT 파일은 `st.file_uploader(type=['txt'])` + `file.read().decode('utf-8')` 로 처리하며 외부 라이브러리 불필요
- 텍스트 직접 붙여넣기는 `st.text_area()` 위젯 하나로 구현 가능, 복잡성 최소화
- 두 입력 방식은 OR 조건으로 처리: 둘 중 하나만 채워도 진행 가능

**Alternatives considered**:
- PyMuPDF + python-docx: PDF·DOCX 지원이지만 MVP 단계에서 복잡도 대비 사용자 이득 낮음
- Google Docs 연동: 외부 OAuth 필요, MVP 범위 외

---

## 결정 2: LLM 프로바이더 및 티어 전략

**Decision**: Google Gemini 단일 프로바이더, `google-genai` SDK, 작업 복잡도에 따라 3단계 티어:
- **Tier 1 (Flash)**: `gemini-2.0-flash` — 수집/요약/매핑 등 반복 저비용 작업
- **Tier 2 (Pro)**: `gemini-2.5-pro` — 자소서 초안/전략 도출 등 중비용 작업
- **Tier 3 (Pro Thinking)**: `gemini-2.5-pro` + thinking mode — 쳙 문장 다듬기/자가진단 결합 등 고품질 작업

**Rationale**:
- 단일 프로바이더로 API Key 1개, 오류 처리 단일화, 운영 선단 단순화
- Gemini Flash 저비용 + Gemini Pro 고품질로 비용 절감과 품질 목표 동시 달성
- `cover_letter/llm_client.py`에 티어 라우팅 집중, 호출측에서는 `tier='flash'|'pro'|'pro-thinking'` 매개변수만 전달
- 구글 AI Studio 무료 플랜 + 수량제로 MVP 개발 비용 최소화 가능

**연동 환경 변수**: `GEMINI_API_KEY` (required), `GEMINI_FLASH_MODEL` (default: `gemini-2.0-flash`), `GEMINI_PRO_MODEL` (default: `gemini-2.5-pro`)

**프롬프트 구조 원칙**:
- System prompt: 역할 정의 + 문체 프로필 + 제약 조건(글자 수, 언어)
- User prompt: 기업 분석 + 직무 분석 + 문항 + 선택된 경험 매핑
- 자가진단 호출: 별도 prompt 파일, 기존 답변 텍스트를 입력으로 사용

**Alternatives considered**:
- 3프로바이더 (Google+OpenAI+Anthropic): API Key 3개, 오류 모드 3개, MVP 복잡도 과잉
- OpenAI GPT-4o 단일: 티어 분리 불가, 과금 리스크
- 로컬 LLM: 한국어 자소서 품질 미달

---

## 결정 3: Streamlit 다단계 UI 패턴

**Decision**: `st.session_state` 기반 단일 앱 파일 + 단계 번호 상태 관리

**Rationale**:
- Streamlit multi-page app(`pages/` 폴더)은 session_state 공유에 제약이 있어 다단계 워크플로에 부적합
- `st.session_state["step"]` 정수값으로 현재 단계 추적, 각 단계는 조건 분기(`if step == N`)로 렌더링
- 이전 단계 복귀 시 session_state 임시 저장 보장 (spec FR-007, Edge Case 요건 충족)
- 단계별 완료 데이터는 session_state dict에 누적, 최종 저장 시에만 DB write

**단계 구성** (5 steps):
```
step 0: 사용자 프로필 등록 (파일 업로드 → 추출 → 검토/수정 → 확인)
step 1: 기업·직무 분석 (입력 → 검색/캐시 → 검토/수정 → 확인)
step 2: 문항 분석 (문항 입력 → LLM 분석 → 검토/수정 → 확인)
step 3: 매핑 테이블 (자동 생성 → 검토/수정/중복 경고 → 확인)
step 4: 답변 생성 (초안 생성 → 자가진단 → 사용자 수정 루프 → 글자 수 검증 → 저장)
```

**Alternatives considered**:
- `streamlit-extras` step indicator: 제3자 라이브러리 의존성 추가, YAGNI
- FastAPI + React 프론트엔드: 스펙 Assumption에서 Streamlit MVP로 명시

---

## 결정 4: 글자 수 제어 전략

**Decision**: 생성 후 Python에서 글자 수 측정 → 범위 이탈 시 System prompt에 목표 글자 수 명시하여 LLM 재호출 (최대 3회)

**Rationale**:
- LLM에 토큰 수 제어를 맡기는 것(max_tokens)은 바이트/문자 수와 상이하여 한국어에서 부정확
- Python `len(text)` 로 공백 포함 글자 수 측정 → `char_limit * 0.90` ~ `char_limit * 0.95` 범위 검사
- 재호출 시 System prompt에 `"현재 {actual}자 / 목표 {target_min}~{target_max}자. 분량을 조정하여 재작성하라"` 를 추가
- 3회 이후 범위 이탈 시 Streamlit warning 메시지 + 현재 답변 표시 (spec FR-009a 충족)

**재시도 루프 의사코드**:
```python
for attempt in range(MAX_RETRIES):  # MAX_RETRIES = 3
    draft = generate_answer(prompt_with_char_hint)
    count = len(draft)
    if target_min <= count <= target_max:
        break
    prompt_with_char_hint = update_char_hint(prompt, count, target_min, target_max)
else:
    # 3회 초과 → 사용자에게 알림, 마지막 draft 반환
```

**Alternatives considered**:
- `max_tokens` 파라미터로 제어: 한국어 토큰-문자 비율 불일치 (1토큰 ≈ 0.5~1.5자)
- 후처리 절사(truncation): 문장 중간 절단으로 품질 저하

---

## 결정 5: AI 자가진단 방법론

**Decision**: 별도 LLM 호출, 진단 전용 시스템 프롬프트 사용, 구조화된 JSON 출력

**Rationale**:
- 규칙 기반 탐지(정규식)로는 "AI처럼 보이는 표현"의 맥락적 판단 불가
- LLM에게 진단 역할 부여가 가장 실용적: 기 생성 답변을 입력으로, 문제 항목을 JSON으로 출력
- 출력 형식: `[{"issue": "AI특유표현", "text": "...", "suggestion": "..."}]`
- spec FR-011 범위(AI 표현·어색한 흐름)에 집중, 문체 일치는 포함하지 않음

**진단 프롬프트 핵심 지시사항**:
```
당신은 한국어 자소서 품질 검토자입니다.
다음 자소서 문단에서 아래 유형의 문제를 찾아 JSON으로 반환하세요:
1. AI가 생성한 것 같은 상투적 표현 ("~에 기여하고자", "열정을 갖고" 등)
2. 문맥이 단절되거나 전개가 어색한 부분
3. 논리 흐름이 자연스럽지 않은 문장 연결
문제가 없으면 빈 배열 []을 반환합니다.
```

**Alternatives considered**:
- GPT-4 function calling으로 구조화 출력: `response_format={"type":"json_object"}`를 사용해 동일 구현 가능, 채택
- 외부 AI 탐지 API(GPTZero 등): spec FR-012에서 Future로 예약, MVP 범위 외

---

## 결정 6: 경험-문항 매핑 적합도 계산

**Decision**: LLM 기반 적합도 평가, JSONB 형식으로 점수·근거 저장

**Rationale**:
- 임베딩 기반(sentence-transformers 등)은 추가 라이브러리 + 모델 다운로드 필요 (MVP 과도)
- LLM에게 `(문항 분석 결과, 경험 설명)` 쌍을 제공하고 `{"score": 1-5, "rationale": "...", "usage_type": "주경험|보조|배경언급"}` 반환
- score 3+ 경험만 테이블에 표시, score 순 정렬
- 중복 활용 방식 경고 로직: 동일 경험의 `usage_type`이 두 문항에서 동일하면 경고 (spec FR-006a 충족)

**Alternatives considered**:
- sentence-transformers cosine similarity: 의미적 유사도만, "어떻게 활용할지" 판단 불가
- BM25 키워드 매칭: 표면적 단어 매칭, 자소서 맥락 이해 부족

---

## 결정 7: 기업 분석 캐싱 전략

**Decision**: PostgreSQL `company_analysis` 테이블에 전체 분석 결과 JSONB 저장, `analyzed_at` 기준 7일 유효

**Rationale**:
- 기업 기본 정보(사업, 인재상)는 변동이 적어 7일 캐시 합리적
- 뉴스 요약은 별도 필드로 분리, 캐시 히트 시에도 최신 뉴스만 재검색하여 보완 (spec FR-004 + US2 시나리오 2 충족)
- `(company_name, updated_at)` 조합으로 캐시 유효성 판단
- 사용자가 분석 결과 수정 시 `user_overrides JSONB` 필드에 오버라이드 저장

**Alternatives considered**:
- Redis 캐시: 단일 사용자 로컬 환경에서 PostgreSQL만으로 충분, 추가 컨테이너 불필요
- 파일 캐시(JSON 파일): DB 트랜잭션 보장 없음, 추후 멀티유저 확장 고려 시 부적합

---

## 결정 8: 기업 정보 3-소스 수집 전략

**Decision**: 기업 분석 정보를 3개 소스에서 병렬 수집하여 통합:
1. **DART API** (`dart-fss` 라이브러리 또는 금감원 OpenAPI 직접 호출) — 최근 3개년 사업보고서에서 주요 제품·서비스, 지식재산권, 시장현황, 주요계약·연구개발 섹션 추출
2. **Naver News API** (기존 TrendOps `crawling/` 모듈 재사용) — 직무·기업 관련 최신 뉴스 수집. 결과 불충분 시 Firecrawl API로 fallback
3. **공식 홈페이지 스크래핑** (`requests` + `BeautifulSoup4`, 기존 TrendOps 스택) — 인재상, 비전·미션 페이지 수집

**수집 오케스트레이션**: `company_service.py`의 `get_or_analyze_company()`가 3개 수집기를 순차 호출 후 결과를 통합하여 Gemini Flash로 단일 요약 생성

**Rationale**:
- DART 사업보고서: 지원 직무 관련 사업 배경·시장 맥락을 객관적 공시 데이터로 확보 → 자소서 신뢰도 향상
- Naver News: 기존 TrendOps 크롤링 모듈 재사용으로 추가 개발 비용 최소화
- 공식 홈페이지: 인사담당자가 실제 홈페이지에서 확인하는 인재상·비전을 직접 수집
- 각 소스 독립 실패 허용 (graceful degradation): DART API Key 미설정이나 홈페이지 스크래핑 실패 시 해당 소스만 스킵하고 나머지로 계속 진행

**수집기 파일 구조**:
```
cover_letter/collectors/
├── dart_collector.py     # DART API 사업보고서 수집
├── naver_collector.py    # Naver News API + Firecrawl fallback
└── website_crawler.py   # 공식 홈페이지 인재상·비전 스크래핑
```

**환경 변수 추가**: `DART_API_KEY` (optional — 미설정 시 DART 소스 스킵), `FIRECRAWL_API_KEY` (optional — Naver fallback용)

**Alternatives considered**:
- DART만 단독 사용: 뉴스 최신성·홈페이지 인재상 누락으로 자소서 맥락 부족
- 단일 웹 검색 API(Google Custom Search 등): 결과 범위 불확실, 공시 데이터 누락
- LangChain Agent 자율 수집: MVP 복잡도 과잉, 수집 결과 재현성 낮음
