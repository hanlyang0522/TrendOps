"""mapping_service 단위 테스트 — 중복 검증 및 매핑 생성."""

import json
from unittest.mock import MagicMock, patch

import pytest

from cover_letter import mapping_service


# ============================================================
# validate_duplicates 테스트
# ============================================================
class TestValidateDuplicates:
    def test_no_duplicates_returns_empty_warnings(self):
        """서로 다른 경험을 사용하면 경고 없음."""
        all_mappings = [
            {
                "question_id": 1,
                "question_text": "Q1",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "primary",
                        "relevance_score": 5,
                        "rationale": "",
                    }
                ],
            },
            {
                "question_id": 2,
                "question_text": "Q2",
                "entries": [
                    {
                        "experience_key": "exp_02",
                        "usage_type": "primary",
                        "relevance_score": 4,
                        "rationale": "",
                    }
                ],
            },
        ]
        warnings = mapping_service.validate_duplicates(all_mappings)
        assert warnings == []

    def test_same_experience_same_usage_type_triggers_warning(self):
        """동일 경험 × 동일 usage_type이 복수 문항에 → 경고 1건."""
        all_mappings = [
            {
                "question_id": 1,
                "question_text": "Q1",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "primary",
                        "relevance_score": 5,
                        "rationale": "",
                    }
                ],
            },
            {
                "question_id": 2,
                "question_text": "Q2",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "primary",
                        "relevance_score": 4,
                        "rationale": "",
                    }
                ],
            },
        ]
        warnings = mapping_service.validate_duplicates(all_mappings)
        assert len(warnings) == 1
        assert warnings[0]["experience_key"] == "exp_01"
        assert warnings[0]["usage_type"] == "primary"
        assert len(warnings[0]["questions"]) == 2

    def test_same_experience_different_usage_type_no_warning(self):
        """동일 경험이지만 usage_type이 다르면 경고 없음."""
        all_mappings = [
            {
                "question_id": 1,
                "question_text": "Q1",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "primary",
                        "relevance_score": 5,
                        "rationale": "",
                    }
                ],
            },
            {
                "question_id": 2,
                "question_text": "Q2",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "supporting",
                        "relevance_score": 3,
                        "rationale": "",
                    }
                ],
            },
        ]
        warnings = mapping_service.validate_duplicates(all_mappings)
        assert warnings == []

    def test_empty_mappings_returns_empty(self):
        """빈 입력에 경고 없음."""
        assert mapping_service.validate_duplicates([]) == []

    def test_single_mapping_no_warning(self):
        """문항이 1개면 중복 불가."""
        all_mappings = [
            {
                "question_id": 1,
                "question_text": "Q1",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "primary",
                        "relevance_score": 5,
                        "rationale": "",
                    }
                ],
            },
        ]
        warnings = mapping_service.validate_duplicates(all_mappings)
        assert warnings == []

    def test_multiple_duplicates_detected(self):
        """복수의 중복 쌍 모두 탐지."""
        all_mappings = [
            {
                "question_id": 1,
                "question_text": "Q1",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "primary",
                        "relevance_score": 5,
                        "rationale": "",
                    },
                    {
                        "experience_key": "exp_02",
                        "usage_type": "supporting",
                        "relevance_score": 4,
                        "rationale": "",
                    },
                ],
            },
            {
                "question_id": 2,
                "question_text": "Q2",
                "entries": [
                    {
                        "experience_key": "exp_01",
                        "usage_type": "primary",
                        "relevance_score": 4,
                        "rationale": "",
                    },
                    {
                        "experience_key": "exp_02",
                        "usage_type": "supporting",
                        "relevance_score": 3,
                        "rationale": "",
                    },
                ],
            },
        ]
        warnings = mapping_service.validate_duplicates(all_mappings)
        assert len(warnings) == 2


# ============================================================
# generate_mapping 테스트
# ============================================================
class TestGenerateMapping:
    def test_returns_empty_list_when_no_experiences(self):
        result = mapping_service.generate_mapping(
            question_id=1,
            question_text="지원동기를 작성하세요.",
            measured_competencies=["열정"],
            expected_level="중간",
            company_name="카카오",
            job_title="백엔드개발자",
            culture_and_values="수평",
            experiences=[],
        )
        assert result == []

    @patch("cover_letter.mapping_service.llm_client.call")
    def test_filters_entries_below_score_3(self, mock_call):
        mock_call.return_value = json.dumps(
            [
                {
                    "experience_key": "exp_01",
                    "usage_type": "primary",
                    "relevance_score": 4,
                    "rationale": "높음",
                },
                {
                    "experience_key": "exp_02",
                    "usage_type": "supporting",
                    "relevance_score": 2,
                    "rationale": "낮음",
                },
            ]
        )
        result = mapping_service.generate_mapping(
            question_id=1,
            question_text="도전 사례를 작성하세요.",
            measured_competencies=["도전"],
            expected_level="높음",
            company_name="카카오",
            job_title="개발자",
            culture_and_values="혁신",
            experiences=[
                {"key": "exp_01", "title": "A사 프로젝트"},
                {"key": "exp_02", "title": "학교 동아리"},
            ],
        )
        assert len(result) == 1
        assert result[0]["experience_key"] == "exp_01"

    @patch("cover_letter.mapping_service.llm_client.call")
    def test_handles_llm_json_parse_failure(self, mock_call):
        mock_call.return_value = "이건 JSON이 아닙니다"
        result = mapping_service.generate_mapping(
            question_id=1,
            question_text="Q",
            measured_competencies=[],
            expected_level="",
            company_name="카카오",
            job_title="개발자",
            culture_and_values="",
            experiences=[{"key": "exp_01", "title": "A"}],
        )
        assert result == []

    @patch("cover_letter.mapping_service.llm_client.call")
    def test_strips_markdown_code_block(self, mock_call):
        payload = [
            {
                "experience_key": "exp_01",
                "usage_type": "primary",
                "relevance_score": 5,
                "rationale": "완벽",
            }
        ]
        mock_call.return_value = f"```json\n{json.dumps(payload)}\n```"
        result = mapping_service.generate_mapping(
            question_id=1,
            question_text="Q",
            measured_competencies=["역량"],
            expected_level="높음",
            company_name="카카오",
            job_title="개발자",
            culture_and_values="수평",
            experiences=[{"key": "exp_01", "title": "A"}],
        )
        assert len(result) == 1

    @patch("cover_letter.mapping_service.llm_client.call")
    def test_handles_llm_exception(self, mock_call):
        mock_call.side_effect = RuntimeError("API 오류")
        result = mapping_service.generate_mapping(
            question_id=1,
            question_text="Q",
            measured_competencies=[],
            expected_level="",
            company_name="카카오",
            job_title="개발자",
            culture_and_values="",
            experiences=[{"key": "exp_01", "title": "A"}],
        )
        assert result == []


# ============================================================
# save_mapping 테스트
# ============================================================
class TestSaveMapping:
    @patch("cover_letter.mapping_service._get_conn")
    def test_returns_mapping_id(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (42,)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_c = MagicMock()
        mock_c.__enter__ = MagicMock(return_value=mock_c)
        mock_c.__exit__ = MagicMock(return_value=False)
        mock_c.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_c

        result = mapping_service.save_mapping(
            question_id=1,
            entries=[
                {
                    "experience_key": "exp_01",
                    "usage_type": "primary",
                    "relevance_score": 5,
                    "rationale": "",
                }
            ],
        )
        assert result == 42
