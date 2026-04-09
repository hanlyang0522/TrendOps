"""company_service, collectors 단위 테스트."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from cover_letter.collectors import dart_collector, naver_collector, website_crawler


# ============================================================
# dart_collector 테스트
# ============================================================
class TestDartCollector:
    def test_returns_empty_dict_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("DART_API_KEY", raising=False)
        result = dart_collector.collect_dart_reports("카카오")
        assert result == {}

    def test_returns_empty_dict_when_dart_fss_not_installed(self, monkeypatch):
        monkeypatch.setenv("DART_API_KEY", "test_key")
        with patch.dict("sys.modules", {"dart_fss": None}):
            result = dart_collector.collect_dart_reports("카카오")
        assert result == {}

    @patch.dict("os.environ", {"DART_API_KEY": ""})
    def test_empty_key_returns_empty_dict(self):
        result = dart_collector.collect_dart_reports("카카오")
        assert result == {}


# ============================================================
# naver_collector 테스트
# ============================================================
class TestNaverCollector:
    def test_returns_empty_list_when_no_credentials(self, monkeypatch):
        monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
        monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
        result = naver_collector.collect_news("카카오")
        assert result == []

    @patch("cover_letter.collectors.naver_collector._fetch_naver_news")
    def test_uses_firecrawl_fallback_when_less_than_5_articles(
        self, mock_naver, monkeypatch
    ):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test_key")
        mock_naver.return_value = [
            {"title": "뉴스1", "description": "", "pubDate": "", "link": "http://a.com"}
        ]  # 1건 < 5건

        with patch(
            "cover_letter.collectors.naver_collector._fetch_firecrawl"
        ) as mock_firecrawl:
            mock_firecrawl.return_value = [
                {
                    "title": "대체뉴스",
                    "description": "",
                    "pubDate": "",
                    "link": "http://b.com",
                }
            ]
            result = naver_collector.collect_news("카카오")

        mock_firecrawl.assert_called_once()
        assert len(result) == 2

    @patch("cover_letter.collectors.naver_collector._fetch_naver_news")
    def test_no_firecrawl_when_5_or_more_articles(self, mock_naver, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test_key")
        mock_naver.return_value = [
            {
                "title": f"뉴스{i}",
                "description": "",
                "pubDate": "",
                "link": f"http://{i}.com",
            }
            for i in range(5)
        ]

        with patch(
            "cover_letter.collectors.naver_collector._fetch_firecrawl"
        ) as mock_firecrawl:
            result = naver_collector.collect_news("카카오")

        mock_firecrawl.assert_not_called()
        assert len(result) == 5

    @patch("cover_letter.collectors.naver_collector._fetch_naver_news")
    def test_no_firecrawl_when_key_missing(self, mock_naver, monkeypatch):
        monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
        mock_naver.return_value = []

        with patch(
            "cover_letter.collectors.naver_collector._fetch_firecrawl"
        ) as mock_firecrawl:
            result = naver_collector.collect_news("카카오")

        mock_firecrawl.assert_not_called()
        assert result == []


# ============================================================
# website_crawler 테스트
# ============================================================
class TestWebsiteCrawler:
    def test_returns_none_when_no_naver_credentials(self, monkeypatch):
        monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
        monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
        result = website_crawler.crawl_company_website("카카오")
        assert result is None

    @patch("cover_letter.collectors.website_crawler._find_homepage")
    def test_returns_none_when_homepage_not_found(self, mock_find):
        mock_find.return_value = None
        result = website_crawler.crawl_company_website("알수없는기업")
        assert result is None

    @patch("cover_letter.collectors.website_crawler._find_homepage")
    @patch("cover_letter.collectors.website_crawler._scrape_page")
    def test_tries_talent_urls_first(self, mock_scrape, mock_find):
        import sys

        fake_requests = MagicMock()
        fake_bs4 = MagicMock()
        with patch.dict("sys.modules", {"requests": fake_requests, "bs4": fake_bs4}):
            mock_find.return_value = "https://kakao.com"
            mock_scrape.return_value = None  # 모든 시도 실패
            result = website_crawler.crawl_company_website("카카오")
        assert result is None
        assert mock_scrape.call_count > 1  # 여러 URL 시도

    @patch("cover_letter.collectors.website_crawler._find_homepage")
    @patch("cover_letter.collectors.website_crawler._scrape_page")
    def test_returns_dict_when_page_scraped(self, mock_scrape, mock_find):
        fake_requests = MagicMock()
        fake_bs4 = MagicMock()
        with patch.dict("sys.modules", {"requests": fake_requests, "bs4": fake_bs4}):
            mock_find.return_value = "https://kakao.com"
            mock_scrape.return_value = {
                "talent": "인재상 내용",
                "vision": "",
                "source_url": "https://kakao.com/recruit",
            }
            result = website_crawler.crawl_company_website("카카오")
        assert result is not None
        assert "talent" in result


# ============================================================
# get_or_analyze_company 테스트
# ============================================================
class TestGetOrAnalyzeCompany:
    @patch("cover_letter.company_service._get_conn")
    @patch("cover_letter.company_service._full_analysis")
    def test_cache_miss_calls_full_analysis(self, mock_full, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_c = MagicMock()
        mock_c.__enter__ = MagicMock(return_value=mock_c)
        mock_c.__exit__ = MagicMock(return_value=False)
        mock_c.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_c

        mock_full.return_value = {"id": 1, "company_name": "카카오"}

        from cover_letter import company_service

        result = company_service.get_or_analyze_company("카카오")

        mock_full.assert_called_once()
        assert result["company_name"] == "카카오"

    @patch("cover_letter.company_service._get_conn")
    @patch("cover_letter.company_service._summarize_news")
    def test_cache_hit_refreshes_news(self, mock_news, mock_conn):
        # analyzed_at이 오늘 (캐시 히트)
        recent = datetime.now(timezone.utc)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            1,
            "카카오",
            "개요",
            "문화",
            "동향",
            "특장점",
            "뉴스",
            "DART요약",
            recent,
            {},
        )
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_c = MagicMock()
        mock_c.__enter__ = MagicMock(return_value=mock_c)
        mock_c.__exit__ = MagicMock(return_value=False)
        mock_c.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_c

        mock_news.return_value = "새 뉴스"

        from cover_letter import company_service

        result = company_service.get_or_analyze_company("카카오")

        assert result["news_summary"] == "새 뉴스"

    @patch("cover_letter.company_service._get_conn")
    @patch("cover_letter.company_service._full_analysis")
    def test_old_cache_triggers_full_analysis(self, mock_full, mock_conn):
        # analyzed_at이 8일 전 (캐시 만료)
        old = datetime.now(timezone.utc) - timedelta(days=8)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            1,
            "카카오",
            "개요",
            "문화",
            "동향",
            "특장점",
            "뉴스",
            "DART요약",
            old,
            {},
        )
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_c = MagicMock()
        mock_c.__enter__ = MagicMock(return_value=mock_c)
        mock_c.__exit__ = MagicMock(return_value=False)
        mock_c.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_c

        mock_full.return_value = {"id": 1, "company_name": "카카오"}

        from cover_letter import company_service

        company_service.get_or_analyze_company("카카오")

        mock_full.assert_called_once()

    @patch("cover_letter.company_service._get_conn")
    @patch("cover_letter.company_service.dart_collector.collect_dart_reports")
    @patch("cover_letter.company_service.naver_collector.collect_news")
    @patch("cover_letter.company_service.website_crawler.crawl_company_website")
    @patch("cover_letter.company_service.llm_client.call")
    def test_partial_source_failure_continues(
        self, mock_llm, mock_web, mock_naver, mock_dart, mock_conn
    ):
        """DART 실패, 홈페이지 실패 시에도 Naver 뉴스만으로 분석 계속."""
        mock_dart.return_value = {}  # DART 실패
        mock_naver.return_value = [
            {
                "title": "뉴스",
                "description": "내용",
                "pubDate": "",
                "link": "http://a.com",
            }
        ]
        mock_web.return_value = None  # 홈페이지 실패

        mock_llm.return_value = json.dumps(
            {
                "overview": "테스트 개요",
                "culture_and_values": "",
                "industry_trends": "",
                "competitive_edge": "",
                "dart_summary": "",
            }
        )

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            None,  # company_analysis 조회 → 없음
            (1, datetime.now(timezone.utc)),  # INSERT RETURNING
        ]
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_c = MagicMock()
        mock_c.__enter__ = MagicMock(return_value=mock_c)
        mock_c.__exit__ = MagicMock(return_value=False)
        mock_c.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_c

        from cover_letter import company_service

        result = company_service.get_or_analyze_company("카카오")

        assert result is not None
        mock_llm.assert_called_once()
