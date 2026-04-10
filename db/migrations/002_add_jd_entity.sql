-- Migration 002: JD 엔티티 추가 + hallucination_retries 컬럼 추가
-- 날짜: 2026-04-10
-- spec: FR-003d (JD 자동 수집), FR-011b (환각 방지 별도 카운트)

-- ============================================================
-- 7. JD (Job Description) — 기업·직무 기반 자동 수집
-- ============================================================
CREATE TABLE IF NOT EXISTS jd (
    id                      SERIAL PRIMARY KEY,
    job_analysis_id         INT NOT NULL REFERENCES job_analysis(id) ON DELETE CASCADE,
    raw_text                TEXT,
    source_url              TEXT,
    source_type             VARCHAR(20),
    -- 'firecrawl' | 'pdf' | 'manual'
    required_competencies   TEXT[] DEFAULT '{}',
    -- LLM 추출 요구 역량 (매핑 우선순위 반영)
    collected_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_overrides          JSONB DEFAULT '{}',
    UNIQUE (job_analysis_id)
);

CREATE INDEX IF NOT EXISTS idx_jd_job_analysis ON jd(job_analysis_id);

-- ============================================================
-- cover_letter_draft: hallucination_retries 컬럼 추가
-- (001 스키마가 이미 배포된 환경용)
-- ============================================================
ALTER TABLE cover_letter_draft
    ADD COLUMN IF NOT EXISTS hallucination_retries INT NOT NULL DEFAULT 0;

COMMENT ON COLUMN cover_letter_draft.hallucination_retries
    IS '환각 방지 재생성 횟수 (FR-011b). char_limit retry(MAX_RETRIES)와 별도 카운트.';
