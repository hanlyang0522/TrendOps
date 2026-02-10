# Naver MCP Integration Guide

## 개요

TrendOps 프로젝트에 Naver OpenAPI 기반의 MCP (Model Context Protocol) 뉴스 크롤러가 통합되었습니다.

## 주요 변경사항

### 1. 새로운 모듈

- **`crawling/naver_mcp_crawler.py`**: Naver OpenAPI를 사용한 뉴스 크롤링 모듈
- **`crawling/news_crawling_mcp.py`**: MCP 기반 크롤링 및 데이터베이스 저장
- **`tests/test_naver_mcp_crawler.py`**: 단위 테스트 및 통합 테스트

### 2. 환경 변수 추가

`.env` 파일에 다음 변수 추가 필요:

```bash
# Naver OpenAPI Configuration
X_NAVER_CLIENT_ID=your_naver_client_id_here
X_NAVER_CLIENT_SECRET=your_naver_client_secret_here

# Optional settings
MAX_PAGES=3              # 크롤링할 페이지 수 (기본값: 3)
SORT_ORDER=date          # 정렬 방식: 'date' 또는 'sim' (기본값: date)
```

## Naver OpenAPI 설정 방법

### 1단계: Naver Developers 가입

1. https://developers.naver.com/ 접속
2. 네이버 계정으로 로그인
3. 우측 상단 "Application" → "애플리케이션 등록" 클릭

### 2단계: 애플리케이션 등록

1. **애플리케이션 이름**: TrendOps (또는 원하는 이름)
2. **사용 API**: "검색" 선택
   - 뉴스 검색 API 체크
3. **비로그인 오픈 API 서비스 환경**: 
   - 웹 서비스 URL: http://localhost (개발용)
4. 등록 완료

### 3단계: Client ID와 Secret 확인

1. 등록된 애플리케이션 목록에서 생성한 앱 클릭
2. **Client ID** 복사
3. **Client Secret** 복사

### 4단계: 환경 변수 설정

```bash
# .env 파일 생성 (없는 경우)
cp .env.example .env

# .env 파일 편집
nano .env

# 다음 내용 추가/수정
X_NAVER_CLIENT_ID=발급받은_Client_ID
X_NAVER_CLIENT_SECRET=발급받은_Client_Secret
```

## 사용 방법

### 방법 1: Python 모듈로 직접 실행

```bash
# 기본 크롤링 (환경 변수 사용)
python -m crawling.naver_mcp_crawler

# 데이터베이스 저장까지 포함
python -m crawling.news_crawling_mcp
```

### 방법 2: Python 코드에서 사용

```python
from crawling.naver_mcp_crawler import NaverMCPCrawler

# 크롤러 초기화
crawler = NaverMCPCrawler(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# 뉴스 검색 (단일 페이지)
result = crawler.search_news(
    query="당근마켓",
    display=10,
    start=1,
    sort="date"
)

# 여러 페이지 크롤링
news_list = crawler.crawl_news(
    keyword="당근마켓",
    max_pages=3,
    sort="date"
)

# 결과 출력
for news in news_list:
    print(f"제목: {news['title']}")
    print(f"링크: {news['link']}")
    print(f"날짜: {news['pubDate']}")
    print()
```

### 방법 3: Docker 환경

```bash
# .env 파일 설정 후
docker-compose run --rm crawler python -m crawling.news_crawling_mcp
```

## 테스트 실행

### 단위 테스트 (mock 사용)

```bash
# pytest 설치 (최초 1회)
pip install pytest pytest-mock

# 테스트 실행
python -m pytest tests/test_naver_mcp_crawler.py -v
```

### 통합 테스트 (실제 API 호출)

```bash
# 환경 변수 설정 후
export X_NAVER_CLIENT_ID=your_client_id
export X_NAVER_CLIENT_SECRET=your_client_secret

# 통합 테스트 포함하여 실행
python -m pytest tests/test_naver_mcp_crawler.py -v
```

## API 제한 사항

### 무료 플랜 (개인용)

- **일일 요청 제한**: 25,000건
- **초당 요청 제한**: 10건
- **표시 결과**: 최대 100개/요청

