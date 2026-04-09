# Implementation Plan: 자소서 작성 자동화 서비스

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-09 | **Spec**: `specs/001-cover-letter-automation/spec.md`
**Input**: Feature specification from `/specs/001-cover-letter-automation/spec.md`

## Summary

취준생을 위한 자소서 자동화 서비스. TXT/텍스트 입력으로 사용자 프로필을 추출하고, DART API(사업보고서)·Naver 뉴스·공식 홈페이지 3-소스 기업 정보 수집, 경험-문항 매핑 테이블 생성, Google Gemini 3단계 티어 LLM으로 답변 초안을 생성한다. Streamlit 5단계 위자드 UI, PostgreSQL DB, Docker Compose 배포.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: google-genai (LLM 티어 라우팅), streamlit (UI), psycopg2-binary (DB — 기존 사용 중), dart-fss (DART 사업보고서 수집, optional), requests+beautifulsoup4 (홈페이지 스크래핑 — 기존 TrendOps 스택). TXT 파일 입력은 내장 `str` 처리로 외부 파서 불필요
**Storage**: PostgreSQL 15 (Docker 컨테이너, 기존 재사용)
**Testing**: pytest (`tests/test_cover_letter_*.py`)
**Target Platform**: 로컬 Docker Compose (이후 클라우드 확장)
**Project Type**: web-service (Streamlit single-page app)
**Performance Goals**: 기업 분석부터 첫 초안까지 사용자 능동 작업 시간 70% 감소
**Constraints**: 한국어 고정, 단일 사용자 (MVP), 로컬 Single Node
**Scale/Scope**: 단일 사용자 로컬 MVP, 6개 DB 엔티티, 5개 서비스 모듈

**LLM Tier 전략**:
- Tier 1 `flash`: `gemini-2.5-flash` — 수집/요약/매핑 (저비용)
- Tier 2 `pro`: `gemini-2.5-pro` — 자소서 초안/전략 (중비용)
- Tier 3 `pro-thinking`: `gemini-2.5-pro` + thinking mode — 자가진단/마무리 (고비용)
- 환경 변수: `GEMINI_API_KEY` (required), `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`

## Constitution Check

*GATE: Phase 0 시작 전 통과 필수. Phase 1 설계 완료 후 재확인.*

- [x] **MLOps-First**: Gemini 3단계 티어 LLM 서빙 + 환경 변수 기반 모델 교체 인터페이스 — MLOps 파이프라인 경험 충족 ✅
- [x] **GitHub Flow**: `main`에서 `001-cover-letter-automation` 분기, PR 대상 `main` ✅
- [x] **ADR 초안**: `docs/decisions/20260407-llm-api-selection.md` 계획됨 (Phase 1에서 작성) ✅
- [x] **Container-First**: `Dockerfile.cover-letter` 신규 추가 예정 (Phase 1) ✅
- [x] **MVP-First**: 로컬 Docker Compose, TXT 입력 전용, 단일 사용자 — 최소 범위 한정 ✅
- [x] **Code Minimalism**: 서비스별 단일 파일 단순 함수 집합, 클래스 불필요(YAGNI) ✅
- [x] **Code Review 계획**: Phase 6에 구현 완료 후 코드리뷰 + 리팩토링 단계 포함 ✅

## Project Structure

### Documentation (this feature)

```text
specs/001-cover-letter-automation/
├── plan.md              ← 이 파일
├── research.md          ← 완료 (8 decisions)
├── data-model.md        ← 완료 (6 entities)
├── quickstart.md        ← 완료
├── contracts/
│   └── service-interfaces.md  ← 완료 (6 서비스 시그니처)
└── tasks.md             ← /speckit.tasks 에서 생성
```

### Source Code (repository root)

