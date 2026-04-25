"""기업 공식 홈페이지 스크래퍼 — 인재상·비전·기업문화 추출.

Firecrawl API 사용. API 장애 시 None 반환.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _normalize_firecrawl_items(results: Any) -> list[dict[str, Any]]:
    """Firecrawl search 응답을 dict 리스트로 정규화.

    firecrawl-py 버전에 따라 list/dict/Pydantic(SearchData) 형태가 다르다.
    """
    if isinstance(results, list):
        return [item for item in results if isinstance(item, dict)]

    if hasattr(results, "web") or hasattr(results, "news"):
        items: list[dict[str, Any]] = []
        for group in (getattr(results, "web", None), getattr(results, "news", None)):
            for entry in group or []:
                if isinstance(entry, dict):
                    items.append(entry)
                elif hasattr(entry, "model_dump"):
                    items.append(entry.model_dump())
        return items

    if isinstance(results, dict):
        raw_items = results.get("data") or results.get("web") or []
        return [item for item in raw_items if isinstance(item, dict)]

    return []


def crawl_company_website_with_status(company_name: str) -> dict:
    """인재상·비전·기업문화 수집 결과와 상태를 함께 반환.

    Returns:
        {
            "success": bool,
            "data": dict | None,
            "reason": str,
        }
    """
    try:
        from firecrawl import FirecrawlApp
    except ImportError:
        return {
            "success": False,
            "data": None,
            "reason": "firecrawl 미설치",
        }

    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        return {
            "success": False,
            "data": None,
            "reason": "FIRECRAWL_API_KEY 미설정",
        }

    try:
        app = FirecrawlApp(api_key=api_key)
        query = f"{company_name} 채용 인재상 기업문화 비전 핵심가치"
        results: Any = app.search(query, limit=3)

        texts: list[str] = []
        source_url = ""
        items = _normalize_firecrawl_items(results)
        for item in items:
            content = (
                item.get("markdown")
                or item.get("content")
                or item.get("text")
                or item.get("description")
                or ""
            )
            if content.strip():
                texts.append(content.strip())
                if not source_url:
                    source_url = item.get("url") or item.get("sourceURL") or ""

        if not texts:
            return {
                "success": False,
                "data": None,
                "reason": "검색 결과 텍스트 없음",
            }

        combined = "\n\n".join(texts)[:3000]
        return {
            "success": True,
            "data": {
                "talent": combined,
                "vision": "",
                "source_url": source_url,
            },
            "reason": "",
        }
    except Exception:
        logger.exception("홈페이지 크롤링 실패: company=%s", company_name)
        return {
            "success": False,
            "data": None,
            "reason": "Firecrawl 검색 호출 실패",
        }


def crawl_company_website(company_name: str) -> dict | None:
    """Firecrawl을 통해 기업 인재상·비전·기업문화 정보 수집.

    Args:
        company_name: 기업명 (예: "카카오", "당근마켓")

    Returns:
        {"talent": str, "vision": str, "source_url": str}
        실패 시 None 반환.
    """
    status = crawl_company_website_with_status(company_name)
    data = status.get("data")
    return data if isinstance(data, dict) else None
