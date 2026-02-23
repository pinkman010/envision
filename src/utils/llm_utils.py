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
)
from src.utils.exception_utils import LLMCallException
from src.core_config import get_logger

logger = get_logger(__name__)


# 初始化OpenAI客户端（兼容所有兼容OpenAI格式的模型）
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
            raise LLMCallException("未安装openai库，请执行: pip install openai")
    return _client


def call_llm(
    messages: List[Dict[str, str]],
    temperature: float = None,  # 默认使用配置文件中的LLM_TEMPERATURE
    max_tokens: int = None,  # 默认使用配置文件中的LLM_MAX_TOKENS
    timeout: int = None,  # 默认使用配置文件中的LLM_TIMEOUT
) -> str:
    """
    统一大模型调用接口，仅保留网络层重试
    :param messages: 对话消息列表
    :param temperature: 温度参数（默认使用配置文件中的LLM_TEMPERATURE）
    :param max_tokens: 最大输出token数（默认使用配置文件中的LLM_MAX_TOKENS）
    :param timeout: 超时时间（秒，默认使用配置文件中的LLM_TIMEOUT）
    :return: 大模型输出文本
    :raises LLMCallException: 调用失败时抛出统一异常
    """
    # 使用配置文件中的参数
    if temperature is None:
        temperature = LLM_TEMPERATURE
    if max_tokens is None:
        max_tokens = LLM_MAX_TOKENS
    if timeout is None:
        timeout = LLM_TIMEOUT
    # 检查API密钥
    if not LLM_API_KEY:
        raise LLMCallException("未配置LLM_API_KEY，请在.env文件中设置")
    
    client = _get_client()
    last_exception = None
    
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            
            # 检查响应是否有效
            if not response.choices or len(response.choices) == 0:
                logger.warning(f"[第{attempt}次尝试] 大模型返回空choices，准备重试...")
                last_exception = LLMCallException("大模型返回空choices")
                if attempt < LLM_MAX_RETRIES:
                    time.sleep(LLM_RETRY_DELAY * attempt)
                continue
            
            message = response.choices[0].message
            content = message.content
            
            # 检查是否有reasoning_content（推理模型如kimi-k2.5, DeepSeek-R1等）
            reasoning_content = getattr(message, 'reasoning_content', None)

            # 推理模型：content 是最终答案，reasoning_content 是思考过程
            # 优先使用 content（最终答案），仅当 content 为空时尝试从 reasoning_content 提取
            if content is not None and content.strip():
                if reasoning_content:
                    logger.debug(f"推理模型返回: content长度={len(content)}, reasoning长度={len(reasoning_content)}")
                return content.strip()

            # content为空，尝试从reasoning_content中提取有用内容
            if reasoning_content and reasoning_content.strip():
                logger.warning(
                    f"[第{attempt}次尝试] 推理模型content为空，尝试从reasoning_content提取 "
                    f"(reasoning长度={len(reasoning_content)})"
                )
                # 尝试从思考过程中提取JSON（推理模型有时把最终结果混在思考过程里）
                import re
                json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\})*)*\})*)*\}', reasoning_content, re.DOTALL)
                if json_match:
                    logger.info("从reasoning_content中提取到JSON片段")
                    return json_match.group(0)
                # 没有JSON就返回原文（可能是非JSON场景的调用）
                logger.info("reasoning_content中无JSON，返回reasoning_content原文")
                return reasoning_content.strip()

            # 两个字段都为空，重试
            logger.warning(f"[第{attempt}次尝试] 大模型返回空内容(content和reasoning_content均为空)，准备重试...")
            last_exception = LLMCallException("大模型返回空内容")
            if attempt < LLM_MAX_RETRIES:
                time.sleep(LLM_RETRY_DELAY * attempt)
            continue
        
        except Exception as e:
            # 获取异常类型
            exc_name = type(e).__name__
            
            # 记录详细错误信息
            error_msg = f"[第{attempt}次尝试] LLM调用失败: {exc_name}: {str(e)}"
            logger.error(error_msg)
            
            # 尝试获取更详细的错误信息（HTTP状态码、响应内容）
            try:
                if hasattr(e, 'status_code'):
                    logger.error(f"  HTTP状态码: {e.status_code}")
                if hasattr(e, 'response'):
                    response_body = e.response.text if hasattr(e.response, 'text') else str(e.response)
                    logger.error(f"  响应内容: {response_body[:500]}")  # 只打印前500字符
                if hasattr(e, 'body'):
                    logger.error(f"  错误详情: {e.body}")
            except Exception as log_e:
                logger.error(f"  解析错误详情失败: {log_e}")
            
            # 打印当前配置（脱敏）
            key_preview = LLM_API_KEY[:8] + "..." if LLM_API_KEY and len(LLM_API_KEY) > 8 else "未设置"
            logger.error(f"  当前配置: BASE_URL={LLM_BASE_URL}, MODEL={LLM_MODEL}, KEY={key_preview}")
            
            # 网络层异常：自动重试
            if exc_name in ["APIConnectionError", "RateLimitError", "APITimeoutError", "Timeout"]:
                last_exception = e
                if attempt < LLM_MAX_RETRIES:
                    logger.warning(f"  网络异常，{LLM_RETRY_DELAY * attempt}秒后重试...")
                    time.sleep(LLM_RETRY_DELAY * attempt)  # 指数退避
                continue
            
            # 模型层异常：不重试，直接抛出
            raise LLMCallException(f"大模型调用失败: {str(e)}", original_exception=e) from e
    
    # 重试次数耗尽
    logger.error(f"LLM调用重试{LLM_MAX_RETRIES}次后仍失败，最后一次错误: {last_exception}")
    raise LLMCallException(
        f"大模型调用重试{LLM_MAX_RETRIES}次后仍失败",
        original_exception=last_exception,
    )
