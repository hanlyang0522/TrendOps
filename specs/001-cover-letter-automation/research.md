# Research: 자소서 작성 자동화 서비스

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-09
**Status**: Complete — 모든 NEEDS CLARIFICATION 해소됨

---

## 결정 1: 문서 파싱 라이브러리

**Decision**: PyMuPDF(`fitz`) for PDF, `python-docx` for DOCX, 내장 `open()` for TXT

**Rationale**:
- PyMuPDF는 렌더링 없이 텍스트 레이어를 직접 추출하여 속도가 빠르고, 한글 문자 처리가 안정적이다
- `pypdf`(구 PyPDF2)는 한글 인코딩 처리에서 간헐적 오류가 보고되어 제외
- `python-docx`는 `.docx` 표준 라이브러리로 사실상 유일한 선택지
- 이미지만 있는 스캔본 PDF는 MVP 범위 외로 OCR 라이브러리(pytesseract)는 도입하지 않음

**Alternatives considered**:
- `pypdf`: 경량이지만 한글 CID 폰트 디코딩 불안정
- `pdfplumber`: PyMuPDF 기반이나 테이블 추출 특화, 오버스펙
- `tesseract + pytesseract`: 스캔 PDF 지원하지만 MVP 범위 외

---

## 결정 2: LLM 프로바이더 및 호출 패턴

**Decision**: OpenAI GPT-4o, `openai` Python SDK, 환경 변수(`OPENAI_API_KEY`)로 관리

**Rationale**:
- 기존 TrendOps 헌법에 `API 기반 (OpenAI 등)` 명시, OpenAI 호환 API는 환경 변수 교체만으로 다른 프로바이더(Anthropic, Google 등) 전환 가능
- 자소서 한국어 생성, 문체 모방, AI 표현 감지 등 모든 작업에 GPT-4o가 충분한 성능 제공
- LLM 호출은 `cover_letter/llm_client.py` 단일 모듈에 집중, 프롬프트 템플릿은 `cover_letter/prompts/` 폴더에 분리하여 모델 교체 용이

**프롬프트 구조 원칙**:
- System prompt: 역할 정의 + 문체 프로필 + 제약 조건(글자 수, 언어)
- User prompt: 기업 분석 + 직무 분석 + 문항 + 선택된 경험 매핑
- 자가진단 호출: 별도 prompt 파일, 기존 답변 텍스트를 입력으로 사용

**Alternatives considered**:
- Anthropic Claude: 장문 생성 품질 우수하나 OpenAI SDK 호환 불완전, 추가 SDK 도입 필요
- 로컬 LLM(Ollama): 비용 절감 가능하나 한국어 자소서 품질이 GPT-4o 수준 미달 (MVP 이후 옵션)

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
