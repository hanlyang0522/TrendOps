# TrendOps 프로젝트 현황 분석 및 기능 개발 가이드라인

## 📊 현재 프로젝트 상태 (Current Status)

### ✅ 완료된 기능 (Completed Features)

#### 1. 기본 인프라 구축 (Infrastructure) - **100% 완료**
- ✅ Docker 기반 컨테이너화
  - `Dockerfile.crawler`: 크롤러 서비스
  - `Dockerfile.db-init`: DB 초기화 서비스
  - `Dockerfile.scheduler`: 스케줄러 서비스
- ✅ Docker Compose 설정
  - 개발 환경: `docker-compose.dev.yml`
  - 프로덕션 환경: `docker-compose.prod.yml`
  - 기본 설정: `docker-compose.yml`
- ✅ PostgreSQL 데이터베이스 설정
  - Health check 구현
  - Volume 관리
  - 네트워크 격리

#### 2. 데이터 크롤링 (Web Scraping) - **90% 완료**
- ✅ 네이버 뉴스 크롤링 모듈 (`crawling/news_crawling.py`)
  - BeautifulSoup4 기반 HTML 파싱
  - requests 라이브러리로 HTTP 요청
  - 최근 7일 뉴스 필터링
  - 환경변수로 검색 키워드 설정 가능
- ✅ 크롤링 데이터 DB 저장
  - 제목(title), URL 저장
  - 중복 처리 미흡 (개선 필요)

#### 3. 데이터베이스 관리 (Database Management) - **85% 완료**
- ✅ DB 연결 모듈 (`db/db_news.py`)
  - psycopg2 기반 PostgreSQL 연결
  - 환경변수 검증 로직
  - 연결 타임아웃 설정
  - SSL 모드 설정
- ✅ CRUD 기능
  - `create_new_news()`: 뉴스 생성
  - `get_news()`: 단일 뉴스 조회
  - `get_all_news()`: 전체 뉴스 조회
  - `update_news_url()`: URL 업데이트
  - `delete_news()`: 뉴스 삭제
- ⚠️ 개선 필요 사항:
  - 연결 풀링 미구현 (성능 이슈 가능)
  - 트랜잭션 관리 미흡
  - 에러 로깅 개선 필요

#### 4. 스케줄링 (Scheduling) - **80% 완료**
- ✅ Python schedule 라이브러리 기반 스케줄러 (`scripts/scheduler.py`)
  - 매일 지정 시간 크롤링 실행
  - 환경변수로 스케줄 설정 (`CRAWL_SCHEDULE`)
  - 시작 시 즉시 실행 옵션 (`RUN_ON_START`)
  - 로깅 구현 (파일 + 콘솔)
  - 5분 타임아웃 설정
- ⚠️ 개선 필요 사항:
  - Airflow 같은 전문 스케줄러 고려
  - 실패 시 재시도 로직 없음
  - 모니터링/알림 기능 없음

#### 5. 개발 도구 및 코드 품질 (Dev Tools) - **100% 완료**
- ✅ Pre-commit 훅 설정
- ✅ 코드 포맷터: black, isort
- ✅ 린터: flake8, pylint, mypy
- ✅ Makefile로 Docker 명령어 간소화
- ✅ 보안 정책 문서 (`SECURITY.md`)
- ✅ 환경변수 템플릿 (`.env.example`)

### 🔄 현재 개발 단계 평가

**전체 진행도: 약 35-40%**

프로젝트는 README의 "1주 차: 데이터 수집 및 저장" 단계를 **완료**하고, 기본 스케줄링까지 구현된 상태입니다.

---

## 🎯 프로젝트 목표 재확인 (Project Goals)

### 최종 목표
> 취업 준비생을 위한 LLM 기반 산업 트렌드 분석 및 자동 요약 메일 서비스

### 핵심 시퀀스
1. 매일 국내 주요 기업 뉴스 크롤링 ✅ (완료)
2. 매주 크롤링 데이터를 LLM으로 요약 ❌ (미구현)
3. 사용자별 맞춤 요약 메일 발송 ❌ (미구현)
4. 웹 UI로 결과 확인 ❌ (미구현)

---

