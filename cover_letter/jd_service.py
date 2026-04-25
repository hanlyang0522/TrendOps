"""JD(직무기술서) 서비스 — 수집·저장·로드·역량 추출."""

import json
import pathlib

from cover_letter import llm_client
from cover_letter.collectors.jd_crawler import crawl_jd
from cover_letter.db import get_conn as _get_conn

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "question_analysis.txt"


def collect_jd(company_name: str, job_title: str) -> dict:
    """기업명·직무명으로 JD 자동 수집.

    Args:
        company_name: 기업명 (예: "카카오")
        job_title: 직무명 (예: "백엔드 개발자")

    Returns:
        {
            "success": bool,
            "text": str | None,
            "source_url": str,
            "source_type": str,   # 'firecrawl' | 'pdf' | 'manual'
            "error_reason": str,  # 실패 사유(성공 시 빈 문자열)
            "required_competencies": list[str],
        }
    """
    result = crawl_jd(company_name, job_title)

    competencies: list[str] = []
    if result["success"] and result["text"]:
        try:
            competencies = extract_required_competencies(result["text"])
        except Exception:
            competencies = []

    return {
        **result,
        "error_reason": result.get("error_reason", ""),
        "required_competencies": competencies,
    }


def extract_required_competencies(jd_text: str) -> list[str]:
    """JD 텍스트에서 LLM으로 요구 역량 목록 추출.

    Args:
        jd_text: JD 원문 텍스트

    Returns:
        역량 키워드 목록 (예: ["Python", "협업", "문제해결력"])
    """
    prompt = (
        "다음 직무기술서에서 요구하는 핵심 역량과 기술을 JSON 배열로 반환하라.\n"
        '예: ["Python", "문제해결력", "팀워크"]\n\n'
        f"직무기술서:\n{jd_text[:3000]}"
    )
    raw = llm_client.call(prompt, tier="flash")
    try:
        # 마크다운 코드블록 제거
        clean = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        data = json.loads(clean)
        if isinstance(data, list):
            return [str(item) for item in data]
    except Exception:
        pass
    return []


def save_jd(job_analysis_id: int, jd_data: dict) -> int:
    """JD 데이터를 DB에 저장(없으면 INSERT, 있으면 UPDATE).

    Args:
        job_analysis_id: job_analysis 테이블 FK
        jd_data: collect_jd 반환값

    Returns:
        저장된 jd.id
    """
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jd (
                    job_analysis_id, raw_text, source_url, source_type,
                    required_competencies
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (job_analysis_id)
                DO UPDATE SET
                    raw_text = EXCLUDED.raw_text,
                    source_url = EXCLUDED.source_url,
                    source_type = EXCLUDED.source_type,
                    required_competencies = EXCLUDED.required_competencies,
                    collected_at = NOW()
                RETURNING id
                """,
                (
                    job_analysis_id,
                    jd_data.get("text"),
                    jd_data.get("source_url", ""),
                    jd_data.get("source_type", "manual"),
                    jd_data.get("required_competencies", []),
                ),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0
    finally:
        conn.close()


def load_jd(job_analysis_id: int) -> dict | None:
    """DB에서 JD 레코드 로드.

    Args:
        job_analysis_id: job_analysis 테이블 FK

    Returns:
        {
            "id": int, "raw_text": str, "source_url": str,
            "source_type": str, "required_competencies": list[str],
            "user_overrides": dict, "collected_at": str
        }
        레코드 없으면 None.
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, raw_text, source_url, source_type,
                       required_competencies, user_overrides, collected_at
                FROM jd
                WHERE job_analysis_id = %s
                """,
                (job_analysis_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "raw_text": row[1],
                "source_url": row[2],
                "source_type": row[3],
                "required_competencies": row[4] or [],
                "user_overrides": row[5] or {},
                "collected_at": str(row[6]),
            }
    finally:
        conn.close()
