"""
Naver MCP 크롤러 테스트

pytest를 사용한 단위 테스트 및 통합 테스트
"""

import os
from unittest.mock import Mock, patch

import pytest

from crawling.naver_mcp_crawler import NaverMCPCrawler


class TestNaverMCPCrawler:
    """Naver MCP 크롤러 테스트"""

    def test_init_with_credentials(self):
        """생성자에 직접 credentials를 전달하는 경우"""
        crawler = NaverMCPCrawler(
            client_id="test_id",
            client_secret="test_secret",
        )
        assert crawler.client_id == "test_id"
        assert crawler.client_secret == "test_secret"

    def test_init_with_env_variables(self):
        """환경 변수에서 credentials를 가져오는 경우"""
        with patch.dict(
            os.environ,
            {
                "X_NAVER_CLIENT_ID": "env_id",
                "X_NAVER_CLIENT_SECRET": "env_secret",
            },
        ):
            crawler = NaverMCPCrawler()
            assert crawler.client_id == "env_id"
            assert crawler.client_secret == "env_secret"

    def test_init_without_credentials(self):
        """credentials가 없는 경우 에러 발생"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="credentials are required"):
                NaverMCPCrawler()

    def test_search_news_invalid_query(self):
        """빈 query로 검색 시 에러 발생"""
        crawler = NaverMCPCrawler(client_id="test", client_secret="test")
        with pytest.raises(ValueError, match="검색 키워드는 필수"):
            crawler.search_news(query="")

    def test_search_news_invalid_display(self):
        """잘못된 display 값으로 검색 시 에러 발생"""
        crawler = NaverMCPCrawler(client_id="test", client_secret="test")
        with pytest.raises(ValueError, match="display는 1~100"):
            crawler.search_news(query="테스트", display=0)
        with pytest.raises(ValueError, match="display는 1~100"):
            crawler.search_news(query="테스트", display=101)

    def test_search_news_invalid_sort(self):
        """잘못된 sort 값으로 검색 시 에러 발생"""
        crawler = NaverMCPCrawler(client_id="test", client_secret="test")
        with pytest.raises(ValueError, match="sort는 'date' 또는 'sim'"):
            crawler.search_news(query="테스트", sort="invalid")

    @patch("crawling.naver_mcp_crawler.requests.get")
    def test_search_news_success(self, mock_get):
        """정상적인 뉴스 검색"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 100,
            "start": 1,
            "display": 10,
            "items": [
                {
                    "title": "<b>당근마켓</b> 뉴스 1",
                    "link": "https://example.com/1",
                    "description": "테스트 설명 1",
                    "pubDate": "Mon, 09 Feb 2026 10:00:00 +0900",
                },
                {
                    "title": "<b>당근마켓</b> 뉴스 2",
                    "link": "https://example.com/2",
                    "description": "테스트 설명 2",
                    "pubDate": "Mon, 09 Feb 2026 09:00:00 +0900",
                },
            ],
        }
        mock_get.return_value = mock_response

        crawler = NaverMCPCrawler(client_id="test", client_secret="test")
        result = crawler.search_news(query="당근마켓", display=10)

        # 결과 검증
        assert result["total"] == 100
        assert len(result["items"]) == 2
        assert result["items"][0]["title"] == "<b>당근마켓</b> 뉴스 1"

        # API 호출 검증
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["params"]["query"] == "당근마켓"
        assert call_args[1]["params"]["display"] == 10

    @patch("crawling.naver_mcp_crawler.requests.get")
    def test_search_news_authentication_error(self, mock_get):
        """인증 실패 시 에러 처리"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")

        mock_get.return_value = mock_response

        crawler = NaverMCPCrawler(client_id="wrong", client_secret="wrong")

        with pytest.raises(ValueError, match="인증 실패"):
            crawler.search_news(query="테스트")

    @patch("crawling.naver_mcp_crawler.requests.get")
    def test_search_news_rate_limit(self, mock_get):
        """API 호출 한도 초과 시 에러 처리"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")

        mock_get.return_value = mock_response

        crawler = NaverMCPCrawler(client_id="test", client_secret="test")

        with pytest.raises(ValueError, match="API 호출 한도"):
            crawler.search_news(query="테스트")

    @patch("crawling.naver_mcp_crawler.requests.get")
    def test_crawl_news_multiple_pages(self, mock_get):
        """여러 페이지 크롤링 테스트"""
        # Mock 응답 설정 (페이지별로 다른 응답)
        def mock_response_side_effect(*args, **kwargs):
            start = kwargs["params"]["start"]
            mock_response = Mock()
            mock_response.status_code = 200

            if start == 1:
                items = [
                    {
                        "title": f"<b>뉴스</b> {i}",
                        "link": f"https://example.com/{i}",
                        "description": f"설명 {i}",
                        "pubDate": f"Mon, 0{i} Feb 2026 10:00:00 +0900",
                    }
                    for i in range(1, 11)
                ]
            elif start == 11:
                items = [
                    {
                        "title": f"<b>뉴스</b> {i}",
                        "link": f"https://example.com/{i}",
                        "description": f"설명 {i}",
                        "pubDate": f"Mon, 0{i} Feb 2026 10:00:00 +0900",
                    }
                    for i in range(11, 21)
                ]
            else:
                items = []

            mock_response.json.return_value = {"items": items}
            return mock_response

        mock_get.side_effect = mock_response_side_effect

        crawler = NaverMCPCrawler(client_id="test", client_secret="test")
        result = crawler.crawl_news(keyword="테스트", max_pages=2)

        # 결과 검증
        assert len(result) == 20
        assert result[0]["title"] == "뉴스 1"  # HTML 태그 제거됨
        assert result[10]["title"] == "뉴스 11"

    def test_remove_html_tags(self):
        """HTML 태그 제거 테스트"""
        crawler = NaverMCPCrawler(client_id="test", client_secret="test")

        # 기본 HTML 태그
        assert crawler._remove_html_tags("<b>굵은글씨</b>") == "굵은글씨"
        assert (
            crawler._remove_html_tags("<b>당근</b><i>마켓</i>") == "당근마켓"
        )

        # HTML 엔티티
        assert crawler._remove_html_tags("&quot;인용&quot;") == '"인용"'
        assert crawler._remove_html_tags("&amp;") == "&"
        assert crawler._remove_html_tags("&lt;&gt;") == "<>"

        # 복합
        assert (
            crawler._remove_html_tags("<b>&quot;당근마켓&quot;</b>")
            == '"당근마켓"'
        )


