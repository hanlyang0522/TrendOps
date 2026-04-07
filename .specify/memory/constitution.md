<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0
Modified principles: 없음
Added sections: 개발 워크플로우 > 브랜치 전략 — GitHub Flow 명시적 정의
Removed sections: 없음
Templates status:
  ✅ .specify/templates/plan-template.md — Constitution Check 브랜치 게이트 반영
  ✅ .github/copilot-instructions.md — Git Flow → GitHub Flow 전면 교체
  ⚠ .specify/templates/spec-template.md — 기존 구조 유지 (변경 불필요)
  ⚠ .specify/templates/tasks-template.md — 기존 구조 유지 (변경 불필요)
Follow-up TODOs:
  - TODO(RATIFICATION_DATE): 프로젝트 최초 시작일을 정확히 알 경우 2026-04-07 → 실제 날짜로 수정
  - NOTE: develop 브랜치가 원격에 존재하면 삭제 또는 main으로 리셋 필요
-->

# TrendOps Constitution

## Core Principles

### I. MLOps 중심 설계 (MLOps-First Design)

TrendOps의 모든 기술 결정은 MLOps 서빙·배포 파이프라인 경험을 쌓기 위한 포트폴리오 목적을 MUST 충족해야 한다.

- 새로운 기능을 추가하거나 기술 스택을 변경할 때, `docs/decisions/` 디렉토리에 ADR(Architecture Decision Record) 형식의 문서를 MUST 작성한다.
- ADR은 다음 네 가지 항목을 MUST 포함한다: **① 무엇이 변했는가**, **② 어떤 문제를 해결하는가**, **③ 왜 이 결정을 했는가**, **④ 이 결정이 최선인가 (대안과 비교)**.
- 결정 문서 없이 주요 아키텍처 변경을 병합하는 PR은 허용하지 않는다.
- 파일 경로 규칙: `docs/decisions/YYYYMMDD-<짧은설명>.md` (예: `docs/decisions/20260407-llm-api-selection.md`)

### II. 컨테이너 우선 (Container-First)

모든 서비스 모듈은 Docker 컨테이너 단위로 관리한다.

- 새로운 서비스는 MUST 전용 Dockerfile을 보유한다.
- 로컬 오케스트레이션은 Docker Compose, 클라우드 확장은 Kubernetes 매니페스트를 사용한다.
- 서비스 간 의존성은 Docker Compose의 `depends_on` 또는 K8s 헬스체크로 선언적으로 관리한다.
- 프로덕션에서 컨테이너 밖 직접 실행은 허용하지 않는다.
- Dockerfile은 멀티스테이지 빌드를 권장하며, 이미지 크기와 보안을 고려한다.

### III. MVP 우선, 확장 가능 설계 (MVP-First, Extensible Design)

먼저 로컬에서 동작하는 최소 제품을 만들고, 이후 모델 고도화·클라우드 서빙으로 점진적으로 확장한다.

- 새 기능은 로컬 MVP 동작 검증 후 병합한다.
- 확장 지점(모델 교체, DB 교체, 서빙 인프라 교체)은 인터페이스·환경 변수로 추상화하되, 실제 필요 전까지 구현을 미룬다 (YAGNI).
- 아키텍처는 단계별로 진화한다: **로컬 Docker Compose → 클라우드 컨테이너 → Kubernetes**.
- 스케일 업 전 현재 단계를 충분히 검증한다.

### IV. 코드 최소화 & 품질 (Code Minimalism & Quality)

기능 구현에 필요한 최소한의 코드만 작성하고, 일관된 품질을 유지한다.

- 불필요한 헬퍼, 추상화, 미래 대비 코드(speculative generality)는 작성하지 않는다.
- 모든 커밋 전 pre-commit 훅(black, isort, flake8, mypy, trailing-whitespace, end-of-file-fixer)이 MUST 통과해야 한다.
- 라인 길이: 88자, 타입 힌트: Python 3.13 네이티브(`list[str]`, `dict[str, int]`), 독스트링: Google 스타일.
- **기능 개발 완료 후 MUST 코드리뷰를 수행**한다: 공통 로직 추출 가능 여부, 리팩토링 필요 여부를 검사하고 마무리한다.
- 보안: 민감 정보는 환경 변수로만 관리하며, 하드코딩 금지.

### V. 의사결정 문서화 (Decision Documentation — NON-NEGOTIABLE)

기술적 결정은 코드만큼 중요한 산출물이다. 이는 MLOps 엔지니어 포트폴리오의 핵심 근거가 된다.

- 원칙 I에서 정의한 ADR 작성은 선택이 아닌 필수이며 PR 병합의 선제 조건이다.
- ADR 파일은 Markdown 형식, 한글로 작성한다.
- 스펙/플랜 문서와 ADR은 `docs/` 하위에서 버전 관리한다.
- ADR은 최소 다음 섹션을 포함한다:
  ```
  ## 상태: (제안 | 승인 | 폐기)
  ## 배경
  ## 결정
  ## 대안 검토
  ## 결과 및 트레이드오프
  ```

