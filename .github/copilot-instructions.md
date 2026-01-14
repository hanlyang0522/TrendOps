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

---

## 2. Branch Strategy (Git Flow - Simplified)

### Core Branches

#### `main`
- **Purpose:** Production-ready code only
- **Protection:** Protected branch, requires PR reviews
- **Releases:** Tagged with semantic versioning (v1.0.0, v1.1.0, v2.0.0, etc.)
- **Direct commits:** Not allowed
- **Merges from:** `hotfix/*` branches only

#### `develop`
- **Purpose:** Integration branch for the next release
- **Default branch:** All feature PRs target this branch
- **Protection:** Protected, requires CI checks to pass
- **Direct commits:** Discouraged, use PRs
- **Merges from:** `feature/*`, `fix/*`, `refactor/*`, `docs/*`, `test/*`, `chore/*`, `hotfix/*`

### Temporary Branches

- **`feature/*`**: New features → merge to `develop`
- **`fix/*`**: Bug fixes → merge to `develop`
- **`hotfix/*`**: Critical production fixes → merge to `main` AND `develop`
- **`refactor/*`**: Code refactoring → merge to `develop`
- **`docs/*`**: Documentation updates → merge to `develop`
- **`test/*`**: Test additions → merge to `develop`
- **`chore/*`**: Maintenance tasks → merge to `develop`

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
hotfix/database-connection
hotfix/memory-leak-scheduler
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
hotfix/issue#123            # Wrong: contains special character #
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
1. Create branch from `develop` (or `main` for hotfix)
2. Commit with conventional messages
3. Push and create PR to `develop`
4. Wait for CI checks to pass
5. Merge after approval

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

1. Target `develop` branch (unless hotfix)
2. Use appropriate branch naming: `<type>/<descriptive-name>`
3. Write conventional commit messages
4. Ensure pre-commit hooks pass
5. Reference related issues: `Closes #123`
6. Keep PRs focused (one feature/fix per PR)

---

## 8. Common Scenarios

### Feature Development
```bash
git checkout -b feature/llm-integration develop
# ... make changes ...
git commit -m "feat(llm): add OpenAI API configuration"
git push origin feature/llm-integration
# Create PR to develop
```

### Bug Fix
```bash
git checkout -b fix/crawler-timeout develop
git commit -m "fix(crawler): increase request timeout to 30s"
# Create PR to develop
```

### Hotfix
```bash
git checkout -b hotfix/db-connection main
git commit -m "hotfix(db): fix connection pool exhaustion"
# Create TWO PRs: one to main, one to develop
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

### Documentation
- Google-style docstrings for all functions
- Update README.md for new features
- Document environment variables in `.env.example`

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
hotfix/critical-issue
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
- **Features, fixes, refactors, docs, tests, chores** → `develop`
- **Hotfixes** → `main` (then merge to `develop`)

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
