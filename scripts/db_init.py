"""DB 초기화 스크립트 — db-init 컨테이너에서 실행됩니다.

1. danggn_market_urls 테이블 생성 (IF NOT EXISTS)
2. cover_letter 서비스 스키마 마이그레이션 적용 (IF NOT EXISTS)
"""

import os
import pathlib

import psycopg2

from db.db_news import setup_database


def apply_migration(conn: psycopg2.extensions.connection, sql_path: str) -> None:
    """SQL 파일을 읽어 실행합니다."""
    sql = pathlib.Path(sql_path).read_text(encoding="utf-8")
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    print(f"Migration applied: {sql_path}")


def main() -> None:
    # 1. danggn_market_urls 테이블 (IF NOT EXISTS 적용됨)
    setup_database()

    # 2. cover_letter 스키마 마이그레이션
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
    )
    try:
        apply_migration(conn, "/app/db/migrations/001_cover_letter_schema.sql")
    finally:
        conn.close()

    print("Database initialization complete.")


if __name__ == "__main__":
    main()
