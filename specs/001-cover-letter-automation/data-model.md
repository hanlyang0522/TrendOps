# Data Model: 자소서 작성 자동화 서비스

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-10 (업데이트)
**Source**: spec.md Key Entities + research.md 결정 사항 (JD 엔티티 추가, CompanyAnalysis 필드 추가)

---

## 엔티티 관계 요약

```
UserProfile
    │
    ├─── (경험 매핑 시 참조)
    │
CompanyAnalysis ──── JobAnalysis ──── JD (신규) ──── Question ──── MappingTable ──── CoverLetterDraft
                                         │                │
                                         └── (문항 분석)  └── (경험 배정)
```

---

## 엔티티 1: UserProfile

**목적**: 사용자의 경험·역량·문체를 저장하는 단일 프로필. 모든 자소서 세션에서 재사용.

```sql
CREATE TABLE user_profile (
    id              SERIAL PRIMARY KEY,
    experiences     JSONB NOT NULL DEFAULT '[]',
    -- [{"key": "exp_01", "title": "프로젝트명", "period": "2024.01~2024.06",
    --   "description": "...", "competencies": ["문제해결", "Python"]}]
    competencies    JSONB NOT NULL DEFAULT '[]',
    -- ["문제해결", "데이터 분석", "팀 협업"]
    writing_style   JSONB NOT NULL DEFAULT '{}',
    -- {"sentence_length": "medium",  -- short/medium/long
    --  "tone": "formal",             -- formal/semi-formal/casual
    --  "expression_patterns": ["..."],
    --  "avoid_patterns": ["~에 기여하고자", ...]}
    source_files    TEXT[] DEFAULT '{}',
    -- 업로드된 파일명 목록
    confirmed_at    TIMESTAMPTZ,
    -- NULL이면 미확인 상태 (DB 비반영)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**검증 규칙**:
- `experiences` 배열의 각 항목은 `key`, `title`, `description` 필드 필수
- `confirme_at` IS NOT NULL인 레코드만 답변 생성에 사용
- MVP: 단일 사용자이므로 id=1 레코드를 upsert 방식으로 유지

**상태 전이**:
```
업로드 완료 → confirmed_at=NULL (임시 상태)
사용자 확인 → confirmed_at=NOW() (저장 완료)
파일 추가 업로드 → confirmed_at=NULL (재검토 필요)
```

---

## 엔티티 2: CompanyAnalysis

**목적**: 기업 분석 결과 캐시. 7일 유효, 이후 재분석 필요.

```sql
CREATE TABLE company_analysis (
    id                  SERIAL PRIMARY KEY,
    company_name        VARCHAR(200) NOT NULL UNIQUE,
    overview            TEXT,          -- 기업 개요 (주요 사업·제품·서비스)
    culture_and_values  TEXT,          -- 인재상·기업 문화
    industry_trends     TEXT,          -- 업계 동향 (최근 3년)
    competitive_edge    TEXT,          -- 경쟁사 대비 특장점
    news_summary        TEXT,          -- 최신 뉴스 요약 (별도 갱신)
    dart_summary        TEXT,          -- DART 사업보고서 요약 (주요 제품·시장현황·연구개발)
    news_updated_at     TIMESTAMPTZ,   -- 뉴스만 별도 갱신 시각
    source_urls         TEXT[] DEFAULT '{}',
    user_overrides      JSONB DEFAULT '{}',
    -- 사용자가 수정한 필드 {"overview": "수정된 내용", ...}
    analyzed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_company_analysis_name ON company_analysis(company_name);
CREATE INDEX idx_company_analysis_date ON company_analysis(analyzed_at);
```

**캐시 유효성 판단**:
- `NOW() - analyzed_at < INTERVAL '7 days'` → 캐시 히트 (뉴스만 재검색)
- `NOW() - analyzed_at >= INTERVAL '7 days'` → 전체 재분석

---

## 엔티티 3: JobAnalysis

**목적**: 특정 기업의 특정 직무에 대한 분석. 기업 분석과 1:N 관계.

```sql
CREATE TABLE job_analysis (
    id                      SERIAL PRIMARY KEY,
    company_analysis_id     INT NOT NULL REFERENCES company_analysis(id) ON DELETE CASCADE,
    job_title               VARCHAR(200) NOT NULL,
    responsibilities        TEXT,        -- 주요 업무
    pain_points             TEXT,        -- 직무 페인 포인트
    expected_competencies   TEXT[] DEFAULT '{}',
    future_direction        TEXT,        -- 미래 전망
    analyzed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_overrides          JSONB DEFAULT '{}',
    UNIQUE(company_analysis_id, job_title)
);
```

---

## 엔티티 4: Question

**목적**: 자소서 문항 + 문항 분석 결과. JobAnalysis와 N:1 관계.

```sql
CREATE TABLE question (
    id                      SERIAL PRIMARY KEY,
    job_analysis_id         INT NOT NULL REFERENCES job_analysis(id) ON DELETE CASCADE,
    text                    TEXT NOT NULL,           -- 문항 원문
    char_limit              INT,                     -- 글자 수 제한 (NULL이면 무제한)
    target_char_min         INT GENERATED ALWAYS AS  -- 90% 하한 (자동 계산)
                            (CASE WHEN char_limit IS NOT NULL
                             THEN ROUND(char_limit * 0.90) ELSE NULL END) STORED,
    target_char_max         INT GENERATED ALWAYS AS  -- 95% 상한 (자동 계산)
                            (CASE WHEN char_limit IS NOT NULL
                             THEN ROUND(char_limit * 0.95) ELSE NULL END) STORED,
    measured_competencies   TEXT[] DEFAULT '{}',     -- 문항이 측정하려는 역량
    expected_level          TEXT,                    -- 신입 기준 기대 수준
    analyzed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_overrides          JSONB DEFAULT '{}'
);
```

**참고**: `target_char_min`, `target_char_max`는 Generated Column으로 자동 계산되어
        application 코드에서 별도 계산 불필요.

---

## 엔티티 5: MappingTable

**목적**: 문항-경험 매핑 결과. Question과 1:N 관계 (동일 문항에 여러 버전 가능).

```sql
CREATE TABLE mapping_table (
    id              SERIAL PRIMARY KEY,
    question_id     INT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    entries         JSONB NOT NULL DEFAULT '[]',
    -- [{"experience_key": "exp_01",
    --   "usage_type": "primary",    -- primary|supporting|background
    --   "relevance_score": 4,       -- 1~5
    --   "rationale": "이 경험이 문항의 X 역량과 연결되는 이유"}]
    confirmed_at    TIMESTAMPTZ,     -- NULL이면 미확정
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mapping_question ON mapping_table(question_id);
```

**중복 활용 방식 검증 로직** (애플리케이션 레이어):
```python
def validate_mapping_duplicates(
    mappings: list[MappingTable],   # 동일 지원 세션의 전체 문항 매핑
) -> list[dict]:                    # 경고 목록 반환
    # experience_key + usage_type 조합이 복수 문항에서 동일하면 경고
```

---

## 엔티티 6: CoverLetterDraft

**목적**: 생성된 자소서 답변 초안. 버전 이력 보관.

```sql
CREATE TABLE cover_letter_draft (
    id                      SERIAL PRIMARY KEY,
    question_id             INT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    mapping_table_id        INT REFERENCES mapping_table(id),
    version                 INT NOT NULL DEFAULT 1,
    text                    TEXT NOT NULL,
    char_count              INT NOT NULL GENERATED ALWAYS AS (LENGTH(text)) STORED,
    self_diagnosis_issues   JSONB DEFAULT '[]',
    -- [{"issue": "AI특유표현", "text": "...", "suggestion": "..."}]
    hallucination_retries   INT NOT NULL DEFAULT 0,  -- 환각 방지 재생성 횟수 (FR-011b)
    generation_params       JSONB DEFAULT '{}',
    -- {"model": "gemini-2.5-pro", "attempt": 1, "user_instruction": "더 구체적으로"}
    status                  VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- 'draft' | 'self_diagnosed' | 'confirmed'
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_draft_question ON cover_letter_draft(question_id);
CREATE INDEX idx_draft_status ON cover_letter_draft(status);
```

**버전 이력**: 수정될 때마다 새 레코드 INSERT. confirmed 상태인 레코드가 최종 버전.

---

## 엔티티 7: JD (Job Description) — 신규 (2026-04-10)

**목적**: 기업·직무 기반으로 자동 수집된 JD(직무기술서) 저장. JobAnalysis와 1:1 관계.

```sql
CREATE TABLE jd (
    id                  SERIAL PRIMARY KEY,
    job_analysis_id     INT NOT NULL REFERENCES job_analysis(id) ON DELETE CASCADE UNIQUE,
    raw_text            TEXT,               -- 수집된 JD 원문
    source_url          TEXT,               -- 수집 출처 URL (Firecrawl 검색 결과)
    source_type         VARCHAR(20),        -- 'firecrawl' | 'pdf' | 'manual'
    required_competencies TEXT[] DEFAULT '{}', -- LLM 추출 요구 역량 (매핑 우선순위 반영)
    collected_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_overrides      JSONB DEFAULT '{}' -- 사용자 수정 내용
);

CREATE INDEX idx_jd_job_analysis ON jd(job_analysis_id);
```

**상태**:
- `source_type = 'firecrawl'`: Firecrawl API로 자동 수집
- `source_type = 'pdf'`: Firecrawl URL → pdfminer.six 추출
- `source_type = 'manual'`: 사용자 수기 텍스트 입력

**검증 규칙**:
- `raw_text IS NOT NULL` AND `LENGTH(raw_text) > 50` → 유효한 JD로 간주
- 유효하지 않으면 `source_type = 'manual'` 입력 안내

---

## DB 마이그레이션 전략

- 초기 테이블 생성 (1~6 엔티티): `db/migrations/001_cover_letter_schema.sql`
- JD 엔티티 추가 (엔티티 7): `db/migrations/002_add_jd_entity.sql`
- `Dockerfile.db-init`의 init 스크립트에서 순서대로 실행
- 기존 `news_articles` 테이블과 네임스페이스 충돌 없음

---

## Python 데이터클래스 (애플리케이션 레이어)

DB 직접 매핑 없이 `dataclasses`로 정의 (SQLAlchemy ORM 불필요 — YAGNI):

```python
# cover_letter/models.py
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Experience:
    key: str
    title: str
    description: str
    period: str = ""
    competencies: list[str] = field(default_factory=list)

@dataclass
class WritingStyle:
    sentence_length: str = "medium"  # short | medium | long
    tone: str = "formal"             # formal | semi-formal | casual
    expression_patterns: list[str] = field(default_factory=list)
    avoid_patterns: list[str] = field(default_factory=list)

@dataclass
class MappingEntry:
    experience_key: str
    usage_type: str       # primary | supporting | background
    relevance_score: int  # 1~5
    rationale: str

@dataclass
class DiagnosisIssue:
    issue: str
    text: str
    suggestion: str

@dataclass
class JD:
    job_analysis_id: int
    raw_text: str
    source_type: str      # 'firecrawl' | 'pdf' | 'manual'
    source_url: str = ""
    required_competencies: list[str] = field(default_factory=list)
```
