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

    @patch("cover_letter.generation_service._get_conn")
    def test_hallucination_retries_param_saved(self, mock_conn):
        """hallucination_retries 파라미터가 DB에 전달된다."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (100,)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_c = MagicMock()
        mock_c.__enter__ = MagicMock(return_value=mock_c)
        mock_c.__exit__ = MagicMock(return_value=False)
        mock_c.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_c

        result = generation_service.confirm_draft(
            question_id=1,
            mapping_table_id=None,
            text="답변",
            self_diagnosis_issues=[],
            generation_params={},
            hallucination_retries=2,
        )
        assert result == 100
        execute_args = mock_cursor.execute.call_args[0][1]
        # hallucination_retries = 2 가 params에 포함됐는지 확인
        assert 2 in execute_args


# ============================================================
# check_hallucination 테스트
# ============================================================
class TestCheckHallucination:
    @patch("cover_letter.generation_service.llm_client.call")
    def test_returns_false_when_not_hallucinated(self, mock_call):
        """LLM이 hallucinated=false 반환 시 False."""
        mock_call.return_value = '{"hallucinated": false, "reason": "정상"}'
        result = generation_service.check_hallucination(
            answer_text="A사 인턴 경험에서 개발했습니다.",
            mapping_entries=_ENTRIES,
            profile=_PROFILE,
        )
        assert result is False

    @patch("cover_letter.generation_service.llm_client.call")
    def test_returns_true_when_hallucinated(self, mock_call):
        """LLM이 hallucinated=true 반환 시 True."""
        mock_call.return_value = '{"hallucinated": true, "reason": "없는 프로젝트"}'
        result = generation_service.check_hallucination(
            answer_text="없는프로젝트 팀장으로 활동했습니다.",
            mapping_entries=_ENTRIES,
            profile=_PROFILE,
        )
        assert result is True

    @patch("cover_letter.generation_service.llm_client.call")
    def test_returns_false_on_json_parse_error(self, mock_call):
        """LLM 응답이 파싱 불가능하면 False(보수적 판단)."""
        mock_call.return_value = "잘못된 응답"
        result = generation_service.check_hallucination(
            answer_text="답변 텍스트",
            mapping_entries=_ENTRIES,
            profile=_PROFILE,
        )
        assert result is False


# ============================================================
# regenerate_without_hallucination 테스트
# ============================================================
class TestRegenerateWithoutHallucination:
    _ANSWER_PARAMS = dict(
        question_id=1,
        question_text="지원 동기를 서술하시오.",
        char_limit=1000,
        target_char_min=800,
        target_char_max=950,
        measured_competencies=[],
        expected_level="",
        company_analysis=_COMPANY,
        job_analysis=_JOB,
        profile=_PROFILE,
        mapping_entries=_ENTRIES,
        user_instruction="",
    )

    @patch("cover_letter.generation_service.check_hallucination", return_value=False)
    @patch("cover_letter.generation_service.generate_answer")
    def test_returns_without_retrying_if_no_hallucination(self, mock_gen, mock_hall):
        """첫 시도에서 환각이 없으면 재생성하지 않는다."""
        mock_gen.return_value = {
            "text": "정상 답변",
            "char_count": 850,
            "in_range": True,
            "attempt": 1,
        }

        result = generation_service.regenerate_without_hallucination(
            answer_params=self._ANSWER_PARAMS,
            mapping_entries=_ENTRIES,
            profile=_PROFILE,
        )

        assert result["hallucination_retries"] == 0
        assert result["hallucination_detected"] is False
        assert mock_gen.call_count == 1

    @patch(
        "cover_letter.generation_service.check_hallucination",
        side_effect=[True, True, True, True],
    )
    @patch("cover_letter.generation_service.generate_answer")
    def test_retries_up_to_max_retries_then_gives_up(self, mock_gen, mock_hall):
        """MAX_RETRIES 초과 후에도 환각이 있으면 hallucination_detected=True 반환."""
        mock_gen.return_value = {
            "text": "환각 포함 답변",
            "char_count": 900,
            "in_range": True,
            "attempt": 1,
        }
        original_max = generation_service.MAX_RETRIES
        generation_service.MAX_RETRIES = 3

        result = generation_service.regenerate_without_hallucination(
            answer_params=self._ANSWER_PARAMS,
            mapping_entries=_ENTRIES,
            profile=_PROFILE,
        )

        generation_service.MAX_RETRIES = original_max
        assert result["hallucination_retries"] == 3
        assert result["hallucination_detected"] is True
