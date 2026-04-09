# Quickstart: 자소서 작성 자동화 서비스 (로컬 실행)

**Branch**: `001-cover-letter-automation` | **Date**: 2026-04-09

---

## 사전 조건

- Docker & Docker Compose 설치
- Python 3.13 + 가상환경 (`.venv`)
- OpenAI API Key 발급

---

## 1. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일에 다음 항목 추가/수정:

```dotenv
# 기존 필수 항목 (변경 없음)
POSTGRES_PASSWORD=your_secure_password

# 자소서 서비스 추가 항목
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o          # 기본값, 교체 가능
COVER_LETTER_MODULE_ENABLED=true
```

---

## 2. DB 마이그레이션 (최초 1회)

```bash
# PostgreSQL 컨테이너 실행
docker compose up -d postgres

# 자소서 서비스 테이블 생성
docker compose run --rm db-init
# 또는 직접 실행:
# psql -h localhost -U postgres -d postgres -f db/migrations/001_cover_letter_schema.sql
```

---

## 3. Python 의존성 설치

```bash
source .venv/bin/activate

pip install \
  pymupdf \
  python-docx \
  openai \
  streamlit
```

> **참고**: 기존 `psycopg2-binary`, `requests` 등은 이미 설치된 상태.

---

## 4. Streamlit 앱 실행

```bash
source .venv/bin/activate
streamlit run frontend/cover_letter_app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 5. Docker Compose로 전체 스택 실행 (선택)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

`docker-compose.dev.yml`에 `cover-letter` 서비스 정의 추가 후 사용 가능.

---

## 6. 첫 사용 흐름

1. **프로필 등록** → 포트폴리오 PDF 또는 합격 자소서 파일 업로드
2. **프로필 검토** → 추출된 경험·역량·문체 요약 확인 후 "저장" 클릭
3. **기업·직무 입력** → 기업명 + 직무명 입력 후 "분석 시작"
4. **문항 입력** → 자소서 문항 텍스트 + 글자 수 제한 입력
5. **매핑 테이블 확인** → 자동 생성된 경험-문항 매핑을 수정 후 "확정"
6. **답변 생성** → "초안 생성" 클릭 → 자가진단 결과 검토 → 필요 시 수정 지시 반복

---

## 환경 변수 전체 목록 (자소서 서비스)

| 변수명 | 필수 | 기본값 | 설명 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API 인증 키 |
| `OPENAI_MODEL` | | `gpt-4o` | 사용할 LLM 모델명 |
| `COMPANY_CACHE_DAYS` | | `7` | 기업 분석 캐시 유효 기간(일) |
| `COVER_LETTER_MAX_RETRIES` | | `3` | 글자 수 재작성 최대 횟수 |