```text
cover_letter/               # 서비스 모듈
├── __init__.py
├── llm_client.py           # Gemini 티어 라우팅 (flash/pro/pro-thinking)
├── profile_service.py      # 텍스트 입력 처리 + LLM 프로필 추출
├── company_service.py      # 기업·직무 분석 + 3-소스 수집 오케스트레이션 + DB 캐싱
├── question_service.py     # 문항 분석
├── mapping_service.py      # 경험-문항 매핑 테이블
├── generation_service.py   # 답변 초안 생성 + 자가진단
├── collectors/
│   ├── dart_collector.py    # DART API 사업보고서 수집 (DART_API_KEY optional)
│   ├── naver_collector.py   # Naver News API + Firecrawl fallback
│   └── website_crawler.py  # 공식 홈페이지 인재상·비전 스크래핑
└── prompts/
    ├── profile_extract.txt
    ├── company_analysis.txt
    ├── question_analysis.txt
    ├── mapping_generate.txt
    ├── answer_generate.txt
    └── self_diagnosis.txt

frontend/
└── cover_letter_app.py     # Streamlit 5단계 위자드

db/
└── migrations/
    └── 001_cover_letter_schema.sql  # 6개 엔티티 DDL

tests/
├── test_cover_letter_profile.py
├── test_cover_letter_company.py
├── test_cover_letter_generation.py
└── test_cover_letter_mapping.py

docs/
└── decisions/
    ├── 20260407-llm-api-selection.md        # ADR: Gemini 단일 프로바이더 + 티어 전략
    ├── 20260407-cover-letter-db-schema.md   # ADR: 6개 엔티티 DB 스키마
    └── 20260407-streamlit-wizard-pattern.md # ADR: Streamlit session_state 위자드
```

## Implementation Phases

### Phase 1: 기반 설정

**목표**: 프로젝트 구조 초기화, DB 마이그레이션, LLM 클라이언트 티어 구현

| 작업 | 파일 | 설명 |
|------|------|------|
| 디렉토리 생성 | `cover_letter/`, `frontend/`, `db/migrations/`, `cover_letter/prompts/` | 패키지 구조 |
| LLM 클라이언트 구현 | `cover_letter/llm_client.py` | `call(prompt, tier, system)` — Flash/Pro/Pro-Thinking 라우팅 |
| DB 마이그레이션 | `db/migrations/001_cover_letter_schema.sql` | 6개 엔티티 DDL |
| Dockerfile 추가 | `Dockerfile.cover-letter` | Streamlit 앱 컨테이너 |
| Docker Compose 업데이트 | `docker-compose.yml` | cover-letter 서비스 추가 |
| ADR 작성 (LLM 선택) | `docs/decisions/20260407-llm-api-selection.md` | Gemini 단일 프로바이더 + 3단계 티어 결정 |
| ADR 작성 (DB 스키마) | `docs/decisions/20260407-cover-letter-db-schema.md` | 6개 엔티티 설계 결정 |
| ADR 작성 (UI 패턴) | `docs/decisions/20260407-streamlit-wizard-pattern.md` | Streamlit session_state 5단계 위자드 결정 |
| 환경 변수 추가 | `.env.example` | `GEMINI_API_KEY`, `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL` |

**완료 조건**: `llm_client.call(prompt, tier='flash')` 호출 시 Gemini 응답 반환 확인

---

### Phase 2: 사용자 프로필 서비스 (FR-001, FR-002, FR-002a)

**목표**: 텍스트 입력 처리 + LLM 프로필 추출 + 확인 저장

| 작업 | 파일 | 설명 |
|------|------|------|
| 텍스트 입력 처리 | `cover_letter/profile_service.py` | TXT 업로드 또는 텍스트 붙여넣기 파싱 |
| 프로필 추출 | `cover_letter/profile_service.py` | `extract_profile()`, Gemini Flash 호출 |
| 프로필 저장/로드 | `cover_letter/profile_service.py` | `save_profile()`, `load_profile()` |
| Streamlit 스텝 0 | `frontend/cover_letter_app.py` | TXT 업로드/텍스트 입력 UI, 프로필 검토/수정 |
| 단위 테스트 | `tests/test_cover_letter_profile.py` | 입력 처리, 추출, 저장 |

