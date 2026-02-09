# TrendOps 문서 모음

이 디렉토리는 TrendOps 프로젝트의 MCP 기반 뉴스 크롤링 서비스 조사 및 비교 문서를 포함합니다.

---

## 📚 문서 목록

### 1. [MCP 뉴스 크롤링 서비스 조사 보고서](./MCP_NEWS_SERVICES_RESEARCH.md)
- **목적**: 사용 가능한 MCP 뉴스 크롤링 서비스 조사
- **내용**:
  - MCP (Model Context Protocol) 개념 소개
  - 3가지 주요 서비스 분석
    - mcp-naver-news (Naver 전용, 무료) ⭐ 추천
    - news-mcp-server (글로벌, 유료)
    - mcp-server-rss (RSS, 무료)
  - 각 서비스별 특징, 장단점, 구현 방법
  - TrendOps 프로젝트 적용 권장사항

### 2. [Naver MCP vs Firecrawl MCP 비교 분석](./NAVER_MCP_VS_FIRECRAWL_MCP.md) 
- **목적**: Naver MCP와 Firecrawl MCP 상세 비교
- **내용**:
  - 두 서비스의 핵심 차이점
  - 데이터 수집 방식 비교 (API vs 웹 스크래핑)
  - 비용 비교 (무료 vs $20/월)
  - 상세 비교표 및 장단점 분석
  - 시나리오별 추천
  - 구현 로드맵 및 마이그레이션 전략

---

## 🎯 핵심 결론

### TrendOps 프로젝트 최종 추천

**1차 추천: Naver MCP (mcp-naver-news)** ⭐⭐⭐⭐⭐

**추천 이유:**
- ✅ **완전 무료** (일 25,000건 제한)
- ✅ **Naver 뉴스 최적화** (공식 API)
- ✅ **빠른 속도** (API 직접 호출)
- ✅ **안정적** (구조화된 데이터)
- ✅ **요구사항 완벽 충족**

**제약사항:**
- Naver 뉴스만 크롤링 가능
- 비상업용 라이선스
- Naver OpenAPI 키 필요 (무료 발급)

---

**2차 추천: Firecrawl MCP** (확장 시)

**사용 시점:**
- Naver 외 다른 뉴스 사이트 크롤링 필요 시
- JavaScript 동적 페이지 처리 필요 시
- 예산 확보 시 ($20/월)

**장점:**
- ✅ 모든 웹사이트 크롤링 가능
- ✅ JavaScript/SPA 지원
- ✅ AI 기반 콘텐츠 추출

**단점:**
- ❌ 유료 ($20/월 Hobby 플랜 필요)
- ❌ Naver 뉴스는 비효율적
- ❌ 속도 느림 (페이지 렌더링)

---

## 📊 비용 비교 요약

| 서비스 | 월 비용 | TrendOps 사용량 | 충분성 |
|--------|---------|----------------|--------|
| **Naver MCP** | **$0** | 900건/월 | ✅ 충분 (25,000건/일) |
| **Firecrawl MCP** | **$20** | 900 크레딧/월 | ⚠️ Hobby 플랜 필요 |

---

## 🚀 다음 단계

### 즉시 실행 가능 (추천)

1. **Naver OpenAPI 신청** (5분 소요)
   - https://developers.naver.com/
   - 뉴스 검색 API 사용 신청
   - Client ID & Secret 발급

2. **mcp-naver-news 통합**
   ```bash
   pip install mcp-naver-news
   ```

3. **코드 구현** (2-3시간)
   - `crawling/news_crawling_mcp.py` 작성
   - 환경 변수 설정
   - 테스트 및 검증

### 향후 확장 (선택)

1. **Firecrawl MCP 추가**
   - Firecrawl 계정 가입 ($20/월)
   - 타 뉴스 사이트 크롤링
   - Naver MCP와 병행 사용

---

## 📖 관련 링크

### Naver MCP
- GitHub: https://github.com/justcoding-ys/mcp-naver-news
- PyPI: https://pypi.org/project/mcp-naver-news/
- Naver OpenAPI: https://developers.naver.com/

### Firecrawl MCP
- GitHub: https://github.com/firecrawl/firecrawl-mcp-server
- 공식 문서: https://docs.firecrawl.dev/mcp-server
- 가격: https://www.firecrawl.dev/pricing

### MCP 프로토콜
- 공식 사이트: https://modelcontextprotocol.io/
- Anthropic 소개: https://www.anthropic.com/news/model-context-protocol

---

**최종 업데이트:** 2026-02-09  
**작성자:** GitHub Copilot