## 🚀 기능 개발 우선순위 및 로드맵 (Feature Roadmap)

### Phase 1: ML 기반 요약 엔진 구축 (우선순위: ⭐⭐⭐⭐⭐ 최고)
**목표**: 크롤링된 뉴스를 LLM으로 요약하는 핵심 기능 구현

#### 작업 목록
1. **뉴스 본문 크롤링 강화**
   - 현재: 제목 + URL만 저장
   - 개선: 뉴스 본문(content) 크롤링 추가
   - DB 스키마 수정 필요
   ```sql
   ALTER TABLE danggn_market_urls ADD COLUMN content TEXT;
   ALTER TABLE danggn_market_urls ADD COLUMN published_date TIMESTAMP;
   ALTER TABLE danggn_market_urls ADD COLUMN source VARCHAR(100);
   ```

2. **LLM 요약 모듈 개발**
   - **권장 접근법 A: OpenAI API 사용 (빠른 프로토타입)**
     ```python
     # summarizer/openai_summarizer.py
     import openai
     
     def summarize_news(articles: list[dict]) -> str:
         """OpenAI API로 뉴스 요약"""
         prompt = "다음 뉴스들을 산업 트렌드 관점에서 요약해주세요..."
         response = openai.ChatCompletion.create(...)
         return response.choices[0].message.content
     ```
     - 장점: 빠른 구현, 높은 품질
     - 단점: API 비용, 외부 의존성

   - **권장 접근법 B: 로컬 LLM (확장성 + 학습 기회)**
     ```python
     # summarizer/local_summarizer.py
     from transformers import pipeline
     
     # 한국어 요약 모델 사용
     summarizer = pipeline(
         "summarization",
         model="gogamza/kobart-summarization"
     )
     ```
     - 장점: 비용 없음, 프라이버시, ML 학습
     - 단점: 리소스 많이 필요, 품질 낮을 수 있음

   - **권장 접근법 C: vLLM/SGLang 서빙 (프로덕션급)**
     ```python
     # vLLM으로 Llama-3 같은 오픈소스 LLM 서빙
     # 병렬 처리로 속도 향상
     ```
     - 장점: 고성능, 확장성, 실무 경험
     - 단점: 복잡도 높음, GPU 필요

