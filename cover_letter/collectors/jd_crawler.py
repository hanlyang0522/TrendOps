"""JD(직무기술서) 크롤러 — Firecrawl 우선, PDF 폴백.

spec: FR-003d — 기업명·직무명으로 JD 자동 수집.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _normalize_firecrawl_items(results: Any) -> list[dict[str, Any]]:
    """Firecrawl search 응답을 dict 리스트로 정규화."""
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


def crawl_jd(company_name: str, job_title: str) -> dict:
    """기업명과 직무명으로 JD 텍스트 자동 수집.

    수집 우선순위:
    1. Firecrawl search API — 채용공고 페이지 텍스트 추출
    2. PDF URL 감지 시 pdfminer.six 폴백
    3. 실패 시 manual 입력 안내

    Args:
        company_name: 기업명 (예: "카카오")
        job_title: 직무명 (예: "백엔드 개발자")

    Returns:
        {
            "success": bool,
            "text": str | None,       # JD 원문
            "source_url": str,        # 출처 URL
            "source_type": str,       # 'firecrawl' | 'pdf' | 'manual'
            "error_reason": str,      # 실패 원인(성공 시 빈 문자열)
        }
    """
    result = _crawl_via_firecrawl(company_name, job_title)
    if result["success"]:
        return result

    return {
        "success": False,
        "text": None,
        "source_url": "",
        "source_type": "manual",
        "error_reason": result.get("error_reason", "JD 자동 수집 실패"),
    }


def _crawl_via_firecrawl(company_name: str, job_title: str) -> dict:
    """Firecrawl search API로 JD 수집."""
    try:
        from firecrawl import FirecrawlApp
    except ImportError:
        return {
            "success": False,
            "text": None,
            "source_url": "",
            "source_type": "manual",
            "error_reason": "firecrawl 미설치",
        }

    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        return {
            "success": False,
            "text": None,
            "source_url": "",
            "source_type": "manual",
            "error_reason": "FIRECRAWL_API_KEY 미설정",
        }

    try:
        app = FirecrawlApp(api_key=api_key)
        query = f"{company_name} {job_title} 채용공고 JD 직무기술서 자격요건 우대사항"
        results: Any = app.search(query, limit=3)

        items = _normalize_firecrawl_items(results)
        if not items:
            return {
                "success": False,
                "text": None,
                "source_url": "",
                "source_type": "manual",
                "error_reason": "검색 결과 없음",
            }

        last_reason = "검색 결과에서 텍스트 추출 실패"
        for item in items:
            url: str = item.get("url") or item.get("sourceURL") or ""
            content: str = (
                item.get("markdown")
                or item.get("content")
                or item.get("text")
                or item.get("description")
                or ""
            ).strip()

            # PDF URL이 감지되고 텍스트가 없으면 pdfminer 폴백
            if url.lower().endswith(".pdf") and not content:
                pdf_text = _extract_pdf_from_url(url)
                if pdf_text:
                    return {
                        "success": True,
                        "text": pdf_text,
                        "source_url": url,
                        "source_type": "pdf",
                        "error_reason": "",
                    }
                last_reason = "PDF 텍스트 추출 실패"
                continue

            if content:
                return {
                    "success": True,
                    "text": content[:5000],
                    "source_url": url,
                    "source_type": "firecrawl",
                    "error_reason": "",
                }
        return {
            "success": False,
            "text": None,
            "source_url": "",
            "source_type": "manual",
            "error_reason": last_reason,
        }
    except Exception:
        logger.exception("JD 수집 실패: company=%s, job=%s", company_name, job_title)
        return {
            "success": False,
            "text": None,
            "source_url": "",
            "source_type": "manual",
            "error_reason": "Firecrawl 검색 호출 실패",
        }

    return {
        "success": False,
        "text": None,
        "source_url": "",
        "source_type": "manual",
        "error_reason": "JD 자동 수집 실패",
    }


def _extract_pdf_from_url(url: str) -> str | None:
    """PDF URL에서 pdfminer.six로 텍스트 추출. 실패 시 None."""
    try:
        import io

        import requests
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams

        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TrendOpsBot/1.0)"},
            timeout=20,
        )
        response.raise_for_status()

        out = io.StringIO()
        extract_text_to_fp(
            io.BytesIO(response.content),
            out,
            laparams=LAParams(),
            output_type="text",
            codec="utf-8",
        )
        text = out.getvalue().strip()
        return text[:5000] if text else None
    except Exception:
        return None
