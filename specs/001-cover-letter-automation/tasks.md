# Tasks: 자소서 작성 자동화 서비스

**브랜치**: `001-cover-letter-automation` | **날짜**: 2026-04-10 (전체 재작성)
**입력 문서**: plan.md · spec.md · research.md · data-model.md · contracts/service-interfaces.md

---

## 형식: `[ID] [P?] [Story?] 설명 — 파일 경로`

- **[P]**: 병렬 실행 가능 (다른 파일, 미완료 태스크 의존 없음)
- **[US1~US4]**: 해당 유저 스토리 레이블 (Setup·Foundation·Polish 단계에는 미부착)
- 각 태스크는 정확한 파일 경로 포함

---

## Phase 1: 설정 (프로젝트 초기화)

**목적**: 환경 변수, DB 마이그레이션 파일, 컨테이너 설정

- [X] T001 [P] `.env.example`에 환경 변수 추가 — `GEMINI_API_KEY` (필수), `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `DART_API_KEY` **(필수)**, `FIRECRAWL_API_KEY` **(필수)**, `NAVER_CLIENT_ID` (필수), `NAVER_CLIENT_SECRET` (필수), `COMPANY_CACHE_DAYS=7`, `COVER_LETTER_MAX_RETRIES=3`
- [X] T002 [P] `pyproject.toml` 의존성 추가 — `firecrawl-py`, `pdfminer.six`, `python-docx` (required), `dart-fss` (required)
- [X] T003 [P] `db/migrations/001_cover_letter_schema.sql` 구현 확인 — 6개 엔티티 DDL (`user_profile`, `company_analysis`, `job_analysis`, `question`, `mapping_table`, `cover_letter_draft`) + `hallucination_retries INT DEFAULT 0` 필드 포함 여부 검증
- [X] T004 `db/migrations/002_add_jd_entity.sql` 생성 — `jd` 테이블 DDL (data-model.md 엔티티 7 기준: `id`, `job_analysis_id UNIQUE FK`, `raw_text`, `source_url`, `source_type VARCHAR(20)`, `required_competencies TEXT[]`, `collected_at`, `user_overrides JSONB`) + `idx_jd_job_analysis` 인덱스
- [X] T005 [P] `Dockerfile.cover-letter` 및 `docker-compose.yml` cover-letter 서비스 확인 — postgres `depends_on`, 포트 8501, `DART_API_KEY`·`FIRECRAWL_API_KEY`·`GEMINI_API_KEY` 환경변수 전달

---

## Phase 2: 기반 (모든 유저 스토리의 선행 조건)

**목적**: Python 데이터클래스, LLM 티어 클라이언트, API Key 기동 검증 — 이 단계 완료 전 US 작업 착수 불가

**⚠️ 블로킹**: 아래 태스크가 완료되어야 US1~US4 병렬 착수 가능

- [X] T006 `cover_letter/models.py` 생성 — `Experience`, `WritingStyle`, `MappingEntry`, `DiagnosisIssue`, `JD` Python dataclass 정의 (data-model.md 기준, `from dataclasses import dataclass, field`)
- [X] T007 `cover_letter/llm_client.py` 구현 — `Tier = Literal["flash","pro","pro-thinking"]`, `call(prompt, tier, system, temperature)` 구현 (google-genai SDK `genai.GenerativeModel`, 환경변수 기반 모델 선택, tier별 temperature 기본값: flash=0.3, pro=0.7, pro-thinking=1.0), `GEMINI_API_KEY` 미설정 시 `RuntimeError`
- [X] T008 [P] API Key 기동 검증 추가 — `cover_letter/__init__.py`에서 `DART_API_KEY`, `FIRECRAWL_API_KEY`, `GEMINI_API_KEY` 중 하나라도 미설정 시 `RuntimeError: "{KEY} 환경변수 필수"` 발생

**체크포인트**: `llm_client.call("테스트", tier='flash')` 호출 시 Gemini 응답 반환 확인 → US1~US4 병렬 착수 가능

---

## Phase 3: User Story 1 — 사용자 프로필 등록 (Priority: P1) 🎯 MVP

**목표**: TXT·MD·DOCX 업로드 또는 텍스트 붙여넣기로 사용자 경험·역량·문체 프로필을 추출하고 DB에 저장

**독립 테스트 기준**: TXT/MD/DOCX 파일 업로드 또는 텍스트 붙여넣기 → 프로필 요약(경험 목록, 핵심 역량, 문체 특성) 화면 표시 → 수정 → DB 저장 확인 (confirmed_at 갱신)

- [X] T009 [P] [US1] `cover_letter/prompts/profile_extract.txt` 작성 — System 프롬프트(역할 정의) + User 프롬프트(입력 텍스트 + JSON 출력 포맷: `{"experiences": [{"key","title","period","description","competencies":[]}], "competencies":[], "writing_style":{"sentence_length","tone","expression_patterns":[],"avoid_patterns":[]}}`)
- [X] T010 [P] [US1] `cover_letter/profile_service.py` - `parse_input(text: str | None, file_bytes: bytes | None, filename: str = "") -> str` 구현 — TXT/MD는 `file_bytes.decode('utf-8')`, DOCX는 `python-docx Document(io.BytesIO(file_bytes)).paragraphs` 단락 추출, text 직접입력 우선, 둘 다 None이면 `ValueError`
- [X] T011 [US1] `cover_letter/profile_service.py` - `extract_profile(texts: list[str]) -> dict` 구현 — `llm_client.call(tier='flash')` + `profile_extract.txt` 프롬프트 호출, 응답 JSON 파싱 후 `{"experiences": [...], "competencies": [...], "writing_style": {...}}` 반환
- [X] T012 [P] [US1] `cover_letter/profile_service.py` - `save_profile(profile: dict) -> None`, `load_profile() -> dict | None`, `merge_profile(existing: dict, new_texts: list[str]) -> dict` 구현 — psycopg2로 `user_profile` 테이블 id=1 upsert, `confirmed_at` 처리 (`save_profile` 시 `NOW()`, 병합 시 `NULL`)
- [X] T013 [US1] `frontend/cover_letter_app.py` Step 0 구현 — `st.file_uploader(type=['txt','md','docx'])` + `st.text_area()` 병용 OR 입력, 프로필 요약 `st.data_editor` 표시(경험·역량·문체 수정 가능), "저장" 버튼 클릭 시 `save_profile()` 호출 + `st.success()`
- [X] T014 [P] [US1] `tests/test_cover_letter_profile.py` 보완 — `parse_input` (TXT 정상, MD 정상, DOCX 정상, 빈 입력 ValueError, 미지원 확장자 ValueError), `save_profile`/`load_profile` (id=1 upsert), `merge_profile` 케이스 단위 테스트

---

## Phase 4: User Story 2 — 기업·직무 분석 및 JD 수집 및 문항 분석 (Priority: P2)

**목표**: 기업명·직무 입력 → DART·Naver·Firecrawl 3-소스 수집 + JD 자동 수집(Firecrawl→PDF폴백→수기) → DB 캐싱, 자소서 문항 역량 분석

**독립 테스트 기준**: 기업명 + 직무 입력 후 분석 요약(기업 특징, 인재상, DART 요약, JD 내용) 표시, 동일 기업 재조회 시 캐시 히트, 문항 입력 후 측정 역량 표시, JD 수집 실패 시 수기 입력 UI 표시

- [X] T015 [P] [US2] `cover_letter/prompts/company_analysis.txt` 작성 — DART 사업보고서(주요 제품·시장현황·연구개발) + Naver 뉴스 요약 + Firecrawl 인재상·비전 3-소스 통합 분석 프롬프트 (overview / culture_and_values / industry_trends / competitive_edge / dart_summary 섹션)
- [X] T016 [P] [US2] `cover_letter/prompts/question_analysis.txt` 작성 — 자소서 문항의 측정 역량(`measured_competencies: list[str]`) + 신입 기대 수준(`expected_level: str`) JSON 출력 분석 프롬프트
- [X] T017 [P] [US2] `cover_letter/collectors/dart_collector.py` 구현 — `collect_dart_reports(company_name: str, years: int = 3) -> dict` — `dart-fss`로 기업 코드 검색 후 최근 N개년 사업보고서 수집, 목표 섹션(주요제품·지식재산권·시장현황·연구개발) 텍스트 추출. `DART_API_KEY` 미설정 시 `{}` 반환 + 로그 경고
- [X] T018 [P] [US2] `cover_letter/collectors/naver_collector.py` 구현 — `collect_news(company_name: str, job_title: str) -> list[dict]` — Naver Search API로 `{company_name} {job_title}` 뉴스 수집, 결과 5건 미만 시 `firecrawl-py` `FirecrawlApp.search()` fallback (FIRECRAWL_API_KEY 환경변수 사용)
- [X] T019 [P] [US2] `cover_letter/collectors/website_crawler.py` 구현 — `crawl_company_website(company_name: str) -> dict | None` — `firecrawl-py` `FirecrawlApp.search("{company_name} 채용 인재상 기업문화 비전")` 으로 공식 홈페이지 인재상·기업문화·비전 수집 (FIRECRAWL_API_KEY 필수), 실패 시 `None` 반환 + 로그
- [X] T020 [P] [US2] `cover_letter/collectors/jd_crawler.py` 생성·구현 — `crawl_jd(company_name: str, job_title: str) -> dict` — `firecrawl-py` `FirecrawlApp.search("{company_name} {job_title} 채용공고 JD 직무기술서")` 호출, 응답이 PDF URL인 경우 `pdfminer.six` `extract_text(io.BytesIO(content))` 폴백, 수집·파싱 모두 실패 시 `{"success": False, "text": None, "source_type": "manual"}` 반환
- [X] T021 [US2] `cover_letter/jd_service.py` 생성·구현 — `collect_jd(company_name: str, job_title: str) -> dict`, `extract_required_competencies(jd_text: str) -> list[str]` (Gemini Flash), `save_jd(job_analysis_id: int, jd_data: dict) -> int` (`jd` 테이블 INSERT), `load_jd(job_analysis_id: int) -> dict | None` (`jd` 테이블 SELECT) 전체 구현
- [X] T022 [US2] `cover_letter/company_service.py` - `get_or_analyze_company(company_name: str) -> dict` 구현 — `company_analysis` 테이블 캐시 조회 (`NOW() - analyzed_at < 7일`), 미스 시 T017·T018·T019 수집기 순차 호출 + `company_analysis.txt` 프롬프트로 `llm_client.call(tier='flash')` 통합 요약, `company_analysis` 테이블 UPSERT
- [X] T023 [US2] `cover_letter/company_service.py` - `analyze_job(company_analysis_id: int, job_title: str) -> dict`, `save_overrides(entity, entity_id, overrides) -> None` 구현 — `job_analysis` 테이블 저장 후 `jd_service.collect_jd()` 호출하여 JD 수집·저장 연동
- [X] T024 [US2] `cover_letter/question_service.py` - `analyze_question(job_analysis_id: int, question_text: str, char_limit: int | None) -> dict` 구현 — `question_analysis.txt` 프롬프트로 `llm_client.call(tier='flash')` 호출, `question` 테이블 저장 (`target_char_min`·`target_char_max` Generated Column 자동 계산)
- [X] T025 [US2] `frontend/cover_letter_app.py` Step 1 구현 — 기업명·직무 입력 폼, "분석 시작" `st.spinner`, 분석 결과 `st.tabs(["기업 개요","인재상","DART","뉴스","JD"])`, 수동 수정 `st.text_area`, JD 수집 실패 시 수기 텍스트 입력 폼 표시, `save_overrides()` 연동
- [X] T026 [US2] `frontend/cover_letter_app.py` Step 2 구현 — 문항 텍스트 + 글자 수 입력, "문항 분석" 버튼, 측정 역량·기대 수준 `st.info()` 표시·수정 UI
- [X] T027 [P] [US2] `tests/test_cover_letter_company.py` 보완 — `dart_collector` (DART_API_KEY 없음 → `{}` mock), `website_crawler` (Firecrawl 실패 → `None`), `naver_collector` (5건 미만 → Firecrawl fallback mock), `get_or_analyze_company` (캐시 히트·미스), 소스 일부 실패 시 부분 결과 반환 케이스
- [X] T028 [P] [US2] `tests/test_cover_letter_jd.py` 생성 — `crawl_jd` (Firecrawl 성공, PDF fallback, 실패→manual), `extract_required_competencies` (LLM mock), `save_jd`/`load_jd` DB 왕복 단위 테스트

---

## Phase 5: User Story 3 — 경험-문항 매핑 테이블 생성 (Priority: P3)

**목표**: 문항 분석 + 사용자 프로필 기반 자동 매핑 생성, JD 요구 역량 우선순위 반영, 중복 배정 경고

**독립 테스트 기준**: 매핑 테이블 생성·표시 → 동일 경험 same usage_type 중복 시 경고 → 경험 선택·수정 → 저장

- [X] T029 [P] [US3] `cover_letter/prompts/mapping_generate.txt` 작성 — 문항 측정 역량 vs 사용자 경험 적합도 평가 + `usage_type`(primary/supporting/background) 분류 + JD 요구 역량 우선순위 반영 지시 포함, JSON 배열 출력 포맷: `[{"experience_key","usage_type","relevance_score","rationale"}]`
- [X] T030 [US3] `cover_letter/mapping_service.py` - `generate_mapping(question_id: int, profile: dict) -> list[dict]` 구현 — `mapping_generate.txt` 프롬프트로 `llm_client.call(tier='flash')` 호출, `relevance_score >= 3` 필터링·내림차순 정렬, JD 수집 결과(`load_jd()`)가 있으면 `required_competencies`를 프롬프트에 포함
- [X] T031 [P] [US3] `cover_letter/mapping_service.py` - `validate_duplicates(question_id, entries, all_session_mappings) -> list[dict]`, `save_mapping(question_id, entries) -> int` 구현 — `experience_key + usage_type` 조합 복수 문항 중복 감지, `mapping_table` INSERT + `confirmed_at` 처리
- [X] T032 [US3] `frontend/cover_letter_app.py` Step 3 구현 — 매핑 테이블 `st.data_editor` 표시(적합도·연결 근거 컬럼 포함), 경험 추가·제거·usage_type 변경 UI, 중복 경고 `st.warning()` 표시, "매핑 확정" 버튼으로 `save_mapping()` 호출
- [X] T033 [P] [US3] `tests/test_cover_letter_mapping.py` 보완 — `generate_mapping` (JD 역량 우선순위 반영 확인, 빈 경험), `validate_duplicates` (중복 있음·없음·usage_type 다름), `save_mapping` DB 저장 단위 테스트

---

## Phase 6: User Story 4 — 자소서 답변 생성 및 품질 검증 (Priority: P4)

**목표**: Gemini Pro 초안 생성 + 글자 수 자동 루프(최대 3회) + 환각 방지 자동 재생성(별도 카운트) + Pro Thinking 자가진단

**독립 테스트 기준**: 매핑 확정 → 초안 생성 → 환각 자동 검증(사용자 미표시) → 자가진단 이슈 목록 표시 → 승인 시 재작성 → DB 저장

- [X] T034 [P] [US4] `cover_letter/prompts/answer_generate.txt` 작성 — System(자소서 전문가 역할 + 문체 지시사항 + 글자수 제약 `{char_min}~{char_max}`자 이내 + 매핑 경험만 사용 강조) + User(기업분석·직무분석·문항·매핑 경험·사용자 지시) 구조
- [X] T035 [P] [US4] `cover_letter/prompts/self_diagnosis.txt` 작성 — AI 특유 표현("~에 기여", "다양한", 추상적 미사여구)·문맥 단절·어색한 전개 탐지 프롬프트 (문체 일치 검사 제외), 출력 포맷: `[{"issue","text","suggestion"}]` JSON 배열
- [X] T036 [P] [US4] `cover_letter/prompts/hallucination_check.txt` 생성·작성 — "아래 경험 목록(experiences)에 없는 고유명사·활동명·수치·프로젝트명이 답변(answer)에 포함되어 있는지 판정하라. True(환각 있음) 또는 False(정상) 중 하나만 JSON으로 반환: `{"hallucinated": bool}`"
- [X] T037 [US4] `cover_letter/generation_service.py` - `generate_answer(question, mapping_table_id, profile, company_analysis, job_analysis, user_instruction) -> dict` 구현 — `answer_generate.txt` 프롬프트로 `llm_client.call(tier='pro')`, `len(text)` 글자 수 측정 후 `target_char_min~target_char_max` 범위 이탈 시 최대 `MAX_RETRIES=3`회 재시도, `cover_letter_draft` INSERT 후 `{"draft_id","text","char_count","within_target","retry_count"}` 반환
- [X] T038 [US4] `cover_letter/generation_service.py` - `check_hallucination(answer_text, mapping_entries, profile) -> bool` 구현 — 1단계: `re` 모듈로 연도(19xx/20xx)·수치(n%)·영문 대문자 단어 추출 후 `profile["experiences"]` 텍스트와 집합 비교, 2단계: `hallucination_check.txt` 프롬프트로 `llm_client.call(tier='flash')` 이진 판정, 어느 한 단계라도 환각 감지 시 `True` 반환
- [X] T039 [US4] `cover_letter/generation_service.py` - `regenerate_without_hallucination(draft_id, mapping_entries, profile, max_retries=3) -> dict` 구현 — `check_hallucination()` 루프 (최대 3회), 환각 감지 시 "매핑 경험만 사용, 없는 내용 생성 금지" 지시 추가하여 재생성, `hallucination_retries` DB 필드 갱신, 3회 후에도 환각 지속 시 `{"hallucination_resolved": False}` 반환
- [X] T040 [US4] `cover_letter/generation_service.py` - `run_self_diagnosis(draft_id: int) -> list[dict]` 구현 — `self_diagnosis.txt` 프롬프트로 `llm_client.call(tier='pro-thinking')` 호출, `self_diagnosis_issues` JSON 저장, 문제 없으면 빈 리스트
- [X] T041 [P] [US4] `cover_letter/generation_service.py` - `apply_diagnosis_and_regenerate(draft_id: int) -> dict`, `confirm_draft(draft_id: int) -> None` 구현 — 재생성 시 기존 문제 목록 포함 프롬프트로 새 버전 INSERT, confirm 시 `status='confirmed'` UPDATE
- [X] T042 [US4] `frontend/cover_letter_app.py` Step 4 구현 — "초안 생성" 버튼 → `generate_answer()` 호출 → `regenerate_without_hallucination()` 자동 실행(사용자 미표시) → 초안 텍스트 + 글자 수 표시 → `run_self_diagnosis()` 자동 실행 → 이슈 목록 `st.expander("자가진단 결과")` → "재작성 승인" / "무시" 버튼 → 수정 지시 `st.text_input` → "최종 저장" 버튼 (`confirm_draft()`), 3회 초과 알림
- [X] T043 [P] [US4] `tests/test_cover_letter_generation.py` 보완 — `generate_answer` (글자 수 루프 3회 제한, 범위 내 조기 종료), `check_hallucination` (규칙 기반 탐지, LLM 판정 mock), `regenerate_without_hallucination` (3회 후 미해결), `run_self_diagnosis` (이슈 없음·있음), `confirm_draft` status 변경

---

## Phase 7: 통합 마무리 (Polish & Cross-Cutting)

**목적**: 5단계 위자드 연결, Streamlit UI 개선(SC-006), E2E 검증, pre-commit 통과

- [X] T044 `frontend/cover_letter_app.py` — `st.set_page_config(layout="centered")` 적용 + 모든 답변 텍스트 출력 영역 `st.markdown()` 자동 확장 (스크롤 없이 전체 표시), `st.text_area`에 `height=max(300, len(text)//2)` 동적 높이 적용 (SC-006)
- [X] T045 `frontend/cover_letter_app.py` 5단계 위자드 통합 — `st.session_state["step"]` 기반 단계 진행, "이전 단계" 복귀 버튼 (현재 단계 데이터 `st.session_state`에 임시 보존), 각 단계 완료 데이터 누적
- [ ] T046 [P] DB 마이그레이션 통합 검증 — Docker Compose 환경에서 `001_cover_letter_schema.sql` → `002_add_jd_entity.sql` 순서 실행, Generated Column(`target_char_min`·`target_char_max`) 정상 동작, `hallucination_retries DEFAULT 0` 확인
- [X] T047 [P] pre-commit 전체 통과 — `pre-commit run --all-files` (black·isort·flake8·mypy·trailing-whitespace·end-of-file-fixer)
- [ ] T048 코드리뷰·리팩토링 — `cover_letter/` 전체 파일 공통 DB 연결 패턴 점검, `llm_client.call()` 중복 호출 패턴 검토, Constitution Check 최종 확인
- [X] T049 [P] `README.md` 업데이트 — 자소서 서비스 실행 방법 추가: `GEMINI_API_KEY·DART_API_KEY·FIRECRAWL_API_KEY 설정 → make up → localhost:8501`

---

## 의존성 그래프

```
Phase 1 (T001~T005) — 환경변수·마이그레이션·컨테이너
    ↓
Phase 2 (T006~T008) — models.py·llm_client·API Key 검증 완료 후 US 착수 가능
    ↓
Phase 3: US1 (T009~T014) ← MVP 최소 구현 단위 (프로필 등록)
    ↓
Phase 4: US2 (T015~T028) ← US1 프로필·models.py 필요 (기업·JD·문항 분석)
    ↓
Phase 5: US3 (T029~T033) ← US2 문항 분석 결과 필요 (매핑 테이블)
    ↓
Phase 6: US4 (T034~T043) ← US3 매핑 테이블 필요 (답변 생성·환각·자가진단)
    ↓
Phase 7 통합 (T044~T049)
```

### 단계 내 병렬 실행 예시

**Phase 2 병렬**:
- T006 (models.py) ‖ T008 (API Key 검증) → 동시 착수
- T007 (llm_client) → google-genai import 확인 후 바로 착수

**Phase 3 병렬**:
- T009 (프롬프트) ‖ T010 (parse_input) → 동시 착수
- T012 (save/load/merge) → T011 완료 후, T014 (테스트) 병렬 착수 가능

**Phase 4 병렬**:
- T015 (company 프롬프트) ‖ T016 (question 프롬프트) ‖ T017 (dart_collector) ‖ T018 (naver_collector) ‖ T019 (website_crawler) ‖ T020 (jd_crawler) → 동시 착수
- T021 (jd_service) → T020 완료 후
- T022 (get_or_analyze_company) → T017·T018·T019 완료 후
- T023 (analyze_job) → T022 + T021 완료 후

**Phase 6 병렬**:
- T034·T035·T036 (프롬프트 3개) → 동시 착수
- T038 (check_hallucination) ‖ T040 (run_self_diagnosis) → T037 완료 후 병렬
- T039 (regenerate_without_hallucination) → T038 완료 후
- T041 (apply+confirm) → T040 완료 후

---

## 구현 전략

**MVP 범위 (US1만으로 독립 가치 제공)**:
- Phase 1 (T001~T005) + Phase 2 (T006~T008) + Phase 3 US1 (T009~T014) = **17개 태스크**
- 완료 시: TXT·MD·DOCX 입력 → 프로필 추출 → 검토·수정 → DB 저장 독립 동작

**점진적 확장**:
- US1 → US2: DART·JD·문항 분석 추가 (**14개 태스크**, T015~T028)
- US2 → US3: 매핑 테이블 추가 (**5개 태스크**, T029~T033)
- US3 → US4: 답변 생성·환각 방지·자가진단 추가 (**10개 태스크**, T034~T043)
- 통합 마무리 (**6개 태스크**, T044~T049)

**총 태스크**: 49개
**US1 MVP**: 17개 | **US2 추가**: 14개 | **US3 추가**: 5개 | **US4 추가**: 10개 | **통합**: 6개 (총 52개 — T002a 포함)
**병렬 기회**: 27개 태스크 ([P] 마킹) — Phase 4에서 최대 6개 동시 실행 가능

**신규 파일 목록** (plan.md 기준):
- `cover_letter/models.py` — T006
- `cover_letter/jd_service.py` — T021
- `cover_letter/collectors/jd_crawler.py` — T020
- `cover_letter/prompts/hallucination_check.txt` — T036
- `db/migrations/002_add_jd_entity.sql` — T004
