# TrendOps 빠른 시작 가이드 (Quick Start Guide)

> 📖 **전체 분석 문서**: [PROJECT_ANALYSIS_AND_ROADMAP.md](./PROJECT_ANALYSIS_AND_ROADMAP.md)

## 🎯 현재 프로젝트 상태

**진행도: 35-40%** ✅ 기본 인프라 완료

### 완료된 것 ✅
- Docker 컨테이너화
- 네이버 뉴스 크롤링 (제목 + URL)
- PostgreSQL 데이터베이스
- 기본 스케줄링 (매일 09:00)
- 코드 품질 도구 (black, flake8, mypy)

### 아직 안 된 것 ❌
- **LLM 요약 기능** ← 가장 중요!
- 웹 UI (Streamlit/FastAPI)
- 이메일 알림
- 사용자 관리

---

## 🚀 다음에 할 일 (우선순위 순)

### 1️⃣ Phase 1: LLM 요약 (최우선) ⭐⭐⭐⭐⭐
**목표**: 크롤링된 뉴스를 AI로 요약

**할 일**:
1. 뉴스 **본문** 크롤링 추가 (현재는 제목만)
2. DB에 `content` 컬럼 추가
3. OpenAI API로 주간 요약 생성
4. 요약을 DB에 저장

**예상 시간**: 1-2주

**시작하기**:
```bash
# 1. OpenAI API 키 받기
https://platform.openai.com/

# 2. .env에 추가
echo "OPENAI_API_KEY=sk-..." >> .env

# 3. 본문 크롤링 추가 (crawling/news_crawling_mcp.py 확장)
# 4. DB 스키마 변경 (migrations/001_add_content_column.sql)
# 5. summarizer/openai_summarizer.py 작성
```

### 2️⃣ Phase 2: 웹 UI (Streamlit) ⭐⭐⭐⭐
**목표**: 요약 결과를 웹에서 확인

**할 일**:
1. Streamlit 앱 작성 (`app/streamlit_app.py`)
2. DB 조회 함수 추가
3. Docker 통합

**예상 시간**: 3-5일

**시작하기**:
```bash
# 1. Streamlit 설치
pip install streamlit

# 2. 앱 작성 (app/streamlit_app.py)
# 3. Docker 빌드
make build

# 4. 실행
make up

# 5. 브라우저에서 확인
open http://localhost:8501
```

### 3️⃣ Phase 3: 사용자 관리 ⭐⭐⭐
**목표**: 사용자별 관심 기업 설정

**예상 시간**: 5-7일

### 4️⃣ Phase 4: 이메일 알림 ⭐⭐⭐
**목표**: 주간 요약 자동 발송

**예상 시간**: 3-5일

### 5️⃣ Phase 5: 고도화 (선택적) ⭐⭐
- 다중 기업 크롤링
- 감정 분석
- 시각화

---

## 📝 Phase 1 구현 체크리스트

### Step 1: 본문 크롤링
```python
# crawling/news_crawling_mcp.py 또는 crawling/naver_mcp_crawler.py 에 추가

def fetch_article_content(url: str) -> str:
    """뉴스 본문 크롤링"""
    response = requests.get(url, headers=header, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    article = soup.select_one('#dic_area')
    return article.get_text(strip=True) if article else ""
```

- [ ] `fetch_article_content()` 함수 작성
- [ ] 메인 로직에 통합
- [ ] 테스트: 본문이 출력되는지 확인

