import psycopg2


def get_connection():
    """
    DB 연결을 생성
    """
    return psycopg2.connect(
        host="localhost", database="postgres", user="postgres", password="pg1234"
    )


def setup_database():
    """
    데이터베이스 설정 함수
    """
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 테이블 생성
        cur.execute(
            """
            CREATE TABLE danggn_market_urls (
                id SERIAL PRIMARY KEY,
                title TEXT,
                url VARCHAR(500) NOT NULL
            );
        """
        )

        # 변경사항 커밋
        conn.commit()
        print("Database setup completed.")

        # 추가적인 데이터베이스 설정 작업 수행 가능
        cur.close()
    except Exception as e:
        print(f"Database setup failed: {e}")
    finally:
        if conn:
            conn.close()


def create_new_news(title, url):
    """
    Create new news in database
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        sql = (
            "INSERT INTO danggn_market_urls (title, url) VALUES (%s, %s) RETURNING id;"
        )
        cur.execute(sql, (title, url))

        news_id = cur.fetchone()[0]

        conn.commit()
        print(f"News created successfully with ID: {news_id}")
        cur.close()

    except Exception as e:
        print(f"Failed to create news: {e}")
    finally:
        if conn:
            conn.close()


def get_news(news_id):
    """
    Retrieve news information by ID
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        sql = "SELECT id, title, url FROM danggn_market_urls WHERE id = %s;"
        cur.execute(sql, (news_id,))
        news = cur.fetchone()
        cur.close()

        return news

    except Exception as e:
        print(f"Failed to retrieve news: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_all_news():
    """
    Read all news from db
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, title, url FROM danggn_market_urls;")

        all_news = cur.fetchall()

        print("All news:")
        if not all_news:
            print("No news found.")
        else:
            for news in all_news:
                print(f" ID: {news[0]}, Title: {news[1]}, URL: {news[2]}")
        print("End of news list.")

        cur.close()
    except Exception as e:
        print(f"Failed to retrieve news: {e}")
    finally:
        if conn:
            conn.close()


def update_news_url(title, new_url):
    """
    Update news's URL by title
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        sql = "UPDATE danggn_market_urls SET url = %s WHERE title = %s;"
        cur.execute(sql, (new_url, title))
        conn.commit()

        print(f"Updated URL for '{title}' to '{new_url}'.")
        cur.close()
    except Exception as e:
        print(f"Failed to update URL: {e}")
    finally:
        if conn:
            conn.close()


def delete_news(title):
    """
    Delete news by title
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        sql = "DELETE FROM danggn_market_urls WHERE title = %s;"
        cur.execute(sql, (title,))
        conn.commit()

        print(f"News '{title}' deleted successfully.")
        cur.close()
    except Exception as e:
        print(f"Failed to delete news: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    setup_database()
    get_all_news()
