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

**Repository Structure:**
```
TrendOps/
├── .github/
│   ├── workflows/              # CI/CD workflows (ci.yml, ci-serving.yml)
│   ├── copilot-instructions.md # This file
│   └── pull_request_template.md (future)
├── crawling/                   # Web scraping modules for news collection
├── db/                         # Database connection and management modules
├── scripts/                    # Utility scripts
├── .flake8                     # Flake8 linting configuration
├── .pre-commit-config.yaml     # Pre-commit hooks configuration
├── pyproject.toml              # Black, isort, mypy configuration
├── requirements.yaml           # Conda environment dependencies
├── docker-compose.yml          # Base Docker Compose configuration
├── docker-compose.dev.yml      # Development environment overrides
├── docker-compose.prod.yml     # Production environment overrides
├── Dockerfile.crawler          # Crawler service container
├── Dockerfile.db-init          # Database initialization container
├── Dockerfile.scheduler        # Scheduler service container
├── Makefile                    # Convenient commands for Docker operations
├── .env.example                # Environment variables template
├── README.md                   # Project documentation
└── SECURITY.md                 # Security policies and guidelines
```

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

#### `feature/*`
- **Purpose:** New features and enhancements
- **Branch from:** `develop`
- **Merge to:** `develop`
- **Examples:** `feature/llm-integration`, `feature/email-notifications`
- **Delete after merge:** Yes

#### `fix/*`
- **Purpose:** Bug fixes for issues in `develop`
- **Branch from:** `develop`
- **Merge to:** `develop`
- **Examples:** `fix/crawler-timeout`, `fix/database-connection-pool`
- **Delete after merge:** Yes

#### `hotfix/*`
- **Purpose:** Critical production fixes that cannot wait for the next release
- **Branch from:** `main`
- **Merge to:** Both `main` AND `develop`
- **Examples:** `hotfix/database-connection-error`, `hotfix/memory-leak`
- **Delete after merge:** Yes
- **Special note:** Create two PRs - one to `main` and one to `develop`

#### `refactor/*`
- **Purpose:** Code refactoring without changing functionality
- **Branch from:** `develop`
- **Merge to:** `develop`
- **Examples:** `refactor/database-module`, `refactor/crawler-structure`
- **Delete after merge:** Yes

#### `docs/*`
- **Purpose:** Documentation updates (README, comments, docstrings)
- **Branch from:** `develop`
- **Merge to:** `develop`
- **Examples:** `docs/api-documentation`, `docs/setup-guide`
- **Delete after merge:** Yes

#### `test/*`
- **Purpose:** Adding or improving tests
- **Branch from:** `develop`
- **Merge to:** `develop`
- **Examples:** `test/crawler-unit-tests`, `test/database-integration-tests`
- **Delete after merge:** Yes

#### `chore/*`
- **Purpose:** Maintenance tasks (dependency updates, config changes)
- **Branch from:** `develop`
- **Merge to:** `develop`
- **Examples:** `chore/update-dependencies`, `chore/improve-ci-pipeline`
- **Delete after merge:** Yes

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

<body>

<footer>
```

### Types
- **feat:** New feature for the user
- **fix:** Bug fix for the user
- **docs:** Documentation changes only
- **style:** Code formatting, missing semicolons, etc. (no logic change)
- **refactor:** Code refactoring (no functional change)
- **test:** Adding or modifying tests
- **chore:** Maintenance tasks, dependency updates, build config
- **perf:** Performance improvements
- **ci:** CI/CD pipeline changes

### Scope (Optional but Recommended)
The part of the codebase affected: `crawler`, `db`, `scheduler`, `docker`, `ci`, `deps`

### Subject
- Use imperative mood: "Add feature" not "Added feature" or "Adds feature"
- Don't capitalize first letter: `feat: add feature` ✅ not `feat: Add feature` ❌
- No period at the end
- Limit to 50-72 characters

### Body (Optional)
- Explain what and why, not how
- Wrap at 72 characters
- Separate from subject with blank line

### Footer (Optional)
- Reference issues: `Closes #123`, `Fixes #456`, `Relates to #789`
- Note breaking changes: `BREAKING CHANGE: description`

### Examples

#### Simple commit
```
feat: add LLM-based news summarization
```

#### Commit with scope
```
fix(crawler): handle empty crawler results gracefully
```

#### Commit with body
```
feat(db): add connection pooling for PostgreSQL

Implements connection pooling to improve database performance
and handle concurrent requests more efficiently. Uses psycopg2
connection pool with min=2, max=10 connections.
```

