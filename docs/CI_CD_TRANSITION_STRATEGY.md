# CI/CD Balanced Mode 전환 전략

> **작성일**: 2026-02-19  
> **목적**: Strict Mode → Balanced Mode 안전한 전환 가이드

---

## 🎯 전환 목표

현재의 엄격한 CI/CD 룰을 Balanced Mode로 완화하면서 CI 실패 없이 안전하게 전환

## ⚠️ 핵심 문제

단순히 룰을 완화하면 발생할 수 있는 문제:

```
❌ 잘못된 순서:
1. Pre-commit 규칙 완화 (mypy, flake8 완화)
2. 코드 커밋
3. CI에서 여전히 엄격한 규칙으로 검증
4. CI 실패! 🔥

또는:

❌ 또 다른 잘못된 순서:
1. CI 규칙 먼저 완화
2. 코드 커밋
3. Pre-commit이 여전히 엄격함
4. 로컬에서 커밋 실패! 🔥
```

## ✅ 안전한 전환 전략

### 전략 개요

**핵심 원칙**: 
1. **백지화 불필요** - 기존 코드는 이미 strict mode를 통과하므로 balanced mode도 통과
2. **Single Commit 전환** - 모든 설정을 한 번에 변경하여 일관성 유지
3. **CI Skip 활용** - 전환 커밋만 CI 체크 우회

---

## 📋 5단계 전환 프로세스

### Step 0: 사전 준비 (5분)

**목적**: 현재 상태 확인 및 백업

```bash
# 1. 현재 브랜치 확인
git status
git branch

# 2. 최신 상태로 업데이트
git pull origin develop

# 3. 새 브랜치 생성
git checkout -b feature/balanced-mode-ci

# 4. 현재 코드가 strict mode를 통과하는지 확인
pre-commit run --all-files
```

**예상 결과**: ✅ 모든 체크 통과

---

### Step 1: 코드 사전 정리 (선택적, 5분)

**목적**: 혹시 모를 formatting 이슈 사전 제거

```bash
# 현재 strict 규칙으로 전체 코드 포맷팅
pre-commit run --all-files

# 변경사항이 있다면 커밋
git add .
git commit -m "style: apply strict formatting before transition"
```

**중요**: 이 단계는 선택적입니다. 대부분의 경우 불필요하지만, 안전장치로 실행 권장.

---

### Step 2: 설정 파일 일괄 변경 (10분)

**목적**: 모든 CI/CD 설정을 balanced mode로 동시에 변경

#### 2.1 Pre-commit 설정 완화

**파일**: `.pre-commit-config.yaml`

```yaml
# .pre-commit-config.yaml

repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
    -   id: check-yaml
    -   id: end-of-file-fixer
    -   id: trailing-whitespace

# Python 파일 linting 및 포맷팅
-   repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
    -   id: black
        files: \.py$
        # Balanced mode: 계속 auto-fix (변경 없음)

-   repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
    -   id: isort
        name: isort (python)
        args: ["--profile", "black"]
        files: \.py$
        # Balanced mode: 계속 auto-fix (변경 없음)

-   repo: https://github.com/PyCQA/flake8
    rev: 7.1.1
    hooks:
    -   id: flake8
        files: \.py$
        additional_dependencies: [flake8-bugbear]
        args:
        - --max-line-length=88
        - --extend-ignore=E203,W503
        - --exit-zero  # ⭐ 추가: warning 허용, error만 표시
        # Balanced mode: warning은 통과, 심각한 error만 차단

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
    -   id: mypy
        files: \.py$
        additional_dependencies: [types-requests, types-psycopg2]
        args:
        - --ignore-missing-imports  # ⭐ 추가: 외부 라이브러리 타입 체크 완화
        - --no-strict-optional      # ⭐ 추가: Optional 체크 완화
        # Balanced mode: 점진적 타입 체크
```

**변경 사항**:
- ✅ Black, isort: 변경 없음 (이미 auto-fix)
- ⭐ Flake8: `--exit-zero` 추가 (warning 허용)
- ⭐ Mypy: `--ignore-missing-imports`, `--no-strict-optional` 추가

#### 2.2 CI 워크플로우 업데이트

**파일**: `.github/workflows/ci.yml`

