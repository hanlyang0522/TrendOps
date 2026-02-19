#!/usr/bin/env python3
"""
Naver MCP 기능 테스트 스크립트

이 스크립트는 Naver MCP 크롤러의 주요 기능을 테스트합니다.
Mock 데이터를 사용하므로 API 키 없이 실행 가능합니다.
"""

import os
import sys
from unittest.mock import Mock, patch

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawling.naver_mcp_crawler import NaverMCPCrawler  # noqa: E402


def test_basic_functionality():
    """기본 기능 테스트 (Mock 사용)"""
    print("=" * 60)
    print("1. 기본 기능 테스트 (Mock 데이터 사용)")
    print("=" * 60)

    with patch("crawling.naver_mcp_crawler.requests.get") as mock_get:
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 100,
            "start": 1,
            "display": 10,
            "items": [
                {
                    "title": "<b>당근마켓</b>, AI 기반 중고거래 플랫폼으로 도약",
                    "link": "https://example.com/news1",
                    "description": "<b>당근마켓</b>이 최근 AI 기술을 도입...",
                    "pubDate": "Mon, 10 Feb 2026 10:00:00 +0900",
                },
                {
                    "title": "<b>당근마켓</b> 사용자 1000만 돌파",
                    "link": "https://example.com/news2",
                    "description": "중고거래 플랫폼 <b>당근마켓</b>의...",
                    "pubDate": "Mon, 10 Feb 2026 09:00:00 +0900",
                },
                {
                    "title": "<b>당근마켓</b>, 지역 기반 서비스 확대",
                    "link": "https://example.com/news3",
                    "description": "<b>당근마켓</b>이 지역사회 연결을...",
                    "pubDate": "Mon, 10 Feb 2026 08:00:00 +0900",
                },
            ],
        }
        mock_get.return_value = mock_response

        # 크롤러 생성 및 테스트
        crawler = NaverMCPCrawler(client_id="test_id", client_secret="test_secret")

        print("\n✅ 크롤러 초기화 성공")
        print(f"   API URL: {crawler.BASE_URL}")

        # 뉴스 검색
        result = crawler.search_news(query="당근마켓", display=10)

        print("\n✅ 뉴스 검색 성공")
        print(f"   총 검색 결과: {result['total']:,}개")
        print(f"   반환된 기사: {len(result['items'])}개")

        # 첫 번째 기사 정보
        if result["items"]:
            first = result["items"][0]
            print("\n📰 첫 번째 기사:")
            print(f"   제목: {first['title']}")
            print(f"   링크: {first['link']}")
            print(f"   날짜: {first['pubDate']}")

        return True


def test_html_tag_removal():
    """HTML 태그 제거 기능 테스트"""
    print("\n" + "=" * 60)
    print("2. HTML 태그 제거 기능 테스트")
    print("=" * 60)

    crawler = NaverMCPCrawler(client_id="test", client_secret="test")

    test_cases = [
        ("<b>당근마켓</b>", "당근마켓"),
        ("<b>당근</b><i>마켓</i>", "당근마켓"),
        ("&quot;인용문&quot;", '"인용문"'),
        ("&amp;", "&"),
        ("<b>&quot;당근마켓&quot;</b>", '"당근마켓"'),
    ]

    all_passed = True
    for html, expected in test_cases:
        result = crawler._remove_html_tags(html)
        if result == expected:
            print(f"✅ '{html}' → '{result}'")
        else:
            print(f"❌ '{html}' → '{result}' (예상: '{expected}')")
            all_passed = False

    return all_passed


def test_multi_page_crawling():
    """다중 페이지 크롤링 테스트"""
    print("\n" + "=" * 60)
    print("3. 다중 페이지 크롤링 테스트")
    print("=" * 60)

    with patch("crawling.naver_mcp_crawler.requests.get") as mock_get:

        def mock_response_side_effect(*args, **kwargs):
            start = kwargs["params"]["start"]
            mock_response = Mock()
            mock_response.status_code = 200

            # 페이지별 다른 응답
            if start == 1:
                items = [
                    {
                        "title": f"<b>뉴스</b> 제목 {i}",
                        "link": f"https://example.com/{i}",
                        "description": f"설명 {i}",
                        "pubDate": f"Mon, 10 Feb 2026 10:0{i}:00 +0900",
                    }
                    for i in range(1, 11)
                ]
            elif start == 11:
                items = [
                    {
                        "title": f"<b>뉴스</b> 제목 {i}",
                        "link": f"https://example.com/{i}",
                        "description": f"설명 {i}",
                        "pubDate": f"Mon, 10 Feb 2026 09:0{i-10}:00 +0900",
                    }
                    for i in range(11, 21)
                ]
            else:
                items = []

            mock_response.json.return_value = {"items": items}
            return mock_response

        mock_get.side_effect = mock_response_side_effect

        crawler = NaverMCPCrawler(client_id="test", client_secret="test")
        result = crawler.crawl_news(keyword="테스트", max_pages=2)

        print("\n✅ 다중 페이지 크롤링 성공")
        print(f"   총 수집 기사: {len(result)}개")
        print(f"   첫 번째 기사: {result[0]['title']}")
        print(f"   마지막 기사: {result[-1]['title']}")

        return len(result) == 20


def test_error_handling():
    """에러 처리 테스트"""
    print("\n" + "=" * 60)
    print("4. 에러 처리 테스트")
    print("=" * 60)

    crawler = NaverMCPCrawler(client_id="test", client_secret="test")

    # 빈 query 테스트
    try:
        crawler.search_news(query="")
        print("❌ 빈 query 에러 처리 실패")
        return False
    except ValueError as e:
        print(f"✅ 빈 query 에러 처리: {e}")

    # 잘못된 display 값 테스트
    try:
        crawler.search_news(query="테스트", display=0)
        print("❌ 잘못된 display 에러 처리 실패")
        return False
    except ValueError as e:
        print(f"✅ 잘못된 display 에러 처리: {e}")

    # 잘못된 sort 값 테스트
    try:
        crawler.search_news(query="테스트", sort="invalid")
        print("❌ 잘못된 sort 에러 처리 실패")
        return False
    except ValueError as e:
        print(f"✅ 잘못된 sort 에러 처리: {e}")

    return True


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("Naver MCP 기능 테스트")
    print("=" * 60)
    print("\n⚠️  이 테스트는 Mock 데이터를 사용하므로")
    print("   API 키 없이 실행 가능합니다!\n")

    results = []

    # 각 테스트 실행
    results.append(("기본 기능", test_basic_functionality()))
    results.append(("HTML 태그 제거", test_html_tag_removal()))
    results.append(("다중 페이지 크롤링", test_multi_page_crawling()))
    results.append(("에러 처리", test_error_handling()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{name:20s}: {status}")

    print("\n" + "=" * 60)
    print(f"총 {len(results)}개 테스트: {passed}개 통과, {failed}개 실패")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 모든 기능 테스트가 성공했습니다!")
        print("\n💡 실제 API를 사용하려면:")
        print("   1. https://developers.naver.com/ 에서 API 키 발급")
        print("   2. 환경 변수 설정:")
        print("      export NAVER_CLIENT_ID=your_id")
        print("      export NAVER_CLIENT_SECRET=your_secret")
        print("   3. 크롤러 실행:")
        print("      python -m crawling.naver_mcp_crawler")
        return 0
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
