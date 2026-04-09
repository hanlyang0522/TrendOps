"""DART 사업보고서 수집기 — dart-fss 라이브러리 기반.

DART_API_KEY 미설정 시 빈 dict 반환 (optional 수집기).
"""

import os


def collect_dart_reports(company_name: str, years: int = 3) -> dict:
    """DART 사업보고서에서 주요 항목 추출.

    Args:
        company_name: 기업명 (예: "카카오", "삼성전자")
        years: 수집 대상 연도 수 (기본: 최근 3년)

    Returns:
        {
            "products": str,        # 주요 제품/서비스
            "market_conditions": str,  # 시장현황
            "r_and_d": str,         # 연구개발
            "major_contracts": str, # 주요계약
        }
        DART_API_KEY 미설정 또는 수집 실패 시 빈 dict 반환.
    """
    api_key = os.getenv("DART_API_KEY", "")
    if not api_key:
        return {}

    try:
        import dart_fss as dart  # type: ignore[import-untyped]
    except ImportError:
        return {}

    try:
        dart.set_api_key(api_key=api_key)
        corp_list = dart.api.filings.get_corp_code()

        # 기업 코드 검색
        target = None
        for corp in corp_list:
            if corp.get("corp_name") == company_name:
                target = corp
                break

        if target is None:
            return {}

        corp_code = target["corp_code"]

        # 최근 사업보고서 검색
        filings = dart.api.filings.get_list(
            corp_code=corp_code,
            bgn_de=_years_ago(years),
            pblntf_ty="A",  # 사업보고서
        )

        if not filings or not filings.get("list"):
            return {}

        latest = filings["list"][0]
        rcp_no = latest["rcept_no"]

        result: dict[str, str] = {}

        # 주요 항목 추출
        _extract_section(dart, rcp_no, "주요 제품 및 서비스", result, "products")
        _extract_section(dart, rcp_no, "시장현황", result, "market_conditions")
        _extract_section(dart, rcp_no, "연구개발", result, "r_and_d")

        return result

    except Exception:
        return {}


def _years_ago(n: int) -> str:
    """n년 전 날짜를 YYYYMMDD 형식으로 반환."""
    from datetime import datetime, timedelta

    past = datetime.now() - timedelta(days=365 * n)
    return past.strftime("%Y%m%d")


def _extract_section(
    dart, rcp_no: str, section_name: str, result: dict, key: str
) -> None:
    """사업보고서에서 특정 섹션 텍스트 추출. 실패 시 무시."""
    try:
        docs = dart.api.document.get_document(rcp_no)
        for item in docs.get("list", []):
            if section_name in item.get("title", ""):
                content = item.get("sub_docs", [{}])[0].get("text_content", "")
                if content:
                    # 최대 2000자로 제한
                    result[key] = content[:2000]
                    return
    except Exception:
        pass