#### Commit with footer
```
fix(scheduler): resolve memory leak in periodic tasks

The scheduler was accumulating task objects without cleanup,
causing memory usage to grow over time.

Closes #45
```

#### Multiple types of work
```
feat: add sentiment analysis module
test: add unit tests for sentiment analyzer
docs: update README with sentiment analysis usage
```
(Note: Prefer separate commits for different types)

### TrendOps-Specific Examples
```
feat(crawler): add BeautifulSoup crawler for Naver News
fix(db): fix connection pool exhaustion under load
docs: update Docker setup instructions in README
refactor(crawler): simplify news extraction logic
test(db): add integration tests for database connection
chore(deps): update Python dependencies in requirements.yaml
perf(crawler): reduce memory usage in batch processing
ci: add PostgreSQL service to GitHub Actions workflow
style(crawler): format code with black and isort
```

---

## 5. Pull Request Guidelines

### PR Workflow

1. **Create branch from `develop`**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature
   ```

2. **Develop and commit** using conventional commit messages

3. **Push to remote**
   ```bash
   git push origin feature/new-feature
   ```

4. **Create PR to `develop`** (NOT `main` directly, unless hotfix)

5. **Wait for CI checks to pass**
   - Pre-commit hooks (black, isort, flake8, mypy)
   - Database connection test
   - Python syntax check

6. **Request code review** (if team members available)

7. **Merge after approval** and CI success

8. **Branch auto-deleted** after merge (enable in GitHub settings)

### PR Title Format

Follow the same format as commit messages:

```
<type>(<scope>): <subject>
```

**Examples:**
```
feat: add sentiment analysis module
fix: resolve crawler timeout issue
docs: update Docker setup guide
refactor: simplify database connection logic
test: add unit tests for news crawler
chore: update Python dependencies to latest versions
```

### PR Description Template

```markdown
## Summary
Brief description of what this PR does.

## Type of Change
- [ ] Feature (new functionality)
- [ ] Fix (bug fix)
- [ ] Refactor (code improvement, no functional change)
- [ ] Documentation (README, comments, docstrings)
- [ ] Test (adding or improving tests)
- [ ] Chore (dependency updates, config changes)

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] CI checks pass
- [ ] Manual testing completed
- [ ] Database connection tested (if applicable)

## Related Issues
Closes #123
Fixes #456
Relates to #789

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Environment variables documented (if added)
```

### PR Size Guidelines

- **Ideal:** 100-300 lines of changes
- **Acceptable:** Up to 500 lines
- **Large:** 500+ lines (consider splitting)
- **Keep PRs focused:** One feature or fix per PR

---

## 6. Code Quality Standards

### Pre-commit Checks

**Before every commit, run:**
```bash
pre-commit run --all-files
```

**Required hooks that must pass:**
- `black` - Code formatter (88 char line length)
- `isort` - Import statement organizer
- `flake8` - Linting for style and errors
- `mypy` - Static type checker
- `trailing-whitespace` - Remove trailing whitespace
- `end-of-file-fixer` - Ensure files end with newline
- `check-yaml` - Validate YAML syntax

**Installation (if not already installed):**
```bash
conda activate TrendOps
pip install pre-commit
pre-commit install
```

### CI Requirements

All GitHub Actions workflows must pass before merge:

1. **Pre-commit hooks** - All hooks must pass
2. **Database connection test** - PostgreSQL connection verified
3. **Python syntax check** - All Python files compile successfully

### Code Style

#### Python Style (PEP 8)
- **Line length:** 88 characters (black default)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes preferred by black
- **Docstrings:** Google-style docstrings

#### Type Hints (Python 3.13)
- **Use native types:** `dict[str, int]` ✅ not `Dict[str, int]` ❌
- **Use native types:** `list[str]` ✅ not `List[str]` ❌
- **Use type hints for all functions:**
```python
def fetch_news(keyword: str, limit: int = 10) -> list[dict[str, str]]:
    """Fetch news articles for the given keyword."""
    pass
```

#### Import Order (enforced by isort)
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import os
from datetime import datetime

# Third-party
import psycopg2
from bs4 import BeautifulSoup

# Local
from db.db_news import get_connection
from crawling.news_crawling import fetch_articles
```

#### File Naming
- **Python files:** `lowercase_with_underscores.py`
- **Directories:** `lowercase` (no underscores)
- **Classes:** `PascalCase`
- **Functions/variables:** `snake_case`
- **Constants:** `UPPER_CASE_WITH_UNDERSCORES`

---

## 7. Development Workflow Instructions for Copilot

When creating PRs or branches, Copilot should:

