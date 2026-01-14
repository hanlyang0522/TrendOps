#!/usr/bin/env python3
"""
뉴스 크롤링을 주기적으로 실행하는 스케줄러입니다.
"""

import logging
import os
import subprocess
import time

import schedule

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/app/logs/scheduler.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def run_crawler():
    """크롤러를 실행합니다."""
    try:
        logger.info("Starting news crawler...")
        result = subprocess.run(
            ["python", "-m", "crawling.news_crawling"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=300,  # 5분 타임아웃
        )

        if result.returncode == 0:
            logger.info(f"Crawler completed successfully: {result.stdout}")
        else:
            logger.error(f"Crawler failed with error: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("Crawler timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Error running crawler: {e}")


def main():
    """메인 스케줄러 함수"""
    # 환경 변수에서 스케줄 설정 가져오기
    schedule_time = os.getenv("CRAWL_SCHEDULE", "09:00")

    logger.info(f"Scheduler started. Will run crawler daily at {schedule_time}")

    # 매일 지정된 시간에 크롤러 실행
    schedule.every().day.at(schedule_time).do(run_crawler)

    # 즉시 한 번 실행 (선택적)
    if os.getenv("RUN_ON_START", "false").lower() == "true":
        logger.info("Running crawler immediately on startup...")
        run_crawler()

    # 스케줄 실행 루프
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크


if __name__ == "__main__":
    main()
