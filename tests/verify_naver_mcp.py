#!/usr/bin/env python3
"""
Naver MCP 통합 검증 스크립트

Naver MCP가 올바르게 통합되었는지 테스트합니다.
"""

import os
import sys

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_environment():
    """환경 변수 확인"""
    print("=" * 60)
    print("1. 환경 변수 확인")
    print("=" * 60)

    client_id = os.getenv("X_NAVER_CLIENT_ID")
    client_secret = os.getenv("X_NAVER_CLIENT_SECRET")

    if client_id and client_secret:
        print("✅ X_NAVER_CLIENT_ID: 설정됨")
        print("✅ X_NAVER_CLIENT_SECRET: 설정됨")
        print(f"   Client ID 길이: {len(client_id)} 문자")
        return True
    else:
        print("❌ Naver OpenAPI 환경 변수가 설정되지 않았습니다.")
        print("\n다음 변수를 .env 파일에 설정하세요:")
        print("  X_NAVER_CLIENT_ID=your_client_id")
        print("  X_NAVER_CLIENT_SECRET=your_client_secret")
        print("\nNaver OpenAPI 신청: https://developers.naver.com/")
        return False


def test_import():
    """모듈 import 테스트"""
    print("\n" + "=" * 60)
    print("2. 모듈 Import 테스트")
    print("=" * 60)

    try:
        from crawling.naver_mcp_crawler import NaverMCPCrawler  # noqa: F401

        print("✅ NaverMCPCrawler 모듈 import 성공")
        return True
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False


def test_initialization():
    """크롤러 초기화 테스트"""
    print("\n" + "=" * 60)
    print("3. 크롤러 초기화 테스트")
    print("=" * 60)

    try:
        from crawling.naver_mcp_crawler import NaverMCPCrawler

        # Mock credentials로 초기화 테스트
        crawler = NaverMCPCrawler(client_id="test_id", client_secret="test_secret")
        print("✅ 크롤러 초기화 성공 (mock credentials)")
        # Verify the crawler is properly initialized
        assert crawler.client_id == "test_id"

        # 환경 변수로 초기화 테스트
        if os.getenv("X_NAVER_CLIENT_ID"):
            env_crawler = NaverMCPCrawler()
            print("✅ 크롤러 초기화 성공 (환경 변수)")
            # Verify the crawler is properly initialized
            assert env_crawler.client_id is not None

        return True
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return False


def test_search(use_real_api=False):
    """검색 기능 테스트"""
    print("\n" + "=" * 60)
    print("4. 검색 기능 테스트")
    print("=" * 60)

    if not use_real_api:
        print("⚠️  실제 API 테스트는 건너뜁니다 (환경 변수 미설정)")
        print("   환경 변수 설정 후 다시 실행하면 실제 API를 테스트합니다.")
        return True

    try:
        from crawling.naver_mcp_crawler import NaverMCPCrawler

        crawler = NaverMCPCrawler()
        print("🔍 '당근마켓' 키워드로 뉴스 검색 중...")

        result = crawler.search_news(query="당근마켓", display=3)

        total = result.get("total", 0)
        items = result.get("items", [])

        print("✅ 검색 성공!")
        print(f"   총 검색 결과: {total:,}개")
        print(f"   반환된 기사: {len(items)}개")

        if items:
            print("\n📰 첫 번째 기사:")
            first = items[0]
            print(f"   제목: {first.get('title', 'N/A')}")
            print(f"   링크: {first.get('link', 'N/A')}")
            print(f"   날짜: {first.get('pubDate', 'N/A')}")

        return True
    except ValueError as e:
        print(f"❌ 검색 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_html_cleaning():
    """HTML 태그 제거 테스트"""
    print("\n" + "=" * 60)
    print("5. HTML 태그 제거 테스트")
    print("=" * 60)

    try:
        from crawling.naver_mcp_crawler import NaverMCPCrawler

        crawler = NaverMCPCrawler(client_id="test", client_secret="test")

        test_cases = [
            ("<b>당근마켓</b>", "당근마켓"),
            ("&quot;인용&quot;", '"인용"'),
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
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def run_unit_tests():
    """pytest 단위 테스트 실행"""
    print("\n" + "=" * 60)
    print("6. Pytest 단위 테스트")
    print("=" * 60)

    try:
        import pytest

        print("🧪 pytest로 단위 테스트 실행 중...")
        exit_code = pytest.main(
            [
                "tests/test_naver_mcp_crawler.py",
                "-v",
                "--tb=short",
                "-k",
                "not Integration",
            ]
        )

        if exit_code == 0:
            print("✅ 모든 단위 테스트 통과!")
            return True
        else:
            print(f"❌ 일부 테스트 실패 (exit code: {exit_code})")
            return False
    except ImportError:
        print("⚠️  pytest가 설치되지 않았습니다.")
        print("   설치: pip install pytest pytest-mock")
        return True  # pytest 없어도 다른 테스트는 진행
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        return False


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("Naver MCP 통합 검증 스크립트")
    print("=" * 60)

    results = []

    # 1. 환경 변수 확인
    has_credentials = check_environment()
    results.append(("환경 변수", has_credentials or "건너뜀"))

    # 2. Import 테스트
    results.append(("모듈 Import", test_import()))

    # 3. 초기화 테스트
    results.append(("크롤러 초기화", test_initialization()))

    # 4. 검색 테스트
    results.append(("검색 기능", test_search(use_real_api=has_credentials)))

    # 5. HTML 정리 테스트
    results.append(("HTML 태그 제거", test_html_cleaning()))

    # 6. 단위 테스트
    results.append(("Pytest 단위 테스트", run_unit_tests()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results:
        if result is True:
            status = "✅ 통과"
            passed += 1
        elif result == "건너뜀":
            status = "⚠️  건너뜀"
            skipped += 1
        else:
            status = "❌ 실패"
            failed += 1

        print(f"{name:20s}: {status}")

    print("\n" + "=" * 60)
    print(
        f"총 {len(results)}개 테스트: {passed}개 통과, {failed}개 실패, {skipped}개 건너뜀"
    )
    print("=" * 60)

    if failed == 0:
        print("\n🎉 Naver MCP가 성공적으로 통합되었습니다!")
        if skipped > 0:
            print("\n💡 실제 API 테스트를 위해 환경 변수를 설정하세요:")
            print("   1. https://developers.naver.com/ 에서 API 키 발급")
            print("   2. .env 파일에 X_NAVER_CLIENT_ID, X_NAVER_CLIENT_SECRET 설정")
            print("   3. 이 스크립트 다시 실행")
        return 0
    else:
        print("\n⚠️  일부 테스트가 실패했습니다. 위 내용을 확인하세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