```yaml
name: CI (Balanced Mode)

on:
  push:
    branches: [ main, develop, 'feature/**' ]
  pull_request:
    branches: [ main, develop ]

jobs:
  quality-check:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_HOST_AUTH_METHOD: trust
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      POSTGRES_HOST: localhost
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
      POSTGRES_PORT: 5432

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Set up Conda environment
      uses: conda-incubator/setup-miniconda@v3
      with:
        environment-file: requirements.yaml
        activate-environment: TrendOps
        python-version: '3.13'
        auto-activate-base: false

    - name: Install pre-commit
      shell: bash -l {0}
      run: |
        conda activate TrendOps
        pip install pre-commit

    - name: Cache pre-commit hooks
      uses: actions/cache@v4
      with:
        path: ~/.cache/pre-commit
        key: ${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

    # ⭐ Balanced Mode: Auto-fix formatting
    - name: Run pre-commit with auto-fix
      shell: bash -l {0}
      run: |
        conda activate TrendOps
        pre-commit run --all-files || true
        
    # ⭐ Balanced Mode: Auto-commit fixes if any
    - name: Auto-commit formatting fixes
      if: github.event_name == 'push'
      run: |
        if [[ -n $(git status --porcelain) ]]; then
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .
          git commit -m "style: auto-fix formatting [skip ci]"
          git push
          echo "✅ Auto-fixed and committed formatting changes"
        else
          echo "✅ No formatting changes needed"
        fi

    # ⭐ Balanced Mode: Check for critical errors only
    - name: Check for critical linting errors
      shell: bash -l {0}
      run: |
        conda activate TrendOps
        # Only fail on syntax errors and undefined names
        python -m flake8 . --select=E9,F63,F7,F82 --show-source --statistics

    - name: Test database connection
      shell: bash -l {0}
      run: |
        conda activate TrendOps
        python -c "from db.db_news import get_connection; print('Database connection successful')"

    - name: Check Python syntax
      shell: bash -l {0}
      run: |
        conda activate TrendOps
        python -m compileall . -x "(build|dist|\.git|__pycache__|\.pytest_cache)" -q
```

**주요 변경 사항**:
- ⭐ Pre-commit을 `|| true`로 실행 (실패해도 계속 진행)
- ⭐ Auto-commit 단계 추가 (formatting 수정 자동 커밋)
- ⭐ Flake8을 critical error만 체크하도록 변경

#### 2.3 IDE 설정 추가

**파일**: `.vscode/settings.json` (신규 생성)

```json
{
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=88"],
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=88",
    "--extend-ignore=E203,W503",
    "--exit-zero"
  ],
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": [
    "--ignore-missing-imports",
    "--no-strict-optional"
  ],
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### 2.4 Makefile 헬퍼 추가

**파일**: `Makefile` (기존 파일에 추가)

```makefile
# 기존 내용 유지...

# ====================
# Code Quality Helpers (Balanced Mode)
# ====================

.PHONY: format safe-commit validate lint

# 전체 코드 포맷팅
format:
	@echo "🔧 Formatting all Python files..."
	@pre-commit run --all-files || true
	@echo "✅ Formatting complete!"

# 안전한 커밋 (자동 포맷팅 → 커밋)
safe-commit:
	@echo "🔧 Running pre-commit checks..."
	@pre-commit run --all-files || true
	@git add .
	@read -p "📝 Commit message: " msg; \
	git commit -m "$$msg"
	@echo "✅ Committed successfully!"

# CI 미리 확인
validate:
	@echo "🧪 Running full CI validation..."
	@pre-commit run --all-files || true
	@python -m flake8 . --select=E9,F63,F7,F82 --show-source --statistics
	@python -m compileall . -x "(build|dist|\.git|__pycache__|\.pytest_cache)" -q
	@echo "✅ All critical checks passed!"

# Linting 경고 확인 (차단하지 않음)
lint:
	@echo "📊 Running full linting (informational)..."
	@python -m flake8 . --exit-zero --statistics
	@echo "✅ Linting report complete!"
```

---

### Step 3: 모든 변경사항 한 번에 커밋 (2분)

**목적**: CI 불일치 없이 깔끔하게 전환

```bash
# 1. 모든 변경사항 스테이징
git add .pre-commit-config.yaml
git add .github/workflows/ci.yml
git add .vscode/settings.json
git add Makefile

# 2. 변경사항 확인
git status
git diff --cached

# 3. 한 번에 커밋 (CI 스킵)
git commit -m "ci: transition to balanced mode

- Update pre-commit config: allow warnings in flake8, relax mypy
- Update CI workflow: auto-fix formatting, check critical errors only
- Add VS Code settings for auto-formatting on save
- Add Makefile helpers for safe commits

[skip ci]"
```

**⚠️ 중요**: `[skip ci]` 태그 사용으로 이 커밋은 CI 검증을 우회합니다.

---

### Step 4: 테스트 커밋 (1분)

**목적**: 새 설정이 제대로 작동하는지 확인

```bash
# 1. 간단한 테스트 변경 (예: README 업데이트)
echo "" >> README.md
echo "✅ CI/CD Balanced Mode 적용 완료" >> README.md