## 기술 스택 & 프로젝트 구조

### 기술 스택

| 계층 | 기술 | 비고 |
|------|------|------|
| 언어 | Python 3.13 | 네이티브 타입 힌트 |
| 프론트엔드 | Streamlit | 빠른 MVP UI |
| 백엔드/API | (Phase 2 이후 결정) | FastAPI 후보 |
| 데이터베이스 | PostgreSQL 15 | Docker 컨테이너 |
| LLM | API 기반 (OpenAI 등) | 환경 변수로 교체 가능 |
| 크롤링 | BeautifulSoup4, requests | Naver Open API |
| 컨테이너 | Docker, Docker Compose | K8s 확장 예정 |
| CI/CD | GitHub Actions | pre-commit 연동 |
| 코드 품질 | black, isort, flake8, mypy | pre-commit 훅 |

### 프로젝트 구조

```text
TrendOps/
├── crawling/          # 크롤링 서비스 로직 (Naver News API 등)
├── db/                # DB 연결 및 쿼리 (PostgreSQL)
├── llm/               # LLM 요약 서비스 모듈 (Phase 1)
├── frontend/          # Streamlit UI (Phase 2)
├── api/               # 백엔드 API 레이어 (필요 시 추가)
├── scripts/           # 스케줄러, 유틸리티 스크립트
├── tests/             # 테스트 (unit, integration, functional)
├── docs/
│   ├── decisions/     # ADR 문서 (YYYYMMDD-<설명>.md)
│   └── README.md      # 개발 가이드
├── .github/
│   ├── workflows/     # GitHub Actions CI/CD
│   └── copilot-instructions.md
├── Dockerfile.<service>  # 서비스별 Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── pyproject.toml
```

### 서비스 로직 배치 규칙

- **비즈니스 로직** → 해당 서비스 모듈(`crawling/`, `llm/`, `api/`)
- **DB 접근** → `db/db_news.py` (쿼리 집중화)
- **설정/환경 변수** → 각 모듈의 상단 `os.getenv()` 호출
- **스케줄링** → `scripts/scheduler.py`
- **공통 유틸리티** → 중복 발생 시에만 `utils/` 생성 (YAGNI)

## 개발 워크플로우

### 기능 개발 사이클

```
1. ADR 초안 작성 (docs/decisions/)
   ↓
2. feature 브랜치 생성 (`main` 기반)
   ↓
3. 최소 코드 구현 + Docker 컨테이너 검증
   ↓
4. pre-commit 훅 통과 + 테스트 작성
   ↓
5. 로컬 MVP 동작 확인
   ↓
6. 코드리뷰: 공통 로직 추출, 리팩토링 검토
   ↓
7. ADR 최종화 (결과 및 트레이드오프 보완)
   ↓
8. PR → `main` (CI 통과 후 병합)
```

### CI/CD 게이트

- **pre-commit**: black, isort, flake8, mypy, trailing-whitespace, end-of-file-fixer
- **GitHub Actions**: lint, type-check, test (pytest)
- PR 병합 조건: CI 통과 + 관련 ADR 존재 (주요 변경 시)

### 브랜치 전략 (GitHub Flow)

TrendOps는 **GitHub Flow**를 브랜치 전략으로 사용한다.

| 규칙 | 설명 |
|------|------|
| 유일한 장기 브랜치 | `main` — 항상 배포 가능한 상태 유지 |
| 작업 브랜치 기반 | 모든 브랜치는 `main`에서 분기 |
| PR 대상 | 모든 PR은 `main`을 타겟으로 생성 |
| 브랜치 수명 | 짧게 유지; 완료 즉시 삭제 |
| 긴급 수정 | 별도 hotfix 브랜치 없음 — `fix/*` 브랜치를 `main`에서 생성 |
| 릴리스 | `main` 병합 후 태그 (v1.0.0) 생성 |

**작업 브랜치 타입 (모두 `main` → `main`):**

```
feature/<name>   # 새 기능
fix/<name>       # 버그 수정 (긴급 포함)
refactor/<name>  # 리팩토링
docs/<name>      # 문서
test/<name>      # 테스트
chore/<name>     # 유지보수
```

상세 브랜치 명명 규칙 및 커밋 컨벤션은 `.github/copilot-instructions.md`를 따른다.

## Governance

- 이 Constitution은 모든 개발 관행보다 우선한다.
- 수정은 MUST 버전 번호를 올리고, 변경 사항을 `SYNC IMPACT REPORT`에 기록한다.
- 버전 정책: MAJOR(원칙 제거·재정의), MINOR(원칙 추가·확장), PATCH(문구 수정·명확화).
- 분기 PR 리뷰 시 이 Constitution 준수 여부를 MUST 확인한다.
- 런타임 개발 가이드는 `.github/copilot-instructions.md`를 참조한다.

**Version**: 1.1.0 | **Ratified**: 2026-04-07 | **Last Amended**: 2026-04-07
