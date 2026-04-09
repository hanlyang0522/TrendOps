"""Gemini LLM 클라이언트 — 3단계 티어 라우팅.

Tier 전략:
  flash       → GEMINI_FLASH_MODEL (수집/요약/매핑, 저비용)
  pro         → GEMINI_PRO_MODEL   (초안/전략, 중비용)
  pro-thinking → GEMINI_PRO_MODEL + thinking mode (자가진단/마무리, 고비용)
"""

import os
from typing import Literal

Tier = Literal["flash", "pro", "pro-thinking"]

_FLASH_DEFAULT = "gemini-2.5-flash"
_PRO_DEFAULT = "gemini-2.5-pro"

_TIER_TEMPERATURE: dict[str, float] = {
    "flash": 0.3,
    "pro": 0.7,
    "pro-thinking": 1.0,
}


def _get_client():  # type: ignore[return]
    """google-genai Client 인스턴스 반환."""
    try:
        from google import genai  # type: ignore[import-untyped]
    except ImportError as e:
        raise RuntimeError(
            "google-genai 패키지가 설치되어 있지 않습니다. "
            "`pip install google-genai`를 실행하세요."
        ) from e

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

    return genai.Client(api_key=api_key)


def call(
    prompt: str,
    tier: Tier = "flash",
    system: str = "",
    temperature: float | None = None,
) -> str:
    """Gemini 모델 호출. tier에 따라 모델 자동 선택.

    Args:
        prompt: 사용자 프롬프트 (user turn)
        tier: 'flash' | 'pro' | 'pro-thinking'
        system: 시스템 프롬프트 (선택)
        temperature: 미지정 시 tier 기본값 사용

    Returns:
        모델 응답 텍스트

    Raises:
        RuntimeError: API 호출 실패 또는 빈 응답
    """
    try:
        from google.genai import types  # type: ignore[import-untyped]
    except ImportError as e:
        raise RuntimeError("google-genai 패키지가 설치되어 있지 않습니다.") from e

    if tier == "flash":
        model_name = os.getenv("GEMINI_FLASH_MODEL", _FLASH_DEFAULT)
    else:
        model_name = os.getenv("GEMINI_PRO_MODEL", _PRO_DEFAULT)

    temp = temperature if temperature is not None else _TIER_TEMPERATURE[tier]

    client = _get_client()

    config_kwargs: dict = {"temperature": temp}

    if tier == "pro-thinking":
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=8192,
        )

    if system:
        config_kwargs["system_instruction"] = system

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API 호출 실패 ({tier}/{model_name}): {e}") from e

    text = response.text
    if not text:
        raise RuntimeError(
            f"Gemini API가 빈 응답을 반환했습니다 ({tier}/{model_name})."
        )

    return str(text)
