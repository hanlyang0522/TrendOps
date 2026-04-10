"""profile_service 단위 테스트."""

import json
from unittest.mock import MagicMock, call, patch

import pytest

from cover_letter import profile_service


# ============================================================
# parse_input 테스트
# ============================================================
class TestParseInput:
    def test_file_bytes_returns_decoded_text(self):
        result = profile_service.parse_input(
            None,
            b"\xec\xa0\x80\xeb\x8a\x94 Python \xea\xb0\x9c\xeb\xb0\x9c\xec\x9e\x90\xec\x9e\x85\xeb\x8b\x88\xeb\x8b\xa4.",
        )
        assert "Python" in result

    def test_text_returns_stripped_text(self):
        result = profile_service.parse_input("  안녕하세요  ", None)
        assert result == "안녕하세요"

    def test_file_bytes_takes_priority_over_text(self):
        result = profile_service.parse_input("텍스트", b"\xed\x8c\x8c\xec\x9d\xbc")
        assert result == "파일"

    def test_both_none_raises_value_error(self):
        with pytest.raises(ValueError, match="입력"):
            profile_service.parse_input(None, None)

    def test_empty_text_and_none_bytes_raises_value_error(self):
        with pytest.raises(ValueError, match="입력"):
            profile_service.parse_input("   ", None)

    def test_empty_bytes_falls_back_to_text(self):
        result = profile_service.parse_input("텍스트 내용", b"")
        assert result == "텍스트 내용"

    def test_both_empty_raises_value_error(self):
        with pytest.raises(ValueError):
            profile_service.parse_input("", b"")

    def test_md_file_returns_decoded_text(self):
        """filename 확장자가 .md일 때 UTF-8 디코드로 처리한다."""
        md_bytes = b"# \xed\x83\x80\xec\x9d\xb4\xed\x8b\x80\n\xeb\x82\xb4\xec\x9a\xa9"  # UTF-8 '타이틀\n내용'
        result = profile_service.parse_input(None, md_bytes, filename="resume.md")
        assert "타이틀" in result
        assert "내용" in result

    def test_txt_with_filename_returns_decoded_text(self):
        """filename 확장자가 .txt일 때도 UTF-8 디코드로 처리한다."""
        txt_bytes = "파이썬 개발자".encode("utf-8")
        result = profile_service.parse_input(None, txt_bytes, filename="data.txt")
        assert "파이썬" in result

    @patch("docx.Document")
    def test_docx_file_extracts_paragraph_text(self, mock_doc_cls):
        """filename 확장자가 .docx일 때 python-docx 단락 텍스트를 추출한다."""
        mock_para1 = MagicMock()
        mock_para1.text = "백엔드 인턴 경험"
        mock_para2 = MagicMock()
        mock_para2.text = "FastAPI 개발"
        mock_para_empty = MagicMock()
        mock_para_empty.text = ""

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para_empty, mock_para2]
        mock_doc_cls.return_value = mock_doc

        result = profile_service.parse_input(
            None, b"fake-docx-bytes", filename="portfolio.docx"
        )
        assert "백엔드 인턴 경험" in result
        assert "FastAPI 개발" in result


# ============================================================
# extract_profile 테스트
# ============================================================
class TestExtractProfile:
    _MOCK_PROFILE = {
        "experiences": [
            {
                "key": "exp_01",
                "title": "백엔드 인턴",
                "period": "2024.01~2024.06",
                "description": "FastAPI 기반 REST API 개발",
                "competencies": ["Python", "RESTful API"],
            }
        ],
        "competencies": ["Python", "문제해결"],
        "writing_style": {
            "sentence_length": "medium",
            "tone": "formal",
            "expression_patterns": [],
            "avoid_patterns": [],
        },
    }

    @patch("cover_letter.profile_service.llm_client.call")
    def test_returns_parsed_dict(self, mock_call):
        mock_call.return_value = json.dumps(self._MOCK_PROFILE, ensure_ascii=False)
        result = profile_service.extract_profile(["경력 자료"])
        assert "experiences" in result
        assert "competencies" in result
        assert "writing_style" in result

    @patch("cover_letter.profile_service.llm_client.call")
    def test_strips_markdown_codeblock(self, mock_call):
        raw = f"```json\n{json.dumps(self._MOCK_PROFILE)}\n```"
        mock_call.return_value = raw
        result = profile_service.extract_profile(["자료"])
        assert result["competencies"] == ["Python", "문제해결"]

    @patch("cover_letter.profile_service.llm_client.call")
    def test_invalid_json_raises_runtime_error(self, mock_call):
        mock_call.return_value = "이건 JSON이 아닙니다"
        with pytest.raises(RuntimeError, match="JSON"):
            profile_service.extract_profile(["자료"])

    @patch("cover_letter.profile_service.llm_client.call")
    def test_uses_flash_tier(self, mock_call):
        mock_call.return_value = json.dumps(self._MOCK_PROFILE)
        profile_service.extract_profile(["자료"])
        _, kwargs = mock_call.call_args
        assert kwargs.get("tier") == "flash" or mock_call.call_args[0][1] == "flash"


