"""generation_service 단위 테스트 — 글자 수 루프, 자가진단."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cover_letter import generation_service

# 공통 픽스처 데이터
_PROFILE = {
    "name": "홍길동",
    "experiences": [{"key": "exp_01", "title": "A사 인턴", "description": "A 개발"}],
    "writing_style": {"sentence_length": "medium", "tone": "formal"},
}
_COMPANY = {
    "company_name": "카카오",
    "culture_and_values": "수평",
    "competitive_edge": "글로벌",
}
_JOB = {"job_title": "백엔드개발자"}
_ENTRIES = [
    {
        "experience_key": "exp_01",
        "usage_type": "primary",
        "relevance_score": 5,
        "rationale": "일치",
    }
]


# ============================================================
# generate_answer 테스트
# ============================================================
class TestGenerateAnswer:
    @patch("cover_letter.generation_service.llm_client.call")
    def test_returns_in_range_on_first_attempt(self, mock_call):
        """첫 번째 시도에서 글자 수 범위 충족 시 attempt=1."""
        target_text = "가" * 850  # 850자 → 800~950 범위 내
        mock_call.return_value = target_text

        result = generation_service.generate_answer(
            question_id=1,
            question_text="Q",
            char_limit=1000,
            target_char_min=800,
            target_char_max=950,
            measured_competencies=["도전"],
            expected_level="높음",
            company_analysis=_COMPANY,
            job_analysis=_JOB,
            profile=_PROFILE,
            mapping_entries=_ENTRIES,
        )

        assert result["in_range"] is True
        assert result["attempt"] == 1
        assert result["char_count"] == 850

    @patch("cover_letter.generation_service.llm_client.call")
    def test_retries_until_in_range(self, mock_call):
        """3회 시도, 3회째에 글자 수 범위 충족."""
        short = "가" * 500  # 범위 미만
        ok = "가" * 850  # 범위 내
        mock_call.side_effect = [short, short, ok]

        result = generation_service.generate_answer(
            question_id=1,
            question_text="Q",
            char_limit=1000,
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
            expected_level="",
            company_analysis=_COMPANY,
            job_analysis=_JOB,
            profile=_PROFILE,
            mapping_entries=_ENTRIES,
        )

        assert result["in_range"] is True
        assert result["attempt"] == 3
        assert mock_call.call_count == 3

    @patch("cover_letter.generation_service.llm_client.call")
    def test_stops_at_max_retries_if_never_in_range(self, mock_call):
        """MAX_RETRIES(3)회 후에도 범위 미충족 시 in_range=False."""
        mock_call.return_value = "가" * 500  # 항상 범위 밖

        result = generation_service.generate_answer(
            question_id=1,
            question_text="Q",
            char_limit=1000,
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
            expected_level="",
            company_analysis=_COMPANY,
            job_analysis=_JOB,
            profile=_PROFILE,
            mapping_entries=_ENTRIES,
        )

        assert result["in_range"] is False
        assert mock_call.call_count == generation_service.MAX_RETRIES

    @patch("cover_letter.generation_service.llm_client.call")
    def test_user_instruction_reflected(self, mock_call):
        """user_instruction이 LLM 호출 시 프롬프트에 포함되어야 함."""
        mock_call.return_value = "가" * 850

        generation_service.generate_answer(
            question_id=1,
            question_text="Q",
            char_limit=1000,
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
            expected_level="",
            company_analysis=_COMPANY,
            job_analysis=_JOB,
            profile=_PROFILE,
            mapping_entries=_ENTRIES,
            user_instruction="수치를 포함하세요",
        )

        call_args = mock_call.call_args[1].get("prompt") or mock_call.call_args[0][0]
        assert "수치를 포함하세요" in call_args

    @patch("cover_letter.generation_service.llm_client.call")
    def test_llm_exception_returns_previous_text(self, mock_call):
        """LLM 예외 발생 시 이전 텍스트를 유지하고 다음 시도."""
        mock_call.side_effect = [RuntimeError("API 오류"), "가" * 850]

        result = generation_service.generate_answer(
            question_id=1,
            question_text="Q",
            char_limit=1000,
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
            expected_level="",
            company_analysis=_COMPANY,
            job_analysis=_JOB,
            profile=_PROFILE,
            mapping_entries=_ENTRIES,
        )

        assert result["char_count"] == 850


# ============================================================
# run_self_diagnosis 테스트
# ============================================================
class TestRunSelfDiagnosis:
    @patch("cover_letter.generation_service.llm_client.call")
    def test_returns_issues_list(self, mock_call):
        issues = [{"issue": "AI특유표현", "text": "~에 있어서", "suggestion": "삭제"}]
        mock_call.return_value = json.dumps(issues)

        result = generation_service.run_self_diagnosis(
            draft_text="이 경험에 있어서 많은 것을 배웠습니다.",
            question_text="Q",
            target_char_min=800,
            target_char_max=950,
            measured_competencies=["협업"],
        )

        assert len(result) == 1
        assert result[0]["issue"] == "AI특유표현"

    @patch("cover_letter.generation_service.llm_client.call")
    def test_returns_empty_when_no_issues(self, mock_call):
        mock_call.return_value = "[]"
        result = generation_service.run_self_diagnosis(
            draft_text="좋은 답변입니다.",
            question_text="Q",
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
        )
        assert result == []

    @patch("cover_letter.generation_service.llm_client.call")
    def test_strips_code_block_from_response(self, mock_call):
        issues = [{"issue": "추상적", "text": "열심히", "suggestion": "수치로 표현"}]
        mock_call.return_value = f"```json\n{json.dumps(issues)}\n```"

        result = generation_service.run_self_diagnosis(
            draft_text="열심히 했습니다.",
            question_text="Q",
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
        )
        assert len(result) == 1

    @patch("cover_letter.generation_service.llm_client.call")
    def test_returns_empty_on_parse_failure(self, mock_call):
        mock_call.return_value = "이건 JSON이 아닙니다."
        result = generation_service.run_self_diagnosis(
            draft_text="답변",
            question_text="Q",
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
        )
        assert result == []


# ============================================================
# apply_diagnosis_and_regenerate 테스트
# ============================================================
class TestApplyDiagnosisAndRegenerate:
    @patch("cover_letter.generation_service.llm_client.call")
    def test_includes_diagnosis_in_instruction(self, mock_call):
        """자가진단 문제가 LLM 호출 프롬프트에 포함되어야 함."""
        mock_call.return_value = "나" * 850

        issues = [{"issue": "AI특유표현", "text": "~에 있어서", "suggestion": "삭제"}]
        generation_service.apply_diagnosis_and_regenerate(
            question_id=1,
            draft_text="기존 초안",
            diagnosis_issues=issues,
            user_instruction="",
            question_text="Q",
            char_limit=1000,
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
            expected_level="",
            company_analysis=_COMPANY,
            job_analysis=_JOB,
            profile=_PROFILE,
            mapping_entries=_ENTRIES,
        )

        call_args = mock_call.call_args[1].get("prompt") or mock_call.call_args[0][0]
        assert "AI특유표현" in call_args

    @patch("cover_letter.generation_service.llm_client.call")
    def test_combines_diagnosis_and_user_instruction(self, mock_call):
        mock_call.return_value = "나" * 850

        issues = [{"issue": "추상적", "text": "열심히", "suggestion": "수치로"}]
        generation_service.apply_diagnosis_and_regenerate(
            question_id=1,
            draft_text="기존",
            diagnosis_issues=issues,
            user_instruction="문장을 더 짧게",
            question_text="Q",
            char_limit=1000,
            target_char_min=800,
            target_char_max=950,
            measured_competencies=[],
            expected_level="",
            company_analysis=_COMPANY,
            job_analysis=_JOB,
            profile=_PROFILE,
            mapping_entries=_ENTRIES,
        )

        call_args = mock_call.call_args[1].get("prompt") or mock_call.call_args[0][0]
        assert "추상적" in call_args
        assert "문장을 더 짧게" in call_args


# ============================================================
# confirm_draft 테스트
# ============================================================
class TestConfirmDraft:
    @patch("cover_letter.generation_service._get_conn")
    def test_returns_draft_id(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (99,)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_c = MagicMock()
        mock_c.__enter__ = MagicMock(return_value=mock_c)
        mock_c.__exit__ = MagicMock(return_value=False)
        mock_c.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_c

        result = generation_service.confirm_draft(
            question_id=1,
            mapping_table_id=5,
            text="최종 답변입니다.",
            self_diagnosis_issues=[],
            generation_params={"attempt": 2},
        )
        assert result == 99
