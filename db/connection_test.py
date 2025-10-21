import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost", dbname="postgres", user="postgres", password="pg1234"
    )

    cur = conn.cursor()

    print("PostgreSQL database version:")
    cur.execute("SELECT version();")

    db_version = cur.fetchone()
    print(db_version)

    cur.close()
    conn.close()
except Exception as e:
    print(f"An error occurred: {e}")
