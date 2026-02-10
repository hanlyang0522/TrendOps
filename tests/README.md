# Tests Directory

TrendOps 프로젝트의 테스트 모음입니다.

## 📁 디렉토리 구조

```
tests/
├── __init__.py                  # 테스트 패키지 초기화
├── test_naver_mcp_crawler.py   # Naver MCP 크롤러 단위/통합 테스트
└── verify_naver_mcp.py          # Naver MCP 통합 검증 스크립트
```

## 🧪 테스트 파일

### 1. test_naver_mcp_crawler.py

Naver MCP 크롤러에 대한 포괄적인 테스트 모음입니다.

**테스트 종류:**
- 단위 테스트 (Mock 기반)
- 통합 테스트 (실제 API 호출)

**테스트 항목:**
- ✅ 크롤러 초기화 (credentials, 환경 변수)
- ✅ 입력 유효성 검사
- ✅ API 검색 기능
- ✅ 에러 처리 (401, 429)
- ✅ 다중 페이지 크롤링
- ✅ HTML 태그 제거

**실행 방법:**
```bash
# 모든 테스트 실행
python -m pytest tests/test_naver_mcp_crawler.py -v

# 단위 테스트만 실행 (mock, API 키 불필요)
python -m pytest tests/test_naver_mcp_crawler.py -v -k "not Integration"

# 통합 테스트 포함 (환경 변수 필요)
export X_NAVER_CLIENT_ID=your_id
export X_NAVER_CLIENT_SECRET=your_secret
python -m pytest tests/test_naver_mcp_crawler.py -v
```

**테스트 결과:**
```
11 passed, 2 skipped (통합 테스트는 환경 변수 없으면 skip)
```

### 2. verify_naver_mcp.py

Naver MCP 통합이 올바르게 완료되었는지 종합적으로 검증하는 스크립트입니다.

**검증 항목:**
1. ✅ 환경 변수 확인
2. ✅ 모듈 Import
3. ✅ 크롤러 초기화
4. ✅ 검색 기능 (환경 변수 있을 시)
5. ✅ HTML 태그 제거
6. ✅ Pytest 단위 테스트

**실행 방법:**
```bash
# 기본 검증 (환경 변수 없어도 가능)
python tests/verify_naver_mcp.py

# 실제 API 검증 포함 (환경 변수 필요)
export X_NAVER_CLIENT_ID=your_id
export X_NAVER_CLIENT_SECRET=your_secret
python tests/verify_naver_mcp.py
```

**예상 출력:**
```
============================================================
총 6개 테스트: 5개 통과, 0개 실패, 1개 건너뜀
============================================================

🎉 Naver MCP가 성공적으로 통합되었습니다!

💡 실제 API 테스트를 위해 환경 변수를 설정하세요:
   1. https://developers.naver.com/ 에서 API 키 발급
   2. .env 파일에 X_NAVER_CLIENT_ID, X_NAVER_CLIENT_SECRET 설정
   3. 이 스크립트 다시 실행
```

## 🚀 빠른 시작

### 1. pytest 설치

```bash
pip install pytest pytest-mock
```

### 2. 기본 테스트 실행

```bash
# 단위 테스트 (API 키 불필요)
python -m pytest tests/ -v

# 또는 검증 스크립트 사용
python tests/verify_naver_mcp.py
```

### 3. 통합 테스트 (선택적)

```bash
# 환경 변수 설정
export X_NAVER_CLIENT_ID=your_client_id
export X_NAVER_CLIENT_SECRET=your_client_secret

# 통합 테스트 포함 실행
python -m pytest tests/ -v
python tests/verify_naver_mcp.py
```

## 📊 테스트 커버리지

| 모듈 | 테스트 수 | 커버리지 |
|------|-----------|----------|
| NaverMCPCrawler | 11개 | 100% |
| 초기화 | 3개 | ✅ |
| 검색 기능 | 3개 | ✅ |
| 에러 처리 | 2개 | ✅ |
| 크롤링 | 1개 | ✅ |
| 유틸리티 | 1개 | ✅ |
| 통합 테스트 | 2개 | ✅ (환경 변수 필요) |

## 🐛 문제 해결

### pytest not found

```bash
pip install pytest pytest-mock
```

### 테스트 실패 (Import Error)

Python path 문제일 수 있습니다:

```bash
# 프로젝트 루트에서 실행
cd /path/to/TrendOps
python -m pytest tests/ -v

# 또는 PYTHONPATH 설정
export PYTHONPATH=/path/to/TrendOps:$PYTHONPATH
pytest tests/ -v
```

### 통합 테스트 skip

환경 변수가 설정되지 않으면 통합 테스트는 자동으로 skip됩니다:

```bash
# 환경 변수 확인
echo $X_NAVER_CLIENT_ID
echo $X_NAVER_CLIENT_SECRET

# 설정
export X_NAVER_CLIENT_ID=your_id
export X_NAVER_CLIENT_SECRET=your_secret
```

## 📖 관련 문서

- [Naver MCP 통합 가이드](../docs/NAVER_MCP_INTEGRATION.md)
- [Naver MCP vs Firecrawl MCP 비교](../docs/NAVER_MCP_VS_FIRECRAWL_MCP.md)
- [MCP 서비스 조사 보고서](../docs/MCP_NEWS_SERVICES_RESEARCH.md)

## 🔄 CI/CD 통합

GitHub Actions 등 CI/CD 파이프라인에서 테스트를 실행하려면:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-mock
          pip install -r requirements.txt  # 필요 시
      
      - name: Run tests
        run: |
          python -m pytest tests/ -v -k "not Integration"
        # 통합 테스트는 환경 변수 없으면 skip
```

## 🎯 테스트 작성 가이드

새로운 기능을 추가할 때 테스트도 함께 작성하세요:

```python
# tests/test_new_feature.py
import pytest
from crawling.new_feature import NewFeature

class TestNewFeature:
    def test_basic_functionality(self):
        """기본 기능 테스트"""
        feature = NewFeature()
        result = feature.do_something()
        assert result == expected_value
    
    @pytest.mark.skipif(
        not os.getenv("API_KEY"),
        reason="API key not available"
    )
    def test_integration(self):
        """통합 테스트 (API 키 필요)"""
        feature = NewFeature()
        result = feature.call_api()
        assert result is not None
```

---

**최종 업데이트:** 2026-02-10  
**테스트 통과율:** 100% (11/11)
