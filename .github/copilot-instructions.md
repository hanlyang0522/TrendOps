# GitHub Copilot Instructions for TrendOps

## 1. Project Overview

**Project Name:** TrendOps

**Description:** LLM-based industry trend analysis and news summarization service. This service crawls news articles about major Korean companies, stores them in a PostgreSQL database, and provides AI-powered summaries to help job seekers analyze industry trends for their applications.

**Tech Stack:**
- **Language:** Python 3.13
- **Database:** PostgreSQL 15
- **Containerization:** Docker, Docker Compose
- **Web Scraping:** BeautifulSoup4, requests
- **Code Quality:** black, isort, flake8, mypy, pre-commit
- **CI/CD:** GitHub Actions
- **Scheduling:** Python-based scheduler (cron-like)

**Key Directories:**
- `crawling/` - Web scraping modules
- `db/` - Database connection and queries
- `scripts/` - Utility scripts

**Working Style:**
- 🎯 **Focus on code**: Prioritize writing/modifying code over creating documentation
- 📝 **Minimal documentation**: Only document when code changes require it
- 🚫 **No unnecessary reports**: Don't create separate analysis/review/report documents unless explicitly requested
- ✅ **Direct answers**: For questions and reviews, provide concise answers in responses, not as separate files

---

## 2. Branch Strategy (GitHub Flow)

### Core Branch

#### `main`
- **Purpose:** 항상 배포 가능한 상태 유지
- **Protection:** 보호 브랜치, PR 리뷰 필수
- **Releases:** 시맨틱 버저닝 태그 (v1.0.0, v1.1.0, v2.0.0 등)
- **Direct commits:** 허용하지 않음
- **Merges from:** 모든 작업 브랜치 (`feature/*`, `fix/*`, `refactor/*`, `docs/*`, `test/*`, `chore/*`)

### 작업 브랜치 (모두 `main`에서 분기 → `main`으로 병합)

- **`feature/*`**: 새 기능 → `main`으로 PR
- **`fix/*`**: 버그 수정 (긴급 포함) → `main`으로 PR
- **`refactor/*`**: 코드 리팩토링 → `main`으로 PR
- **`docs/*`**: 문서 업데이트 → `main`으로 PR
- **`test/*`**: 테스트 추가 → `main`으로 PR
- **`chore/*`**: 유지보수 작업 → `main`으로 PR

### GitHub Flow 규칙

1. `main` 브랜치는 항상 배포 가능한 상태여야 한다
2. 모든 작업은 `main`에서 브랜치를 생성해 진행한다
3. 브랜치는 짧게 유지하고 빠르게 병합한다
4. PR은 항상 `main`을 대상으로 한다
5. CI 통과 + 리뷰 승인 후 `main`에 병합한다
6. 병합 후 필요 시 즉시 배포한다

---

## 3. Branch Naming Conventions

### Format
```
<type>/<descriptive-name>
```

### Rules
- **Use lowercase only:** `feature/news-crawler` ✅ not `Feature/News-Crawler` ❌
- **Use hyphens (-) for spaces:** `fix/timeout-error` ✅ not `fix/timeout_error` ❌
- **Be descriptive but concise:** 2-4 words is ideal
- **No special characters:** Avoid `#`, `@`, `!`, `$`, etc.
- **Use present tense:** `feature/add-summarizer` ✅ not `feature/added-summarizer` ❌

### Valid Examples
```
feature/llm-integration
feature/sentiment-analysis
fix/crawler-timeout
fix/empty-results-handling
fix/database-connection
refactor/database-connection
refactor/simplify-crawler-logic
docs/docker-setup-guide
docs/update-readme
test/add-crawler-tests
test/database-integration
chore/update-dependencies
chore/improve-makefile
```

### Invalid Examples
```
Feature/NewFeature          # Wrong: uppercase, not descriptive
fix_bug                     # Wrong: underscore instead of hyphen, not descriptive
feature/add-new-feature-for-summarizing-news-articles  # Wrong: too long
fix/issue#123               # Wrong: contains special character #
```

---

## 4. Commit Message Conventions (Conventional Commits)

### Format
```
<type>(<scope>): <subject>
```

### Types
- **feat**, **fix**, **docs**, **style**, **refactor**, **test**, **chore**, **perf**, **ci**

### Rules
- Imperative mood: "add" not "added"
- No capital first letter
- No period at end
- Use scope when helpful: `feat(crawler):`, `fix(db):`

### Examples

```
feat(crawler): add BeautifulSoup crawler for Naver News
fix(db): fix connection pool exhaustion under load
docs: update Docker setup instructions
refactor(crawler): simplify news extraction logic
```

---

## 5. Pull Request Guidelines

### Workflow
1. `main`에서 브랜치 생성
2. 컨벤셔널 커밋 메시지로 커밋
3. Push 후 `main`을 대상으로 PR 생성
4. CI 통과 및 리뷰 승인 대기
5. 승인 후 `main`에 병합

### Title Format
Same as commit messages: `<type>(<scope>): <subject>`

### Description Template
```markdown
## Summary
Brief description

## Type of Change
- [ ] Feature / Fix / Refactor / Docs / Test / Chore

## Changes Made
- Change 1
- Change 2

## Testing
- [ ] Pre-commit hooks pass
- [ ] CI checks pass

## Related Issues
Closes #123
```

---

## 6. Code Quality Standards

### Pre-commit Hooks
Run `pre-commit run --all-files` before committing.

Required: black, isort, flake8, mypy, trailing-whitespace, end-of-file-fixer

### Code Style
- Line length: 88 characters
- Python 3.13 native type hints: `dict[str, int]`, `list[str]`
- Google-style docstrings
- Import order: standard library → third-party → local