### Step 2: DB 스키마 변경
```sql
-- db/migrations/001_add_content_column.sql

ALTER TABLE danggn_market_urls ADD COLUMN content TEXT;
ALTER TABLE danggn_market_urls ADD COLUMN published_date TIMESTAMP;
ALTER TABLE danggn_market_urls ADD COLUMN crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE UNIQUE INDEX idx_url ON danggn_market_urls(url);

-- 요약 테이블 생성
CREATE TABLE news_summaries (
    id SERIAL PRIMARY KEY,
    summary_date DATE NOT NULL,
    keyword VARCHAR(100),
    summary_text TEXT NOT NULL,
    article_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- [ ] 마이그레이션 파일 작성
- [ ] DB에 적용
  ```bash
  docker-compose exec postgres psql -U postgres -d postgres -f /path/to/migration.sql
  ```
- [ ] 테이블 확인
  ```bash
  docker-compose exec postgres psql -U postgres -d postgres -c "\d danggn_market_urls"
  ```

### Step 3: OpenAI 요약 모듈
```python
# summarizer/openai_summarizer.py (새 파일)

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_weekly_news(articles: list[dict]) -> str:
    """주간 뉴스 요약"""
    combined_text = "\n\n".join([
        f"제목: {a['title']}\n내용: {a['content'][:500]}..."
        for a in articles
    ])

    prompt = f"""
    취업 준비생을 위한 산업 트렌드 분석:
    {combined_text}

    형식:
    1. 주요 동향 (2-3문장)
    2. 핵심 키워드 (5개)
    3. 취업 인사이트 (3-4문장)
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "산업 트렌드 분석 전문가"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content
```

- [ ] `summarizer/` 디렉토리 생성
- [ ] `openai_summarizer.py` 작성
- [ ] OpenAI API 키 설정
- [ ] 수동 테스트
  ```bash
  python -m summarizer.openai_summarizer
  ```

### Step 4: DB 함수 추가
```python
# db/db_news.py 에 추가

def get_recent_news(days: int = 7) -> list[dict]:
    """최근 N일 뉴스 조회"""
    # ... (구현은 전체 문서 참고)

def save_summary(summary_text: str, article_count: int, keyword: str = "당근마켓"):
    """요약 저장"""
    # ... (구현은 전체 문서 참고)
```

- [ ] `get_recent_news()` 함수 추가
- [ ] `save_summary()` 함수 추가
- [ ] 테스트

### Step 5: Docker 통합
- [ ] `Dockerfile.summarizer` 작성
- [ ] `docker-compose.yml`에 summarizer 서비스 추가
- [ ] 빌드 및 테스트
  ```bash
  make build
  docker-compose run --rm summarizer
  ```

### Step 6: 스케줄러 통합
```python
# scripts/scheduler.py 에 추가

def run_summarizer():
    """요약 생성"""
    # ... (구현은 전체 문서 참고)

# 매주 일요일 저녁 9시
schedule.every().sunday.at("21:00").do(run_summarizer)
```

- [ ] `run_summarizer()` 함수 추가
- [ ] 스케줄 설정
- [ ] 테스트

---

## 🔧 필수 환경 변수

```bash
# .env 파일

# 기존
POSTGRES_HOST=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
SEARCH_KEYWORD=당근마켓
CRAWL_SCHEDULE=09:00

# 추가 필요 (Phase 1)
OPENAI_API_KEY=sk-...
SUMMARY_SCHEDULE=21:00

# 추가 필요 (Phase 4)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## 📚 유용한 명령어

### Docker
```bash
# 전체 빌드 및 실행
make build && make up

# 로그 확인
make logs

# 크롤러 한 번만 실행
docker-compose run --rm crawler

# 요약 생성 (Phase 1 이후)
docker-compose run --rm summarizer

# DB 접속
make shell-postgres
```

### DB 조회
```bash
# 뉴스 확인
docker-compose exec postgres psql -U postgres -d postgres -c "SELECT * FROM danggn_market_urls LIMIT 5;"

# 요약 확인 (Phase 1 이후)
docker-compose exec postgres psql -U postgres -d postgres -c "SELECT * FROM news_summaries;"
```

### Git
```bash
# 새 브랜치 생성
git checkout -b feature/llm-summarizer develop

# 커밋
git add .
git commit -m "feat(summarizer): add OpenAI summarization module"

# PR 생성 (develop 브랜치로)
git push origin feature/llm-summarizer
```

---

## 💡 핵심 팁

### ✅ DO
1. **작게 시작하기**: Phase 1부터 순서대로
2. **자주 테스트**: 각 단계마다 Docker 실행 확인
3. **로그 확인**: 에러 발생 시 `make logs` 먼저
4. **환경변수 관리**: `.env` 파일 절대 커밋하지 말 것
5. **문서 참고**: 막힐 때 [전체 문서](./PROJECT_ANALYSIS_AND_ROADMAP.md) 참고

### ❌ DON'T
1. **한 번에 다 하려고 하지 말기**: 단계별로!
2. **하드코딩 금지**: 모든 설정은 환경변수로
3. **OpenAI 비용 주의**: 개발 시 GPT-4o-mini 사용
4. **크롤링 무리하지 말기**: 요청 간 딜레이 필수

---

## 📊 마일스톤

### MVP (3-4주)
- [ ] 뉴스 본문 크롤링
- [ ] LLM 주간 요약
- [ ] Streamlit UI
- [ ] Docker로 전체 실행

### 완성 버전 (6-8주)
- [ ] MVP 완료
- [ ] 사용자 관리
- [ ] 이메일 발송
- [ ] 다중 기업 지원

---

## 🆘 도움이 필요할 때

### 문서
- [전체 분석 문서](./PROJECT_ANALYSIS_AND_ROADMAP.md) - 상세 구현 가이드
- [README.md](../README.md) - 프로젝트 개요 및 실행 방법
- [SECURITY.md](../SECURITY.md) - 보안 가이드

### 학습 자료
- **OpenAI API**: https://platform.openai.com/docs/quickstart
- **Streamlit**: https://docs.streamlit.io/get-started
- **Docker Compose**: https://docs.docker.com/compose/

### 커뮤니티
- Stack Overflow
- Reddit r/learnprogramming
- GitHub Issues (각 라이브러리)

---

## 📌 다음 액션

**오늘 할 일**:
1. ✅ 프로젝트 분석 문서 읽기
2. ⬜ OpenAI API 계정 만들기 → https://platform.openai.com/
3. ⬜ API 키 받아서 `.env`에 추가
4. ⬜ 본문 크롤링 함수 작성 시작

**이번 주 목표**:
- [ ] Phase 1 완료 (LLM 요약)
- [ ] 최소 1번 요약 성공적으로 생성

**다음 주 목표**:
- [ ] Phase 2 시작 (Streamlit UI)

---

**마지막 업데이트**: 2026-01-19
**버전**: 1.0.0

🎉 **화이팅! 한 단계씩 차근차근 진행하면 됩니다!**
