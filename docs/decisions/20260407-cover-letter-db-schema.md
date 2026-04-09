# ADR 002: 자소서 서비스 DB 스키마 — 6개 엔티티 설계

**날짜**: 2026-04-07
**상태**: 승인
**작성자**: TrendOps 개발팀

---

## 컨텍스트

자소서 자동화 서비스는 다음 데이터를 영속 저장해야 한다:
- 사용자 경험·역량·문체 프로필
- 기업 분석 결과 (3-소스 통합, 7일 캐시)
- 직무 분석, 문항 분석
- 경험-문항 매핑 테이블
- 자소서 초안 (버전 이력)

기존 TrendOps 스택(PostgreSQL 15 + psycopg2)을 재사용하며, ORM 없이 직접 SQL 쿼리를 사용한다.

---

## 결정

**6개 엔티티로 구성된 PostgreSQL 스키마** 채택.

| 엔티티 | 역할 | 핵심 설계 결정 |
|--------|------|---------------|
| `user_profile` | 단일 사용자 프로필 (id=1 upsert) | `confirmed_at` NULL = 미확인 |
| `company_analysis` | 기업 분석 캐시 | `UNIQUE(company_name)`, 7일 유효성 |
| `job_analysis` | 직무 분석 | `UNIQUE(company_analysis_id, job_title)` |
| `question` | 문항 + 분석 결과 | `target_char_min/max` Generated Column |
| `mapping_table` | 경험-문항 매핑 | `entries` JSONB 배열 |
| `cover_letter_draft` | 초안 버전 이력 | `char_count` Generated Column, `status` Enum |

---

## 이유

- **JSONB 활용**: 경험·매핑 등 구조가 가변적인 데이터는 JSONB로 유연하게 저장
- **Generated Column**: `target_char_min/max`, `char_count`는 DB 레이어에서 자동 계산 → 애플리케이션 코드 단순화
- **`user_overrides` JSONB**: 각 엔티티에 사용자 수정 내용을 별도 필드에 보관 → 원본 데이터 보존
- **캐시 전략**: `analyzed_at` 컬럼으로 7일 유효성 판단 → 별도 캐시 레이어 불필요

---

## 결과 및 트레이드오프

**긍정**:
- PostgreSQL 단일 DB로 운영 복잡도 최소화
- Generated Column으로 글자 수 계산 로직 DB에 위임
- `ON DELETE CASCADE`로 참조 무결성 자동 관리

**부정**:
- JSONB 필드는 컬럼 단위 인덱스 불가 (GIN 인덱스별도 필요 시)
- MVP에서 단일 사용자이므로 `user_profile` id=1 단일 레코드 전제 — 다중 사용자 확장 시 스키마 변경 필요

---

## 대안 검토

| 대안 | 기각 사유 |
|------|-----------|
| SQLAlchemy ORM | 의존성 추가, MVP 단순 함수 집합 원칙에 위배 (YAGNI) |
| MongoDB | 기존 PostgreSQL 재사용 원칙 위배, 운영 복잡도 증가 |
| 별도 캐시 서버 (Redis) | 단순 `analyzed_at` 필드로 캐시 유효성 충분, MVP 오버엔지니어링 |
