"""매핑 테이블 생성·검증·저장 서비스.

LLM이 지원자 경험과 자소서 문항의 적합도를 1~5점으로 평가하며,
score≥3인 경험만 매핑 결과에 포함합니다.
"""

import json
import pathlib

from cover_letter import llm_client
from cover_letter.db import get_conn as _get_conn

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "mapping_generate.txt"


def generate_mapping(
    question_id: int,
    question_text: str,
    measured_competencies: list[str],
    expected_level: str,
    company_name: str,
    job_title: str,
    culture_and_values: str,
    experiences: list[dict],
) -> list[dict]:
    """LLM으로 문항-경험 매핑 생성. score≥3인 경험만 반환.

    Args:
        question_id: 문항 ID (현재 미사용, 향후 캐싱용)
        question_text: 문항 텍스트
        measured_competencies: 측정 역량 목록
        expected_level: 기대 수준
        company_name: 기업명
        job_title: 직무명
        culture_and_values: 기업 문화·가치관
        experiences: 지원자 경험 목록 ({"key", "title", "description", ...})

    Returns:
        매핑 항목 목록:
        [{"experience_key": str, "usage_type": str, "relevance_score": int, "rationale": str}]
        실패 시 빈 리스트 반환.
    """
    if not experiences:
        return []

    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    system_part, user_part = prompt_template.split("## User\n", 1)
    system_text = system_part.replace("## System\n", "", 1).strip()

    user_text = user_part.format(
        question_text=question_text,
        measured_competencies=", ".join(measured_competencies),
        expected_level=expected_level,
        company_name=company_name,
        job_title=job_title,
        culture_and_values=culture_and_values,
        experiences_json=json.dumps(experiences, ensure_ascii=False, indent=2),
    )

    try:
        raw = llm_client.call(prompt=user_text, tier="pro", system=system_text)
        # JSON 코드블록 래핑 제거 (모델이 포함할 경우)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        entries = json.loads(raw)
    except Exception:
        return []

    if not isinstance(entries, list):
        return []

    # score < 3 필터링
    return [
        e for e in entries if isinstance(e, dict) and e.get("relevance_score", 0) >= 3
    ]


def validate_duplicates(all_mappings: list[dict]) -> list[dict]:
    """동일 경험×usage_type 조합이 복수 문항에서 반복되면 경고 반환.

    Args:
        all_mappings: 동일 지원 세션의 전체 매핑 목록.
            각 항목: {"question_id": int, "question_text": str, "entries": list[dict]}

    Returns:
        경고 목록:
        [{"experience_key": str, "usage_type": str, "questions": [{"id": int, "text": str}]}]
    """
    # (experience_key, usage_type) → [(question_id, question_text)]
    seen: dict[tuple[str, str], list[dict]] = {}

    for mapping in all_mappings:
        q_id = mapping.get("question_id")
        q_text = mapping.get("question_text", "")
        for entry in mapping.get("entries", []):
            key = (entry.get("experience_key", ""), entry.get("usage_type", ""))
            if key not in seen:
                seen[key] = []
            seen[key].append({"id": q_id, "text": q_text})

    warnings = []
    for (exp_key, usage_type), questions in seen.items():
        if len(questions) > 1:
            warnings.append(
                {
                    "experience_key": exp_key,
                    "usage_type": usage_type,
                    "questions": questions,
                }
            )
    return warnings


def save_mapping(question_id: int, entries: list[dict]) -> int:
    """매핑 결과를 DB에 저장.

    Args:
        question_id: 문항 ID
        entries: 매핑 항목 목록

    Returns:
        생성된 mapping_table.id
    """
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mapping_table (question_id, entries)
                VALUES (%s, %s)
                RETURNING id
                """,
                (question_id, json.dumps(entries, ensure_ascii=False)),
            )
            row = cur.fetchone()
            return int(row[0])
    finally:
        conn.close()
