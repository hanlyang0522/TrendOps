"""
네이버 뉴스 API를 사용하여 특정 키워드로 뉴스를 검색하고 데이터베이스에 저장하는 스크립트입니다.
Naver News API (MCP)를 통해 뉴스 데이터를 안전하고 안정적으로 가져옵니다.
"""

import os

import requests

from db.db_news import create_new_news, get_connection


def get_naver_api_credentials() -> tuple[str, str]:
    """
    환경 변수에서 네이버 API 인증 정보를 가져옵니다.

    Returns:
        tuple[str, str]: (client_id, client_secret)

    Raises:
        ValueError: 필수 환경 변수가 없을 경우
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "Missing required Naver API credentials. "
            "Please set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET environment variables."
        )

    return client_id, client_secret


def search_naver_news(
    query: str, display: int = 10, start: int = 1, sort: str = "date"
) -> list[dict[str, str]]:
    """
    네이버 뉴스 API를 사용하여 뉴스를 검색합니다.

    Args:
        query: 검색 키워드
        display: 표시할 결과 수 (기본값: 10, 최대: 100)
        start: 결과 시작 위치 (기본값: 1)
        sort: 정렬 옵션 (sim: 관련도, date: 날짜)

    Returns:
        list[dict[str, str]]: 뉴스 기사 목록

    Raises:
        requests.exceptions.RequestException: API 요청 실패 시
    """
    client_id, client_secret = get_naver_api_credentials()

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params: dict[str, str | int] = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items: list[dict[str, str]] = data.get("items", [])
        return items

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch news from Naver API: {e}")
        raise


if __name__ == "__main__":
    # 환경 변수에서 검색 키워드 가져오기
    search_keyword = os.getenv("SEARCH_KEYWORD", "당근마켓")
    max_articles = int(os.getenv("MAX_ARTICLES", "50"))

    print(f"Searching for news with keyword: {search_keyword}")
    print(f"Maximum articles to fetch: {max_articles}")

    # Store news in the database
    get_connection()

    # 네이버 뉴스 API를 통해 뉴스 검색
    try:
        articles = search_naver_news(query=search_keyword, display=max_articles)

        for article in articles:
            # HTML 태그 제거 (네이버 API는 제목에 <b> 태그를 포함할 수 있음)
            title = article.get("title", "").replace("<b>", "").replace("</b>", "")
            url = article.get("link", "")

            if title and url:
                create_new_news(title, url)
                print(f"Title: {title}\nURL: {url}\n")

        print(f"Total articles fetched: {len(articles)}")

    except ValueError as e:
        print(f"Configuration error: {e}")
        print(
            "Please set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET "
            "in your environment variables."
        )
        exit(1)
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)