**완료 조건**: TXT 업로드 또는 텍스트 붙여넣기 → 프로필 요약 표시 → 수정 → DB 저장 확인

---

### Phase 3: 기업·직무·문항 분석 서비스 (FR-003~FR-005)

**목표**: 기업 분석 크롤링, DB 캐싱, 문항 분석

| 작업 | 파일 | 설명 |
|------|------|------|
| DART 수집기 | `cover_letter/collectors/dart_collector.py` | `collect_dart_reports(company_name, years=3)` — 사업보고서 주요 섹션 추출, `DART_API_KEY` 없으면 빈 dict 반환 |
| 뉴스 수집기 | `cover_letter/collectors/naver_collector.py` | `collect_news(company_name, job_title)` — Naver News API 1차, 결과 부족 시 Firecrawl fallback |
| 홈페이지 크롤러 | `cover_letter/collectors/website_crawler.py` | `crawl_company_website(company_name)` — 인재상·비전 페이지 BeautifulSoup 스크래핑, 실패 시 None 반환 |
| 기업 분석 서비스 | `cover_letter/company_service.py` | `get_or_analyze_company()` — 3-소스 수집 오케스트레이션 + Gemini Flash 통합 요약 |
| DB 캐싱 | `cover_letter/company_service.py` | `get_cached_analysis()`, `cache_analysis()` |
| 문항 분석 서비스 | `cover_letter/question_service.py` | `analyze_question()`, Gemini Flash 호출 |
| Streamlit 스텝 1·2 | `frontend/cover_letter_app.py` | 기업/직무 입력 + 문항 입력 UI |
| 단위 테스트 | `tests/test_cover_letter_company.py` | 3-소스 수집기 mock, 캐싱, 문항 분석 |

**완료 조건**: 기업명 + 직무 입력 → 분석 결과 표시 → 캐시 재사용 확인

---

### Phase 4: 매핑 테이블 서비스 (FR-006, FR-006a)

**목표**: 경험-문항 매핑 자동 생성, 중복 경고

| 작업 | 파일 | 설명 |
|------|------|------|
| 매핑 서비스 | `cover_letter/mapping_service.py` | `generate_mapping()`, Gemini Flash 호출, 중복 검증 |
| 중복 경고 로직 | `cover_letter/mapping_service.py` | `check_duplicate_usage()` |
| Streamlit 스텝 3 | `frontend/cover_letter_app.py` | 매핑 테이블 검토/수정 UI |
| 단위 테스트 | `tests/test_cover_letter_mapping.py` | 매핑 생성, 중복 검증 |

**완료 조건**: 매핑 테이블 표시 → 동일 경험 중복 배정 시 경고 확인

---

### Phase 5: 답변 생성 서비스 (FR-008~FR-011a)

**목표**: Gemini Pro 답변 초안 생성, 글자 수 루프, Gemini Pro Thinking 자가진단

| 작업 | 파일 | 설명 |
|------|------|------|
| 답변 생성 | `cover_letter/generation_service.py` | `generate_answer()`, Gemini Pro (`tier='pro'`) |
| 글자 수 제어 루프 | `cover_letter/generation_service.py` | 90~95% 범위, 최대 3회 재시도 |
| 자가진단 | `cover_letter/generation_service.py` | `run_self_diagnosis()`, Gemini Pro Thinking (`tier='pro-thinking'`) |
| 재작성 적용 | `cover_letter/generation_service.py` | `apply_diagnosis_and_regenerate()` |
| Streamlit 스텝 4 | `frontend/cover_letter_app.py` | 답변 표시, 자가진단 목록, 수정 지시 UI |
| 단위 테스트 | `tests/test_cover_letter_generation.py` | 생성, 글자 수 루프, 자가진단 |

