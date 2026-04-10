# Implementation Plan: 자소서 작성 자동화 서비스

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-10 | **Spec**: [spec.md](spec.md)
**Input**: LLM 기반 자소서 자동 작성 서비스 — 기업 3-소스 분석(DART·뉴스·홈페이지), JD 자동 수집(Firecrawl), 경험-문항 매핑, 답변 생성·자가진단·환각 방지, Streamlit UI

## Summary

취준생이 기업명·직무를 입력하면 DART API(사업보고서), Naver News, Firecrawl(인재상·JD 자동 검색)로 기업 정보와 JD를 수집하고, 사용자 포트폴리오(TXT·MD·DOCX)에서 추출한 경험 프로필과 매핑 테이블을 생성하여 자소서 초안을 Gemini Pro로 생성한다. 생성 직후 환각 방지 검증(규칙 기반 + LLM 보조)과 AI 자가진단(Gemini Pro Thinking)을 수행하며, Streamlit 5-step 위저드 UI로 전체 워크플로를 진행한다.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: google-genai (LLM 3-tier), streamlit (UI), psycopg2-binary (DB), dart-fss (DART 사업보고서), firecrawl-py (JD·인재상 크롤링), pdfminer.six (JD PDF 파싱), python-docx (DOCX 포트폴리오 파싱), requests + beautifulsoup4 (보조 스크래핑)
**Storage**: PostgreSQL 15 (Docker 컨테이너, 기존 재사용)
**Testing**: pytest (`tests/` 디렉토리 기존 구조)
**Target Platform**: 로컬 Docker Compose (단일 사용자 MVP)
**Project Type**: web-service (Streamlit 프론트엔드 + Python 서비스 레이어 + PostgreSQL)
**Performance Goals**: 기업 분석(캐시 미스) < 30초, 캐시 히트 < 3초, 답변 초안 생성 < 20초
**Constraints**: 단일 사용자, 한국어 전용, DART_API_KEY·FIRECRAWL_API_KEY·GEMINI_API_KEY 필수
**Scale/Scope**: 1 사용자, 5-step 워크플로, 7개 DB 엔티티(JD 엔티티 포함), 8개 서비스 모듈

## Constitution Check

*GATE: Phase 0 연구 전 통과 필수. Phase 1 설계 후 재확인.*

**TrendOps Constitution v1.1.0 — 통과 기준:**

- [x] **MLOps-First**: Gemini 3-tier 라우팅, DART·Firecrawl 멀티소스 파이프라인, 환각 방지 검증 루프 — LLM 서빙 파이프라인 경험 직접 기여
- [x] **GitHub Flow**: `main`에서 `001-cover-letter-automation` 분기, PR 대상 `main`
- [x] **ADR 초안**: `docs/decisions/` 에 4개 ADR 작성 완료 (llm-api, db-schema, streamlit-wizard, company-3-source)
- [x] **Container-First**: `Dockerfile.cover-letter` 기존 존재, docker-compose에 `cover-letter` 서비스 정의 예정
- [x] **MVP-First**: 단일 로컬 사용자, Streamlit MVP, 클라우드 확장은 Future
- [x] **Code Minimalism**: 서비스 레이어 함수형(클래스 없음), 추상화 없이 직접 호출
- [x] **Code Review 계획**: tasks.md 마지막 태스크로 코드리뷰·리팩토링 단계 포함 예정

**Constitution 위반 없음 — Phase 0 진행 승인**

## Project Structure

### Documentation (this feature)

```text
specs/001-cover-letter-automation/
├── plan.md              # 이 파일
├── research.md          # Phase 0 산출물 (기결정 사항 포함, 신규 결정 추가)
├── data-model.md        # Phase 1 산출물 (JD 엔티티 추가)
├── quickstart.md        # Phase 1 산출물 (환경변수·의존성 업데이트)
├── contracts/
│   └── service-interfaces.md  # Phase 1 산출물 (JD 수집·환각 방지 시그니처 추가)
└── tasks.md             # Phase 2 산출물 (/speckit.tasks 명령 — plan 단계에서 미생성)
```

### Source Code (repository root)

```text
cover_letter/                    # 서비스 레이어
├── __init__.py
├── llm_client.py                # Gemini 3-tier 라우팅
├── profile_service.py           # 포트폴리오 파싱(TXT·MD·DOCX)·프로필 추출·DB 저장
├── company_service.py           # 기업 분석 캐시·3-소스 수집 오케스트레이션
├── question_service.py          # 문항 저장·LLM 분석
├── mapping_service.py           # 경험-문항 매핑·중복 검증
├── generation_service.py        # 답변 생성·글자수 루프·자가진단·환각 방지 검증
├── jd_service.py                # JD 자동 수집 (신규) — Firecrawl·pdfminer·수기입력
├── prompts/
│   ├── profile_extract.txt
│   ├── company_analysis.txt
│   ├── question_analysis.txt
│   ├── mapping_generate.txt
│   ├── answer_generate.txt
│   ├── self_diagnosis.txt
│   └── hallucination_check.txt  # 신규 — 환각 방지 LLM 보조 판정 프롬프트
└── collectors/
    ├── __init__.py
    ├── dart_collector.py        # DART API 사업보고서
    ├── naver_collector.py       # Naver News + Firecrawl fallback
    ├── website_crawler.py       # 공식 홈페이지 인재상·문화
    └── jd_crawler.py            # 신규 — Firecrawl JD 자동 검색·수집

frontend/
└── cover_letter_app.py          # Streamlit 5-step 위저드 (padding·자동 확장 UI)

db/
└── migrations/
    ├── 001_cover_letter_schema.sql   # 기존 6개 엔티티
    └── 002_add_jd_entity.sql         # 신규 — JD 엔티티 추가

tests/
├── test_cover_letter_company.py
├── test_cover_letter_generation.py
├── test_cover_letter_mapping.py
├── test_cover_letter_profile.py
└── test_cover_letter_jd.py      # 신규 — JD 수집·파싱 테스트
```

## Complexity Tracking

> Constitution Check 위반 없음 — 이 섹션 해당 없음
