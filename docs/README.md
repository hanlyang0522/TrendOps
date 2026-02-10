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
# TrendOps Documentation

이 디렉토리는 TrendOps 프로젝트의 분석 및 개발 가이드 문서를 포함합니다.

## 📚 문서 목록

### 1. [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md)
**빠른 시작 가이드 - 지금 바로 읽으세요! 👈**

- 현재 프로젝트 상태 요약
- 다음 단계 체크리스트
- Phase 1 구현 가이드
- 필수 명령어 모음
- 핵심 팁

**누구를 위한 문서**: 바로 개발을 시작하고 싶은 개발자

**예상 읽기 시간**: 10-15분

---

### 2. [PROJECT_ANALYSIS_AND_ROADMAP.md](./PROJECT_ANALYSIS_AND_ROADMAP.md)
**상세 프로젝트 분석 및 로드맵**

- 완전한 프로젝트 현황 분석
- 5개 Phase 상세 설명
- 단계별 구현 가이드 (코드 예제 포함)
- 기술 스택 추천 및 비교
- 학습 리소스 링크
- 타임라인 및 성공 지표

**누구를 위한 문서**: 전체 그림을 이해하고 싶은 개발자, 프로젝트 기획자

**예상 읽기 시간**: 30-45분

---

## 🚀 처음 오신 분들께

### 추천 순서

1. **[QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md)** 읽기 (10분)
   - 현재 상태 파악
   - 다음 액션 확인

2. **Phase 1 시작**
   - OpenAI API 키 발급
   - 본문 크롤링 구현
   - 요약 모듈 개발

3. 막힐 때 **[PROJECT_ANALYSIS_AND_ROADMAP.md](./PROJECT_ANALYSIS_AND_ROADMAP.md)** 참고
   - 상세 구현 가이드
   - 코드 예제
   - 트러블슈팅

---

## 📊 프로젝트 현황 (2026-01-19 기준)

```
전체 진행도: 35-40%

✅ 완료: 크롤링, DB, 스케줄링
🚧 진행 중: -
❌ 미구현: LLM 요약, UI, 이메일

다음 마일스톤: Phase 1 (LLM 요약) - 1-2주 예상
```

---

## 🎯 핵심 목표

**최종 목표**: 취업 준비생을 위한 LLM 기반 산업 트렌드 자동 요약 서비스

### MVP (3-4주 목표)
- [x] 뉴스 크롤링
- [ ] LLM 요약 ← **현재 여기**
- [ ] 웹 UI
- [ ] 기본 스케줄링

### 완성 버전 (6-8주 목표)
- [ ] 사용자 관리
- [ ] 이메일 발송
- [ ] 다중 기업 지원
- [ ] 고급 기능 (감정 분석, 시각화 등)

---

## 💡 문서 활용 팁

### 개발 중
- Phase별 체크리스트 활용
- 코드 예제 복사-붙여넣기 OK (수정해서 사용)
- 막힐 때 "학습 리소스" 섹션 참고

### 리뷰 요청 시
- 완료한 체크리스트 체크 ✓
- 성공 지표 달성 여부 확인
- 문서의 권장 사항 준수 확인

### 프로젝트 관리
- 마일스톤을 GitHub Issues로 전환
- Phase별로 브랜치 생성
- 주간 진행도 업데이트

---

## 🔄 문서 업데이트

이 문서들은 프로젝트 진행에 따라 업데이트될 예정입니다.

**마지막 업데이트**: 2026-01-19
**다음 업데이트 예정**: Phase 1 완료 후

---

## ❓ 질문이나 피드백

- GitHub Issues에 등록
- 문서 개선 제안 환영
- 구현 중 막힌 부분 공유

---

**Happy Coding! 🎉**
