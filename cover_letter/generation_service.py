"""답변 생성 + 글자 수 루프 + 자가진단 + 환각 방지 서비스.

글자 수 범위(target_char_min~target_char_max)를 충족할 때까지
최대 MAX_RETRIES(3)회 재생성합니다.
환각 감지 시 추가 재생성 (hallucination_retries 별도 카운트).
"""

import json
import os
import pathlib

from cover_letter import llm_client
from cover_letter.db import get_conn as _get_conn

_ANSWER_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "answer_generate.txt"
_DIAG_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "self_diagnosis.txt"
_HALLUCINATION_PROMPT_PATH = (
    pathlib.Path(__file__).parent / "prompts" / "hallucination_check.txt"
)
MAX_RETRIES = int(os.getenv("COVER_LETTER_MAX_RETRIES", "3"))


def _build_mapped_experiences_text(entries: list[dict], experiences: list[dict]) -> str:
    """매핑된 경험을 텍스트로 포맷팅."""
    lines = []
    for entry in entries:
        exp = next(
            (e for e in experiences if e.get("key") == entry.get("experience_key")),
            None,
        )
        if exp:
            lines.append(
                f"[{entry.get('usage_type', 'supporting').upper()}] {exp.get('title', '')} "
                f"(적합도: {entry.get('relevance_score', '')}/5)\n"
                f"  내용: {exp.get('description', '')}\n"
                f"  연결 이유: {entry.get('rationale', '')}"
            )
    return "\n\n".join(lines) if lines else "매핑된 경험 없음"


def generate_answer(
    question_id: int,
    question_text: str,
    char_limit: int,
    target_char_min: int,
    target_char_max: int,
    measured_competencies: list[str],
    expected_level: str,
    company_analysis: dict,
    job_analysis: dict,
    profile: dict,
    mapping_entries: list[dict],
    user_instruction: str = "",
) -> dict:
    """자기소개서 답변 생성 (글자 수 루프, 최대 MAX_RETRIES회).

    Args:
        question_id: 문항 ID
        question_text: 문항 텍스트
        char_limit: 글자 수 제한
        target_char_min: 목표 최소 글자 수
        target_char_max: 목표 최대 글자 수
        measured_competencies: 측정 역량
        expected_level: 기대 수준
        company_analysis: 기업 분석 결과 dict
        job_analysis: 직무 분석 결과 dict
        profile: 지원자 프로필 dict
        mapping_entries: 매핑 항목 목록
        user_instruction: 사용자 수동 지시 (재생성 시 반영)

    Returns:
        {
            "text": str,
            "char_count": int,
            "attempt": int,
            "in_range": bool,
        }
    """
    prompt_template = _ANSWER_PROMPT_PATH.read_text(encoding="utf-8")
    system_part, user_part = prompt_template.split("## User\n", 1)
    system_text = system_part.replace("## System\n", "", 1).strip()

    experiences = profile.get("experiences", [])
    mapped_text = _build_mapped_experiences_text(mapping_entries, experiences)

    writing_style = profile.get("writing_style", {})
    user_instruction_section = (
        f"[사용자 지시]\n{user_instruction}\n\n" if user_instruction else ""
    )

    best_text = ""
    best_attempt = 0

    for attempt in range(1, MAX_RETRIES + 1):
        user_text = user_part.format(
            question_text=question_text,
            char_limit=char_limit,
            target_char_min=target_char_min,
            target_char_max=target_char_max,
            measured_competencies=", ".join(measured_competencies),
            expected_level=expected_level,
            company_name=company_analysis.get("company_name", ""),
            job_title=job_analysis.get("job_title", ""),
            culture_and_values=company_analysis.get("culture_and_values", ""),
            competitive_edge=company_analysis.get("competitive_edge", ""),
            name=profile.get("name", ""),
            sentence_length=writing_style.get("sentence_length", "medium"),
            tone=writing_style.get("tone", "formal"),
            mapped_experiences_text=mapped_text,
            user_instruction_section=user_instruction_section,
        )

        try:
            text = llm_client.call(
                prompt=user_text, tier="pro", system=system_text
            ).strip()
        except Exception:
            text = best_text

        char_count = len(text)
        best_text = text
        best_attempt = attempt

        if target_char_min <= char_count <= target_char_max:
            break

    final_count = len(best_text)
    return {
        "text": best_text,
        "char_count": final_count,
        "attempt": best_attempt,
        "in_range": target_char_min <= final_count <= target_char_max,
    }


def run_self_diagnosis(
    draft_text: str,
    question_text: str,
    target_char_min: int,
    target_char_max: int,
    measured_competencies: list[str],
) -> list[dict]:
    """자소서 초안의 문제점 자가진단.

    Args:
        draft_text: 검토할 자소서 답변 텍스트
        question_text: 문항 텍스트
        target_char_min: 목표 최소 글자 수
        target_char_max: 목표 최대 글자 수
        measured_competencies: 측정 역량

    Returns:
        문제 목록:
        [{"issue": str, "text": str, "suggestion": str}]
        문제 없으면 빈 리스트.
    """
    prompt_template = _DIAG_PROMPT_PATH.read_text(encoding="utf-8")
    system_part, user_part = prompt_template.split("## User\n", 1)
    system_text = system_part.replace("## System\n", "", 1).strip()

    user_text = user_part.format(
        question_text=question_text,
        target_char_min=target_char_min,
        target_char_max=target_char_max,
        measured_competencies=", ".join(measured_competencies),
        char_count=len(draft_text),
        draft_text=draft_text,
    )

    try:
        raw = llm_client.call(
            prompt=user_text, tier="pro-thinking", system=system_text
        ).strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        issues = json.loads(raw)
        if not isinstance(issues, list):
            return []
        return issues
    except Exception:
        return []


