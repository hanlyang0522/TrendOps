"""
네이버 뉴스에서 특정 키워드로 뉴스를 크롤링하여 데이터베이스에 저장하는 스크립트입니다.
"""

import requests
from bs4 import BeautifulSoup

from db.db_news import create_new_news, get_connection

header = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )
}

# search = input("Enter search term: ")
search = "당근마켓"
url = "https://search.naver.com/search.naver?"

params: dict[str, str | int] = {
    "where": "news",
    "query": search,
    "start": 0,
    "nso": "so:r,p:7d,a:all",  # 최근 7일
}


if __name__ == "__main__":
    re_url = requests.get(url=url, headers=header, params=params)
    html = BeautifulSoup(re_url.text, "html.parser")

    articles = html.select('a[data-heatmap-target=".nav"]')

    # Store news in the database
    get_connection()

    for article in articles:
        title = article.text.strip()
        url = article["href"].strip()
        create_new_news(title, url)
        print(f"Title: {title}\nURL: {url}\n")

    print(f"Total articles fetched: {len(articles)}")
