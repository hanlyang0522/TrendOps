"""jd_crawler + jd_service 단위 테스트."""

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cover_letter import jd_service
from cover_letter.collectors import jd_crawler


# ============================================================
# jd_crawler.crawl_jd 테스트
# ============================================================
class TestCrawlJD:
    def _make_firecrawl_app(self, items: list[dict]) -> MagicMock:
        app = MagicMock()
        app.search.return_value = items
        return app

    @patch("cover_letter.collectors.jd_crawler.os.getenv", return_value="fake-key")
    @patch("cover_letter.collectors.jd_crawler.FirecrawlApp", create=True)
    def test_firecrawl_success_returns_text(self, mock_fc_cls, mock_getenv):
        mock_fc_cls.return_value = self._make_firecrawl_app(
            [
                {
                    "url": "https://example.com/job",
                    "markdown": "## 직무 기술서\n- Python 필수",
                }
            ]
        )

        with patch.dict(
            "sys.modules", {"firecrawl": MagicMock(FirecrawlApp=mock_fc_cls)}
        ):
            result = jd_crawler.crawl_jd("카카오", "백엔드 개발자")

        assert result["success"] is True
        assert result["source_type"] == "firecrawl"
        assert result["text"] is not None

    @patch("cover_letter.collectors.jd_crawler.os.getenv", return_value="fake-key")
    @patch("cover_letter.collectors.jd_crawler.FirecrawlApp", create=True)
    def test_pdf_url_triggers_pdfminer_fallback(self, mock_fc_cls, mock_getenv):
        """PDF URL 감지 시 pdfminer fallback이 호출된다."""
        mock_fc_cls.return_value = self._make_firecrawl_app(
            [{"url": "https://example.com/jd.pdf", "markdown": ""}]
        )

        with patch(
            "cover_letter.collectors.jd_crawler._extract_pdf_from_url"
        ) as mock_pdf:
            mock_pdf.return_value = "PDF에서 추출된 직무기술서 내용"
            with patch.dict(
                "sys.modules", {"firecrawl": MagicMock(FirecrawlApp=mock_fc_cls)}
            ):
                result = jd_crawler.crawl_jd("삼성", "SW 개발자")

        assert result["success"] is True
        assert result["source_type"] == "pdf"

    @patch("cover_letter.collectors.jd_crawler.os.getenv", return_value="")
    def test_missing_api_key_returns_manual(self, mock_getenv):
        """FIRECRAWL_API_KEY 없으면 manual 반환."""
        result = jd_crawler.crawl_jd("당근마켓", "iOS 개발자")
        assert result["success"] is False
        assert result["source_type"] == "manual"
        assert result["text"] is None

    @patch("cover_letter.collectors.jd_crawler.os.getenv", return_value="fake-key")
    @patch("cover_letter.collectors.jd_crawler.FirecrawlApp", create=True)
    def test_firecrawl_exception_returns_manual(self, mock_fc_cls, mock_getenv):
        """Firecrawl 예외 시 manual 반환."""
        mock_app = MagicMock()
        mock_app.search.side_effect = Exception("네트워크 오류")
        mock_fc_cls.return_value = mock_app

        with patch.dict(
            "sys.modules", {"firecrawl": MagicMock(FirecrawlApp=mock_fc_cls)}
        ):
            result = jd_crawler.crawl_jd("네이버", "데이터 분석가")

        assert result["success"] is False
        assert result["source_type"] == "manual"


# ============================================================
# jd_service.extract_required_competencies 테스트
# ============================================================
class TestExtractRequiredCompetencies:
    @patch("cover_letter.jd_service.llm_client.call")
    def test_returns_list_from_json_array(self, mock_call):
        mock_call.return_value = '["Python", "문제해결력", "팀워크"]'
        result = jd_service.extract_required_competencies("Python 3년 이상 경험자 우대")
        assert "Python" in result
        assert isinstance(result, list)

    @patch("cover_letter.jd_service.llm_client.call")
    def test_strips_markdown_codeblock(self, mock_call):
        mock_call.return_value = '```json\n["협업", "커뮤니케이션"]\n```'
        result = jd_service.extract_required_competencies("JD 텍스트")
        assert "협업" in result

    @patch("cover_letter.jd_service.llm_client.call")
    def test_invalid_json_returns_empty_list(self, mock_call):
        mock_call.return_value = "이건 JSON이 아님"
        result = jd_service.extract_required_competencies("JD 텍스트")
        assert result == []


# ============================================================
# jd_service.save_jd / load_jd DB 왕복 테스트
# ============================================================
class TestSaveLoadJD:
    _JD_DATA = {
        "success": True,
        "text": "Python, FastAPI 개발 경험 필수",
        "source_url": "https://example.com/job",
        "source_type": "firecrawl",
        "required_competencies": ["Python", "FastAPI"],
    }

    @patch("cover_letter.jd_service._get_conn")
    def test_save_jd_executes_upsert(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (42,)
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        result_id = jd_service.save_jd(1, self._JD_DATA)

        mock_cur.execute.assert_called_once()
        sql = mock_cur.execute.call_args[0][0]
        assert "INSERT INTO jd" in sql
        assert "ON CONFLICT" in sql
        assert result_id == 42

    @patch("cover_letter.jd_service._get_conn")
    def test_load_jd_returns_none_when_no_row(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        result = jd_service.load_jd(999)
        assert result is None

    @patch("cover_letter.jd_service._get_conn")
    def test_load_jd_returns_dict_when_row_exists(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (
            7,  # id
            "Python, FastAPI 개발 경험 필수",  # raw_text
            "https://example.com/job",  # source_url
            "firecrawl",  # source_type
            ["Python", "FastAPI"],  # required_competencies
            {},  # user_overrides
            "2026-04-10 00:00:00+00:00",  # collected_at
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        result = jd_service.load_jd(1)
        assert result is not None
        assert result["id"] == 7
        assert result["source_type"] == "firecrawl"
        assert "Python" in result["required_competencies"]
