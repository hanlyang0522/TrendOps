"""JD(직무기술서) 크롤러 — Firecrawl 우선, PDF 폴백.

spec: FR-003d — 기업명·직무명으로 JD 자동 수집.
"""

import os
from typing import Any


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
        }

    api_key = os.getenv("FIRECRAWL_API_KEY", "")
    if not api_key:
        return {
            "success": False,
            "text": None,
            "source_url": "",
            "source_type": "manual",
        }

    try:
        app = FirecrawlApp(api_key=api_key)
        query = f"{company_name} {job_title} 채용공고 JD 직무기술서 자격요건 우대사항"
        results: Any = app.search(query, limit=3)

        items = results if isinstance(results, list) else (results.get("data") or [])
        for item in items:
            url: str = item.get("url") or item.get("sourceURL") or ""
            content: str = (
                item.get("markdown") or item.get("content") or item.get("text") or ""
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
                    }
                continue

            if content:
                return {
                    "success": True,
                    "text": content[:5000],
                    "source_url": url,
                    "source_type": "firecrawl",
                }
    except Exception:
        pass

    return {"success": False, "text": None, "source_url": "", "source_type": "manual"}


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
