"""
Naver MCP 기반 뉴스 크롤링 및 데이터베이스 저장

Naver OpenAPI를 사용하여 뉴스를 크롤링하고 PostgreSQL 데이터베이스에 저장합니다.
"""

import os

from crawling.naver_mcp_crawler import NaverMCPCrawler
from db.db_news import create_new_news, get_connection


def main():
    """메인 실행 함수"""
    # 환경 변수에서 설정 가져오기
    keyword = os.getenv("SEARCH_KEYWORD", "당근마켓")
    max_pages = int(os.getenv("MAX_PAGES", "3"))
    sort = os.getenv("SORT_ORDER", "date")

    print("=== Naver MCP 뉴스 크롤링 및 DB 저장 시작 ===")
    print(f"키워드: {keyword}")
    print(f"최대 페이지: {max_pages}")
    print(f"정렬: {sort}")
    print("")

    try:
        # Naver MCP 크롤러 초기화
        crawler = NaverMCPCrawler()

        # 뉴스 크롤링
        news_list = crawler.crawl_news(
            keyword=keyword,
            max_pages=max_pages,
            sort=sort,
        )

        if not news_list:
            print("수집된 뉴스가 없습니다.")
            return

        print(f"\n총 {len(news_list)}개의 기사를 수집했습니다.")

        # 데이터베이스 연결 테스트
        print("\n데이터베이스에 저장 중...")
        get_connection()

        # 데이터베이스에 저장
        success_count = 0
        error_count = 0

        for news in news_list:
            try:
                create_new_news(news["title"], news["link"])
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"저장 실패 - {news['title']}: {e}")

        print(f"\n저장 완료: {success_count}개 성공, {error_count}개 실패")
        print("=== 크롤링 및 DB 저장 완료 ===")

    except ValueError as e:
        print(f"설정 오류: {e}")
        print(
            "\n환경 변수를 확인하세요:"
            "\n  X_NAVER_CLIENT_ID"
            "\n  X_NAVER_CLIENT_SECRET"
            "\n  POSTGRES_HOST"
            "\n  POSTGRES_DB"
            "\n  POSTGRES_USER"
            "\n  POSTGRES_PASSWORD"
        )
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
