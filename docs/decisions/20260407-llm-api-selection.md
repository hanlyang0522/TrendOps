# ADR 001: LLM API 선택 — Gemini 단일 프로바이더 + 3단계 티어 전략

**날짜**: 2026-04-07
**상태**: 승인
**작성자**: TrendOps 개발팀

---

## 컨텍스트

자소서 자동화 서비스에서 LLM을 세 가지 용도로 활용한다:
1. 텍스트 요약·분류 (저비용, 대량 호출)
2. 자소서 초안 생성 (중비용, 품질 우선)
3. 자가진단 및 심층 추론 (고비용, 신뢰성 우선)

LLM 프로바이더 선택 기준: 한국어 성능, API 안정성, 비용, 통합 복잡도.

---

## 결정

**Google Gemini 단일 프로바이더 + 3단계 티어 모델 전략** 채택.

| 티어 | 모델 | 활용 목적 | temperature |
|------|------|-----------|-------------|
| `flash` | `gemini-2.5-flash` | 수집/요약/매핑 (FR-003~005) | 0.3 |
| `pro` | `gemini-2.5-pro` | 자소서 초안 생성 (FR-006) | 0.7 |
| `pro-thinking` | `gemini-2.5-pro` + thinking_budget=8192 | 자가진단 (FR-007) | 1.0 |

모든 티어는 `cover_letter/llm_client.py`의 `call(prompt, tier, system, temperature)` 단일 인터페이스로 추상화.
모델명은 `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL` 환경 변수로 교체 가능.

---

## 이유

- **한국어 성능**: Gemini 2.0 Flash·2.5 Pro는 한국어 자소서 도메인에서 충분한 품질
- **단일 프로바이더**: API 키 1개, SDK 1개로 운영 복잡도 최소화
- **티어 분리**: 호출 목적에 따라 비용/품질 균형 최적화
- **환경 변수 교체**: 모델 버전 업그레이드 시 코드 변경 없이 환경 변수만 교체

---

## 결과 및 트레이드오프

**긍정**:
- 단일 SDK(`google-genai`)로 통합 단순화
- 티어별 비용 최적화 (flash 단가 대비 pro 약 10배 차이)
- `thinking_budget` 파라미터로 pro-thinking 추론 깊이 제어 가능

**부정**:
- Google 서비스 장애 시 전체 LLM 기능 중단 (단일 장애점)
- `gemini-2.5-pro` thinking mode API 스펙이 GA 전 변경 가능성 있음

**완화**:
- 환경 변수 기반 모델 교체로 장기적 공급업체 전환 용이
- retry 로직은 호출부에서 처리 (llm_client는 단순 래퍼 유지)

---

## 대안 검토

| 대안 | 기각 사유 |
|------|-----------|
| OpenAI GPT-4o | API 비용 및 한국어 자소서 도메인 성능 미검증 |
| Anthropic Claude | 멀티 프로바이더 복잡도 증가, 동일 SDK 미사용 |
| 로컬 LLM (Ollama) | 품질 미달, GPU 의존성, MVP 범위 초과 |