---

## 7. Development Workflow

When creating PRs or branches, Copilot should:

1. `main` 브랜치를 대상으로 PR 생성
2. 브랜치 명명 규칙 사용: `<type>/<descriptive-name>`
3. 컨벤셔널 커밋 메시지 사용
4. pre-commit 훅 통과 확인
5. 관련 이슈 참조: `Closes #123`
6. PR은 하나의 기능/수정에 집중 (focused PR)

---

## 8. Common Scenarios

### 기능 개발
```bash
git checkout -b feature/llm-integration main
# ... make changes ...
git commit -m "feat(llm): add OpenAI API configuration"
git push origin feature/llm-integration
# Create PR to main
```

### 버그 수정
```bash
git checkout -b fix/crawler-timeout main
git commit -m "fix(crawler): increase request timeout to 30s"
# Create PR to main
```

### 긴급 수정 (Hotfix)
```bash
git checkout -b fix/db-connection main
git commit -m "fix(db): fix connection pool exhaustion"
# Create PR to main (GitHub Flow — 별도 hotfix 브랜치 불필요)
```

---

## 9. Environment Variables

Never hardcode sensitive data. Use environment variables:

```python
import os

db_host = os.getenv("POSTGRES_HOST", "localhost")
db_password = os.getenv("POSTGRES_PASSWORD", "")

if not db_password:
    raise ValueError("POSTGRES_PASSWORD required")
```

Required variables: `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `SEARCH_KEYWORD`, `CRAWL_SCHEDULE`

## 10. Testing & Documentation

### Testing
- Write tests for new features
- Test files: `tests/test_<module>.py`
- Use meaningful names: `test_crawler_handles_empty_results()`

### Documentation Guidelines

**When to Document:**
- ✅ **Code changes only**: Update documentation when modifying actual code
- ✅ **New features**: Update README.md for significant new features
- ✅ **Environment changes**: Document new environment variables in `.env.example`
- ❌ **Don't create reports**: Avoid creating separate report/analysis documents unless explicitly requested
- ❌ **No documentation for reviews**: Simple code reviews, analysis, or verification tasks don't need separate documentation files

**Code Documentation:**
- Google-style docstrings for all functions
- Inline comments only when logic is complex

Example:
```python
def fetch_news(keyword: str, limit: int = 10) -> list[dict[str, str]]:
    """Fetch news articles from Naver News.

    Args:
        keyword: Search keyword (e.g., "당근마켓")
        limit: Maximum articles to fetch

    Returns:
        List of dictionaries with article data

    Raises:
        ValueError: If keyword is empty
    """
    pass
```

## 11. Copilot Code Generation

When generating code:

1. Follow established patterns in the codebase
2. Use Python 3.13 native type hints
3. Add Google-style docstrings
4. Handle errors gracefully
5. Use environment variables from `os.getenv()`
6. Follow 88 character line length

### Context-Aware
- Database operations use `db/db_news.py`
- Web scraping uses BeautifulSoup4
- Configuration from environment variables
- Docker is primary deployment

---

## Quick Reference Card

### Branch Naming
```
feature/descriptive-name
fix/bug-description
refactor/component-name
docs/topic
test/test-name
chore/task-name
```

### Commit Messages
```
feat: add new feature
fix: fix bug
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: maintenance task
perf: improve performance
ci: update CI/CD
```

### PR Targets
- **모든 브랜치 (feature, fix, refactor, docs, test, chore)** → `main`

### Pre-commit
```bash
pre-commit run --all-files
```

### Docker Commands
```bash
make build          # Build all containers
make up             # Start all services
make down           # Stop all services
make logs           # View logs
make test           # Run crawler once
make clean          # Remove all containers and volumes
```

---

**Last Updated:** 2026-01-14

**Version:** 1.0.0

This document should be updated whenever significant changes to the project structure, workflow, or conventions are made.

## Recent Changes
- 001-cover-letter-automation: Added Python 3.13 + google-genai (LLM 티어 라우팅), streamlit (UI), psycopg2-binary (DB — 기존 사용 중). TXT 파일 입력은 내장 `str` 처리로 외부 파서 불필요
- 001-cover-letter-automation: google-genai SDK (Gemini Flash/Pro/Pro-Thinking 3단계 티어 LLM), Streamlit (프론트엔드 UI), `cover_letter/` 서비스 모듈, `frontend/` Streamlit 앱, `db/migrations/` DB 마이그레이션 스크립트, `GEMINI_API_KEY` 환경 변수. 입력 방식: TXT 파일 업로드 + 텍스트 직접 붙여넣기 (PDF·DOCX 파싱 MVP 범위 외)
- 001-cover-letter-automation: 기업 정보 수집 3-소스 확장 — DART API(`dart-fss`, `DART_API_KEY` optional), Naver News API + Firecrawl fallback, 공식 홈페이지 BeautifulSoup4 스크래핑. 수집기 모듈: `cover_letter/collectors/dart_collector.py`, `naver_collector.py`, `website_crawler.py`. `DART_API_KEY`·`FIRECRAWL_API_KEY` 환경 변수 추가

## Active Technologies
- Python 3.13 + google-genai (LLM 티어 라우팅), streamlit (UI), psycopg2-binary (DB — 기존 사용 중). TXT 파일 입력은 내장 `str` 처리로 외부 파서 불필요 (001-cover-letter-automation)
- PostgreSQL 15 (Docker 컨테이너, 기존 재사용) (001-cover-letter-automation)
- dart-fss (DART 사업보고서 수집, optional), requests+beautifulsoup4 (홈페이지 스크래핑, 기존 TrendOps 스택), Firecrawl API (Naver News fallback, optional) (001-cover-letter-automation)
