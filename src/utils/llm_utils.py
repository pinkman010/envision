"""
大模型API统一封装：仅保留网络层重试、token管控，无任何业务逻辑
AI仅做工具调用，不做专业判断
"""

import time
import re
from typing import Any, Dict, List, Optional

from src.config.settings import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_MAX_RETRIES,
    LLM_RETRY_DELAY,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT,
    LLM_THINKING_DISABLED,
    LLM_THINKING_TYPE,
    LLM_REASONING_EFFORT,
    LLM_RESPONSE_FORMAT,
)
from src.utils.exception_utils import LLMCallException
from src.config import get_logger

logger = get_logger(__name__)

_client = None


def _get_client():
    """延迟初始化OpenAI客户端"""
    global _client
    if _client is None:
        try:
            from openai import OpenAI
            _client = OpenAI(
                api_key=LLM_API_KEY,
                base_url=LLM_BASE_URL,
            )
        except ImportError:
            raise LLMCallException("未安装openai库")
    return _client


def _build_chat_completion_params(
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> Dict[str, Any]:
    api_params: Dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "timeout": timeout,
    }

    thinking_type = LLM_THINKING_TYPE
    if LLM_THINKING_DISABLED:
        thinking_type = "disabled"

    if thinking_type == "enabled":
        api_params["reasoning_effort"] = LLM_REASONING_EFFORT
        api_params["extra_body"] = {"thinking": {"type": "enabled"}}
    else:
        api_params["temperature"] = temperature
        api_params["extra_body"] = {"thinking": {"type": "disabled"}}

    if LLM_RESPONSE_FORMAT == "json_object":
        api_params["response_format"] = {"type": "json_object"}

    return api_params


def _usage_to_dict(usage: Any) -> Dict[str, Any]:
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if isinstance(usage, dict):
        return usage

    result: Dict[str, Any] = {}
    for key in [
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "prompt_cache_hit_tokens",
        "prompt_cache_miss_tokens",
    ]:
        value = getattr(usage, key, None)
        if value is not None:
            result[key] = value

    details = getattr(usage, "completion_tokens_details", None)
    if details is not None:
        if hasattr(details, "model_dump"):
            result["completion_tokens_details"] = details.model_dump()
        else:
            reasoning_tokens = getattr(details, "reasoning_tokens", None)
            if reasoning_tokens is not None:
                result["completion_tokens_details"] = {"reasoning_tokens": reasoning_tokens}
    return result


def _extract_response_content(message: Any) -> Optional[str]:
    content = getattr(message, "content", None)
    if content is not None and content.strip():
        return content.strip()

    reasoning_content = getattr(message, "reasoning_content", None)
    if reasoning_content and reasoning_content.strip():
        json_match = re.search(r"\{.*\}", reasoning_content, re.DOTALL)
        if json_match:
            return json_match.group(0)
    return None


def _is_retryable_exception(exc: Exception) -> bool:
    return type(exc).__name__ in [
        "APIConnectionError",
        "RateLimitError",
        "APITimeoutError",
        "Timeout",
        "TimeoutError",
    ]


def call_llm_with_metadata(
    messages: List[Dict[str, str]],
    temperature: float = None,
    max_tokens: int = None,
    timeout: int = None,
) -> Dict[str, Any]:
    """
    调用 LLM 并返回 text + metadata，供 Stage E 保存 usage 与 finish_reason。
    """
    if temperature is None:
        temperature = LLM_TEMPERATURE
    if max_tokens is None:
        max_tokens = LLM_MAX_TOKENS
    if timeout is None:
        timeout = LLM_TIMEOUT

    if not LLM_API_KEY:
        raise LLMCallException("未配置LLM_API_KEY")

    client = _get_client()
    last_exception: Optional[Exception] = None

    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            api_params = _build_chat_completion_params(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )

            response = client.chat.completions.create(**api_params)

            if not response.choices or len(response.choices) == 0:
                last_exception = LLMCallException("大模型返回空choices")
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(LLM_RETRY_DELAY * attempt)
                continue

            choice = response.choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason == "length":
                last_exception = LLMCallException("大模型输出因 length 截断")
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(LLM_RETRY_DELAY * attempt)
                continue

            content = _extract_response_content(choice.message)
            if content:
                thinking_type = "disabled" if LLM_THINKING_DISABLED else LLM_THINKING_TYPE
                return {
                    "content": content,
                    "metadata": {
                        "model": LLM_MODEL,
                        "base_url": LLM_BASE_URL,
                        "thinking_type": thinking_type,
                        "reasoning_effort": LLM_REASONING_EFFORT if thinking_type == "enabled" else None,
                        "response_format": LLM_RESPONSE_FORMAT or None,
                        "finish_reason": finish_reason,
                        "usage": _usage_to_dict(getattr(response, "usage", None)),
                    },
                }

            last_exception = LLMCallException("大模型返回空内容")
            if attempt < LLM_MAX_RETRIES:
                time.sleep(LLM_RETRY_DELAY * attempt)
            continue

        except Exception as e:
            exc_name = type(e).__name__
            logger.error(f"LLM调用失败: {exc_name}: {str(e)}")

            if _is_retryable_exception(e):
                last_exception = e
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(LLM_RETRY_DELAY * attempt)
                continue

            raise LLMCallException(f"大模型调用失败: {str(e)}") from e

    if last_exception is not None:
        raise LLMCallException(f"重试{LLM_MAX_RETRIES}次后仍失败: {str(last_exception)}") from last_exception
    raise LLMCallException(f"重试{LLM_MAX_RETRIES}次后仍失败")


def call_llm(
    messages: List[Dict[str, str]],
    temperature: float = None,
    max_tokens: int = None,
    timeout: int = None,
) -> str:
    """
    统一大模型调用接口
    :param messages: 对话消息列表
    :param temperature: 温度参数
    :param max_tokens: 最大输出token数
    :param timeout: 超时时间
    :return: 大模型输出文本
    """
    result = call_llm_with_metadata(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return result["content"]