3. **요약 결과 저장**
   - 새 테이블 생성: `news_summaries`
   ```sql
   CREATE TABLE news_summaries (
       id SERIAL PRIMARY KEY,
       summary_date DATE NOT NULL,
       keyword VARCHAR(100),
       summary_text TEXT NOT NULL,
       article_count INTEGER,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

4. **주간 요약 스케줄러 추가**
   - 매주 일요일 저녁 실행
   - 지난 7일간 뉴스 수집 → 요약 → 저장

#### 구현 순서 (추천)
1. 뉴스 본문 크롤링 추가 (1-2일)
2. DB 스키마 확장 (0.5일)
3. OpenAI API로 프로토타입 (1-2일) ← **먼저 시작**
4. 로컬 LLM으로 대체 검토 (3-5일)
5. 주간 요약 스케줄러 통합 (1일)

**예상 소요 기간**: 1-2주

---

### Phase 2: 웹 UI 구축 (우선순위: ⭐⭐⭐⭐ 높음)
**목표**: 사용자가 요약된 뉴스를 웹에서 확인할 수 있게

#### 작업 목록
1. **Streamlit 기반 대시보드**
   ```python
   # app/streamlit_app.py
   import streamlit as st
   import pandas as pd
   from db.db_news import get_all_summaries
   
   st.title("TrendOps - 산업 트렌드 요약")
   
   # 최근 요약 표시
   summaries = get_all_summaries()
   st.dataframe(summaries)
   
   # 키워드별 필터링
   keyword = st.selectbox("기업 선택", ["당근마켓", "토스", "네이버"])
   ```

2. **FastAPI 백엔드 (선택적)**
   - Streamlit이 단순하면 충분
   - 확장 필요 시 FastAPI 추가
   ```python
   # api/main.py
   from fastapi import FastAPI
   
   app = FastAPI()
   
   @app.get("/summaries")
   def get_summaries(keyword: str = None):
       """요약 조회 API"""
       pass
   ```

3. **Docker 통합**
   ```dockerfile
   # Dockerfile.streamlit
   FROM python:3.13-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install streamlit pandas psycopg2-binary
   COPY app/ ./app/
   COPY db/ ./db/
   CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501"]
   ```

4. **docker-compose 업데이트**
   ```yaml
   streamlit:
     build:
       context: .
       dockerfile: Dockerfile.streamlit
     ports:
       - "8501:8501"
     depends_on:
       - postgres
   ```

**예상 소요 기간**: 3-5일

---

### Phase 3: 사용자 관리 및 맞춤 서비스 (우선순위: ⭐⭐⭐ 중간)
**목표**: 사용자별 관심 기업/직무 설정 및 맞춤 요약

#### 작업 목록
1. **사용자 테이블 설계**
   ```sql
   CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       email VARCHAR(255) UNIQUE NOT NULL,
       name VARCHAR(100),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   CREATE TABLE user_interests (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       company_keyword VARCHAR(100),
       job_category VARCHAR(100)
   );
   ```

2. **사용자 등록 UI**
   - Streamlit 폼으로 간단히 구현
   - 또는 FastAPI + HTML 폼

3. **관심사 기반 필터링**
   ```python
   def get_personalized_summary(user_id: int) -> str:
       """사용자 관심사에 맞는 요약만 추출"""
       interests = get_user_interests(user_id)
       summaries = []
       for keyword in interests:
           summaries.extend(get_summaries_by_keyword(keyword))
       return combine_summaries(summaries)
   ```

**예상 소요 기간**: 5-7일

---

### Phase 4: 이메일 알림 시스템 (우선순위: ⭐⭐⭐ 중간)
**목표**: 주간 요약을 사용자 이메일로 자동 발송

#### 작업 목록
1. **이메일 발송 모듈**
   ```python
   # emailer/send_mail.py
   import smtplib
   from email.mime.text import MIMEText
   from email.mime.multipart import MIMEMultipart
   
   def send_weekly_summary(user_email: str, summary: str):
       """주간 요약 메일 발송"""
       msg = MIMEMultipart()
       msg['Subject'] = "이번 주 산업 트렌드 요약"
       msg['From'] = "trendops@example.com"
       msg['To'] = user_email
       
       body = f"""
       안녕하세요,
       
       이번 주 주요 산업 트렌드입니다:
       
       {summary}
       
       TrendOps 드림
       """
       msg.attach(MIMEText(body, 'plain'))
       
       # Gmail SMTP 예시
       server = smtplib.SMTP('smtp.gmail.com', 587)
       server.starttls()
       server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
       server.send_message(msg)
       server.quit()
   ```

2. **HTML 템플릿 (개선)**
   - 예쁜 이메일 템플릿 작성
   - 회사 로고, 스타일링

3. **스케줄러 통합**
   - 매주 일요일 저녁 자동 발송
   ```python
   # scripts/scheduler.py 수정
   schedule.every().sunday.at("20:00").do(send_weekly_emails)
   ```

4. **환경변수 추가**
   ```bash
   # .env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

**예상 소요 기간**: 3-5일

---

### Phase 5: 고도화 기능 (우선순위: ⭐⭐ 낮음, 선택적)
**목표**: 서비스 품질 향상 및 차별화

#### 5.1 다중 기업 크롤링
- 현재: 단일 키워드만 지원
- 개선: 여러 기업 동시 크롤링
```python
# .env
SEARCH_KEYWORDS=당근마켓,토스,네이버,카카오,쿠팡
```

#### 5.2 감정 분석 (Sentiment Analysis)
- 뉴스 긍정/부정 분석
- 트렌드 방향성 파악
```python
from transformers import pipeline

sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="snunlp/KR-FinBert-SC"
)
```

#### 5.3 벡터 DB (Vector Database)
- 현재: 관계형 DB만 사용
- 개선: 의미 기반 검색을 위한 벡터 DB
```python
# ChromaDB 또는 Pinecone 사용
# "당근마켓과 비슷한 회사" 검색 가능
```

#### 5.4 시각화
- 트렌드 그래프
- 워드 클라우드
- 기업별 뉴스 빈도

