"""기업·직무 분석 서비스 — 3-소스 수집 오케스트레이션 + DB 캐싱."""

import json
import logging
import pathlib
from datetime import datetime, timezone

from cover_letter import llm_client
from cover_letter.collectors import dart_collector, naver_collector, website_crawler
from cover_letter.db import get_conn as _get_conn

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "company_analysis.txt"
_CACHE_DAYS = 7
logger = logging.getLogger(__name__)


def get_or_analyze_company(company_name: str) -> dict:
    """기업 분석 결과 반환. 캐시 히트 시 뉴스만 재수집, 미스 시 3-소스 전체 분석.

    Args:
        company_name: 기업명

    Returns:
        company_analysis 레코드에 해당하는 dict
        {
            "id": int, "company_name": str, "overview": str,
            "culture_and_values": str, "industry_trends": str,
            "competitive_edge": str, "news_summary": str,
            "dart_summary": str, "analyzed_at": str
        }
    """
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, company_name, overview, culture_and_values, industry_trends,
                       competitive_edge, news_summary, dart_summary,
                       analyzed_at, user_overrides
                FROM company_analysis
                WHERE company_name = %s
                """,
                (company_name,),
            )
            row = cur.fetchone()

        if row is not None:
            cached = _row_to_dict(row)
            analyzed_at = cached["analyzed_at"]
            if isinstance(analyzed_at, str):
                analyzed_at = datetime.fromisoformat(analyzed_at)
            age_days = (
                datetime.now(timezone.utc) - analyzed_at.replace(tzinfo=timezone.utc)
            ).days

            if age_days < _CACHE_DAYS:
                # 캐시 히트: 뉴스만 재수집
                fresh_news = _summarize_news(company_name, "")
                if fresh_news:
                    with conn, conn.cursor() as cur:
                        cur.execute(
                            "UPDATE company_analysis SET news_summary=%s, news_updated_at=NOW() WHERE id=%s",
                            (fresh_news, cached["id"]),
                        )
                    cached["news_summary"] = fresh_news
                dart_ok = bool(cached.get("dart_summary"))
                website_ok = bool(cached.get("culture_and_values"))
                cached["source_status"] = {
                    "dart": {
                        "success": dart_ok,
                        "reason": (
                            "" if dart_ok else "이전 분석 시 수집 실패 (쫨시 참조)"
                        ),
                    },
                    "website": {
                        "success": website_ok,
                        "reason": (
                            "" if website_ok else "이전 분석 시 수집 실패 (쫨시 참조)"
                        ),
                    },
                }
                return cached

        # 캐시 미스: 3-소스 전체 분석
        return _full_analysis(company_name, conn)
    finally:
        conn.close()


def _full_analysis(company_name: str, conn) -> dict:
    """3-소스 수집 후 LLM 통합 요약, DB 저장."""
    # 1. DART 사업보고서
    dart_result = dart_collector.collect_dart_reports_with_status(company_name)
    dart_data = dart_result.get("data", {}) if isinstance(dart_result, dict) else {}
    dart_text = _format_dart(dart_data)

    # 2. Naver 뉴스
    news_articles = naver_collector.collect_news(company_name)
    news_text = _format_news(news_articles)

    # 3. 홈페이지 스크래핑
    website_result = website_crawler.crawl_company_website_with_status(company_name)
    website_data = (
        website_result.get("data", {}) if isinstance(website_result, dict) else {}
    )
    website_text = website_data.get("talent", "") if website_data else ""

    source_status = {
        "dart": {
            "success": bool(dart_result.get("success")),
            "reason": str(dart_result.get("reason", "")),
        },
        "website": {
            "success": bool(website_result.get("success")),
            "reason": str(website_result.get("reason", "")),
        },
    }
    for source, status in source_status.items():
        if not status["success"]:
            logger.warning(
                "company source collection failed: company=%s source=%s reason=%s",
                company_name,
                source,
                status["reason"],
            )

    # LLM 통합 요약
    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    system = ""
    user = prompt_template
    if "## System\n" in prompt_template and "## User\n" in prompt_template:
        parts = prompt_template.split("## User\n", 1)
        system = parts[0].replace("## System\n", "").strip()
        user = parts[1].strip()

    user = (
        user.replace("{company_name}", company_name)
        .replace("{dart_summary}", dart_text or "자료 없음")
        .replace("{news_summary}", news_text or "자료 없음")
        .replace("{website_summary}", website_text or "자료 없음")
    )

    raw = llm_client.call(user, tier="flash", system=system)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError:
        analysis = {
            "overview": "",
            "culture_and_values": "",
            "industry_trends": "",
            "competitive_edge": "",
            "dart_summary": "",
        }

    # DB 저장
    source_urls = []
    if website_data and website_data.get("source_url"):
        source_urls.append(website_data["source_url"])

    with conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO company_analysis
                (company_name, overview, culture_and_values, industry_trends,
                 competitive_edge, news_summary, dart_summary, source_urls, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (company_name) DO UPDATE SET
                overview           = EXCLUDED.overview,
                culture_and_values = EXCLUDED.culture_and_values,
                industry_trends    = EXCLUDED.industry_trends,
                competitive_edge   = EXCLUDED.competitive_edge,
                news_summary       = EXCLUDED.news_summary,
                dart_summary       = EXCLUDED.dart_summary,
                source_urls        = EXCLUDED.source_urls,
                analyzed_at        = NOW()
            RETURNING id, analyzed_at
            """,
            (
                company_name,
                analysis.get("overview", ""),
                analysis.get("culture_and_values", ""),
                analysis.get("industry_trends", ""),
                analysis.get("competitive_edge", ""),
                news_text,
                analysis.get("dart_summary", ""),
                source_urls,
            ),
        )
        row = cur.fetchone()
        new_id, analyzed_at = row[0], row[1]

    return {
        "id": new_id,
        "company_name": company_name,
        "overview": analysis.get("overview", ""),
        "culture_and_values": analysis.get("culture_and_values", ""),
        "industry_trends": analysis.get("industry_trends", ""),
        "competitive_edge": analysis.get("competitive_edge", ""),
        "news_summary": news_text,
        "dart_summary": analysis.get("dart_summary", ""),
        "analyzed_at": (
            analyzed_at.isoformat()
            if hasattr(analyzed_at, "isoformat")
            else str(analyzed_at)
        ),
        "source_status": source_status,
        "user_overrides": {},
    }