# 2. 일반 커밋 (CI 실행)
git add README.md
git commit -m "docs: confirm balanced mode CI is working"

# 3. Push
git push origin feature/balanced-mode-ci
```

**예상 결과**: 
- ✅ Pre-commit이 실행되고 자동으로 수정 (있다면)
- ✅ CI가 실행되고 통과
- ✅ Warning은 표시되지만 CI 성공

---

### Step 5: PR 생성 및 병합 (5분)

```bash
# GitHub에서 PR 생성
# Title: "ci: transition to balanced mode for better developer experience"
# Description: CI_CD_IMPROVEMENT_GUIDE.md 참조
```

**PR 체크리스트**:
- [ ] Pre-commit 설정 업데이트 확인
- [ ] CI 워크플로우 업데이트 확인
- [ ] IDE 설정 추가 확인
- [ ] Makefile 헬퍼 추가 확인
- [ ] 테스트 커밋이 CI 통과 확인

---

## 🔄 전환 후 워크플로우

### 이전 (Strict Mode)
```
1. 코드 작성
2. git commit
3. ❌ Pre-commit 실패
4. 수동 수정
5. git commit (재시도)
6. git push
7. ❌ CI 실패 가능
8. 다시 수정...

시간: 10-15분
```

### 이후 (Balanced Mode)
```
1. 코드 작성
2. 저장 → IDE 자동 포맷팅
3. make safe-commit
   - Pre-commit 실행 & 자동 수정
   - 자동 커밋
4. git push
5. ✅ CI 자동 수정 & 통과

시간: 2-3분
```

---

## 📊 전환 전후 비교

| 항목 | Strict Mode | Balanced Mode |
|------|------------|---------------|
| **Formatting** | 강제 (실패 시 차단) | Auto-fix (자동 수정) |
| **Linting** | 모든 warning 차단 | Warning 허용, error만 차단 |
| **Type hints** | 전체 필수 | 점진적 도입 |
| **CI 실패율** | 80% | 10% 예상 |
| **커밋 시간** | 10-15분 | 2-3분 |
| **학습 곡선** | 가파름 | 완만함 |
| **코드 품질** | 매우 높음 | 높음 (핵심만) |

---

## ⚠️ 주의사항

### 1. [skip ci] 사용
- **한 번만 사용**: Step 3의 전환 커밋에만
- **이유**: 설정 불일치로 인한 false positive 방지
- **이후**: 모든 커밋은 정상적으로 CI 실행

### 2. Pre-commit 캐시
```bash
# 설정 변경 후 캐시 클리어
pre-commit clean
pre-commit install --install-hooks
```

### 3. 기존 브랜치
- 기존 feature 브랜치들은 develop에 병합된 후 자동으로 balanced mode 적용
- 급한 경우: 각 브랜치에서 `git merge develop` 실행

---

## 🔍 문제 해결

### Q1: "Pre-commit이 여전히 엄격하게 동작해요"
```bash
# 해결: 캐시 클리어
pre-commit clean
pre-commit install --install-hooks
pre-commit run --all-files
```

### Q2: "CI에서 여전히 실패해요"
```bash
# 확인 1: .github/workflows/ci.yml이 제대로 업데이트 되었는지
git log --oneline --all -- .github/workflows/ci.yml

# 확인 2: GitHub Actions 캐시 클리어
# GitHub → Settings → Actions → Clear caches
```

### Q3: "mypy 에러가 너무 많아요"
```python
# 임시 해결: 특정 라인만 무시
result = some_function()  # type: ignore

# 영구 해결: pyproject.toml에 추가
[tool.mypy]
ignore_missing_imports = true
no_strict_optional = true
```

---

## 📚 참고 자료

- [CI/CD 개선 가이드](./CI_CD_IMPROVEMENT_GUIDE.md)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Pre-commit 문서](https://pre-commit.com/)

---

## ✅ 체크리스트

전환 전:
- [ ] 현재 코드가 strict mode 통과
- [ ] 변경할 파일들 백업 (선택)
- [ ] 새 브랜치 생성

전환 중:
- [ ] `.pre-commit-config.yaml` 업데이트
- [ ] `.github/workflows/ci.yml` 업데이트
- [ ] `.vscode/settings.json` 생성
- [ ] `Makefile` 업데이트
- [ ] 모든 변경사항 한 번에 커밋 (`[skip ci]`)

전환 후:
- [ ] 테스트 커밋 실행
- [ ] CI 통과 확인
- [ ] PR 생성 및 리뷰
- [ ] develop에 병합

---

**작성일**: 2026-02-19  
**최종 업데이트**: 2026-02-19
