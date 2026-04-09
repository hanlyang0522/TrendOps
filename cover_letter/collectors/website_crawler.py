"""기업 공식 홈페이지 스크래퍼 — 인재상·비전 페이지 추출.

네트워크 오류 또는 알 수 없는 페이지 구조 시 None 반환.
"""

import re

# 인재상·채용 관련 URL 패턴 (한국 기업 공식 홈페이지 공통 패턴)
_TALENT_URL_PATTERNS = [
    "/recruit/culture",
    "/recruit/talent",
    "/career/culture",
    "/company/culture",
    "/about/culture",
    "/people",
    "/team-culture",
    "/talent",
    "/recruit",
    "/career",
]

_VISION_KEYWORDS = ["인재상", "비전", "미션", "핵심가치", "우리가 추구하는", "우리는"]


def crawl_company_website(company_name: str) -> dict | None:
    """기업 공식 홈페이지에서 인재상·비전 정보 스크래핑.

    Args:
        company_name: 기업명 (예: "카카오", "당근마켓")

    Returns:
        {"talent": str, "vision": str, "source_url": str}
        실패(네트워크 오류·알 수 없는 페이지 구조) 시 None 반환.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    # 1. 기업 공식 홈페이지 URL 추측 (Naver 검색으로 확인)
    homepage_url = _find_homepage(company_name)
    if not homepage_url:
        return None

    # 2. 인재상/비전 관련 하위 URL 시도
    for pattern in _TALENT_URL_PATTERNS:
        candidate = homepage_url.rstrip("/") + pattern
        result = _scrape_page(candidate)
        if result:
            return result

    # 3. 홈페이지 메인 페이지에서 추출 시도
    return _scrape_page(homepage_url)


def _find_homepage(company_name: str) -> str | None:
    """Naver 검색으로 기업 공식 홈페이지 URL 추출. 실패 시 None."""
    try:
        import requests

        client_id = __import__("os").getenv("NAVER_CLIENT_ID", "")
        client_secret = __import__("os").getenv("NAVER_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            return None

        response = requests.get(
            "https://openapi.naver.com/v1/search/webkr.json",
            params={"query": f"{company_name} 공식 홈페이지", "display": "3"},
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        if items:
            return str(items[0].get("link", ""))
    except Exception:
        pass
    return None


def _scrape_page(url: str) -> dict | None:
    """단일 URL에서 인재상/비전 텍스트 추출. 실패 시 None."""
    try:
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TrendOpsBot/1.0)"},
            timeout=10,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # script, style 제거
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # 인재상/비전 관련 내용 포함 여부 확인
        if not any(kw in text for kw in _VISION_KEYWORDS):
            return None

        # 관련 섹션 추출 (최대 1500자)
        relevant = _extract_relevant_section(text)
        if not relevant:
            return None

        return {
            "talent": relevant,
            "vision": "",
            "source_url": url,
        }
    except Exception:
        return None


def _extract_relevant_section(text: str) -> str:
    """텍스트에서 인재상/비전 관련 섹션만 추출."""
    lines = text.split("\n")
    result_lines: list[str] = []
    capturing = False
    captured_length = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if any(kw in stripped for kw in _VISION_KEYWORDS):
            capturing = True

        if capturing:
            result_lines.append(stripped)
            captured_length += len(stripped)
            if captured_length >= 1500:
                break

    return "\n".join(result_lines)
