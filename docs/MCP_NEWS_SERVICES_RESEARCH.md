# MCP 뉴스 크롤링 서비스 조사 보고서

**작성일**: 2026-02-09  
**목적**: TrendOps 프로젝트에 적용 가능한 MCP 기반 뉴스 크롤링 서비스 조사

---

## 📋 요약

현재 TrendOps는 BeautifulSoup으로 Naver 뉴스 웹페이지를 직접 크롤링하는 방식을 사용하고 있습니다. 이를 MCP (Model Context Protocol) 기반 뉴스 크롤링 서비스로 전환하기 위한 조사를 수행했습니다.

### 주요 발견사항
1. **Naver News 전용 MCP 서버가 존재함** - 한국 시장에 특화된 솔루션
2. **글로벌 뉴스 MCP 서버도 사용 가능** - 200개국 이상 지원
3. **RSS 기반 MCP 서버** - 범용 뉴스 피드 파싱

---

## 🔍 조사한 MCP 서비스

### 1. mcp-naver-news ⭐ **[최고 추천]**

**GitHub**: https://github.com/justcoding-ys/mcp-naver-news  
**PyPI**: `pip install mcp-naver-news`

#### 특징
- ✅ **Naver News API 공식 지원** - Naver OpenAPI 사용
- ✅ **한국어 완벽 지원**
- ✅ **날짜 범위 필터링** - 원하는 기간 설정 가능
- ✅ **정렬 옵션** - 관련도(sim), 날짜(date)
- ✅ **두 가지 검색 모드**:
  - `search_news`: 제목/요약만 빠르게 조회 (API 응답)
  - `search_news_detail`: 실제 기사 본문까지 크롤링 (robust 추출)
- ✅ **Python 3.10+ 지원**
- ✅ **Claude Desktop 통합**

#### 장점
- Naver 뉴스에 최적화됨
- 공식 API 사용으로 안정적
- 본문 추출 기능 제공
- 무료 (비상업용)

#### 단점
- Naver OpenAPI 키 필요 (무료 발급 가능)
- 비상업용 라이선스 (상업용 금지)
- API 요청 제한 존재 (일 25,000건)

#### 구현 방법
```python
# 설치
pip install mcp-naver-news

# 환경 변수 설정
export X_NAVER_CLIENT_ID="your_client_id"
export X_NAVER_CLIENT_SECRET="your_client_secret"

# 사용 예시
from mcp_naver_news import search_news

results = search_news(
    query="당근마켓",
    display=10,
    start=1,
    sort="date"  # or "sim" for relevance
)
```

---

### 2. news-mcp-server

**PyPI**: `pip install news-mcp-server`  
**문서**: https://pypi.org/project/news-mcp-server/

#### 특징
- ✅ **200개국 이상 지원**
- ✅ **18개 언어 지원** (한국어 포함)
- ✅ **대규모 뉴스 소스** - 전 세계 수천 개 매체
- ✅ **LangChain, CrewAI 통합**
- ✅ **Redis 캐싱 지원**
- ✅ **Prometheus 모니터링**

#### 장점
- 글로벌 뉴스 커버리지
- 프로덕션 급 성능
- AI 프레임워크 통합
- 풍부한 메타데이터 (감정 분석, 엔티티 추출 등)

#### 단점
- ❌ **유료 API 필요** - Press Monitor API 구독 필요
- ❌ **비용 발생** - AWS Marketplace에서 구독
- Naver News 특화 기능 없음
- 설정 복잡도 높음

#### 구현 방법
```python
# 설치
pip install news-mcp-server[full]

# 환경 변수 설정
export PRESS_MONITOR_API_KEY="your_key:subscription_id"

# 서버 실행
news-mcp-server run

# 클라이언트 사용
from news_mcp_server.api.client import NewsMCPClient

async with NewsMCPClient() as client:
    headlines = await client.get_headlines(
        query="AI breakthrough",
        country_code="KR",
        lang_code="ko"
    )
```

---

### 3. mcp-server-rss

**PyPI**: `pip install mcp-server-rss`  
**문서**: https://pypi.org/project/mcp-server-rss/

#### 특징
- ✅ **RSS/Atom 피드 자동 탐지**
- ✅ **여러 RSS 형식 지원** (RSS 2.0, RSS 1.0, Atom 1.0)
- ✅ **HTML 정리 기능**
- ✅ **무료 오픈소스**
- ✅ **Claude Desktop 통합**

#### 장점
- 완전 무료
- API 키 불필요
- 간단한 설정
- 범용적으로 사용 가능