**완료 조건**: 매핑 확정 → 초안 생성 → 자가진단 실행 → 승인 시 재작성 → DB 저장 확인

---

### Phase 6: 통합 마무리

**목표**: 전체 5단계 위자드 연결, 엣지 케이스, Docker 검증, 코드리뷰

| 작업 | 파일 | 설명 |
|------|------|------|
| 위자드 통합 | `frontend/cover_letter_app.py` | 이전 단계 복귀, session_state 임시 저장 |
| Docker 통합 테스트 | `docker-compose.yml` | `make up` 후 전체 흐름 E2E 검증 |
| pre-commit 정리 | 전체 | black, isort, flake8, mypy 통과 |
| 코드리뷰 | 전체 | 공통 로직 추출 여부, 리팩토링 검토 |
| ADR 최종화 | `docs/decisions/` | 결과 및 트레이드오프 보완 후 상태: 제안 → 승인 |
| README 업데이트 | `README.md` | 자소서 서비스 실행 방법 추가 |

**완료 조건**: `make up` 후 5단계 전체 흐름 E2E 통과, pre-commit 전체 통과, ADR 승인 상태 확인

---

## Constitution Development Workflow

> **Constitution v1.1.0 — 이 feature의 개발은 아래 8단계 사이클을 따른다. Phase 번호와 대응:**

```
[Before Phase 1]  1. ADR 초안 작성 (docs/decisions/)
[Phase 1]         2. feature 브랜치 생성 — 001-cover-letter-automation (main 기반) ✅
[Phase 1~5]       3. 최소 코드 구현 + Docker 컨테이너 검증
[Phase 2~5]       4. pre-commit 훅 통과 + 테스트 작성 (pytest)
[Phase 5 완료]    5. 로컬 MVP 동작 확인
[Phase 6]         6. 코드리뷰: 공통 로직 추출, 리팩토링 검토
[Phase 6]         7. ADR 최종화 (결과 및 트레이드오프 보완)
[Phase 6 완료]    8. PR → main (CI 통과 후 병합)
```

### 필수 ADR 목록

Constitution Principle I + V에 의해 아래 주요 기술 결정은 PR 병합 전 ADR이 존재해야 한다:

| ADR 파일 | 결정 내용 | 생성 시점 | 상태 |
|----------|-----------|----------|------|
| `docs/decisions/20260407-llm-api-selection.md` | Gemini 단일 프로바이더 선택 + 3단계 티어 전략 | Phase 1 | 제안 |
| `docs/decisions/20260407-cover-letter-db-schema.md` | 6개 엔티티 DB 스키마 설계 | Phase 1 | 제안 |
| `docs/decisions/20260407-streamlit-wizard-pattern.md` | Streamlit session_state 기반 5단계 위자드 | Phase 1 | 제안 |
| `docs/decisions/20260409-company-3-source-collection.md` | DART API·Naver News·공식 홈페이지 3-소스 기업 정보 수집 전략 | Phase 3 | 제안 |

### MLOps 포트폴리오 기여 근거

Constitution Principle I — 이 feature가 MLOps 포트폴리오에 기여하는 구체적 근거:

- **LLM 서빙 티어 라우팅**: 작업 복잡도별 모델 선택 로직 (`llm_client.py`) — 프로덕션 LLM 서빙 설계 패턴
- **환경 변수 기반 모델 교체**: `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL` 환경 변수로 모델 버전 고정 — MLOps 모델 버전 관리 패턴
- **Docker 컨테이너 서빙**: `Dockerfile.cover-letter` + Docker Compose — 컨테이너 기반 ML 서비스 배포 경험
- **DB 캐싱 전략**: 동일 기업 분석 재사용 (`company_service.py`) — LLM 호출 비용 최적화 패턴
- **ADR 문서화**: 기술 결정 근거 기록 — MLOps 엔지니어 포트폴리오 핵심 산출물
