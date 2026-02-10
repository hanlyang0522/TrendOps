"""
Naver MCP 기반 뉴스 크롤링 모듈

Naver OpenAPI를 사용하여 뉴스를 검색하고 크롤링합니다.
"""

import os
from typing import Any, Optional

import requests


class NaverMCPCrawler:
    """Naver OpenAPI를 사용한 뉴스 크롤러"""

    BASE_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Naver MCP 크롤러 초기화

        Args:
            client_id: Naver OpenAPI Client ID
            client_secret: Naver OpenAPI Client Secret
        """
        self.client_id = client_id or os.getenv("X_NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("X_NAVER_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Naver OpenAPI credentials are required. "
                "Set X_NAVER_CLIENT_ID and X_NAVER_CLIENT_SECRET environment variables."
            )

    def search_news(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
    ) -> Any:
        """
        Naver 뉴스 검색

        Args:
            query: 검색 키워드
            display: 한 번에 표시할 검색 결과 개수 (최대 100)
            start: 검색 시작 위치 (1부터 시작)
            sort: 정렬 옵션 ('date': 날짜순, 'sim': 정확도순)

        Returns:
            검색 결과 딕셔너리

        Raises:
            requests.exceptions.RequestException: API 호출 실패 시
        """
        if not query:
            raise ValueError("검색 키워드는 필수입니다.")

        if display < 1 or display > 100:
            raise ValueError("display는 1~100 사이의 값이어야 합니다.")

        if sort not in ["date", "sim"]:
            raise ValueError("sort는 'date' 또는 'sim'이어야 합니다.")

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        params: dict[str, str | int] = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort,
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=10,
            )

            # 에러 상태 코드 체크
            if response.status_code == 401:
                raise ValueError(
                    "Naver OpenAPI 인증 실패. Client ID와 Secret을 확인하세요."
                )
            elif response.status_code == 429:
                raise ValueError(
                    "API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요."
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "Naver OpenAPI 인증 실패. Client ID와 Secret을 확인하세요."
                ) from e
            elif e.response.status_code == 429:
                raise ValueError(
                    "API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요."
                ) from e
            raise

    def crawl_news(
        self,
        keyword: str,
        max_pages: int = 3,
        sort: str = "date",
    ) -> list[dict[str, str]]:
        """
        여러 페이지의 뉴스를 크롤링

        Args:
            keyword: 검색 키워드
            max_pages: 크롤링할 최대 페이지 수
            sort: 정렬 방식 ('date' 또는 'sim')

        Returns:
            뉴스 기사 목록 (title, link, description, pubDate 포함)
        """
        all_news = []

        for page in range(max_pages):
            start = page * 10 + 1
            print(f"페이지 {page + 1} 크롤링 중... (start={start})")

            try:
                result = self.search_news(
                    query=keyword,
                    display=10,
                    start=start,
                    sort=sort,
                )

                items = result.get("items", [])
                if not items:
                    print(f"페이지 {page + 1}에서 더 이상 기사를 찾을 수 없습니다.")
                    break

                # HTML 태그 제거 및 데이터 정리
                for item in items:
                    cleaned_item = {
                        "title": self._remove_html_tags(item.get("title", "")),
                        "link": item.get("link", ""),
                        "description": self._remove_html_tags(
                            item.get("description", "")
                        ),
                        "pubDate": item.get("pubDate", ""),
                    }
                    all_news.append(cleaned_item)

                print(f"페이지 {page + 1}: {len(items)}개 기사 수집 완료")

            except Exception as e:
                print(f"페이지 {page + 1} 크롤링 중 오류 발생: {e}")
                break

        return all_news

    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """HTML 태그 제거"""
        import re

        # <b>, </b> 등 HTML 태그 제거
        clean = re.sub(r"<[^>]+>", "", text)
        # &quot;, &amp; 등 HTML 엔티티 변환
        clean = clean.replace("&quot;", '"')
        clean = clean.replace("&amp;", "&")
        clean = clean.replace("&lt;", "<")
        clean = clean.replace("&gt;", ">")
        return clean.strip()


def main():
    """메인 실행 함수"""
    # 환경 변수에서 설정 가져오기
    keyword = os.getenv("SEARCH_KEYWORD", "당근마켓")
    max_pages = int(os.getenv("MAX_PAGES", "3"))
    sort = os.getenv("SORT_ORDER", "date")

    print("=== Naver MCP 뉴스 크롤링 시작 ===")
    print(f"키워드: {keyword}")
    print(f"최대 페이지: {max_pages}")
    print(f"정렬: {sort}")
    print("")

    try:
        # Naver MCP 크롤러 초기화
        crawler = NaverMCPCrawler()

        # 뉴스 크롤링
        news_list = crawler.crawl_news(
            keyword=keyword,
            max_pages=max_pages,
            sort=sort,
        )

        if not news_list:
            print("수집된 뉴스가 없습니다.")
            return

        print(f"\n총 {len(news_list)}개의 기사를 수집했습니다.")

        # 결과 출력
        for i, news in enumerate(news_list, 1):
            print(f"\n[{i}] {news['title']}")
            print(f"    링크: {news['link']}")
            print(f"    날짜: {news['pubDate']}")
            print(f"    요약: {news['description'][:100]}...")

        print("\n=== 크롤링 완료 ===")

    except ValueError as e:
        print(f"설정 오류: {e}")
        print(
            "\n환경 변수를 확인하세요:"
            "\n  X_NAVER_CLIENT_ID"
            "\n  X_NAVER_CLIENT_SECRET"
        )
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
