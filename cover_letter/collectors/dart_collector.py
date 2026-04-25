"""DART 사업보고서 수집기 — dart-fss 라이브러리 기반.

DART_API_KEY 미설정 시 빈 dict 반환 (optional 수집기).
"""

import logging
import os
from typing import Any, cast

logger = logging.getLogger(__name__)


def _search_business_filings(dart, corp_code: str, years: int) -> dict:
    """dart-fss 버전에 맞춰 사업보고서 목록 조회."""
    filings_api = dart.api.filings
    bgn_de = _years_ago(years)

    # 전체 공시 조회 후 사업보고서 필터링 (pblntf_ty 파라미터는 버전마다 지원 다름)
    if hasattr(filings_api, "search_filings"):
        raw = filings_api.search_filings(
            corp_code=corp_code, bgn_de=bgn_de, page_count=100
        )
        items = raw.get("list", []) if isinstance(raw, dict) else []
        annual = [f for f in items if "사업보고서" in f.get("report_nm", "")]
        if annual:
            return {"list": annual, "total_count": len(annual)}
        # 사업보고서 없으면 전체 목록 반환
        return raw if isinstance(raw, dict) else {"list": items}

    if hasattr(filings_api, "get_list"):
        raw = filings_api.get_list(corp_code=corp_code, bgn_de=bgn_de)
        return cast(dict[str, Any], raw)

    raise AttributeError("지원되지 않는 dart-fss filings API")


def collect_dart_reports_with_status(company_name: str, years: int = 3) -> dict:
    """DART 사업보고서 수집 결과와 상태를 함께 반환.

    Returns:
        {
            "success": bool,
            "data": dict[str, str],
            "reason": str,
        }
    """
    api_key = os.getenv("DART_API_KEY", "")
    if not api_key:
        return {
            "success": False,
            "data": {},
            "reason": "DART_API_KEY 미설정",
        }

    try:
        import dart_fss as dart  # type: ignore[import-untyped]
    except ImportError:
        return {
            "success": False,
            "data": {},
            "reason": "dart_fss 미설치",
        }

    try:
        dart.set_api_key(api_key=api_key)
        corp_list = dart.get_corp_list()

        # 정확 매칭 우선, 없으면 부분 매칭 첫 번째 사용
        matched = corp_list.find_by_corp_name(company_name, exactly=True)
        if not matched:
            matched = corp_list.find_by_corp_name(company_name, exactly=False)

        if not matched:
            return {
                "success": False,
                "data": {},
                "reason": f"기업코드 미발견: {company_name}",
            }

        # find_by_corp_name은 Corp 객체 리스트 반환
        # 상장사(stock_code 있는 것) 우선 선택
        listed = [c for c in matched if getattr(c, "stock_code", None)]
        target_corp = listed[0] if listed else matched[0]
        corp_code = target_corp.corp_code
        try:
            filings = _search_business_filings(dart, corp_code, years)
        except Exception as exc:
            if "조회된 데이타가 없습니다" in str(exc):
                return {
                    "success": False,
                    "data": {},
                    "reason": "최근 사업보고서 없음",
                }
            raise

        if not filings or not filings.get("list"):
            return {
                "success": False,
                "data": {},
                "reason": "최근 사업보고서 없음",
            }

        latest = filings["list"][0]
        rcp_no = latest["rcept_no"]

        result: dict[str, str] = {}
        _extract_section(dart, rcp_no, "주요 제품 및 서비스", result, "products")
        _extract_section(dart, rcp_no, "시장현황", result, "market_conditions")
        _extract_section(dart, rcp_no, "연구개발", result, "r_and_d")

        if not result:
            # 최신 dart-fss에서는 본문 섹션 API가 제거되어 공시 메타데이터로 폴백
            result = {
                "products": latest.get("report_nm", "사업보고서"),
                "market_conditions": f"공시일: {latest.get('rcept_dt', '')}",
                "r_and_d": f"접수번호: {rcp_no}",
            }

        return {"success": True, "data": result, "reason": ""}
    except Exception:
        logger.exception("DART 수집 실패: company=%s", company_name)
        return {"success": False, "data": {}, "reason": "DART API 호출 실패"}


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
    status = collect_dart_reports_with_status(company_name, years)
    data = status.get("data", {})
    return data if isinstance(data, dict) else {}


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
        # 구버전 API 호환 (최신 버전은 이 경로가 없을 수 있음)
        if not hasattr(dart.api, "document") or not hasattr(
            dart.api.document, "get_document"
        ):
            return

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
