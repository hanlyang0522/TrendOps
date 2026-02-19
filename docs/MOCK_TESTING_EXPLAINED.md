# Mock 테스트란? API 키 없이 테스트하는 방법

## 🤔 질문: API 키 없이 어떻게 테스트가 가능한가요?

**답변: Mock (모의 객체) 테스트를 사용했기 때문입니다!**

Mock 테스트는 실제 API를 호출하지 않고도 코드를 테스트할 수 있는 방법입니다.

---

## 📚 Mock 테스트의 원리

### 일반적인 API 호출 흐름

```
[테스트 코드]
    ↓
[우리 코드: NaverMCPCrawler]
    ↓
[requests.get()] ← 실제 네트워크 호출
    ↓
[Naver API 서버] ← API 키 필요!
    ↓
[응답 반환]
```

### Mock을 사용한 테스트 흐름

```
[테스트 코드]
    ↓
[우리 코드: NaverMCPCrawler]
    ↓
[requests.get()] ← Mock으로 대체!
    ↓
[가짜 응답 반환] ← 미리 정의한 데이터
    ↓
[테스트 완료] ← API 키 불필요!
```

---

## 💡 실제 예시로 이해하기

### 예시 1: Mock 없이 테스트하면? (실패)

```python
# 실제 API 호출 - API 키 필요
from crawling.naver_mcp_crawler import NaverMCPCrawler

crawler = NaverMCPCrawler(
    client_id="wrong_id",  # 잘못된 키
    client_secret="wrong_secret"
)

# ❌ 실패: 401 Unauthorized
result = crawler.search_news(query="당근마켓")
```

### 예시 2: Mock을 사용하면? (성공!)

```python
from unittest.mock import Mock, patch

# Mock 객체 생성
@patch("crawling.naver_mcp_crawler.requests.get")
def test_with_mock(mock_get):
    # 가짜 응답 정의
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total": 100,
        "items": [
            {
                "title": "테스트 뉴스",
                "link": "https://example.com",
                "description": "테스트 설명",
                "pubDate": "Mon, 10 Feb 2026 10:00:00 +0900"
            }
        ]
    }

    # mock_get이 호출되면 위의 가짜 응답 반환
    mock_get.return_value = mock_response

    # ✅ 성공: 실제 API 호출 없이 테스트
    crawler = NaverMCPCrawler(
        client_id="test_id",  # 아무 값이나 가능
        client_secret="test_secret"
    )

    result = crawler.search_news(query="당근마켓")
    print(result)  # 위에서 정의한 가짜 데이터 출력
```

---

## 🔍 TrendOps 프로젝트의 테스트 구조

### 1. 단위 테스트 (Unit Tests) - Mock 사용 ✅

**파일**: `tests/test_naver_mcp_crawler.py`

```python
class TestNaverMCPCrawler:
    """Mock을 사용한 단위 테스트"""

    @patch("crawling.naver_mcp_crawler.requests.get")
    def test_search_news_success(self, mock_get):
        # 🎭 Mock 설정: 가짜 응답 정의
        mock_response = Mock()
        mock_response.json.return_value = {"items": [...]}
        mock_get.return_value = mock_response

        # ✅ API 키 없이 테스트 가능!
        crawler = NaverMCPCrawler(
            client_id="test",
            client_secret="test"
        )
        result = crawler.search_news(query="테스트")

        # 검증: Mock이 올바르게 호출되었는지 확인
        assert result["items"] is not None
        mock_get.assert_called_once()
```

**특징:**
- ✅ **API 키 불필요**
- ✅ **빠른 실행** (~0.1초)
- ✅ **네트워크 불필요**
- ✅ **항상 성공** (외부 의존성 없음)

### 2. 통합 테스트 (Integration Tests) - 실제 API ⚠️

**파일**: `tests/test_naver_mcp_crawler.py`