### TrendOps 예상 사용량

- 매일 1회 크롤링 (30페이지 × 10개) = 30건/일
- 월간 약 900건 (일일 제한의 3.6%)
- **결론**: 무료 플랜으로 충분

## 기존 코드와의 비교

### 기존 방식 (BeautifulSoup)

```python
# crawling/news_crawling.py
import requests
from bs4 import BeautifulSoup

url = "https://search.naver.com/search.naver"
response = requests.get(url, params=params)
html = BeautifulSoup(response.text, "html.parser")
articles = html.select('a[data-heatmap-target=".nav"]')
```

**단점:**
- HTML 구조 변경 시 깨짐
- 동적 콘텐츠 처리 어려움
- 제한적인 메타데이터

### 새로운 방식 (Naver MCP)

```python
# crawling/naver_mcp_crawler.py
from crawling.naver_mcp_crawler import NaverMCPCrawler

crawler = NaverMCPCrawler()
result = crawler.search_news(query="당근마켓")
```

**장점:**
- 공식 API로 안정적
- 구조화된 JSON 응답
- 풍부한 메타데이터 (날짜, 출처 등)
- HTML 파싱 불필요

## 문제 해결

### 401 Unauthorized 에러

```bash
ValueError: Naver OpenAPI 인증 실패. Client ID와 Secret을 확인하세요.
```

**해결 방법:**
1. Client ID와 Secret이 정확한지 확인
2. 애플리케이션이 활성화 상태인지 확인
3. 뉴스 검색 API가 선택되어 있는지 확인

### 429 Too Many Requests 에러

```bash
ValueError: API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요.
```

**해결 방법:**
1. 잠시 대기 후 재시도 (1분)
2. MAX_PAGES 값 줄이기
3. 일일 요청 제한 확인 (25,000건)

### Missing credentials 에러

```bash
ValueError: Naver OpenAPI credentials are required.
```

**해결 방법:**
1. `.env` 파일 생성 및 설정
2. 환경 변수가 올바르게 로드되는지 확인

```bash
# 환경 변수 확인
echo $X_NAVER_CLIENT_ID
echo $X_NAVER_CLIENT_SECRET
```

## 마이그레이션 가이드

### 기존 코드 → Naver MCP

1. **환경 변수 추가**
   ```bash
   # .env 파일
   X_NAVER_CLIENT_ID=...
   X_NAVER_CLIENT_SECRET=...
   ```

2. **코드 변경**
   ```python
   # 기존
   from crawling.news_crawling import main
   
   # 새로운 방식
   from crawling.news_crawling_mcp import main
   ```

3. **Docker 업데이트** (선택적)
   ```yaml
   # docker-compose.yml
   environment:
     - X_NAVER_CLIENT_ID=${X_NAVER_CLIENT_ID}
     - X_NAVER_CLIENT_SECRET=${X_NAVER_CLIENT_SECRET}
   ```

## 성능 비교

| 항목 | BeautifulSoup | Naver MCP |
|------|---------------|-----------|
| 속도 | ~5-10초 | ~1-2초 |
| 안정성 | ⭐⭐⭐ (HTML 변경 취약) | ⭐⭐⭐⭐⭐ (공식 API) |
| 메타데이터 | 제한적 | 풍부 (날짜, 출처 등) |
| 에러 처리 | 복잡 | 간단 (구조화된 응답) |
| 유지보수 | 높음 | 낮음 |

## 참고 자료

- [Naver Developers](https://developers.naver.com/)
- [Naver 뉴스 검색 API 문서](https://developers.naver.com/docs/serviceapi/search/news/news.md)
- [TrendOps MCP 조사 보고서](../docs/MCP_NEWS_SERVICES_RESEARCH.md)
- [Naver MCP vs Firecrawl MCP 비교](../docs/NAVER_MCP_VS_FIRECRAWL_MCP.md)

## 버전 히스토리

- **v1.0.0** (2026-02-10): Naver MCP 초기 통합
  - NaverMCPCrawler 클래스 추가
  - 단위 테스트 및 통합 테스트
  - 문서화 완료

---

**문서 작성일**: 2026-02-10  
**최종 업데이트**: 2026-02-10
