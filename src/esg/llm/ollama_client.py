"""LLM客户端模块

提供与本地大模型服务(Ollama)的交互功能。
支持文本生成、结构化提取等通用LLM接口。

后期切换API：只需在llm/base.py中修改get_llm_client()返回kimi_client
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

import requests

# 配置日志
logger = logging.getLogger(__name__)


class LLMError(Exception):
    """LLM客户端基础异常"""

    pass


class LLMConnectionError(LLMError):
    """连接异常"""

    pass


class LLMTimeoutError(LLMError):
    """超时异常"""

    pass


class LLMResponseError(LLMError):
    """响应异常"""

    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

    def __str__(self) -> str:
        msg = super().__str__()
        if self.status_code is not None:
            msg = f"[{self.status_code}] {msg}"
        return msg


# ============================================================================
# LLM抽象基类
# ============================================================================


class LLMClient(ABC):
    """LLM客户端抽象基类

    定义LLM交互的标准接口，支持不同的LLM后端实现。
    后期切换API只需实现此接口。
    """

    @abstractmethod
    def generate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048, **options
    ) -> str:
        """通用文本生成接口

        Args:
            prompt: 提示词
            temperature: 温度参数，控制随机性（0.0-1.0）
            max_tokens: 最大生成token数
            **options: 额外的生成选项

        Returns:
            生成的文本内容
        """
        pass

    @abstractmethod
    def extract_structured(
        self, prompt: str, schema: Dict[str, Any], temperature: float = 0.3, **options
    ) -> Dict[str, Any]:
        """结构化提取接口

        从文本中提取结构化数据。

        Args:
            prompt: 提示词
            schema: 输出结构定义
            temperature: 温度参数
            **options: 额外的生成选项

        Returns:
            结构化数据字典
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **options,
    ) -> str:
        """对话接口

        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **options: 额外的生成选项

        Returns:
            助手的回复内容
        """
        pass

    @abstractmethod
    def check(self) -> bool:
        """检查服务状态"""
        pass

    @abstractmethod
    def close(self):
        """关闭客户端，释放资源"""
        pass


# ============================================================================
# Ollama实现
# ============================================================================