```python
@pytest.mark.skipif(
    not os.getenv("X_NAVER_CLIENT_ID"),
    reason="Naver OpenAPI credentials not available"
)
class TestNaverMCPCrawlerIntegration:
    """실제 API를 사용한 통합 테스트"""

    def test_real_api_search(self):
        # ⚠️ 실제 API 호출 - API 키 필요!
        crawler = NaverMCPCrawler()  # 환경 변수에서 키 로드
        result = crawler.search_news(query="당근마켓")

        # 실제 응답 검증
        assert "items" in result
```

**특징:**
- ⚠️ **API 키 필요**
- ⚠️ **네트워크 필요**
- ⚠️ **느린 실행** (~1-2초)
- 🔄 **API 키 없으면 자동 skip**

---

## 🎯 왜 이렇게 나뉘어져 있나요?

### 단위 테스트 (Mock)의 목적
1. **로직 검증**: 우리 코드가 올바르게 작동하는지
2. **빠른 피드백**: 몇 초 만에 모든 테스트 완료
3. **CI/CD 통합**: GitHub Actions 등에서 API 키 없이 실행

### 통합 테스트 (Real API)의 목적
1. **실제 동작 확인**: Naver API와 실제로 통신되는지
2. **API 변경 감지**: Naver API가 변경되었는지
3. **최종 검증**: 배포 전 실제 환경에서 테스트

---

## 🧪 실제로 확인해보기

### Mock 테스트 실행 (API 키 불필요)

```bash
# 환경 변수 없이 실행
cd /home/runner/work/TrendOps/TrendOps
python -m pytest tests/test_naver_mcp_crawler.py -v -k "not Integration"

# 결과:
# ✅ 11 passed, 2 skipped in 0.09s
```

### 통합 테스트 실행 (API 키 필요)

```bash
# 환경 변수 설정
export X_NAVER_CLIENT_ID=your_client_id
export X_NAVER_CLIENT_SECRET=your_client_secret

# 전체 테스트 실행
python -m pytest tests/test_naver_mcp_crawler.py -v

# 결과:
# ✅ 13 passed in 2.5s (통합 테스트 포함)
```

---

## 📊 Mock vs Real API 비교표

| 항목 | Mock 테스트 | 실제 API 테스트 |
|------|-------------|----------------|
| **API 키 필요** | ❌ 불필요 | ✅ 필요 |
| **네트워크** | ❌ 불필요 | ✅ 필요 |
| **속도** | ⚡ 매우 빠름 (0.1초) | 🐢 느림 (1-2초) |
| **신뢰성** | ✅ 항상 성공 | ⚠️ API 상태에 따라 |
| **비용** | 💰 무료 (API 호출 없음) | 💰 API 할당량 소모 |
| **테스트 범위** | 코드 로직 | 실제 통합 |
| **CI/CD** | ✅ 쉬움 | ⚠️ Secret 관리 필요 |

---

## 🔧 Mock 테스트 작동 원리 상세

### 1. `@patch` 데코레이터

```python
@patch("crawling.naver_mcp_crawler.requests.get")
#      ↑ 이 경로의 함수를 Mock으로 대체
def test_function(mock_get):
    #                ↑ Mock 객체가 인자로 전달됨
```

### 2. Mock 객체 설정

```python
# Mock 응답 생성
mock_response = Mock()
mock_response.status_code = 200  # 상태 코드 설정
mock_response.json.return_value = {...}  # JSON 응답 설정

# requests.get()이 호출되면 이 Mock 반환
mock_get.return_value = mock_response
```

### 3. 실제 코드 실행

```python
# 우리 코드에서 requests.get() 호출
response = requests.get(url, headers=headers)

# ↑ 이것은 실제로 Mock 객체를 반환!
# 네트워크 호출 없음, API 키 불필요!

result = response.json()  # Mock에서 정의한 가짜 데이터 반환
```

### 4. 검증

```python
# Mock이 예상대로 호출되었는지 확인
mock_get.assert_called_once()
mock_get.assert_called_with(url, headers=headers, params=params)
```

---

## 💻 직접 실습해보기

### 실습 1: 간단한 Mock 예시

