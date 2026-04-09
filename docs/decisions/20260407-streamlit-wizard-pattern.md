# ADR 003: UI 패턴 — Streamlit session_state 5단계 위자드

**날짜**: 2026-04-07
**상태**: 승인
**작성자**: TrendOps 개발팀

---

## 컨텍스트

자소서 자동화 서비스는 5가지 상호 의존적 단계를 순서대로 안내해야 한다:
1. 프로필 등록
2. 기업·직무 분석
3. 문항 분석
4. 경험-문항 매핑
5. 답변 생성 및 자가진단

각 단계의 결과가 다음 단계의 입력이 되므로, 단계 간 데이터 흐름이 명확해야 한다.
취준생 1인이 로컬에서 혼자 사용하는 MVP 시나리오이다.

---

## 결정

**Streamlit `session_state["step"]` 기반 5단계 위자드 패턴** 채택.

```python
# frontend/cover_letter_app.py 핵심 구조
import streamlit as st

if "step" not in st.session_state:
    st.session_state["step"] = 0

STEPS = ["프로필 등록", "기업·직무 분석", "문항 분석", "경험-문항 매핑", "답변 생성"]
st.progress(st.session_state["step"] / (len(STEPS) - 1))
st.subheader(f"Step {st.session_state['step'] + 1}: {STEPS[st.session_state['step']]}")
```

각 단계:
- 이전 단계 결과를 `session_state`에 누적
- "이전 단계로" 버튼으로 복귀 가능
- 최종 저장(`save_profile`, `save_mapping`, `confirm_draft`)은 각 단계 확정 시 즉시 실행

---

## 이유

- **Streamlit 기본 기능 활용**: 복잡한 라우팅 라이브러리 없이 `session_state`만으로 구현
- **단계 간 데이터 흐름 명확**: 각 단계 결과가 `session_state`에 키로 보관 → 다음 단계에서 직접 참조
- **로컬 MVP 적합**: 단일 사용자, 브라우저 1개 탭, 새로고침 시 초기화 허용

---

## 결과 및 트레이드오프

**긍정**:
- 추가 의존성 없음 (Streamlit 내장)
- 단계 진행 상태를 `st.progress()`로 시각화 용이
- 각 단계를 독립 함수로 분리 → 테스트 용이

**부정**:
- 브라우저 탭 새로고침 시 `session_state` 초기화 → 작업 중인 데이터 손실
- Streamlit Cloud 다중 사용자 시나리오 확장 불가 (MVP 전제임)

**완화**:
- 각 단계 확정 버튼 클릭 시 즉시 DB 저장 → 재시작 시 DB에서 복원 가능

---

## 대안 검토

| 대안 | 기각 사유 |
|------|-----------|
| 멀티 페이지 Streamlit (`pages/`) | 단계 간 데이터 공유 복잡, session_state 전달 어려움 |
| FastAPI + React | 개발 복잡도 급증, MVP 오버엔지니어링 |
| Gradio | Streamlit 대비 커스터마이징 제한, 한국어 UI 품질 낮음 |
