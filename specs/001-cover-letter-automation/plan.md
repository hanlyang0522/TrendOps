# Implementation Plan: 자소서 작성 자동화 서비스

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-cover-letter-automation/spec.md`

---

## Summary

취준생이 기업 조사·직무 분석·경험 매핑·자소서 답변 생성까지의 6단계 프로세스를 자동화하는 서비스.
PostgreSQL로 기업 분석 캐싱, OpenAI GPT-4o로 분석·생성·자가진단, Streamlit으로 5단계 대화형 UI를 구현한다.
`cover_letter/` 서비스 모듈, `frontend/` Streamlit 앱, `db/migrations/` 마이그레이션 스크립트를 신규 추가한다.

---

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: openai (LLM), streamlit (UI), PyMuPDF (PDF 파싱), python-docx (DOCX 파싱), psycopg2-binary (DB — 기존 사용 중)
**Storage**: PostgreSQL 15 (기존 컨테이너 재사용), JSONB for flexible fields
**Testing**: pytest (기존 패턴 유지), `tests/test_cover_letter_*.py`
**Target Platform**: 로컬 Docker Compose (단일 사용자 MVP)
**Project Type**: web-service (Streamlit) + service library (`cover_letter/`)
**Performance Goals**: 기업 분석 캐시 히트 시 응답 < 5초, 답변 초안 생성 < 30초
**Constraints**: 단일 사용자 MVP, 한국어 전용, 이미지 스캔 PDF 제외
**Scale/Scope**: 1 사용자, ~10개 기업, ~50개 문항, 로컬 실행

---

## Constitution Check

*GATE: Phase 0 리서치 전 평가 → Phase 1 설계 후 재평가*

**TrendOps Constitution v1.1.0 gates:**

- [x] **MLOps-First**: OpenAI API 서빙, Streamlit UI 배포, Docker 컨테이너화, 환경 변수 기반 모델 교체 — MLOps 서빙·배포 파이프라인 경험에 직접 기여
- [x] **GitHub Flow**: 브랜치 `001-cover-letter-automation`은 `main`에서 분기, PR 대상 `main`
- [x] **ADR 초안**: `docs/decisions/20260409-cover-letter-tech-stack.md` 생성 예정 (Phase 2 구현 전 필수)
- [x] **Container-First**: `Dockerfile.cover-letter` 신규 추가 계획 (Phase 2에서 작성)
- [x] **MVP-First**: 단일 사용자 로컬 Docker Compose, 외부 배포·인증 없음
- [x] **Code Minimalism**: 서비스 5개 파일, ORM 없이 직접 psycopg2, 추상화 최소화
- [x] **Code Review 계획**: Phase 4 마무리 단계에서 공통 LLM 호출 로직 추출 검토

**Post-Design 재평가**: ✅ 모든 게이트 통과. 설계 결과물(data-model, contracts)이 헌법 원칙과 충돌 없음.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-cover-letter-automation/
├── spec.md              ← 기능 명세
├── plan.md              ← 이 파일
├── research.md          ← Phase 0 산출물 (기술 결정 7개)
├── data-model.md        ← Phase 1 산출물 (6개 엔티티 + SQL)
├── quickstart.md        ← Phase 1 산출물 (로컬 실행 가이드)
├── contracts/
│   └── service-interfaces.md  ← Phase 1 산출물 (5개 서비스 시그니처)
└── tasks.md             ← Phase 2 산출물 (/speckit.tasks 명령으로 생성)
```

### Source Code (repository root)

