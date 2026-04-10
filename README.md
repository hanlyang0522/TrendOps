# TrendOps: LLM 기반 산업 트렌드 요약 + 자소서 작성 자동화

취업 준비생을 위한 서비스. 국내 주요 기업의 뉴스를 자동 수집하고, Google Gemini LLM으로 기업 분석 → 문항 분석 → 경험 매핑 → 자소서 답변 생성까지 5단계를 자동화합니다.

---

## 📐 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  docker-compose                      │
│                                                     │
│  postgres ──► db-init                               │
│      │                                              │
│      ├──► crawler (네이버 뉴스 크롤링, 매일 09:00)       │
│      │         └── scheduler                        │
│      │                                              │
│      └──► cover-letter :8501 (Streamlit 위자드)      │
│                └── google-genai (Gemini API)         │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

`.env`에서 아래 항목을 채웁니다.

| 변수 | 필수 | 설명 |
|------|------|------|
| `POSTGRES_PASSWORD` | ✅ | DB 비밀번호 |
| `GEMINI_API_KEY` | ✅ | [Google AI Studio](https://aistudio.google.com/)에서 발급 |
| `NAVER_CLIENT_ID` | ✅ | [Naver Developers](https://developers.naver.com/)에서 발급 |
| `NAVER_CLIENT_SECRET` | ✅ | Naver Client Secret |
| `DART_API_KEY` | ✅ | [DART 오픈API](https://opendart.fss.or.kr/)에서 발급 (기업 사업보고서 수집) |
| `FIRECRAWL_API_KEY` | ✅ | [Firecrawl](https://firecrawl.dev/)에서 발급 (JD·인재상·뉴스 fallback) |

### 2. 빌드 & 실행

```bash
make build && make up
```

### 3. 자소서 위자드 접속

브라우저에서 **http://localhost:8501** 열기

---

## ✍️ 자소서 위자드 사용법

Streamlit 5단계 위자드 (`frontend/cover_letter_app.py`)

### Step 0 — 내 프로필 등록
- 경력기술서 또는 자기소개 텍스트를 **TXT·MD·DOCX 파일로 업로드** 하거나 **텍스트 직접 붙여넣기**
- LLM이 자동으로 이름·경험 목록·글쓰기 스타일을 JSON으로 구조화
- 추출 결과를 편집 후 저장

### Step 1 — 기업·직무 분석
- 기업명과 지원 직무 입력
- 4가지 소스에서 자동 수집 (7일 캐시):
  - DART 사업보고서 (`DART_API_KEY` 필수)
  - 네이버 뉴스 (5건 미만이면 Firecrawl fallback)
  - 공식 홈페이지 인재상·비전 페이지 (Firecrawl, `FIRECRAWL_API_KEY` 필수)
  - JD(직무기술서) 자동 수집 (Firecrawl→PDF폴백→수기 입력)
- 자소서 문항 목록 입력 → LLM이 측정역량·기대수준 분석

### Step 2 — 문항 분석
- 각 문항의 측정 역량, 기대 수준, 목표 글자 수 확인
- 내용 수정 후 다음 단계로 진행

### Step 3 — 경험-문항 매핑
- LLM이 내 경험과 각 문항의 적합도를 1~5점으로 평가
- **score ≥ 3인 경험만 표시** (primary / supporting / background 분류)
- 동일 경험을 여러 문항에 중복 사용 시 ⚠️ 경고 표시
- 활용 유형 직접 수정 후 확정

### Step 4 — 답변 생성
- LLM이 매핑된 경험 기반으로 답변 초안 생성
- **글자 수 자동 루프**: 목표 범위에 들어올 때까지 최대 3회 재시도
- **AI 자가진단**: AI 특유 표현·추상적 서술·근거 없는 내용 자동 탐지
- 수정 지시를 입력하면 자가진단 결과를 반영해 재생성
- 최종 확인 후 DB에 저장

---

## 📋 서비스 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| `postgres` | 5432 | 뉴스 + 자소서 데이터 저장소 |
| `db-init` | — | 스키마 초기화 (뉴스 + 자소서 6개 엔티티) |
| `crawler` | — | 네이버 뉴스 크롤링 |
| `scheduler` | — | 크롤링 주기 실행 (매일 09:00) |
| `cover-letter` | **8501** | Streamlit 자소서 작성 위자드 |

---

## 🛠️ 환경 변수

```bash
# ── 필수 ─────────────────────────────────────────────
POSTGRES_PASSWORD=your_secure_password_here
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
GEMINI_API_KEY=your_gemini_api_key_here

# ── 선택 (LLM 모델 오버라이드) ──────────────────────────
GEMINI_FLASH_MODEL=gemini-2.5-flash
GEMINI_PRO_MODEL=gemini-2.5-pro

# ── 선택 (기업 분석 강화) ──────────────────────────────
DART_API_KEY=                    # DART 사업보고서
FIRECRAWL_API_KEY=               # 뉴스 fallback

# ── 크롤러 ───────────────────────────────────────────
SEARCH_KEYWORD=your_search_keyword_here
CRAWL_SCHEDULE=0 9 * * *
```

전체 항목은 [`.env.example`](.env.example) 참고.

---

## 📊 데이터베이스 스키마

### 뉴스 크롤링
| 테이블 | 설명 |
|--------|------|
| `news_articles` | 크롤링된 뉴스 기사 |

### 자소서 자동화
| 테이블 | 설명 |
|--------|------|
| `user_profile` | 지원자 프로필 (경험 목록, 글쓰기 스타일) |
| `company_analysis` | 기업 분석 결과 (4-소스, 7일 캐시) |
| `job_analysis` | 직무별 분석 결과 |
| `jd` | 직무기술서 JD (Firecrawl→PDF폴백→수기) |
| `question` | 자소서 문항 (측정역량, 목표 글자 수) |
| `mapping_table` | 경험-문항 매핑 결과 |
| `cover_letter_draft` | 생성된 답변 초안 (버전 이력, 환각 재시도 카운트) |

DDL:
- [`db/migrations/001_cover_letter_schema.sql`](db/migrations/001_cover_letter_schema.sql)
- [`db/migrations/002_add_jd_entity.sql`](db/migrations/002_add_jd_entity.sql)

---

## 🧪 개발

```bash
# 개발용 컨테이너 접속
make shell-crawler

# PostgreSQL 접속
make shell-postgres

# 전체 테스트 실행
source .venv/bin/activate
python -m pytest tests/ -v

# pre-commit 검사
pre-commit run --all-files
```

---

## 🔧 문제 해결

```bash
# 서비스 재시작
make restart

# 전체 초기화 (데이터 삭제 주의)
make clean && make build && make up

# 크롤러 한 번만 실행
docker-compose run --rm crawler python -m crawling.news_crawling_mcp

# 자소서 서비스 로그
docker-compose logs -f cover-letter
```

---

## 🔒 보안

```bash
# 1. 환경 변수 파일 생성
cp .env.example .env

# 2. .env 수정 (패스워드, API 키 입력)
nano .env
```

- `.env` 파일은 절대 git에 커밋하지 않습니다 (`.gitignore` 설정됨)
- 자세한 내용은 [SECURITY.md](./SECURITY.md) 참고