```python
# test_mock_example.py
from unittest.mock import Mock, patch
import requests

def fetch_data(url):
    """간단한 API 호출 함수"""
    response = requests.get(url)
    return response.json()

@patch("requests.get")
def test_fetch_data(mock_get):
    # Mock 설정
    mock_response = Mock()
    mock_response.json.return_value = {"data": "테스트"}
    mock_get.return_value = mock_response

    # 테스트
    result = fetch_data("https://api.example.com")

    # 검증
    assert result == {"data": "테스트"}
    print("✅ Mock 테스트 성공!")

# 실행
test_fetch_data()
```

### 실습 2: Naver MCP Mock 테스트

```python
# test_my_crawler.py
from unittest.mock import Mock, patch
from crawling.naver_mcp_crawler import NaverMCPCrawler

@patch("crawling.naver_mcp_crawler.requests.get")
def test_my_crawler(mock_get):
    # 가짜 뉴스 데이터
    fake_news = {
        "total": 1,
        "items": [
            {
                "title": "내가 만든 테스트 뉴스",
                "link": "https://test.com",
                "description": "이것은 Mock 테스트입니다",
                "pubDate": "2026-02-10"
            }
        ]
    }

    # Mock 설정
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_news
    mock_get.return_value = mock_response

    # 크롤러 실행 (API 키 없이!)
    crawler = NaverMCPCrawler(
        client_id="fake_id",
        client_secret="fake_secret"
    )

    result = crawler.search_news(query="테스트", display=1)

    # 검증
    assert result["total"] == 1
    assert result["items"][0]["title"] == "내가 만든 테스트 뉴스"
    print(f"✅ 테스트 성공! 뉴스 제목: {result['items'][0]['title']}")

# 실행
test_my_crawler()
```

---

## 🎓 핵심 정리

### Q1: Mock이 뭔가요?
**A**: 실제 객체를 흉내내는 가짜 객체입니다. API 호출 대신 미리 정의된 데이터를 반환합니다.

### Q2: 왜 Mock을 사용하나요?
**A**:
1. API 키 없이 테스트 가능
2. 빠른 실행 속도
3. 외부 서비스에 의존하지 않음
4. 예측 가능한 테스트

### Q3: Mock 테스트만으로 충분한가요?
**A**: 아니요! Mock 테스트로 **로직**을 검증하고, 통합 테스트로 **실제 동작**을 확인해야 합니다.

### Q4: 실제 API 키는 언제 필요한가요?
**A**:
- 통합 테스트를 실행할 때
- 실제 뉴스를 크롤링할 때
- 배포 전 최종 검증할 때

---

## 🚀 다음 단계

### 1. Mock 테스트 체험하기
```bash
cd /home/runner/work/TrendOps/TrendOps
python -m pytest tests/test_naver_mcp_crawler.py -v -k "not Integration"
```

### 2. 실제 API 키 발급받기
```bash
# https://developers.naver.com/ 방문
# 뉴스 검색 API 신청
# Client ID & Secret 발급
```

### 3. 통합 테스트 실행하기
```bash
export X_NAVER_CLIENT_ID=발급받은_ID
export X_NAVER_CLIENT_SECRET=발급받은_SECRET
python -m pytest tests/test_naver_mcp_crawler.py -v
```

---

## 📚 추가 자료

### Mock 관련 문서
- [Python unittest.mock 공식 문서](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-mock 플러그인](https://pytest-mock.readthedocs.io/)

### 관련 TrendOps 문서
- [테스트 가이드](README.md)
- [Naver MCP 통합 가이드](../docs/NAVER_MCP_INTEGRATION.md)

---

**작성일**: 2026-02-10
**버전**: 1.0
**작성자**: GitHub Copilot

---

## 🎉 결론

**API 키 없이도 테스트가 가능한 이유는 Mock 테스트를 사용했기 때문입니다!**

Mock은 실제 API를 호출하지 않고도 코드의 로직을 검증할 수 있게 해주는 강력한 도구입니다.
TrendOps 프로젝트의 11개 단위 테스트는 모두 Mock을 사용하여 API 키 없이도 실행됩니다.

실제 API 키는 통합 테스트나 실제 뉴스 크롤링을 할 때만 필요합니다! 🎊
