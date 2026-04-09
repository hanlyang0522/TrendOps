# Tasks: 자소서 작성 자동화 서비스

**브랜치**: `001-cover-letter-automation` | **날짜**: 2026-04-09
**입력 문서**: plan.md · spec.md · research.md · data-model.md · contracts/service-interfaces.md

---

## 형식: `[ID] [P?] [Story?] 설명 — 파일 경로`

- **[P]**: 병렬 실행 가능 (다른 파일, 미완료 태스크 의존 없음)
- **[US1~US4]**: 해당 유저 스토리 레이블 (Setup·Foundation·Polish 단계에는 미부착)
- 각 태스크는 정확한 파일 경로 포함

---

## Phase 1: 설정 (프로젝트 초기화)

**목적**: 프로젝트 디렉토리 구조, 환경 변수, 컨테이너 설정

- [ ] T001 프로젝트 디렉토리 구조 생성 — `cover_letter/`, `cover_letter/prompts/`, `cover_letter/collectors/`, `frontend/`, `db/migrations/`
- [ ] T002 [P] `.env.example`에 환경 변수 추가 — `GEMINI_API_KEY`, `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `DART_API_KEY` (optional), `FIRECRAWL_API_KEY` (optional)
- [ ] T002a [P] `pyproject.toml` 의존성 추가 — `dart-fss` (optional, DART 수집), `firecrawl` (optional, Naver fallback) extra-requires로 등록
- [ ] T003 [P] `Dockerfile.cover-letter` 작성 — Streamlit 앱 컨테이너 (Python 3.13 베이스)
- [ ] T004 [P] `docker-compose.yml` cover-letter 서비스 추가 — postgres `depends_on`, 포트 8501 노출

---

## Phase 2: 기반 (모든 유저 스토리의 선행 조건)

**목적**: DB 스키마, LLM 티어 클라이언트, ADR 초안 — 이 단계 완료 전 US 작업 착수 불가

**⚠️ 블로킹**: 아래 태스크가 완료되어야 US1~US4 병렬 착수 가능

- [ ] T005 `db/migrations/001_cover_letter_schema.sql` 작성 — 6개 엔티티 DDL (`user_profile`, `company_analysis`, `job_analysis`, `question`, `mapping_table`, `cover_letter_draft`)
- [ ] T006 `cover_letter/llm_client.py` 구현 — `call(prompt, tier, system, temperature)` Gemini Flash·Pro·Pro-Thinking 티어 라우팅, 환경 변수 기반 모델 선택
- [ ] T007 [P] `cover_letter/__init__.py` 생성 — 패키지 초기화 (빈 파일)
- [ ] T008 [P] ADR 초안 4개 작성
  - `docs/decisions/20260407-llm-api-selection.md` — Gemini 단일 프로바이더 + 3단계 티어 결정
  - `docs/decisions/20260407-cover-letter-db-schema.md` — 6개 엔티티 DB 스키마 설계 결정
  - `docs/decisions/20260407-streamlit-wizard-pattern.md` — Streamlit session_state 5단계 위자드 결정
  - `docs/decisions/20260409-company-3-source-collection.md` — DART API·Naver News·홈페이지 3-소스 수집 전략 결정

**체크포인트**: `llm_client.call("테스트", tier='flash')` 호출 시 Gemini 응답 반환 확인 → US1 착수 가능

---

## Phase 3: User Story 1 — 사용자 프로필 등록 (Priority: P1) 🎯 MVP

**목표**: TXT 업로드 또는 텍스트 붙여넣기로 사용자 경험·역량·문체 프로필을 추출하고 DB에 저장

**독립 테스트 기준**: TXT 파일 업로드 또는 텍스트 붙여넣기 → 프로필 요약(경험 목록, 핵심 역량, 문체 특성) 화면 표시 → 수정 → DB 저장 확인

- [ ] T009 [P] [US1] `cover_letter/prompts/profile_extract.txt` 작성 — 경험·역량·문체 추출 프롬프트 (System + User turn 구조)
- [ ] T010 [P] [US1] `cover_letter/profile_service.py` - `parse_input(text: str | None, file_bytes: bytes | None) -> str` 구현 — TXT 업로드(`file_bytes.decode('utf-8')`) 또는 텍스트 붙여넣기 처리, 둘 다 None이면 ValueError
- [ ] T011 [US1] `cover_letter/profile_service.py` - `extract_profile(texts: list[str]) -> dict` 구현 — `llm_client.call(tier='flash')` 호출, 결과 `{"experiences": [...], "competencies": [...], "writing_style": {...}}` 반환
- [ ] T012 [P] [US1] `cover_letter/profile_service.py` - `save_profile(profile: dict) -> None`, `load_profile() -> dict | None`, `merge_profile(existing: dict, new_texts: list[str]) -> dict` 구현 — psycopg2로 `user_profile` 테이블 upsert (id=1 단일 레코드)
- [ ] T013 [US1] `frontend/cover_letter_app.py` Step 0 구현 — `st.file_uploader(type=['txt'])` + `st.text_area()` OR 입력, 프로필 요약 표시, 항목 수정·삭제·추가 UI, 확인 버튼 클릭 시 `save_profile()` 호출
- [ ] T014 [P] [US1] `tests/test_cover_letter_profile.py` 작성 — `parse_input` (빈 입력 오류, TXT 정상 파싱), `save_profile`/`load_profile` (DB 왕복), `merge_profile` (기존 + 신규 병합) 단위 테스트

---

## Phase 4: User Story 2 — 기업·직무 분석 및 문항 분석 (Priority: P2)

**목표**: 기업명·직무 입력 → Naver 뉴스 크롤링 + Gemini Flash 요약 → DB 캐싱, 자소서 문항 역량 분석

**독립 테스트 기준**: 기업명 + 직무 입력 후 분석 요약(기업 특징, 직무 페인 포인트) 표시, 동일 기업 재조회 시 캐시 히트 확인, 문항 입력 후 측정 역량 표시

- [ ] T015 [P] [US2] `cover_letter/prompts/company_analysis.txt` 작성 — DART 사업보고서(주요 제품·시장현황·연구개발) + 뉴스 + 인재상·비전 3-소스 통합 요약 프롬프트
- [ ] T016 [P] [US2] `cover_letter/prompts/question_analysis.txt` 작성 — 문항 측정 역량·기대 수준 분석 프롬프트
- [ ] T017 [US2] `cover_letter/company_service.py` - `get_or_analyze_company(company_name: str) -> dict` 구현 — `company_analysis` 테이블 캐시 조회(7일 유효), 캐시 미스 시 3개 수집기(`dart_collector`, `naver_collector`, `website_crawler`) 순차 호출 후 `llm_client.call(tier='flash')`로 통합 요약
- [ ] T017a [P] [US2] `cover_letter/collectors/dart_collector.py` 구현 — `collect_dart_reports(company_name: str, years: int = 3) -> dict` — `dart-fss` 라이브러리로 사업보고서 주요 시스템인 항목(주요 제품/서비스, 지식재산권, 시장현황, 주요계약·연구개발) 추출. `DART_API_KEY` 미설정 시 빈 dict 반환
- [ ] T017b [P] [US2] `cover_letter/collectors/website_crawler.py` 구현 — `crawl_company_website(company_name: str) -> dict | None` — `requests` + `BeautifulSoup4`로 인재상·비전 페이지 스크래핑. 실패(네트워크 오류·알 수 없는 페이지 구조) 시 None 반환
- [ ] T017c [P] [US2] `cover_letter/collectors/naver_collector.py` 구현 — `collect_news(company_name: str, job_title: str) -> list[dict]` — 기존 `crawling/` 모듈 괰용. Naver 결과 5건 미만시 Firecrawl API fallback (FIRECRAWL_API_KEY 필요)
- [ ] T018 [P] [US2] `cover_letter/company_service.py` - `analyze_job(company_analysis_id: int, job_title: str) -> dict`, `save_overrides(entity: str, entity_id: int, overrides: dict) -> None` 구현 — `job_analysis` 테이블 저장
- [ ] T019 [US2] `cover_letter/question_service.py` - `analyze_question(job_analysis_id: int, question_text: str, char_limit: int | None) -> dict` 구현 — `llm_client.call(tier='flash')` 호출, `question` 테이블 저장 (`target_char_min`/`target_char_max` Generated Column 자동 계산)
- [ ] T020 [US2] `frontend/cover_letter_app.py` Step 1 구현 — 기업명·직무 입력 폼, 분석 결과 검토·수정 UI, 캐시 히트 시 "이전 분석 결과 재사용" 표시, `save_overrides()` 연동
- [ ] T021 [US2] `frontend/cover_letter_app.py` Step 2 구현 — 문항 텍스트 입력 + 글자 수 제한 입력, 문항 분석 결과(측정 역량·기대 수준) 검토·수정 UI
- [ ] T022 [P] [US2] `tests/test_cover_letter_company.py` 작성 — `dart_collector` (API Key 없음 시 빈 dict mock), `naver_collector` (Firecrawl fallback mock), `website_crawler` (None 반환 케이스), `get_or_analyze_company` (캐시 히트·미스·소스 일부 실패 시나리오)

---

## Phase 5: User Story 3 — 경험-문항 매핑 테이블 생성 (Priority: P3)

**목표**: 문항 분석 결과 + 사용자 프로필 기반 자동 매핑 생성, 동일 경험 중복 배정 경고

**독립 테스트 기준**: 매핑 테이블 표시 → 사용자 경험 선택·수정 → 동일 경험 같은 방식 중복 시 경고 표시 → 저장

- [ ] T023 [P] [US3] `cover_letter/prompts/mapping_generate.txt` 작성 — 문항 역량 vs 사용자 경험 적합도 평가 + `usage_type`(primary/supporting/background) 분류 프롬프트
- [ ] T024 [US3] `cover_letter/mapping_service.py` - `generate_mapping(question_id: int, profile: dict) -> list[dict]` 구현 — `llm_client.call(tier='flash')` 호출, `relevance_score >= 3` 필터링, score 내림차순 반환
- [ ] T025 [P] [US3] `cover_letter/mapping_service.py` - `validate_duplicates(question_id, entries, all_session_mappings) -> list[dict]`, `save_mapping(question_id, entries) -> int` 구현 — `experience_key + usage_type` 조합 중복 검증, `mapping_table` 테이블 저장
- [ ] T026 [US3] `frontend/cover_letter_app.py` Step 3 구현 — 매핑 테이블 표시(적합도·연결 근거 포함), 경험 추가·제거·순서 변경 UI, 중복 경고 `st.warning()` 표시, 확정 버튼 클릭 시 `save_mapping()` 호출
- [ ] T027 [P] [US3] `tests/test_cover_letter_mapping.py` 작성 — `generate_mapping` (빈 경험 처리), `validate_duplicates` (중복 있음·없음), `save_mapping` DB 저장 단위 테스트

---

## Phase 6: User Story 4 — 자소서 답변 생성 및 품질 검증 (Priority: P4)

**목표**: Gemini Pro 초안 생성 + 글자 수 자동 제어 루프 (최대 3회) + Gemini Pro Thinking 자가진단

**독립 테스트 기준**: 매핑 확정 → 초안 생성 → 자가진단 목록 표시 → 승인 시 재작성 → DB 저장

- [ ] T028 [P] [US4] `cover_letter/prompts/answer_generate.txt` 작성 — System(역할+문체+글자 수 제약) + User(기업분석+직무분석+문항+매핑) 프롬프트 구조
- [ ] T029 [P] [US4] `cover_letter/prompts/self_diagnosis.txt` 작성 — AI 특유 표현·문맥 단절·어색한 전개 탐지 프롬프트 (문체 일치 검사 제외)
- [ ] T030 [US4] `cover_letter/generation_service.py` - `generate_answer(question, mapping_table_id, profile, company_analysis, job_analysis, user_instruction) -> dict` 구현 — `llm_client.call(tier='pro')`, 글자 수 `len(text)` 측정 후 `target_char_min~target_char_max` 범위 이탈 시 최대 `MAX_RETRIES=3`회 재시도, `cover_letter_draft` 테이블 저장
- [ ] T031 [US4] `cover_letter/generation_service.py` - `run_self_diagnosis(draft_id: int) -> list[dict]` 구현 — `llm_client.call(tier='pro-thinking')`, 문제 항목 `[{"issue", "text", "suggestion"}]` 반환, `self_diagnosis_issues` 필드 갱신
- [ ] T032 [P] [US4] `cover_letter/generation_service.py` - `apply_diagnosis_and_regenerate(draft_id: int) -> dict`, `confirm_draft(draft_id: int) -> None` 구현 — 재생성 시 새 버전 INSERT, confirm 시 status `'confirmed'` 업데이트
- [ ] T033 [US4] `frontend/cover_letter_app.py` Step 4 구현 — 생성 중 스피너, 초안 + 글자 수 표시, 자가진단 문제 목록 `st.expander()`, 재작성 승인·무시 버튼, 수정 지시 `st.text_input()`, 3회 초과 시 `st.warning()`, 최종 저장 버튼
- [ ] T034 [P] [US4] `tests/test_cover_letter_generation.py` 작성 — `generate_answer` (글자 수 루프 3회 제한, 범위 내 조기 종료), `run_self_diagnosis` (문제 있음·없음), `confirm_draft` 상태 변경 단위 테스트

---

## Phase 7: 통합 마무리 (Polish & Cross-Cutting)

**목적**: 전체 5단계 위자드 연결, E2E 검증, ADR 최종화, pre-commit 통과, 코드리뷰

- [ ] T035 `frontend/cover_letter_app.py` 5단계 위자드 통합 — `st.session_state["step"]` 기반 이전 단계 복귀 버튼, 각 단계 완료 데이터 session_state 누적, 최종 저장 시에만 DB write
- [ ] T036 [P] `docker-compose.yml` 통합 검증 — `make up` 후 DB 마이그레이션 자동 실행, Streamlit 앱 접속 확인
- [ ] T037 [P] pre-commit 전체 통과 — `pre-commit run --all-files` (black, isort, flake8, mypy, trailing-whitespace, end-of-file-fixer)
- [ ] T038 코드리뷰 — 공통 DB 연결 패턴 추출 여부 검토, `llm_client.call()` 중복 호출 패턴 리팩토링 검토
- [ ] T039 [P] ADR 3개 최종화 — 결과 및 트레이드오프 섹션 보완, 상태 `제안 → 승인`
- [ ] T040 `README.md` 업데이트 — 자소서 서비스 실행 방법 (`GEMINI_API_KEY 설정 → make up → localhost:8501`) 추가

---

## 의존성 그래프

```
Phase 1 (T001~T004)
    ↓