# 통합 테스트 (실제 API 호출 - 환경 변수 필요)
@pytest.mark.skipif(
    not os.getenv("X_NAVER_CLIENT_ID") or not os.getenv("X_NAVER_CLIENT_SECRET"),
    reason="Naver OpenAPI credentials not available",
)
class TestNaverMCPCrawlerIntegration:
    """Naver MCP 크롤러 통합 테스트 (실제 API 호출)"""

    def test_real_api_search(self):
        """실제 API를 사용한 뉴스 검색"""
        crawler = NaverMCPCrawler()
        result = crawler.search_news(query="당근마켓", display=5)

        # 응답 구조 검증
        assert "total" in result
        assert "items" in result
        assert isinstance(result["items"], list)

        # 최소 1개 이상의 결과
        if result["items"]:
            item = result["items"][0]
            assert "title" in item
            assert "link" in item
            assert "description" in item
            assert "pubDate" in item

    def test_real_api_crawl(self):
        """실제 API를 사용한 다중 페이지 크롤링"""
        crawler = NaverMCPCrawler()
        result = crawler.crawl_news(keyword="당근마켓", max_pages=1)

        assert isinstance(result, list)
        if result:
            # HTML 태그가 제거되었는지 확인
            assert "<b>" not in result[0]["title"]
            assert "&quot;" not in result[0]["title"]
