"""프로필 서비스 — 파일 파싱, LLM 프로필 추출, DB 저장/로드."""

import io
import json
import pathlib

from cover_letter import llm_client
from cover_letter.db import get_conn as _get_conn

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "profile_extract.txt"


def parse_input(
    text: str | None,
    file_bytes: bytes | None,
    filename: str = "",
) -> str:
    """텍스트 직접 붙여넣기 또는 파일 바이트에서 문자열 추출.

    지원 형식: TXT, MD (UTF-8 디코드), DOCX (python-docx 단락 추출)

    Args:
        text: Streamlit text_area에서 받은 문자열 (없으면 None)
        file_bytes: st.file_uploader에서 받은 파일 bytes (없으면 None)
        filename: 업로드된 파일명. 확장자로 형식을 판별한다.

    Returns:
        처리된 텍스트 문자열

    Raises:
        ValueError: text와 file_bytes 모두 None이거나 빈 값인 경우
    """
    if file_bytes is not None:
        ext = pathlib.Path(filename).suffix.lower() if filename else ".txt"

        if ext == ".docx":
            import docx  # python-docx

            doc = docx.Document(io.BytesIO(file_bytes))
            decoded = "\n".join(
                p.text for p in doc.paragraphs if p.text.strip()
            ).strip()
        else:
            # .txt, .md — UTF-8 디코드
            decoded = file_bytes.decode("utf-8", errors="replace").strip()

        if decoded:
            return decoded

    if text is not None:
        stripped = text.strip()
        if stripped:
            return stripped

    raise ValueError("텍스트 또는 파일 중 하나 이상 입력해야 합니다.")


def extract_profile(texts: list[str]) -> dict:
    """LLM을 통해 텍스트 목록에서 경험·역량·문체 프로필 추출.

    Args:
        texts: 파싱된 파일 텍스트 목록

    Returns:
        {"experiences": [...], "competencies": [...], "writing_style": {...}}
    """
    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    combined_text = "\n\n---\n\n".join(texts)
    prompt = prompt_template.replace("{texts}", combined_text)

    # System / User 구분: 프롬프트 파일에서 ## System / ## User 섹션 분리
    system = ""
    user = prompt
    if "## System\n" in prompt and "## User\n" in prompt:
        parts = prompt.split("## User\n", 1)
        system = parts[0].replace("## System\n", "").strip()
        user = parts[1].strip()

    raw = llm_client.call(user, tier="flash", system=system, temperature=0.3)

    # JSON 파싱
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"LLM이 유효하지 않은 JSON을 반환했습니다: {e}\n원문: {raw[:200]}"
        ) from e

    return dict(result)


def load_profile() -> dict | None:
    """DB에서 확인된 사용자 프로필 로드. 없으면 None 반환."""
    try:
        conn = _get_conn()
    except Exception:
        return None

    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT experiences, competencies, writing_style, source_files "
                "FROM user_profile WHERE id = 1 AND confirmed_at IS NOT NULL"
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "experiences": row[0],
                "competencies": row[1],
                "writing_style": row[2],
                "source_files": row[3] or [],
            }
    finally:
        conn.close()


def save_profile(profile: dict) -> None:
    """사용자가 확인한 프로필을 DB에 저장 (confirmed_at 갱신).

    Args:
        profile: extract_profile() 반환값 또는 사용자 수정 버전
    """
    experiences = json.dumps(profile.get("experiences", []), ensure_ascii=False)
    competencies = json.dumps(profile.get("competencies", []), ensure_ascii=False)
    writing_style = json.dumps(profile.get("writing_style", {}), ensure_ascii=False)
    source_files = profile.get("source_files", [])

    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_profile (id, experiences, competencies, writing_style,
                                          source_files, confirmed_at, updated_at)
                VALUES (1, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    experiences   = EXCLUDED.experiences,
                    competencies  = EXCLUDED.competencies,
                    writing_style = EXCLUDED.writing_style,
                    source_files  = EXCLUDED.source_files,
                    confirmed_at  = NOW(),
                    updated_at    = NOW()
                """,
                (experiences, competencies, writing_style, source_files),
            )
    finally:
        conn.close()


def merge_profile(existing: dict, new_texts: list[str]) -> dict:
    """기존 프로필에 새 텍스트를 추가 분석하여 병합.

    Args:
        existing: 기존 저장된 프로필 dict
        new_texts: 새로 추가할 텍스트 목록

    Returns:
        병합된 프로필 dict
    """
    new_profile = extract_profile(new_texts)

    # 경험: key 기준 deduplicate (새 경험 우선)
    existing_keys = {e["key"] for e in existing.get("experiences", [])}
    merged_experiences = list(existing.get("experiences", []))
    for exp in new_profile.get("experiences", []):
        if exp["key"] not in existing_keys:
            merged_experiences.append(exp)

    # 역량: 합집합 (중복 제거)
    merged_competencies = list(
        dict.fromkeys(
            existing.get("competencies", []) + new_profile.get("competencies", [])
        )
    )

    # 문체: 새 분석 우선 (기존 것이 있으면 새 것으로 교체)
    merged_writing_style = existing.get("writing_style", {})
    merged_writing_style.update(new_profile.get("writing_style", {}))

    return {
        "experiences": merged_experiences,
        "competencies": merged_competencies,
        "writing_style": merged_writing_style,
        "source_files": existing.get("source_files", []),
    }
