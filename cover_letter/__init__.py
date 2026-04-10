"""자소서 자동화 서비스 패키지.

이 모듈이 임포트될 때 필수 API Key가 설정되어 있는지 검증합니다.
"""

import os

_REQUIRED_KEYS: list[str] = [
    "GEMINI_API_KEY",
    "DART_API_KEY",
    "FIRECRAWL_API_KEY",
]

for _key in _REQUIRED_KEYS:
    if not os.getenv(_key):
        raise RuntimeError(
            f"{_key} 환경변수가 설정되지 않았습니다. 서비스를 시작할 수 없습니다.\n"
            f".env 파일 또는 환경변수에 {_key}를 설정한 후 다시 시도하세요."
        )
