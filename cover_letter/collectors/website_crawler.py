"""기업 공식 홈페이지 스크래퍼 — 인재상·비전·기업문화 추출.

Firecrawl API 사용. API 장애 시 None 반환.
"""

import os
from typing import Any


def crawl_company_website(company_name: str) -> dict | None:
    """Firecrawl을 통해 기업 인재상·비전·기업문화 정보 수집.

    Args:
        company_name: 기업명 (예: "카카오", "당근마켓")

    Returns:
        {"talent": str, "vision": str, "source_url": str}
        실패 시 None 반환.
    """
    try:
        from firecrawl import FirecrawlApp
    except ImportError:
        return None

    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        return None

    try:
        app = FirecrawlApp(api_key=api_key)
        query = f"{company_name} 채용 인재상 기업문화 비전 핵심가치"
        results: Any = app.search(query, limit=3)

        texts: list[str] = []
        source_url = ""
        items = results if isinstance(results, list) else (results.get("data") or [])
        for item in items:
            content = (
                item.get("markdown") or item.get("content") or item.get("text") or ""
            )
            if content.strip():
                texts.append(content.strip())
                if not source_url:
                    source_url = item.get("url") or item.get("sourceURL") or ""

        if not texts:
            return None

        combined = "\n\n".join(texts)[:3000]
        return {
            "talent": combined,
            "vision": "",
            "source_url": source_url,
        }
    except Exception:
        return None
