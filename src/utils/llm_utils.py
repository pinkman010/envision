"""
大模型API统一封装：仅保留网络层重试、token管控，无任何业务逻辑
AI仅做工具调用，不做专业判断
"""

import time
from typing import Dict, List, Optional

from src.core_config.settings import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_MAX_RETRIES,
    LLM_RETRY_DELAY,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT,
    LLM_THINKING_DISABLED,
)
from src.utils.exception_utils import LLMCallException
from src.core_config import get_logger

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
    if temperature is None:
        temperature = LLM_TEMPERATURE
    if max_tokens is None:
        max_tokens = LLM_MAX_TOKENS
    if timeout is None:
        timeout = LLM_TIMEOUT
    
    if not LLM_API_KEY:
        raise LLMCallException("未配置LLM_API_KEY")
    
    client = _get_client()
    last_exception = None
    
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            api_params = {
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": timeout,
            }
            
            if LLM_THINKING_DISABLED:
                api_params["extra_body"] = {"thinking": {"type": "disabled"}}
            
            response = client.chat.completions.create(**api_params)
            
            if not response.choices or len(response.choices) == 0:
                last_exception = LLMCallException("大模型返回空choices")
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(LLM_RETRY_DELAY * attempt)
                continue
            
            message = response.choices[0].message
            content = message.content
            reasoning_content = getattr(message, 'reasoning_content', None)

            if content is not None and content.strip():
                return content.strip()

            if reasoning_content and reasoning_content.strip():
                import re
                json_match = re.search(r'\{.*\}', reasoning_content, re.DOTALL)
                if json_match:
                    return json_match.group(0)
                return reasoning_content.strip()

            last_exception = LLMCallException("大模型返回空内容")
            if attempt < LLM_MAX_RETRIES:
                time.sleep(LLM_RETRY_DELAY * attempt)
            continue
        
        except Exception as e:
            exc_name = type(e).__name__
            logger.error(f"LLM调用失败: {exc_name}: {str(e)}")
            
            if exc_name in ["APIConnectionError", "RateLimitError", "APITimeoutError", "Timeout"]:
                last_exception = e
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(LLM_RETRY_DELAY * attempt)
                continue
            
            raise LLMCallException(f"大模型调用失败: {str(e)}") from e
    
    raise LLMCallException(f"重试{LLM_MAX_RETRIES}次后仍失败")