1. **Always target `develop` branch** unless it's a hotfix
   - Hotfixes target `main` first, then `develop`

2. **Use appropriate branch naming** based on the task type
   - Feature: `feature/descriptive-name`
   - Bug fix: `fix/bug-description`
   - Hotfix: `hotfix/critical-issue`
   - Refactor: `refactor/component-name`
   - Docs: `docs/topic`
   - Test: `test/test-description`
   - Chore: `chore/task-description`

3. **Write conventional commit messages**
   - Format: `<type>(<scope>): <subject>`
   - Use imperative mood
   - Be descriptive but concise

4. **Create descriptive PR titles and descriptions**
   - Title follows commit message format
   - Description includes summary, type, testing checklist, related issues

5. **Ensure all pre-commit hooks pass**
   - Run `pre-commit run --all-files` before committing
   - Fix any issues reported by black, isort, flake8, mypy

6. **Reference related issues**
   - Use `Closes #123` for issues this PR resolves
   - Use `Fixes #456` for bugs this PR fixes
   - Use `Relates to #789` for related issues

7. **Add appropriate labels** to PRs
   - `enhancement` for features
   - `bug` for fixes
   - `documentation` for docs
   - `refactoring` for refactors
   - `testing` for tests
   - `maintenance` for chores

8. **Keep PRs focused**
   - One feature or fix per PR
   - Avoid mixing multiple unrelated changes

9. **Keep PR size manageable**
   - Ideal: 100-300 lines of changes
   - Large PRs should be split into smaller ones

---

## 8. Common Scenarios

### Scenario 1: Adding a New Feature

**Objective:** Add LLM integration for news summarization

```bash
# 1. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/llm-integration

# 2. Implement changes with multiple commits
git add crawling/llm_summarizer.py
git commit -m "feat(llm): add OpenAI API configuration"

git add crawling/summarization_service.py
git commit -m "feat(llm): implement news summarization service"

git add tests/test_summarizer.py
git commit -m "test(llm): add unit tests for summarizer"

git add README.md
git commit -m "docs: add LLM summarization usage to README"

# 3. Push and create PR
git push origin feature/llm-integration
# Create PR: feature/llm-integration → develop
```

**PR Title:** `feat: add LLM-based news summarization`

---

### Scenario 2: Fixing a Bug

**Objective:** Fix crawler timeout issues

```bash
# 1. Create fix branch
git checkout develop
git pull origin develop
git checkout -b fix/crawler-timeout

# 2. Fix the issue
git add crawling/news_crawling.py
git commit -m "fix(crawler): increase request timeout to 30s" -m "The crawler was timing out on slow news sites. Increased timeout from 10s to 30s and added retry logic with exponential backoff." -m "Closes #42"

git add tests/test_crawler.py
git commit -m "test(crawler): add timeout test case"

# 3. Push and create PR
git push origin fix/crawler-timeout
# Create PR: fix/crawler-timeout → develop
```

**PR Title:** `fix: resolve crawler timeout issue`

---

### Scenario 3: Hotfix for Production

**Objective:** Fix critical database connection error in production

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/database-connection-error

# 2. Fix the critical issue
git add db/db_news.py
git commit -m "hotfix(db): fix connection pool exhaustion" -m "Connection pool was not properly releasing connections, causing exhaustion under load. Added explicit connection cleanup in finally blocks." -m "Closes #78"

# 3. Push and create TWO PRs
git push origin hotfix/database-connection-error

# Create PR 1: hotfix/database-connection-error → main (priority)
# Create PR 2: hotfix/database-connection-error → develop (to keep in sync)
```

**PR Titles:**
- To `main`: `hotfix: fix database connection pool exhaustion`
- To `develop`: `hotfix: fix database connection pool exhaustion`

---

### Scenario 4: Refactoring Code

**Objective:** Simplify database connection logic

```bash
# 1. Create refactor branch
git checkout develop
git pull origin develop
git checkout -b refactor/database-connection

# 2. Refactor code
git add db/db_news.py db/connection_pool.py
git commit -m "refactor(db): extract connection pool to separate module" -m "Moved connection pool logic to dedicated module for better maintainability and reusability. No functional changes."

git add tests/test_db_connection.py
git commit -m "test(db): update tests for refactored connection module"

# 3. Push and create PR
git push origin refactor/database-connection
# Create PR: refactor/database-connection → develop
```

**PR Title:** `refactor: simplify database connection logic`

---

### Scenario 5: Documentation Update

**Objective:** Update Docker setup instructions

```bash
# 1. Create docs branch
git checkout develop
git pull origin develop
git checkout -b docs/docker-setup-guide