#### 5.5 RAG (Retrieval-Augmented Generation)
- 사용자 질문에 대한 LLM 답변
- "당근마켓의 최근 전략은?" → LLM이 뉴스 기반 답변

**예상 소요 기간**: 각 기능당 2-5일

---

## 📝 세부 구현 가이드 (Implementation Guide)

### 1️⃣ Phase 1 시작하기: LLM 요약 (최우선)

#### Step 1: 본문 크롤링 추가
**파일**: `crawling/news_crawling.py`

```python
def fetch_article_content(url: str) -> str:
    """뉴스 본문 크롤링"""
    try:
        response = requests.get(url, headers=header, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 뉴스 본문 선택자
        article = soup.select_one('#dic_area')
        if article:
            return article.get_text(strip=True)
        return ""
    except Exception as e:
        print(f"Failed to fetch content: {e}")
        return ""

# 메인 로직에 추가
for article in articles:
    title = article.text.strip()
    url = article["href"].strip()
    content = fetch_article_content(url)  # 본문 크롤링
    create_new_news(title, url, content)  # DB 저장 시 본문 포함
```

#### Step 2: DB 스키마 마이그레이션
**파일**: `db/migrations/001_add_content_column.sql` (새 파일)

```sql
-- 기존 테이블에 컬럼 추가
ALTER TABLE danggn_market_urls ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE danggn_market_urls ADD COLUMN IF NOT EXISTS published_date TIMESTAMP;
ALTER TABLE danggn_market_urls ADD COLUMN IF NOT EXISTS crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 중복 방지를 위한 유니크 제약
CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON danggn_market_urls(url);
```

마이그레이션 실행:
```bash
docker-compose exec postgres psql -U postgres -d postgres -f /path/to/migration.sql
```

#### Step 3: OpenAI 요약 모듈 (빠른 시작)
**파일**: `summarizer/openai_summarizer.py` (새 파일)

```python
"""OpenAI API를 사용한 뉴스 요약 모듈"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_weekly_news(articles: list[dict[str, str]]) -> str:
    """
    주간 뉴스를 산업 트렌드 관점에서 요약합니다.
    
    Args:
        articles: [{"title": "...", "content": "...", "url": "..."}]
    
    Returns:
        요약된 텍스트
    """
    # 기사 텍스트 결합
    combined_text = "\n\n".join([
        f"제목: {a['title']}\n내용: {a['content'][:500]}..."
        for a in articles
    ])
    
    prompt = f"""
    당신은 취업 준비생을 위한 산업 트렌드 분석가입니다.
    다음 뉴스 기사들을 분석하여, 해당 기업의 주요 동향과 
    취업 지원자가 알아야 할 핵심 인사이트를 요약해주세요.
    
    뉴스 기사들:
    {combined_text}
    
    다음 형식으로 요약해주세요:
    1. 주요 동향 (2-3문장)
    2. 핵심 키워드 (5개)
    3. 취업 준비생을 위한 인사이트 (3-4문장)
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 비용 효율적
        messages=[
            {"role": "system", "content": "당신은 산업 트렌드 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content


def main():
    """테스트용 메인 함수"""
    from db.db_news import get_recent_news
    
    # 최근 7일 뉴스 가져오기
    articles = get_recent_news(days=7)
    
    if not articles:
        print("요약할 뉴스가 없습니다.")
        return
    
    summary = summarize_weekly_news(articles)
    print("=== 주간 요약 ===")
    print(summary)
    
    # DB에 저장
    from db.db_news import save_summary
    save_summary(summary, len(articles))


if __name__ == "__main__":
    main()
```

**환경변수 추가** (`.env`):
```bash
OPENAI_API_KEY=sk-...
```

#### Step 4: DB 함수 추가
**파일**: `db/db_news.py` (기존 파일 수정)

