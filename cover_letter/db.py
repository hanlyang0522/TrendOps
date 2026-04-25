"""공통 DB 연결 — cover_letter 서비스 전용."""

import os

import psycopg2


def get_conn():
    """PostgreSQL 연결 반환.

    환경변수 기반 접속 설정:
        POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_PORT

    Returns:
        psycopg2 Connection 객체
    """
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        connect_timeout=10,
    )
