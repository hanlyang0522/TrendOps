# Service Interface Contracts: 자소서 작성 자동화 서비스

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-09
**Source**: spec.md FR 요건 + data-model.md + research.md 결정 사항

이 문서는 `cover_letter/` 서비스 모듈의 공개 함수 시그니처를 정의합니다.
각 서비스는 단일 파일, 단순 함수 집합으로 구현합니다 (클래스 불필요 — YAGNI).

---

## 1. profile_service.py

**목적**: 파일 파싱, LLM 프로필 추출, DB 저장/로드

```python
# cover_letter/profile_service.py

def parse_file(file_path: str) -> str:
    """PDF/DOCX/TXT 파일에서 텍스트 추출.

    Args:
        file_path: 업로드된 파일의 로컬 경로

    Returns:
        추출된 텍스트 문자열

    Raises:
        ValueError: 지원하지 않는 파일 형식
        RuntimeError: 파싱 실패 (이미지 전용 PDF 등)
    """

def extract_profile(texts: list[str]) -> dict:
    """LLM을 통해 텍스트 목록에서 경험·역량·문체 프로필 추출.

    Args:
        texts: 파싱된 파일 텍스트 목록 (포트폴리오, 합격 자소서 등)

    Returns:
        {
            "experiences": list[Experience],
            "competencies": list[str],
            "writing_style": WritingStyle
        }
    """

def load_profile() -> dict | None:
    """DB에서 확인된 사용자 프로필 로드. 없으면 None 반환."""

def save_profile(profile: dict) -> None:
    """사용자가 확인한 프로필을 DB에 저장 (confirmed_at 갱신).

    Args:
        profile: extract_profile() 반환값 또는 사용자 수정 버전
    """

def merge_profile(existing: dict, new_texts: list[str]) -> dict:
    """기존 프로필과 새 파일 텍스트를 LLM으로 병합.

    Returns:
        병합된 프로필 dict (confirmed_at=None 상태)
    """
```

---

## 2. company_service.py

**목적**: 기업·직무 분석, 캐시 조회/저장, 뉴스 재검색

```python
# cover_letter/company_service.py

def get_or_analyze_company(company_name: str) -> dict:
    """기업 분석 결과를 캐시에서 조회하거나 없으면 새로 분석.

    캐시 유효기간 7일. 캐시 히트 시 뉴스만 재검색하여 news_summary 갱신.

    Args:
        company_name: 기업명 (예: "삼성전자")

    Returns:
        CompanyAnalysis에 해당하는 dict
        {
            "id": int, "company_name": str,
            "overview": str, "culture_and_values": str,
            "industry_trends": str, "competitive_edge": str,
            "news_summary": str, "source_urls": list[str],
            "cache_hit": bool
        }
    """

def analyze_job(company_analysis_id: int, job_title: str) -> dict:
    """직무 분석 수행 및 저장.

    Args:
        company_analysis_id: 연결된 기업 분석 ID
        job_title: 지원 직무명

    Returns:
        JobAnalysis에 해당하는 dict
    """

def save_overrides(entity: str, entity_id: int, overrides: dict) -> None:
    """사용자 수정 내용을 user_overrides 필드에 저장.

    Args:
        entity: 'company' | 'job'
        entity_id: 해당 레코드 ID
        overrides: 수정된 필드 dict
    """
```

---

## 3. question_service.py

**목적**: 문항 저장 및 LLM 기반 문항 분석

```python
# cover_letter/question_service.py

def analyze_question(
    job_analysis_id: int,
    question_text: str,
    char_limit: int | None = None,
) -> dict:
    """LLM을 통해 문항이 측정하는 역량과 기대 수준을 분석하고 저장.

    Args:
        job_analysis_id: 연결된 직무 분석 ID
        question_text: 자소서 문항 원문
        char_limit: 글자 수 제한 (없으면 None)

    Returns:
        Question에 해당하는 dict
        {
            "id": int, "text": str, "char_limit": int | None,
            "target_char_min": int | None, "target_char_max": int | None,
            "measured_competencies": list[str], "expected_level": str
        }
    """
```

---

## 4. mapping_service.py

**목적**: 경험-문항 매핑 테이블 생성, 중복 검증

```python
# cover_letter/mapping_service.py

def generate_mapping(question_id: int, profile: dict) -> list[dict]:
    """LLM을 사용하여 문항과 사용자 경험 간 적합도를 평가하고 매핑 후보를 반환.

    Args:
        question_id: 분석된 문항 ID
        profile: load_profile() 반환값

    Returns:
        score 3 이상의 MappingEntry 목록, score 내림차순 정렬
        [{"experience_key": str, "usage_type": str,
          "relevance_score": int, "rationale": str}]
    """

def validate_duplicates(
    question_id: int,
    entries: list[dict],
    all_session_mappings: list[dict],
) -> list[dict]:
    """동일 지원 세션 내 동일 경험을 동일 usage_type으로 복수 문항에 배정했는지 검증.

    Args:
        question_id: 현재 문항 ID
        entries: 현재 문항의 MappingEntry 목록
        all_session_mappings: 같은 job_analysis 하의 모든 확정된 매핑

    Returns:
        경고 목록 [{"experience_key": str, "usage_type": str,
                     "conflicting_question_id": int}]
        경고 없으면 빈 리스트
    """

def save_mapping(question_id: int, entries: list[dict]) -> int:
    """확정된 매핑 테이블을 DB에 저장.

    Args:
        question_id: 문항 ID
        entries: 최종 MappingEntry 목록

    Returns:
        생성된 mapping_table.id
    """
```

---

## 5. generation_service.py

**목적**: 답변 초안 생성, 글자 수 제어 루프, AI 자가진단

```python
# cover_letter/generation_service.py

MAX_RETRIES = 3

def generate_answer(
    question: dict,
    mapping_table_id: int,
    profile: dict,
    company_analysis: dict,
    job_analysis: dict,
    user_instruction: str = "",
) -> dict:
    """매핑 테이블 기반 자소서 답변 초안 생성.

    글자 수 제한이 있으면 90~95% 범위 충족 시까지 최대 MAX_RETRIES회 재시도.

    Args:
        question: analyze_question() 반환값
        mapping_table_id: 확정된 매핑 ID
        profile: 사용자 프로필 (문체 포함)
        company_analysis: 기업 분석 결과
        job_analysis: 직무 분석 결과
        user_instruction: 사용자 수정 지시 (재생성 시)

    Returns:
        {
            "draft_id": int,
            "text": str,
            "char_count": int,
            "within_target": bool,
            "retry_count": int  # 실제 재시도 횟수
        }
    """

def run_self_diagnosis(draft_id: int) -> list[dict]:
    """생성된 답변에 대해 AI 자가진단 실행.

    Args:
        draft_id: 진단할 CoverLetterDraft ID

    Returns:
        문제 항목 목록 (없으면 빈 리스트)
        [{"issue": str, "text": str, "suggestion": str}]
    """

def apply_diagnosis_and_regenerate(draft_id: int) -> dict:
    """자가진단 결과를 반영하여 답변 재생성.

    Args:
        draft_id: 진단 결과가 저장된 CoverLetterDraft ID

    Returns:
        generate_answer()와 동일한 구조의 새 draft dict
    """

def confirm_draft(draft_id: int) -> None:
    """최종 답변을 confirmed 상태로 저장."""
```