```python
def get_recent_news(days: int = 7) -> list[dict[str, str]]:
    """최근 N일간의 뉴스를 가져옵니다."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
            SELECT title, content, url, published_date
            FROM danggn_market_urls
            WHERE crawled_at >= NOW() - INTERVAL '%s days'
            ORDER BY crawled_at DESC;
        """
        cur.execute(sql, (days,))
        rows = cur.fetchall()
        cur.close()
        
        return [
            {
                "title": row[0],
                "content": row[1],
                "url": row[2],
                "published_date": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        print(f"Failed to fetch recent news: {e}")
        return []
    finally:
        if conn:
            conn.close()


def save_summary(summary_text: str, article_count: int, keyword: str = "당근마켓"):
    """요약을 DB에 저장합니다."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
            INSERT INTO news_summaries (summary_date, keyword, summary_text, article_count)
            VALUES (CURRENT_DATE, %s, %s, %s)
            RETURNING id;
        """
        cur.execute(sql, (keyword, summary_text, article_count))
        summary_id = cur.fetchone()[0]
        
        conn.commit()
        print(f"Summary saved with ID: {summary_id}")
        cur.close()
    except Exception as e:
        print(f"Failed to save summary: {e}")
    finally:
        if conn:
            conn.close()
```

#### Step 5: 요약 Dockerfile
**파일**: `Dockerfile.summarizer` (새 파일)

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    psycopg2-binary \
    openai \
    python-dotenv

# Copy source code
COPY summarizer/ ./summarizer/
COPY db/ ./db/

ENV PYTHONPATH=/app

CMD ["python", "-m", "summarizer.openai_summarizer"]
```

#### Step 6: docker-compose 업데이트
**파일**: `docker-compose.yml` (기존 파일 수정)

```yaml
# 기존 서비스 아래에 추가
  summarizer:
    build:
      context: .
      dockerfile: Dockerfile.summarizer
    container_name: trendops-summarizer
    depends_on:
      - postgres
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: ${POSTGRES_DB:-postgres}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
      OPENAI_API_KEY: ${OPENAI_API_KEY:?OPENAI_API_KEY is required}
      SEARCH_KEYWORD: ${SEARCH_KEYWORD:-당근마켓}
    networks:
      - trendops-network
    restart: "no"  # 수동 실행 또는 스케줄러로 트리거