```text
TrendOps/
├── cover_letter/                  # 자소서 서비스 비즈니스 로직 (신규)
│   ├── __init__.py
│   ├── models.py                  # Experience, WritingStyle, MappingEntry 등 dataclass
│   ├── llm_client.py              # OpenAI API 호출 공통 모듈 (환경 변수 기반)
│   ├── prompts/                   # 프롬프트 템플릿 파일
│   │   ├── extract_profile.txt
│   │   ├── analyze_company.txt
│   │   ├── analyze_question.txt
│   │   ├── generate_mapping.txt
│   │   ├── generate_answer.txt
│   │   └── self_diagnosis.txt
│   ├── profile_service.py         # 파일 파싱, LLM 프로필 추출, DB 저장
│   ├── company_service.py         # 기업·직무 분석, 7일 캐싱
│   ├── question_service.py        # 문항 분석
│   ├── mapping_service.py         # 매핑 테이블 생성, 중복 검증
│   └── generation_service.py      # 답변 생성, 글자 수 루프(최대 3회), 자가진단
│
├── frontend/                      # Streamlit UI (신규)
│   └── cover_letter_app.py        # 단일 앱 파일, st.session_state 5단계 위자드
│
├── db/
│   ├── __init__.py
│   ├── db_news.py                 # 기존 뉴스 DB 쿼리 (변경 없음)
│   ├── db_cover_letter.py         # 자소서 서비스 DB 쿼리 (신규)
│   └── migrations/
│       └── 001_cover_letter_schema.sql  # 신규 테이블 DDL (신규)
│
├── docs/
│   └── decisions/
│       └── 20260409-cover-letter-tech-stack.md  # ADR (신규, Phase 2 전 필수)
│
├── tests/
│   ├── test_cover_letter_profile.py    # 신규
│   ├── test_cover_letter_mapping.py    # 신규
│   └── test_cover_letter_generation.py # 신규
│
├── Dockerfile.cover-letter        # 신규
└── docker-compose.yml             # cover-letter 서비스 추가 예정
```

**Structure Decision**: 기존 `crawling/`, `db/` 패턴을 따라 `cover_letter/` 서비스 모듈 추가.
Streamlit 앱은 `frontend/`에 단일 파일로 구성하여 복잡도 최소화.

---

## Implementation Phases

### Phase 1: 기반 설정 (Foundation)

**목표**: DB 스키마, 공통 모듈, ADR 작성

| 작업 | 파일 | 설명 |
|------|------|------|
| DB 마이그레이션 스크립트 작성 | `db/migrations/001_cover_letter_schema.sql` | 6개 테이블 DDL |
| DB 쿼리 모듈 작성 | `db/db_cover_letter.py` | CRUD 함수 |
| 데이터 모델 정의 | `cover_letter/models.py` | dataclass 5개 |
| LLM 클라이언트 | `cover_letter/llm_client.py` | OpenAI SDK 래퍼, env var 관리 |
| 프롬프트 템플릿 | `cover_letter/prompts/*.txt` | 6개 프롬프트 파일 |
| ADR 작성 | `docs/decisions/20260409-cover-letter-tech-stack.md` | **PR 병합 필수 선행 조건** |
| Dockerfile 작성 | `Dockerfile.cover-letter` | python:3.13-slim 기반 |

**완료 조건**: `psql`에서 6개 테이블 생성 확인, `llm_client.py` 단독 호출 성공

---

### Phase 2: 프로필 서비스 (User Story P1)

**목표**: 파일 파싱 + LLM 프로필 추출 + 확인 저장

| 작업 | 파일 | 설명 |
|------|------|------|
| 파일 파서 구현 | `cover_letter/profile_service.py` | PyMuPDF, python-docx, TXT |
| 프로필 추출 | `cover_letter/profile_service.py` | `extract_profile()`, LLM 호출 |
| 프로필 저장/로드 | `cover_letter/profile_service.py` | `save_profile()`, `load_profile()` |
| Streamlit 스텝 0 | `frontend/cover_letter_app.py` | 파일 업로드 UI, 프로필 검토/수정 |
| 단위 테스트 | `tests/test_cover_letter_profile.py` | 파서, 추출, 저장 |

**완료 조건**: PDF·DOCX·TXT 업로드 → 프로필 요약 표시 → 수정 → DB 저장 확인

---

### Phase 3: 기업·직무·문항 분석 (User Story P2)

**목표**: 웹 검색 + 캐싱 + LLM 분석