Phase 2 (T005~T008) — T005·T006 완료 후 Phase 3~6 착수 가능
    ↓
Phase 3: US1 (T009~T014) ← MVP 최소 구현 단위
    ↓
Phase 4: US2 (T015~T022) ← US1 프로필 필요
    ↓
Phase 5: US3 (T023~T027) ← US2 문항 분석 필요
    ↓
Phase 6: US4 (T028~T034) ← US3 매핑 테이블 필요
    ↓
Phase 7 통합 (T035~T040)
```

### 단계 내 병렬 실행 예시

**Phase 2 병렬**:
- T005 (DB 마이그레이션) ‖ T007 (패키지 init) ‖ T008 (ADR 초안 3개)
- T006 (llm_client) → T005 완료 후 DB 연동 테스트

**Phase 3 병렬**:
- T009 (프롬프트 작성) ‖ T010 (parse_input 구현) → 동시 착수 가능
- T011 (extract_profile) → T010 완료 후
- T012 (save/load/merge) ‖ T014 (테스트) → T011 이후 병렬

**Phase 4 병렬**:
- T015 (company 프롬프트) ‖ T016 (question 프롬프트) → 동시 착수
- T017 (company_service) ‖ T018 (job+overrides), T019 (question_service) → T017 완료 후

**Phase 6 병렬**:
- T028 (answer 프롬프트) ‖ T029 (diagnosis 프롬프트) → 동시 착수
- T031 (run_self_diagnosis) ‖ T032 (apply+confirm) → T030 완료 후 병렬

---

## 구현 전략

**MVP 범위 (US1만으로 독립 가치 제공)**:
- T001~T008 + T002a (Phase 1·2) + T009~T014 (Phase 3) = 15개 태스크
- 완료 시: TXT/텍스트 입력 → 프로필 추출 → 검토/수정 → DB 저장 동작

**점진적 확장**:
- US1 → US2: 기업·직무·문항 분석 추가 (11개 태스크)
- US2 → US3: 매핑 테이블 추가 (5개 태스크)
- US3 → US4: 답변 생성·자가진단 추가 (7개 태스크)
- 통합 마무리 (6개 태스크)

**속 태스크**: 44개
**US1 MVP**: 15개 | **US2 추가**: 11개 | **US3 추가**: 5개 | **US4 추가**: 7개 | **통합**: 6개
**병렬 기회**: 24개 태스크 ([P] 마킹) — Phase별 최대 3개 동시 실행 가능
