"""문항 분석 서비스 — LLM 기반 문항 역량 분석 및 DB 저장."""

import json
import pathlib

from cover_letter import llm_client
from cover_letter.db import get_conn as _get_conn

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "question_analysis.txt"


def analyze_question(
    job_analysis_id: int,
    question_text: str,
    char_limit: int | None = None,
) -> dict:
    """LLM을 통해 문항이 측정하는 역량과 기대 수준을 분석하고 DB에 저장.

    Args:
        job_analysis_id: 연결된 직무 분석 ID
        question_text: 자소서 문항 원문
        char_limit: 글자 수 제한 (없으면 None)

    Returns:
        question 레코드에 해당하는 dict
        {
            "id": int, "text": str, "char_limit": int | None,
            "target_char_min": int | None, "target_char_max": int | None,
            "measured_competencies": list[str], "expected_level": str
        }
    """
    conn = _get_conn()
    try:
        # 기업명·직무명 조회
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT ja.job_title, ca.company_name
                FROM job_analysis ja
                JOIN company_analysis ca ON ca.id = ja.company_analysis_id
                WHERE ja.id = %s
                """,
                (job_analysis_id,),
            )
            row = cur.fetchone()

        if row is None:
            raise ValueError(f"job_analysis id={job_analysis_id} 없음")

        job_title, company_name = row[0], row[1]

        # 프롬프트 빌드
        prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
        system = ""
        user = prompt_template
        if "## System\n" in prompt_template and "## User\n" in prompt_template:
            parts = prompt_template.split("## User\n", 1)
            system = parts[0].replace("## System\n", "").strip()
            user = parts[1].strip()

        user = (
            user.replace("{company_name}", company_name)
            .replace("{job_title}", job_title)
            .replace("{question_text}", question_text)
            .replace("{char_limit}", str(char_limit) if char_limit else "제한 없음")
        )

        raw = llm_client.call(user, tier="flash", system=system)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError:
            analysis = {"measured_competencies": [], "expected_level": ""}

        # DB 저장
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO question
                    (job_analysis_id, text, char_limit,
                     measured_competencies, expected_level)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, target_char_min, target_char_max
                """,
                (
                    job_analysis_id,
                    question_text,
                    char_limit,
                    analysis.get("measured_competencies", []),
                    analysis.get("expected_level", ""),
                ),
            )
            q_row = cur.fetchone()
            q_id, target_min, target_max = q_row[0], q_row[1], q_row[2]

        return {
            "id": q_id,
            "text": question_text,
            "char_limit": char_limit,
            "target_char_min": target_min,
            "target_char_max": target_max,
            "measured_competencies": analysis.get("measured_competencies", []),
            "expected_level": analysis.get("expected_level", ""),
        }
    finally:
        conn.close()