# 2. Update documentation
git add README.md
git commit -m "docs: update Docker setup instructions" -m "Added detailed steps for Docker installation, environment variable configuration, and common troubleshooting tips."

git add SECURITY.md
git commit -m "docs: add Docker security best practices"

# 3. Push and create PR
git push origin docs/docker-setup-guide
# Create PR: docs/docker-setup-guide → develop
```

**PR Title:** `docs: update Docker setup guide`

---

## 9. File Structure Conventions

```
TrendOps/
├── .github/
│   ├── workflows/              # CI/CD GitHub Actions workflows
│   │   ├── ci.yml             # Main CI pipeline
│   │   └── ci-serving.yml     # Serving-specific CI
│   ├── copilot-instructions.md # GitHub Copilot workflow guide
│   └── pull_request_template.md # PR template (future)
│
├── crawling/                   # Web scraping and news collection
│   ├── news_crawling.py       # Main crawler logic
│   └── (other crawler modules)
│
├── db/                         # Database modules
│   ├── db_news.py             # Database connection and queries
│   └── (other database modules)
│
├── scripts/                    # Utility scripts
│   └── (helper scripts)
│
├── tests/                      # Test files (if added)
│   ├── test_crawler.py
│   └── test_db.py
│
├── .flake8                     # Flake8 linting configuration
├── .pre-commit-config.yaml     # Pre-commit hooks setup
├── pyproject.toml              # Black, isort, mypy configuration
├── requirements.yaml           # Conda environment dependencies
│
├── docker-compose.yml          # Base Docker Compose configuration
├── docker-compose.dev.yml      # Development overrides
├── docker-compose.prod.yml     # Production overrides
│
├── Dockerfile.crawler          # Crawler service Dockerfile
├── Dockerfile.db-init          # Database init Dockerfile
├── Dockerfile.scheduler        # Scheduler service Dockerfile
│
├── Makefile                    # Convenience commands
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore patterns
├── README.md                   # Project documentation
└── SECURITY.md                 # Security policies and guidelines
```

### Module Organization

- **`crawling/`**: All web scraping logic, news fetching, and data extraction
- **`db/`**: Database connection management, queries, and data persistence
- **`scripts/`**: Standalone utility scripts for maintenance and operations
- **`tests/`**: Unit tests, integration tests (if applicable)

---

## 10. Environment-Specific Instructions

### Environment Variables

**Never hardcode sensitive data.** Always use environment variables.

#### Required Environment Variables

```bash
# Database Configuration
POSTGRES_HOST=postgres          # Database host (use 'localhost' for local dev)
POSTGRES_DB=postgres            # Database name
POSTGRES_USER=postgres          # Database user
POSTGRES_PASSWORD=pg1234        # Database password (MUST change in production)
POSTGRES_PORT=5432              # Database port

# Crawler Configuration
SEARCH_KEYWORD=당근마켓          # Keyword to search for
CRAWL_SCHEDULE=09:00            # Daily crawl time

# Scheduler Configuration
RUN_ON_START=true               # Run crawler immediately on startup
```

#### Usage in Code

```python
import os

# Access environment variables with default fallback
db_host = os.getenv("POSTGRES_HOST", "localhost")
db_name = os.getenv("POSTGRES_DB", "postgres")
db_user = os.getenv("POSTGRES_USER", "postgres")
db_password = os.getenv("POSTGRES_PASSWORD", "")

# Validate required environment variables
if not db_password:
    raise ValueError("POSTGRES_PASSWORD environment variable is required")
```

#### Environment Setup

1. **Copy template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your local values

3. **Never commit `.env` file** - it's in `.gitignore`

4. **Document new variables** in `.env.example` and README.md

---

## 11. Testing Requirements

### Test Files

- **Location:** `tests/` directory (if created)
- **Naming:** `test_<module_name>.py`
- **Function naming:** `test_<functionality>_<expected_behavior>`

### Test Guidelines

1. **Write tests for new features**
   - Unit tests for functions
   - Integration tests for database operations

2. **Maintain or improve code coverage**
   - Aim for >80% coverage for new code

3. **Test database connections with CI PostgreSQL service**
   - CI provides a test PostgreSQL instance
   - Use test database credentials from environment variables

4. **Use meaningful test names**
   ```python
   def test_crawler_handles_empty_results():
       """Test that crawler gracefully handles empty search results."""
       pass

   def test_database_connection_retries_on_failure():
       """Test that database connection retries 3 times on failure."""
       pass
   ```

### Running Tests

```bash
# Run all tests (if test framework is set up)
pytest