def apply_diagnosis_and_regenerate(
    question_id: int,
    draft_text: str,
    diagnosis_issues: list[dict],
    user_instruction: str,
    question_text: str,
    char_limit: int,
    target_char_min: int,
    target_char_max: int,
    measured_competencies: list[str],
    expected_level: str,
    company_analysis: dict,
    job_analysis: dict,
    profile: dict,
    mapping_entries: list[dict],
) -> dict:
    """자가진단 결과 + 사용자 지시를 반영하여 답변 재생성.

    Args:
        question_id: 문항 ID
        draft_text: 기존 초안 텍스트
        diagnosis_issues: 자가진단 문제 목록
        user_instruction: 사용자 추가 지시
        (나머지 인자는 generate_answer와 동일)

    Returns:
        generate_answer와 동일한 구조의 dict.
    """
    # 진단 결과를 user_instruction에 통합
    if diagnosis_issues:
        issue_lines = "\n".join(
            f"- [{i['issue']}] \"{i['text']}\" → {i['suggestion']}"
            for i in diagnosis_issues
        )
        combined_instruction = f"다음 문제점을 반드시 수정하세요:\n{issue_lines}"
        if user_instruction:
            combined_instruction += f"\n\n추가 지시:\n{user_instruction}"
    else:
        combined_instruction = user_instruction

    return generate_answer(
        question_id=question_id,
        question_text=question_text,
        char_limit=char_limit,
        target_char_min=target_char_min,
        target_char_max=target_char_max,
        measured_competencies=measured_competencies,
        expected_level=expected_level,
        company_analysis=company_analysis,
        job_analysis=job_analysis,
        profile=profile,
        mapping_entries=mapping_entries,
        user_instruction=combined_instruction,
    )


def confirm_draft(
    question_id: int,
    mapping_table_id: int | None,
    text: str,
    self_diagnosis_issues: list[dict],
    generation_params: dict,
    version: int = 1,
    hallucination_retries: int = 0,
) -> int:
    """답변 초안을 DB에 저장.

    Args:
        question_id: 문항 ID
        mapping_table_id: 매핑 테이블 ID (없으면 None)
        text: 최종 답변 텍스트
        self_diagnosis_issues: 자가진단 문제 목록
        generation_params: 생성 파라미터 (모델명, 시도 횟수, 사용자 지시 등)
        version: 버전 번호
        hallucination_retries: 환각 방지 재생성 횟수

    Returns:
        생성된 cover_letter_draft.id
    """
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cover_letter_draft
                    (question_id, mapping_table_id, version, text,
                     self_diagnosis_issues, hallucination_retries,
                     generation_params, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft')
                RETURNING id
                """,
                (
                    question_id,
                    mapping_table_id,
                    version,
                    text,
                    json.dumps(self_diagnosis_issues, ensure_ascii=False),
                    hallucination_retries,
                    json.dumps(generation_params, ensure_ascii=False),
                ),
            )
            row = cur.fetchone()
            return int(row[0])
    finally:
        conn.close()


def check_hallucination(
    answer_text: str,
    mapping_entries: list[dict],
    profile: dict,
) -> bool:
    """답변에 경험 목록에 없는 내용(환각)이 포함되었는지 LLM으로 검증.

    Args:
        answer_text: 검증할 자소서 답변 텍스트
        mapping_entries: 매핑 테이블 엔트리 목록 (experience_key 포함)
        profile: 프로필 dict (experiences 키 포함)

    Returns:
        True: 환각 감지됨, False: 정상
    """
    prompt_template = _HALLUCINATION_PROMPT_PATH.read_text(encoding="utf-8")

    # 사용된 경험만 추출
    experiences = profile.get("experiences", [])
    used_keys = {e.get("experience_key") for e in mapping_entries}
    used_experiences = [
        exp for exp in experiences if exp.get("key") in used_keys
    ] or experiences

    exp_lines = "\n".join(
        f"- [{e.get('key', '')}] {e.get('title', '')}: {e.get('description', '')}"
        for e in used_experiences
    )

    prompt = prompt_template.replace("{experiences}", exp_lines).replace(
        "{answer_text}", answer_text
    )

    try:
        raw = llm_client.call(prompt, tier="flash")
        clean = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        data = json.loads(clean)
        return bool(data.get("hallucinated", False))
    except Exception:
        return False


def regenerate_without_hallucination(
    answer_params: dict,
    mapping_entries: list[dict],
    profile: dict,
) -> dict:
    """환각이 없는 답변이 나올 때까지 최대 MAX_RETRIES회 재생성.

    Args:
        answer_params: generate_answer 호출 파라미터 dict
        mapping_entries: 매핑 테이블 엔트리 목록
        profile: 프로필 dict

    Returns:
        {
            "text": str,
            "hallucination_retries": int,  # 재생성 횟수
            "hallucination_detected": bool,  # 최종 답변에 여전히 환각 있는지
        }
    """
    retries = 0
    result = generate_answer(**answer_params)
    text: str = result.get("text", "")

    while retries < MAX_RETRIES:
        if not check_hallucination(text, mapping_entries, profile):
            break
        retries += 1
        # 재생성 지시를 포함해 다시 생성
        patched_params = {
            **answer_params,
            "user_instruction": (
                (answer_params.get("user_instruction") or "")
                + "\n\n[주의] 제공된 경험 목록에 없는 고유명사·프로젝트명·수치를 절대 사용하지 마시오."
            ),
        }
        result = generate_answer(**patched_params)
        text = result.get("text", "")

    still_hallucinated = check_hallucination(text, mapping_entries, profile)
    return {
        "text": text,
        "hallucination_retries": retries,
        "hallucination_detected": still_hallucinated,
    }