#### 단점
- Naver News 특화 기능 없음
- RSS 피드에 의존적
- 검색 기능 제한적
- 본문 추출 품질 불확실

#### 구현 방법
```python
# 설치
pip install mcp-server-rss

# 실행
mcp-server-rss --host 0.0.0.0 --port 8000

# 사용 (Claude Desktop 통합)
{
  "mcpServers": {
    "rss": {
      "command": "mcp-server-rss"
    }
  }
}
```

---

## 💡 TrendOps 프로젝트 적용 권장사항

### ✅ **추천: mcp-naver-news**

#### 이유
1. **Naver News에 최적화** - 프로젝트의 주요 데이터 소스
2. **무료 사용 가능** - 비상업용이므로 학습/개인 프로젝트에 적합
3. **한국어 완벽 지원** - 한국 뉴스 크롤링에 최적
4. **날짜 범위 필터링** - 요구사항 충족
5. **본문 추출 기능** - 상세 분석 가능

#### 제약사항
- **Naver OpenAPI 신청 필요** (5분 소요, 무료)
- **일일 요청 제한**: 25,000건 (충분함)
- **비상업용**: 상업적 사용 시 라이선스 확인 필요

---

## 📊 비교표

| 항목 | mcp-naver-news | news-mcp-server | mcp-server-rss |
|------|---------------|-----------------|----------------|
| **Naver News 지원** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **한국어 지원** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **비용** | 무료 | 유료 | 무료 |
| **날짜 필터링** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **본문 추출** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **설정 난이도** | 쉬움 | 중간 | 매우 쉬움 |
| **유지보수** | 활발 | 활발 | 보통 |
| **프로덕션 급** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🚀 다음 단계 (구현 계획)

### Phase 1: Naver OpenAPI 준비
1. Naver Developers 회원가입
2. 애플리케이션 등록
3. 뉴스 검색 API 사용 신청
4. Client ID & Secret 발급

### Phase 2: mcp-naver-news 통합
1. `mcp-naver-news` 패키지 설치
2. 환경 변수 설정 (`.env` 파일)
3. 기존 `crawling/news_crawling.py` 리팩토링
4. MCP 기반 크롤링으로 전환

### Phase 3: 테스트 및 검증
1. 단위 테스트 작성
2. 날짜 범위 필터링 테스트
3. 본문 추출 품질 검증
4. API 제한 모니터링

### Phase 4: 배포 및 모니터링
1. Docker 이미지 업데이트
2. 환경 변수 문서화
3. 스케줄러 업데이트
4. 로깅 및 모니터링 강화

---

## 📚 참고 자료

### Naver OpenAPI
- **신청 페이지**: https://developers.naver.com/
- **뉴스 검색 API 문서**: https://developers.naver.com/docs/serviceapi/search/news/news.md
- **요청 제한**: 일 25,000건 (무료)

### MCP 프로토콜
- **공식 사이트**: https://modelcontextprotocol.io/
- **Anthropic 소개**: https://www.anthropic.com/news/model-context-protocol

### GitHub 저장소
- **mcp-naver-news**: https://github.com/justcoding-ys/mcp-naver-news
- **news-mcp-server**: https://pypi.org/project/news-mcp-server/
- **mcp-server-rss**: https://pypi.org/project/mcp-server-rss/

---

## ❓ FAQ

### Q1: Naver OpenAPI는 정말 무료인가요?
**A**: 네, 개인 및 비상업용으로는 완전 무료입니다. 일일 25,000건의 요청 한도가 있습니다.

### Q2: 상업적으로 사용하려면?
**A**: Naver OpenAPI 상업용 라이선스 또는 `news-mcp-server` (유료) 사용을 고려해야 합니다.

### Q3: 기존 크롤링 코드는 어떻게 되나요?
**A**: 백업 후 새로운 MCP 기반 코드로 대체하거나, fallback 옵션으로 유지할 수 있습니다.

### Q4: API 제한을 초과하면?
**A**: 요청 간격 조절, 캐싱 활용, 또는 상업용 API 고려가 필요합니다.

---

## 🎯 결론

**TrendOps 프로젝트에는 `mcp-naver-news`가 가장 적합합니다.**

- ✅ Naver News에 최적화
- ✅ 무료 사용 가능 (비상업용)
- ✅ 날짜 범위 필터링 지원
- ✅ 본문 추출 기능
- ✅ 한국어 완벽 지원

다만, Naver OpenAPI 신청이 필요하므로 즉시 적용은 어렵습니다. 신청 후 승인까지 약 1-2일 소요될 수 있습니다.