# Run specific test file
pytest tests/test_crawler.py

# Run with coverage
pytest --cov=crawling --cov=db
```

### Test Example

```python
import pytest
from crawling.news_crawling import fetch_news
from db.db_news import get_connection


def test_fetch_news_returns_list():
    """Test that fetch_news returns a list of news articles."""
    result = fetch_news("당근마켓", limit=5)
    assert isinstance(result, list)
    assert len(result) <= 5


def test_database_connection_successful():
    """Test that database connection can be established."""
    conn = get_connection()
    assert conn is not None
    conn.close()


def test_crawler_handles_timeout_gracefully():
    """Test that crawler handles timeout without crashing."""
    # Mock slow response
    result = fetch_news("test", timeout=0.001)
    assert result == []  # Should return empty list on timeout
```

---

## 12. Documentation Requirements

### When to Update Documentation

1. **New features** - Add usage instructions to README.md
2. **API changes** - Update function/class docstrings
3. **Environment variables** - Document in `.env.example` and README.md
4. **Security-related changes** - Update SECURITY.md
5. **Docker changes** - Update Docker setup instructions
6. **Breaking changes** - Clearly document in commit message and PR

### Docstring Format (Google Style)

```python
def fetch_news(keyword: str, limit: int = 10, timeout: int = 30) -> list[dict[str, str]]:
    """Fetch news articles from Naver News for the given keyword.

    Args:
        keyword: Search keyword for news articles (e.g., "당근마켓").
        limit: Maximum number of articles to fetch. Defaults to 10.
        timeout: Request timeout in seconds. Defaults to 30.

    Returns:
        A list of dictionaries containing news article data. Each dictionary
        has keys: 'title', 'url', 'content', 'published_date'.

    Raises:
        ValueError: If keyword is empty or None.
        requests.Timeout: If request exceeds timeout duration.
        requests.RequestException: If request fails for other reasons.

    Example:
        >>> articles = fetch_news("당근마켓", limit=5)
        >>> print(len(articles))
        5
        >>> print(articles[0]['title'])
        '당근마켓, 새로운 서비스 출시'
    """
    pass
```

### README Updates

When adding new functionality, update README.md with:
- Feature description
- Usage examples
- Configuration options
- Troubleshooting tips

---

## 13. Copilot-Specific Instructions

### Code Generation Guidelines

When Copilot generates code for this project, it should:

1. **Follow established patterns in the codebase**
   - Review existing modules before generating new code
   - Match the style and structure of similar components

2. **Use modern Python 3.13 syntax**
   - Native type hints: `dict[str, int]`, `list[str]`
   - Use `match`/`case` for complex conditionals (Python 3.10+)
   - Use modern type annotations and features available in Python 3.13

3. **Add comprehensive docstrings**
   - Google-style docstrings for all public functions and classes
   - Include Args, Returns, Raises, and Examples sections

4. **Include type hints**
   - All function parameters and return values
   - Variable annotations where type is not obvious

5. **Handle errors gracefully with try-except**
   ```python
   try:
       connection = get_connection()
       # ... perform operations
   except psycopg2.OperationalError as e:
       logger.error(f"Database connection failed: {e}")
       raise
   finally:
       if connection:
           connection.close()
   ```

6. **Log important events**
   ```python
   import logging

   logger = logging.getLogger(__name__)

   logger.info("Starting news crawling for keyword: %s", keyword)
   logger.warning("Received empty response from %s", url)
   logger.error("Failed to parse article: %s", error)
   ```

7. **Use environment variables from `os.getenv()`**
   ```python
   db_host = os.getenv("POSTGRES_HOST", "localhost")
   ```

8. **Follow the repository's code style automatically**
   - 88 character line length
   - Double quotes for strings
   - Proper import ordering (standard, third-party, local)

### Context-Aware Suggestions

Copilot should understand:
- **Database operations** use `db/db_news.py` connection utilities
- **Web scraping** uses BeautifulSoup4 and requests
- **Configuration** comes from environment variables
- **Logging** should be used for debugging and monitoring
- **Error handling** should be comprehensive but not swallow errors
- **Docker** is the primary deployment method
- **CI/CD** validates all code with pre-commit hooks

### Prohibited Actions

Copilot should **never**:
- Hardcode sensitive data (passwords, API keys, secrets)
- Commit directly to `main` branch
- Skip pre-commit hooks
- Ignore type hints
- Use deprecated Python features
- Use Python 2.x syntax
- Import `Dict`, `List` from `typing` (use native types instead)

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
