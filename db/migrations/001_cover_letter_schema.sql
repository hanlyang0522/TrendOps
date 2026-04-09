-- Migration: 001_cover_letter_schema.sql
-- 자소서 작성 자동화 서비스 DB 스키마
-- 6개 엔티티: user_profile, company_analysis, job_analysis, question, mapping_table, cover_letter_draft

-- ============================================================
-- 1. UserProfile
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profile (
    id              SERIAL PRIMARY KEY,
    experiences     JSONB NOT NULL DEFAULT '[]',
    -- [{"key": "exp_01", "title": "프로젝트명", "period": "2024.01~2024.06",
    --   "description": "...", "competencies": ["문제해결", "Python"]}]
    competencies    JSONB NOT NULL DEFAULT '[]',
    -- ["문제해결", "데이터 분석", "팀 협업"]
    writing_style   JSONB NOT NULL DEFAULT '{}',
    -- {"sentence_length": "medium", "tone": "formal",
    --  "expression_patterns": ["..."], "avoid_patterns": ["..."]}
    source_files    TEXT[] DEFAULT '{}',
    confirmed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. CompanyAnalysis
-- ============================================================
CREATE TABLE IF NOT EXISTS company_analysis (
    id                  SERIAL PRIMARY KEY,
    company_name        VARCHAR(200) NOT NULL UNIQUE,
    overview            TEXT,
    culture_and_values  TEXT,
    industry_trends     TEXT,
    competitive_edge    TEXT,
    news_summary        TEXT,
    dart_summary        TEXT,
    news_updated_at     TIMESTAMPTZ,
    source_urls         TEXT[] DEFAULT '{}',
    user_overrides      JSONB DEFAULT '{}',
    analyzed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_analysis_name ON company_analysis(company_name);
CREATE INDEX IF NOT EXISTS idx_company_analysis_date ON company_analysis(analyzed_at);

-- ============================================================
-- 3. JobAnalysis
-- ============================================================
CREATE TABLE IF NOT EXISTS job_analysis (
    id                      SERIAL PRIMARY KEY,
    company_analysis_id     INT NOT NULL REFERENCES company_analysis(id) ON DELETE CASCADE,
    job_title               VARCHAR(200) NOT NULL,
    responsibilities        TEXT,
    pain_points             TEXT,
    expected_competencies   TEXT[] DEFAULT '{}',
    future_direction        TEXT,
    analyzed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_overrides          JSONB DEFAULT '{}',
    UNIQUE(company_analysis_id, job_title)
);

-- ============================================================
-- 4. Question
-- ============================================================
CREATE TABLE IF NOT EXISTS question (
    id                      SERIAL PRIMARY KEY,
    job_analysis_id         INT NOT NULL REFERENCES job_analysis(id) ON DELETE CASCADE,
    text                    TEXT NOT NULL,
    char_limit              INT,
    target_char_min         INT GENERATED ALWAYS AS (
                                CASE WHEN char_limit IS NOT NULL
                                THEN ROUND(char_limit * 0.90) ELSE NULL END
                            ) STORED,
    target_char_max         INT GENERATED ALWAYS AS (
                                CASE WHEN char_limit IS NOT NULL
                                THEN ROUND(char_limit * 0.95) ELSE NULL END
                            ) STORED,
    measured_competencies   TEXT[] DEFAULT '{}',
    expected_level          TEXT,
    analyzed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_overrides          JSONB DEFAULT '{}'
);

-- ============================================================
-- 5. MappingTable
-- ============================================================
CREATE TABLE IF NOT EXISTS mapping_table (
    id              SERIAL PRIMARY KEY,
    question_id     INT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    entries         JSONB NOT NULL DEFAULT '[]',
    -- [{"experience_key": "exp_01", "usage_type": "primary",
    --   "relevance_score": 4, "rationale": "..."}]
    confirmed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mapping_question ON mapping_table(question_id);

-- ============================================================
-- 6. CoverLetterDraft
-- ============================================================
CREATE TABLE IF NOT EXISTS cover_letter_draft (
    id                      SERIAL PRIMARY KEY,
    question_id             INT NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    mapping_table_id        INT REFERENCES mapping_table(id),
    version                 INT NOT NULL DEFAULT 1,
    text                    TEXT NOT NULL,
    char_count              INT NOT NULL GENERATED ALWAYS AS (LENGTH(text)) STORED,
    self_diagnosis_issues   JSONB DEFAULT '[]',
    -- [{"issue": "AI특유표현", "text": "...", "suggestion": "..."}]
    generation_params       JSONB DEFAULT '{}',
    -- {"model": "gemini-2.5-pro", "attempt": 1, "user_instruction": "더 구체적으로"}
    status                  VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- 'draft' | 'self_diagnosed' | 'confirmed'
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_draft_question ON cover_letter_draft(question_id);
CREATE INDEX IF NOT EXISTS idx_draft_status ON cover_letter_draft(status);