```

#### Step 7: 스케줄러에 요약 추가
**파일**: `scripts/scheduler.py` (기존 파일 수정)

```python
def run_summarizer():
    """요약 생성기를 실행합니다."""
    try:
        logger.info("Starting news summarizer...")
        result = subprocess.run(
            ["python", "-m", "summarizer.openai_summarizer"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=600,  # 10분 타임아웃
        )
        
        if result.returncode == 0:
            logger.info(f"Summarizer completed: {result.stdout}")
        else:
            logger.error(f"Summarizer failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running summarizer: {e}")


def main():
    """메인 스케줄러 함수"""
    schedule_time = os.getenv("CRAWL_SCHEDULE", "09:00")
    summary_time = os.getenv("SUMMARY_SCHEDULE", "21:00")  # 저녁 9시
    
    logger.info(f"Scheduler started.")
    logger.info(f"Crawler: daily at {schedule_time}")
    logger.info(f"Summarizer: weekly on Sunday at {summary_time}")
    
    # 매일 크롤링
    schedule.every().day.at(schedule_time).do(run_crawler)
    
    # 매주 일요일 요약 생성
    schedule.every().sunday.at(summary_time).do(run_summarizer)
    
    # 시작 시 즉시 실행
    if os.getenv("RUN_ON_START", "false").lower() == "true":
        logger.info("Running crawler immediately...")
        run_crawler()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

#### 테스트 방법
```bash
# 1. 환경변수 설정
echo "OPENAI_API_KEY=sk-..." >> .env

# 2. 빌드
make build

# 3. DB 마이그레이션
docker-compose exec postgres psql -U postgres -d postgres < db/migrations/001_add_content_column.sql

# 4. 크롤러 실행 (본문 포함)
docker-compose run --rm crawler

# 5. 요약 생성
docker-compose run --rm summarizer

# 6. 결과 확인
docker-compose exec postgres psql -U postgres -d postgres -c "SELECT * FROM news_summaries;"
```

---

### 2️⃣ Phase 2 시작하기: Streamlit UI

#### Step 1: Streamlit 앱 작성
**파일**: `app/streamlit_app.py` (새 파일)

```python
"""TrendOps Streamlit 대시보드"""
import streamlit as st
import pandas as pd
from db.db_news import get_all_summaries, get_all_news

st.set_page_config(
    page_title="TrendOps",
    page_icon="📈",
    layout="wide"
)

st.title("📈 TrendOps - 산업 트렌드 요약 대시보드")
st.markdown("취업 준비생을 위한 기업 뉴스 트렌드 분석 서비스")

# 탭 구성
tab1, tab2 = st.tabs(["📊 주간 요약", "📰 전체 뉴스"])

with tab1:
    st.header("주간 트렌드 요약")
    
    # 요약 목록 가져오기
    summaries = get_all_summaries()
    
    if summaries:
        for summary in summaries:
            with st.expander(
                f"🗓️ {summary['summary_date']} - {summary['keyword']} "
                f"({summary['article_count']}개 기사)"
            ):
                st.markdown(summary['summary_text'])
    else:
        st.info("아직 생성된 요약이 없습니다. 크롤링과 요약을 실행해주세요.")

with tab2:
    st.header("크롤링된 전체 뉴스")
    
    # 검색 키워드 필터
    keyword_filter = st.text_input("기업명으로 검색", "")
    
    # 뉴스 목록
    news = get_all_news()
    
    if news:
        df = pd.DataFrame(news, columns=['ID', 'Title', 'URL', 'Crawled At'])
        
        if keyword_filter:
            df = df[df['Title'].str.contains(keyword_filter, case=False, na=False)]
        
        st.dataframe(df, use_container_width=True)
        st.metric("총 뉴스 수", len(df))
    else:
        st.warning("크롤링된 뉴스가 없습니다.")

# 사이드바 - 통계
with st.sidebar:
    st.header("📌 통계")
    total_news = len(get_all_news())
    total_summaries = len(get_all_summaries())
    
    st.metric("전체 뉴스", total_news)
    st.metric("생성된 요약", total_summaries)
    
    st.markdown("---")
    st.markdown("### 🔄 업데이트")
    st.info("매일 오전 9시 뉴스 크롤링\n매주 일요일 저녁 9시 요약 생성")
```

#### Step 2: DB 함수 추가
**파일**: `db/db_news.py` (기존 파일 수정)

```python
def get_all_summaries() -> list[dict]:
    """모든 요약을 가져옵니다."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT summary_date, keyword, summary_text, article_count, created_at
            FROM news_summaries
            ORDER BY summary_date DESC;
        """)
        
        rows = cur.fetchall()
        cur.close()
        
        return [
            {
                "summary_date": row[0],
                "keyword": row[1],
                "summary_text": row[2],
                "article_count": row[3],
                "created_at": row[4]
            }
            for row in rows
        ]
    except Exception as e:
        print(f"Failed to fetch summaries: {e}")
        return []
    finally:
        if conn:
            conn.close()
```

#### Step 3: Streamlit Dockerfile
**파일**: `Dockerfile.streamlit` (새 파일)

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    streamlit \
    pandas \
    psycopg2-binary

# Copy source code
COPY app/ ./app/
COPY db/ ./db/

ENV PYTHONPATH=/app

EXPOSE 8501

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Step 4: docker-compose 업데이트
**파일**: `docker-compose.yml` (기존 파일 수정)

```yaml
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    container_name: trendops-streamlit
    depends_on:
      - postgres
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: ${POSTGRES_DB:-postgres}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
    ports:
      - "8501:8501"
    networks:
      - trendops-network
    restart: unless-stopped
```

#### 테스트 방법
```bash
# 1. 빌드 및 실행
make build
make up

# 2. 브라우저에서 접속
open http://localhost:8501

# 3. 대시보드 확인
# - 주간 요약 탭에서 요약 확인
# - 전체 뉴스 탭에서 크롤링 결과 확인
```

---

## 🔧 기술 스택 추천 (Tech Stack Recommendations)

### 현재 스택 ✅
- **크롤링**: BeautifulSoup4, requests
- **DB**: PostgreSQL 15
- **스케줄링**: Python schedule
- **컨테이너**: Docker, Docker Compose
- **코드 품질**: black, flake8, mypy

### 추가 권장 스택

#### ML/LLM (Phase 1)
1. **OpenAI API** (최우선 추천) ⭐⭐⭐⭐⭐
   - 빠른 프로토타입
   - 높은 품질
   - 비용: GPT-4o-mini 약 $0.15/1M tokens

2. **HuggingFace Transformers** (학습용) ⭐⭐⭐⭐
   - 무료
   - 한국어 모델: `gogamza/kobart-summarization`
   - CPU에서도 작동

3. **vLLM + Llama-3** (프로덕션급) ⭐⭐⭐
   - 고성능
   - GPU 필요
   - 실무 경험 쌓기 좋음

#### 웹 프레임워크 (Phase 2)
1. **Streamlit** (최우선 추천) ⭐⭐⭐⭐⭐
   - 빠른 개발
   - Python 친화적
   - 프로토타입에 완벽

2. **FastAPI** (확장 시) ⭐⭐⭐⭐
   - RESTful API
   - 자동 문서화
   - 모바일 앱 연동 시 필요

#### 스케줄링 (개선)
1. **Apache Airflow** (실무급) ⭐⭐⭐⭐
   - DAG 기반 워크플로우
   - 모니터링 UI
   - 실패 재시도
   - 오버킬일 수 있음

2. **Python APScheduler** (현실적) ⭐⭐⭐⭐⭐
   - 현재 schedule 라이브러리보다 강력
   - 간단한 통합
   - 충분히 실용적

#### 이메일 (Phase 4)
1. **SendGrid** (프로덕션) ⭐⭐⭐⭐⭐
   - 안정적
   - 템플릿 지원
   - 무료 플랜: 100통/일

2. **Gmail SMTP** (테스트용) ⭐⭐⭐
   - 무료
   - 간단한 설정
   - 제한: 500통/일

---

## 📅 전체 타임라인 (Overall Timeline)

### 최소 기능 프로토타입 (MVP) - 3-4주
- ✅ Week 1: 크롤링 + DB (완료)
- 🔄 Week 2-3: LLM 요약 + Streamlit UI (Phase 1-2)
- Week 4: 사용자 관리 + 이메일 (Phase 3-4 기본)

### 완성 버전 - 6-8주
- Week 1-4: MVP (위와 동일)
- Week 5-6: 다중 기업, 감정 분석
- Week 7-8: 벡터 DB, RAG, 시각화

---

## 💡 핵심 팁 및 주의사항 (Key Tips)

### ✅ DO (해야 할 것)
1. **작은 단위로 테스트하며 개발**
   - 크롤링 → DB 저장 → 요약 → UI 순서로
   - 각 단계마다 Docker 컨테이너로 독립 실행

2. **환경변수로 모든 설정 관리**
   - 절대 하드코딩 금지
   - `.env` 파일을 git에 커밋하지 말 것

3. **로깅 철저히**
   - 모든 단계에 로그 추가
   - 실패 원인 추적 가능하게

4. **OpenAI API부터 시작**
   - 로컬 LLM은 나중에 고려
   - 빠른 검증이 중요

5. **Git 브랜치 전략 준수**
   - `feature/llm-summarizer`
   - `feature/streamlit-ui`
   - PR로 `develop`에 머지

### ❌ DON'T (피해야 할 것)
1. **처음부터 완벽하게 만들려 하지 말기**
   - 프로토타입 먼저, 최적화는 나중에
   - "동작하는 더러운 코드" > "동작 안 하는 깨끗한 코드"

2. **크롤링 시 IP 차단 주의**
   - 요청 간 딜레이 추가 (`time.sleep(1)`)
   - User-Agent 헤더 필수
   - 필요시 Proxy 고려

3. **LLM 비용 폭탄 주의**
   - OpenAI API 사용량 모니터링
   - 토큰 리미트 설정
   - 개발 시 GPT-4o-mini 사용

4. **DB 마이그레이션 없이 스키마 변경 금지**
   - 항상 마이그레이션 스크립트 작성
   - 롤백 방법 준비

5. **보안 정보 노출**
   - `.env`를 절대 커밋하지 말 것
   - GitHub Actions Secrets 사용

---

## 🎓 학습 리소스 (Learning Resources)

### 크롤링
- BeautifulSoup4 공식 문서: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- 네이버 뉴스 크롤링 주의사항: robots.txt 확인

### LLM/ML
- **OpenAI API 퀵스타트**: https://platform.openai.com/docs/quickstart
- **HuggingFace 요약 튜토리얼**: https://huggingface.co/docs/transformers/tasks/summarization
- **vLLM GitHub**: https://github.com/vllm-project/vllm
- **한국어 LLM 모델 목록**: https://huggingface.co/models?language=ko

### 웹 개발
- **Streamlit 튜토리얼**: https://docs.streamlit.io/get-started
- **FastAPI 공식 문서**: https://fastapi.tiangolo.com/

### Docker
- **Docker Compose 공식 문서**: https://docs.docker.com/compose/
- **멀티스테이지 빌드**: 이미지 크기 최적화

### 스케줄링
- **APScheduler**: https://apscheduler.readthedocs.io/
- **Airflow 튜토리얼**: https://airflow.apache.org/docs/

---

## 🚦 다음 단계 (Next Steps)

### 이번 주에 시작할 것 (This Week)
1. **DB 스키마 확장**
   - `content`, `published_date` 컬럼 추가
   - 마이그레이션 스크립트 작성

2. **뉴스 본문 크롤링**
   - `news_crawling.py`에 `fetch_article_content()` 함수 추가
   - 테스트: 본문이 DB에 제대로 저장되는지 확인

3. **OpenAI API 계정 생성**
   - https://platform.openai.com/ 가입
   - API 키 발급
   - 크레딧 확인 (무료 크레딧 있음)

4. **요약 모듈 프로토타입**
   - `summarizer/openai_summarizer.py` 작성
   - 수동 실행으로 테스트

### 다음 주 계획 (Next Week)
1. 요약 스케줄러 통합
2. Streamlit UI 개발 시작
3. Docker Compose 업데이트

---

## 📊 성공 지표 (Success Metrics)

### MVP 완성 기준
- [ ] 매일 자동으로 뉴스 크롤링 (제목 + 본문)
- [ ] 매주 LLM 요약 자동 생성
- [ ] 웹 UI에서 요약 확인 가능
- [ ] Docker로 전체 시스템 실행
- [ ] 최소 1개 기업 키워드 지원

### 완성 버전 기준
- [ ] 5개 이상 기업 동시 크롤링
- [ ] 사용자 등록 및 관심사 설정
- [ ] 주간 요약 이메일 자동 발송
- [ ] 감정 분석 또는 시각화 중 1개
- [ ] 안정적인 스케줄링 (실패 시 재시도)

---

## 🤝 커뮤니티 및 지원 (Community & Support)

### 막힐 때 참고할 곳
1. **스택 오버플로우**: 기술적 질문
2. **GitHub Issues**: 라이브러리 관련 문제
3. **Reddit r/learnprogramming**: 학습 조언
4. **Discord/Slack**: 한국 개발자 커뮤니티

### 피드백 환영
- 이 문서에 대한 개선 제안
- 구현 중 막힌 부분 공유
- 새로운 아이디어 제안

---

## 📌 요약 (Summary)

### 현재 상태
**진행도: 35-40%**
- ✅ 크롤링, DB, 스케줄링 완료
- ❌ LLM 요약, UI, 이메일 미구현

### 최우선 작업
**Phase 1: LLM 요약 (1-2주)**
1. 뉴스 본문 크롤링 추가
2. OpenAI API로 주간 요약 생성
3. 스케줄러 통합

### 추천 기술 스택
- **LLM**: OpenAI API (GPT-4o-mini)
- **UI**: Streamlit
- **이메일**: SendGrid 또는 Gmail SMTP

### 타임라인
- **MVP**: 3-4주 (Phase 1-2)
- **완성**: 6-8주 (Phase 1-5)

---

**마지막 업데이트**: 2026-01-19
**버전**: 1.0.0
**작성자**: GitHub Copilot

이 문서는 프로젝트 진행에 따라 지속적으로 업데이트될 예정입니다.