# ============================================================
# save_profile / load_profile DB 왕복 테스트
# ============================================================
class TestSaveLoadProfile:
    _PROFILE = {
        "experiences": [
            {
                "key": "exp_01",
                "title": "테스트",
                "period": "",
                "description": "설명",
                "competencies": [],
            }
        ],
        "competencies": ["역량1"],
        "writing_style": {
            "sentence_length": "medium",
            "tone": "formal",
            "expression_patterns": [],
            "avoid_patterns": [],
        },
        "source_files": ["test.txt"],
    }

    @patch("cover_letter.profile_service._get_conn")
    def test_save_profile_executes_upsert(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        profile_service.save_profile(self._PROFILE)

        mock_cur.execute.assert_called_once()
        sql = mock_cur.execute.call_args[0][0]
        assert "INSERT INTO user_profile" in sql
        assert "ON CONFLICT" in sql

    @patch("cover_letter.profile_service._get_conn")
    def test_load_profile_returns_none_when_no_row(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cur.fetchone.return_value = None

        result = profile_service.load_profile()
        assert result is None

    @patch("cover_letter.profile_service._get_conn")
    def test_load_profile_returns_dict_when_row_exists(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cur.fetchone.return_value = (
            [{"key": "exp_01", "title": "테스트"}],
            ["역량1"],
            {"sentence_length": "medium"},
            ["test.txt"],
        )

        result = profile_service.load_profile()
        assert result is not None
        assert "experiences" in result

    @patch("cover_letter.profile_service._get_conn")
    def test_load_profile_returns_none_on_connection_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("연결 실패")
        result = profile_service.load_profile()
        assert result is None


# ============================================================
# merge_profile 테스트
# ============================================================
class TestMergeProfile:
    _EXISTING = {
        "experiences": [
            {
                "key": "exp_01",
                "title": "기존 경험",
                "period": "",
                "description": "",
                "competencies": [],
            }
        ],
        "competencies": ["역량A"],
        "writing_style": {"sentence_length": "medium", "tone": "formal"},
        "source_files": ["old.txt"],
    }

    _NEW_PROFILE_RESULT = {
        "experiences": [
            {
                "key": "exp_02",
                "title": "신규 경험",
                "period": "",
                "description": "",
                "competencies": [],
            }
        ],
        "competencies": ["역량B"],
        "writing_style": {"sentence_length": "long", "tone": "semi-formal"},
    }

    @patch("cover_letter.profile_service.extract_profile")
    def test_merge_combines_unique_experiences(self, mock_extract):
        mock_extract.return_value = self._NEW_PROFILE_RESULT
        result = profile_service.merge_profile(self._EXISTING, ["신규 텍스트"])
        keys = [e["key"] for e in result["experiences"]]
        assert "exp_01" in keys
        assert "exp_02" in keys

    @patch("cover_letter.profile_service.extract_profile")
    def test_merge_deduplicates_competencies(self, mock_extract):
        existing = dict(self._EXISTING, competencies=["역량A", "역량B"])
        mock_extract.return_value = dict(
            self._NEW_PROFILE_RESULT, competencies=["역량B", "역량C"]
        )
        result = profile_service.merge_profile(existing, ["텍스트"])
        assert result["competencies"].count("역량B") == 1

    @patch("cover_letter.profile_service.extract_profile")
    def test_merge_writing_style_new_wins(self, mock_extract):
        mock_extract.return_value = self._NEW_PROFILE_RESULT
        result = profile_service.merge_profile(self._EXISTING, ["텍스트"])
        assert result["writing_style"]["sentence_length"] == "long"
