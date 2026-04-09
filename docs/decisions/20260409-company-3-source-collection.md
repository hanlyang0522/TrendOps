# ADR 004: 기업 정보 수집 전략 — DART API·Naver News·홈페이지 3-소스

**날짜**: 2026-04-09
**상태**: 승인
**작성자**: TrendOps 개발팀

---

## 컨텍스트

자소서용 기업 분석은 단순 뉴스 검색만으로는 깊이가 부족하다. 취준생이 실제로 활용하려면:
- **사업 구조·전략**: 주요 제품/서비스, 시장 현황, 연구개발 방향
- **인재상·문화**: 공식 홈페이지의 채용 철학, 인재상
- **최신 동향**: 최근 3~6개월 뉴스

세 가지 소스가 상호 보완적이다. 기존 TrendOps의 Naver 뉴스 크롤러를 재활용 가능하며,
DART API는 무료이나 API 키 등록 필요, 홈페이지 스크래핑은 네트워크 상태에 따라 실패 가능하다.

---

## 결정

**3-소스 순차 수집 + 부분 실패 허용 전략** 채택.

| 소스 | 모듈 | 의존성 | 실패 시 |
|------|------|--------|---------|
| DART 사업보고서 | `dart_collector.py` | `dart-fss` (optional), `DART_API_KEY` | 빈 dict 반환, 계속 진행 |
| Naver News | `naver_collector.py` | 기존 `crawling/` 모듈 | 5건 미만 시 Firecrawl fallback |
| 홈페이지 스크래핑 | `website_crawler.py` | `requests` + `beautifulsoup4` | None 반환, 계속 진행 |

수집 결과를 `llm_client.call(tier='flash')`로 통합 요약 후 `company_analysis` 테이블에 캐싱.
`DART_API_KEY` 미설정 시 DART 수집을 무음으로 스킵.

---

## 이유

- **DART 필수화 금지**: API 키 등록 부담으로 진입장벽 증가 → optional로 처리
- **기존 크롤러 재활용**: `crawling/naver_mcp_crawler.py` 로직 재사용으로 코드 중복 최소화
- **홈페이지 스크래핑**: 인재상·비전은 공식 홈페이지가 가장 정확, requests+BS4로 충분
- **부분 실패 허용**: 소스 1~2개 실패 시에도 나머지 소스로 분석 가능 → 서비스 중단 없음

---

## 결과 및 트레이드오프

**긍정**:
- DART API 활성화 시 자소서 기업 분석 깊이 대폭 향상 (재무·R&D 정보)
- 소스별 독립 모듈로 각각 테스트·모킹 용이
- 7일 캐시로 동일 기업 반복 조회 시 LLM 비용 절감

**부정**:
- 3개 소스 순차 수집 시 첫 분석 최대 30~60초 소요 (Streamlit 스피너 필요)
- 홈페이지 스크래핑은 사이트 구조 변경 시 유지보수 필요
- Naver Firecrawl fallback은 `FIRECRAWL_API_KEY` 별도 필요

**완화**:
- Streamlit `st.status()` 또는 `st.spinner()`로 진행상황 표시
- 홈페이지 스크래핑 실패는 None 반환으로 허용, 분석 품질에 미미한 영향

---

## 대안 검토

| 대안 | 기각 사유 |
|------|-----------|
| Naver 단일 소스 | 사업 전략·인재상 정보 부재 → 자소서 품질 저하 |
| 유료 기업정보 API | 비용 부담, MVP 범위 초과 |
| LLM Web Browse | API 비용 증가, 응답 지연, 구조화 어려움 |
