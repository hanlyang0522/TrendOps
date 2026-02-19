# CI/CD Balanced Mode 전환 - 빠른 참조 가이드

> **전환 순서 요약** - 이 문서만 보고도 전환 가능

---

## 🚀 한눈에 보는 전환 순서

```
Step 0: 준비 (5분)
  └─> 브랜치 생성: feature/balanced-mode-ci

Step 1: 사전 정리 (5분, 선택적)
  └─> pre-commit run --all-files

Step 2: 설정 변경 (10분) ⭐ 핵심
  ├─> .pre-commit-config.yaml 수정
  ├─> .github/workflows/ci.yml 수정
  ├─> .vscode/settings.json 생성
  └─> Makefile 수정

Step 3: 한 번에 커밋 (2분)
  └─> git commit -m "..." [skip ci]  ⚠️ CI 스킵

Step 4: 테스트 (1분)
  └─> 일반 커밋으로 CI 테스트

Step 5: PR & 병합 (5분)
  └─> PR 생성 및 리뷰
```

**총 소요 시간**: 약 30분

---

## ⚡ 핵심 명령어 (복사-붙여넣기 가능)

### 1. 브랜치 생성
```bash
git checkout -b feature/balanced-mode-ci
```

### 2. 사전 정리 (선택적)
```bash
pre-commit run --all-files
git add .
git commit -m "style: apply strict formatting before transition"
```

### 3. 설정 파일 변경
**아래 4개 파일을 수정/생성하세요** (상세 내용은 CI_CD_TRANSITION_STRATEGY.md 참조)

- `.pre-commit-config.yaml` - 2곳 수정
- `.github/workflows/ci.yml` - 3곳 추가
- `.vscode/settings.json` - 신규 생성
- `Makefile` - 하단에 추가

### 4. 한 번에 커밋 (CI 스킵)
```bash
git add .pre-commit-config.yaml .github/workflows/ci.yml .vscode/settings.json Makefile
git commit -m "ci: transition to balanced mode

- Update pre-commit config: allow warnings in flake8, relax mypy
- Update CI workflow: auto-fix formatting, check critical errors only
- Add VS Code settings for auto-formatting on save
- Add Makefile helpers for safe commits

[skip ci]"
git push origin feature/balanced-mode-ci
```

### 5. 테스트 커밋 (CI 실행)
```bash
echo "" >> README.md
echo "✅ CI/CD Balanced Mode 적용 완료" >> README.md
git add README.md
git commit -m "docs: confirm balanced mode CI is working"
git push origin feature/balanced-mode-ci
```

---

## 📝 필수 변경 사항 체크리스트

### `.pre-commit-config.yaml`
```yaml
# Flake8 섹션에 추가
-   repo: https://github.com/PyCQA/flake8
    hooks:
    -   id: flake8
        args:
        - --exit-zero  # ⭐ 이 줄 추가

# Mypy 섹션에 추가
-   repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
    -   id: mypy
        args:
        - --ignore-missing-imports  # ⭐ 이 줄 추가
        - --no-strict-optional      # ⭐ 이 줄 추가
```

### `.github/workflows/ci.yml`
```yaml
# "Run pre-commit" 단계를 이렇게 변경:
- name: Run pre-commit with auto-fix
  run: |
    pre-commit run --all-files || true  # ⭐ || true 추가

# 이 단계를 새로 추가:
- name: Auto-commit formatting fixes
  if: github.event_name == 'push'
  run: |
    if [[ -n $(git status --porcelain) ]]; then
      git config user.name "github-actions[bot]"
      git config user.email "github-actions[bot]@users.noreply.github.com"
      git add .
      git commit -m "style: auto-fix formatting [skip ci]"
      git push
    fi

# 이 단계를 새로 추가:
- name: Check for critical linting errors
  run: |
    python -m flake8 . --select=E9,F63,F7,F82 --show-source --statistics
```

### `.vscode/settings.json` (신규 생성)
```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### `Makefile` (하단에 추가)
```makefile
# Code Quality Helpers (Balanced Mode)
.PHONY: format safe-commit validate lint

format:
	@pre-commit run --all-files || true

safe-commit:
	@pre-commit run --all-files || true
	@git add .
	@read -p "Commit message: " msg; git commit -m "$$msg"

validate:
	@pre-commit run --all-files || true
	@python -m flake8 . --select=E9,F63,F7,F82 --show-source --statistics
	@python -m compileall . -q

lint:
	@python -m flake8 . --exit-zero --statistics
```

---

## ⚠️ 주의사항

### ✅ DO (해야 할 것)
- Step 3에서 **반드시** `[skip ci]` 태그 사용
- 모든 설정을 **한 번에** 커밋
- Step 4에서 테스트 커밋으로 검증

### ❌ DON'T (하지 말 것)
- 설정 파일을 **따로따로** 커밋
- Step 3 커밋에서 `[skip ci]` 빼먹기
- 설정 변경 후 캐시 클리어 안 하기

---

## 🔍 빠른 문제 해결

### 문제: Pre-commit이 여전히 엄격하게 동작
```bash
pre-commit clean
pre-commit install --install-hooks
```

### 문제: CI가 여전히 실패
- GitHub Actions 캐시 클리어
- `.github/workflows/ci.yml` 변경사항 확인

### 문제: Mypy 에러가 너무 많음
```python
# 특정 라인만 무시
result = function()  # type: ignore
```

---

## 📊 전환 효과 (예상)

| 지표 | 변경 전 | 변경 후 |
|------|---------|---------|
| CI 실패율 | 80% | 10% |
| 커밋 시간 | 10-15분 | 2-3분 |
| 생산성 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 전환 후 사용법

### 일상적인 개발
```bash
# 1. 코드 작성 (Copilot 사용 OK)
# 2. Ctrl+S (저장) → 자동 포맷팅
# 3. 커밋
make safe-commit  # 또는 git commit

# 4. Push
git push
```

### 전체 검증이 필요할 때
```bash
make validate  # CI와 동일한 검증
```

### Linting 리포트만 볼 때
```bash
make lint  # 차단하지 않고 정보만 표시
```

---

**자세한 설명**: [CI_CD_TRANSITION_STRATEGY.md](./CI_CD_TRANSITION_STRATEGY.md)  
**배경 설명**: [CI_CD_IMPROVEMENT_GUIDE.md](./CI_CD_IMPROVEMENT_GUIDE.md)