def analyze_job(company_analysis_id: int, job_title: str) -> dict:
    """직무 분석 (간단 프롬프트) 후 DB 저장.

    Args:
        company_analysis_id: 연결된 기업 분석 ID
        job_title: 직무명

    Returns:
        job_analysis 레코드에 해당하는 dict
    """
    # 기업 정보 조회
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT company_name, overview, industry_trends FROM company_analysis WHERE id=%s",
                (company_analysis_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise ValueError(f"company_analysis id={company_analysis_id} 없음")
        company_name, overview, industry_trends = row[0], row[1], row[2]

        prompt = (
            f"기업: {company_name}\n직무: {job_title}\n\n"
            f"기업 개요: {overview}\n업계 동향: {industry_trends}\n\n"
            "위 정보를 바탕으로 해당 직무의 주요 업무(responsibilities), "
            "직무 페인 포인트(pain_points), 기대 역량(expected_competencies, 배열), "
            "미래 전망(future_direction)을 JSON으로 반환하세요."
        )

        system = "당신은 직무 분석 전문가입니다. 반드시 순수 JSON만 반환하세요."
        raw = llm_client.call(prompt, tier="flash", system=system)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        try:
            job_data = json.loads(raw)
        except json.JSONDecodeError:
            job_data = {}

        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO job_analysis
                    (company_analysis_id, job_title, responsibilities, pain_points,
                     expected_competencies, future_direction)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (company_analysis_id, job_title) DO UPDATE SET
                    responsibilities      = EXCLUDED.responsibilities,
                    pain_points           = EXCLUDED.pain_points,
                    expected_competencies = EXCLUDED.expected_competencies,
                    future_direction      = EXCLUDED.future_direction,
                    analyzed_at           = NOW()
                RETURNING id
                """,
                (
                    company_analysis_id,
                    job_title,
                    job_data.get("responsibilities", ""),
                    job_data.get("pain_points", ""),
                    job_data.get("expected_competencies", []),
                    job_data.get("future_direction", ""),
                ),
            )
            job_id = cur.fetchone()[0]

        return {
            "id": job_id,
            "company_analysis_id": company_analysis_id,
            "job_title": job_title,
            **job_data,
        }
    finally:
        conn.close()


def save_overrides(entity: str, entity_id: int, overrides: dict) -> None:
    """사용자 수정 내용을 user_overrides 필드에 저장.

    Args:
        entity: 'company' | 'job'
        entity_id: 해당 레코드 ID
        overrides: 수정된 필드 dict
    """
    table = "company_analysis" if entity == "company" else "job_analysis"
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                f"UPDATE {table} SET user_overrides = %s WHERE id = %s",  # noqa: S608
                (json.dumps(overrides, ensure_ascii=False), entity_id),
            )
    finally:
        conn.close()


# ============================================================
# 내부 헬퍼
# ============================================================
def _format_dart(dart_data: dict) -> str:
    if not dart_data:
        return ""
    parts = []
    if dart_data.get("products"):
        parts.append(f"[주요 제품/서비스]\n{dart_data['products']}")
    if dart_data.get("market_conditions"):
        parts.append(f"[시장현황]\n{dart_data['market_conditions']}")
    if dart_data.get("r_and_d"):
        parts.append(f"[연구개발]\n{dart_data['r_and_d']}")
    return "\n\n".join(parts)


def _format_news(articles: list[dict]) -> str:
    if not articles:
        return ""
    parts = []
    for a in articles[:10]:
        title = a.get("title", "")
        desc = a.get("description", "")
        parts.append(f"- {title}: {desc}")
    return "\n".join(parts)


def _summarize_news(company_name: str, job_title: str) -> str:
    articles = naver_collector.collect_news(company_name, job_title)
    return _format_news(articles)


def _row_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "company_name": row[1],
        "overview": row[2],
        "culture_and_values": row[3],
        "industry_trends": row[4],
        "competitive_edge": row[5],
        "news_summary": row[6],
        "dart_summary": row[7],
        "analyzed_at": row[8],
        "source_status": {},
        "user_overrides": row[9] or {},
    }