| 작업 | 파일 | 설명 |
|------|------|------|
| 기업 분석 + 캐싱 | `cover_letter/company_service.py` | `get_or_analyze_company()`, 7일 캐시 |
| 직무 분석 | `cover_letter/company_service.py` | `analyze_job()` |
| 문항 분석 | `cover_letter/question_service.py` | `analyze_question()`, target_char 자동 계산 |
| Streamlit 스텝 1~2 | `frontend/cover_letter_app.py` | 기업/직무 입력, 문항 입력 UI |

**완료 조건**: 동일 기업 재입력 시 캐시 히트(< 5초), 문항 분석 결과 표시

---

### Phase 4: 매핑 테이블 (User Story P3)

**목표**: LLM 적합도 평가 + 중복 경고 + 확정 저장

| 작업 | 파일 | 설명 |
|------|------|------|
| 매핑 생성 | `cover_letter/mapping_service.py` | `generate_mapping()`, score≥3 필터 |
| 중복 검증 | `cover_letter/mapping_service.py` | `validate_duplicates()` |
| 매핑 저장 | `cover_letter/mapping_service.py` | `save_mapping()` |
| Streamlit 스텝 3 | `frontend/cover_letter_app.py` | 매핑 테이블 편집 UI, 중복 경고 표시 |
| 단위 테스트 | `tests/test_cover_letter_mapping.py` | 중복 검증 로직 |

**완료 조건**: 매핑 테이블 표시, 동일 경험 동일 usage_type 중복 시 경고 메시지 확인

---

### Phase 5: 답변 생성 + 자가진단 (User Story P4)

**목표**: 답변 초안, 글자 수 제어 루프, AI 자가진단

| 작업 | 파일 | 설명 |
|------|------|------|
| 답변 생성 + 글자 수 루프 | `cover_letter/generation_service.py` | `generate_answer()`, 최대 3회 재시도 |
| 자가진단 | `cover_letter/generation_service.py` | `run_self_diagnosis()`, JSON 출력 |
| 진단 반영 재생성 | `cover_letter/generation_service.py` | `apply_diagnosis_and_regenerate()` |
| 답변 저장 | `cover_letter/generation_service.py` | `confirm_draft()` |
| Streamlit 스텝 4 | `frontend/cover_letter_app.py` | 초안 표시, 진단 결과, 수정 지시 입력 |
| 단위 테스트 | `tests/test_cover_letter_generation.py` | 글자 수 루프, 자가진단 |

**완료 조건**: 글자 수 범위 자동 조정 확인, 자가진단 문제 목록 표시, 수동 수정 지시 반영

---

### Phase 6: 통합 및 마무리

**목표**: 전체 플로우 통합 테스트, 코드리뷰, docker-compose 연동

| 작업 | 설명 |
|------|------|
| `docker-compose.yml` 업데이트 | `cover-letter` 서비스 추가 (Streamlit 포트 8501) |
| `.env.example` 업데이트 | `OPENAI_API_KEY`, `OPENAI_MODEL` 항목 추가 |
| E2E 시나리오 테스트 | US1→US2→US3→US4 전체 흐름 수동 검증 |
| 코드리뷰 (헌법 IV) | 공통 LLM 호출 로직 `llm_client.py` 집중 여부 확인, 중복 제거 |
| ADR 최종화 | `docs/decisions/20260409-cover-letter-tech-stack.md` 상태 → 승인 |
| pre-commit 통과 | `pre-commit run --all-files` |

---

## Constitution Check (Post-Design 재평가)

| 원칙 | 상태 | 근거 |
|------|------|------|
| MLOps-First | ✅ | Docker 서빙, OpenAI API 환경 변수 교체로 모델 스왑 가능, 실제 배포 경험 |
| GitHub Flow | ✅ | `001-cover-letter-automation` ← main, PR → main |
| ADR 초안 | ✅ | Phase 1에서 작성 예정, PR 병합 선행 조건으로 명시 |
| Container-First | ✅ | `Dockerfile.cover-letter` Phase 1에서 작성 |
| MVP-First | ✅ | 단일 사용자, 로컬 Docker, 인증 없음 |
| Code Minimalism | ✅ | 서비스 5파일, ORM 없음, 클래스 미사용 |
| Code Review 계획 | ✅ | Phase 6에서 `llm_client.py` 중복 제거 검토 |
