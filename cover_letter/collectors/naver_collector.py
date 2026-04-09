"""Naver News 수집기 — 기존 crawling 모듈 활용 + Firecrawl fallback.

5건 미만 수집 시 FIRECRAWL_API_KEY가 있으면 Firecrawl API로 fallback.
"""

import os


def collect_news(company_name: str, job_title: str = "") -> list[dict]:
    """Naver News API로 기업 관련 뉴스 수집.

    Args:
        company_name: 기업명
        job_title: 직무명 (검색어 보강에 사용)

    Returns:
        뉴스 항목 목록:
        [{"title": str, "description": str, "pubDate": str, "link": str}]
        수집 실패 시 빈 리스트 반환.
    """
    query = f"{company_name} {job_title}".strip() if job_title else company_name

    articles = _fetch_naver_news(query, display=10)

    if len(articles) < 5:
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")
        if firecrawl_key:
            fallback = _fetch_firecrawl(query, firecrawl_key)
            # 중복 없이 병합
            existing_links = {a.get("link") for a in articles}
            for item in fallback:
                if item.get("link") not in existing_links:
                    articles.append(item)

    return articles


def _fetch_naver_news(query: str, display: int = 10) -> list[dict]:
    """Naver OpenAPI로 뉴스 검색. 자격증명 없으면 빈 리스트 반환."""
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return []

    try:
        import requests  # type: ignore[import-untyped]

        response = requests.get(
            "https://openapi.naver.com/v1/search/news.json",
            params={"query": query, "display": str(display), "sort": "date"},
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return list(data.get("items", []))
    except Exception:
        return []


def _fetch_firecrawl(query: str, api_key: str) -> list[dict]:
    """Firecrawl API로 뉴스 검색 fallback. 실패 시 빈 리스트 반환."""
    try:
        import requests  # type: ignore[import-untyped]

        response = requests.post(
            "https://api.firecrawl.dev/v1/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"query": query, "limit": 10, "lang": "ko"},
            timeout=15,
        )
        response.raise_for_status()
        results = response.json().get("data", [])
        return [
            {
                "title": r.get("title", ""),
                "description": r.get("description", ""),
                "pubDate": r.get("publishedDate", ""),
                "link": r.get("url", ""),
            }
            for r in results
        ]
    except Exception:
        return []