class OllamaClient(LLMClient):
    """Ollama HTTP客户端

    用于与Ollama本地大模型服务进行交互。
    支持文本生成、对话和结构化提取功能。

    配置项:
        model_name: 模型名称
        temperature: 默认温度
        max_tokens: 默认最大token数
    """

    DEFAULT_TIMEOUT = 120
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0

    def __init__(
        self,
        model_name: str = "llama2",
        url: str = "http://localhost:11434",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """初始化Ollama客户端

        Args:
            model_name: 模型名称，如 "llama2", "mistral" 等
            url: Ollama服务的基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            temperature: 默认温度参数
            max_tokens: 默认最大token数
        """
        self.model_name = model_name
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 创建会话对象以支持连接池
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        # 适配器配置（连接池）
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=0)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.debug(f"OllamaClient 初始化完成: url={url}, model={model_name}")

    def _make_request(
        self, method: str, endpoint: str, json_data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        """发送HTTP请求（带重试机制）"""
        url = f"{self.url}{endpoint}"
        delay = self.retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method, url=url, json=json_data, timeout=self.timeout, **kwargs
                )

                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f": {error_detail}"
                    except Exception:
                        error_msg += f": {response.text[:200]}"

                    if response.status_code in (400, 401, 403, 404):
                        raise LLMResponseError(
                            error_msg, status_code=response.status_code, response_text=response.text
                        )

                    response.raise_for_status()

                return response.json()

            except requests.Timeout as e:
                last_exception = LLMTimeoutError(f"请求超时（{self.timeout}秒）: {e}")
                logger.warning(f"请求超时，第 {attempt + 1} 次尝试")

            except requests.ConnectionError as e:
                last_exception = LLMConnectionError(f"连接失败: {e}")
                logger.warning(f"连接失败，第 {attempt + 1} 次尝试")

            except requests.HTTPError as e:
                last_exception = LLMResponseError(f"HTTP错误: {e}")
                logger.warning(f"HTTP错误，第 {attempt + 1} 次尝试")

            except requests.RequestException as e:
                last_exception = LLMConnectionError(f"请求异常: {e}")
                logger.warning(f"请求异常，第 {attempt + 1} 次尝试")

            if attempt < self.max_retries:
                wait_time = min(delay * (2**attempt), 30)
                logger.info(f"{wait_time}秒后重试...")
                time.sleep(wait_time)

        logger.error(f"在 {self.max_retries} 次重试后仍然失败")
        raise last_exception

    def generate(
        self, prompt: str, temperature: float = None, max_tokens: int = None, **options
    ) -> str:
        """通用文本生成接口

        Args:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大生成token数
            **options: 额外的生成选项

        Returns:
            生成的文本内容
        """
        if not self.model_name:
            raise ValueError("必须先指定模型名称才能生成文本")

        if not prompt:
            logger.warning("输入提示词为空")
            return ""

        # 使用默认值
        if temperature is None:
            temperature = self.temperature
        if max_tokens is None:
            max_tokens = self.max_tokens

        # 过滤options中的None值
        options = {k: v for k, v in options.items() if v is not None}
        options["temperature"] = temperature
        options["num_predict"] = max_tokens

        try:
            result = self._make_request(
                "POST",
                "/api/generate",
                {"model": self.model_name, "prompt": prompt, "stream": False, "options": options},
            )

            response = result.get("response")
            if response is None:
                raise LLMResponseError("响应中缺少 response 字段")

            logger.debug(f"成功生成文本，长度: {len(response)}")
            return response

        except LLMError:
            raise
        except Exception as e:
            logger.error(f"生成文本时发生未知错误: {e}")
            raise LLMError(f"生成文本失败: {e}")

    def extract_structured(
        self, prompt: str, schema: Dict[str, Any], temperature: float = None, **options
    ) -> Dict[str, Any]:
        """结构化提取接口

        从文本中提取结构化数据。

        Args:
            prompt: 提示词
            schema: 输出结构定义
            temperature: 温度参数
            **options: 额外的生成选项

        Returns:
            结构化数据字典
        """
        if temperature is None:
            temperature = 0.3  # 低温度更适合结构化提取

        # 构建结构化提取提示
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        structured_prompt = f"""请从以下文本中提取结构化信息，并以JSON格式输出。

输出格式要求：
{schema_str}

需要提取的文本：
{prompt}

请直接输出JSON，不要包含其他内容："""

        try:
            result = self.generate(
                prompt=structured_prompt, temperature=temperature, max_tokens=4096, **options
            )

            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]

            return json.loads(result.strip())

        except json.JSONDecodeError as e:
            logger.error(f"结构化提取JSON解析失败: {e}")
            raise LLMError(f"结构化提取失败: {e}")
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"结构化提取时发生未知错误: {e}")
            raise LLMError(f"结构化提取失败: {e}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        **options,
    ) -> str:
        """对话接口

        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            **options: 额外的生成选项

        Returns:
            助手的回复内容
        """
        if not self.model_name:
            raise ValueError("必须先指定模型名称才能进行对话")

        if not messages:
            raise ValueError("消息列表不能为空")

        # 验证消息格式
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"第 {i} 条消息必须是字典类型")
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"第 {i} 条消息必须包含 'role' 和 'content' 字段")
            if msg["role"] not in ("system", "user", "assistant"):
                raise ValueError(f"第 {i} 条消息的 'role' 必须是 system/user/assistant 之一")

        if temperature is None:
            temperature = self.temperature
        if max_tokens is None:
            max_tokens = self.max_tokens

        # 过滤options中的None值
        options = {k: v for k, v in options.items() if v is not None}
        options["temperature"] = temperature

        try:
            result = self._make_request(
                "POST",
                "/api/chat",
                {
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": options,
                },
            )

            message = result.get("message", {})
            content = message.get("content")

            if content is None:
                raise LLMResponseError("响应中缺少 message.content 字段")

            logger.debug(f"成功获取对话回复，长度: {len(content)}")
            return content

        except LLMError:
            raise
        except Exception as e:
            logger.error(f"对话时发生未知错误: {e}")
            raise LLMError(f"对话失败: {e}")

    def check(self) -> bool:
        """检查Ollama服务状态"""
        try:
            response = self.session.get(self.url, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.debug(f"健康检查失败: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if not self.model_name:
            raise ValueError("必须先指定模型名称")

        try:
            result = self._make_request("POST", "/api/show", {"name": self.model_name})
            return result
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"获取模型信息时发生错误: {e}")
            raise LLMError(f"获取模型信息失败: {e}")

    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有可用模型"""
        try:
            result = self._make_request("GET", "/api/tags")
            return result.get("models", [])
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"列出模型时发生错误: {e}")
            raise LLMError(f"列出模型失败: {e}")

    def close(self):
        """关闭客户端，释放资源"""
        if hasattr(self, "session"):
            self.session.close()
            logger.debug("OllamaClient 会话已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
