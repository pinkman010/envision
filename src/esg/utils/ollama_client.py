"""Ollama HTTP 客户端模块

提供与 Ollama 本地大模型服务的交互功能，包括文本向量化、文本生成、对话等功能。
支持自动重试、连接池、健康检查等高级特性。
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import requests

# 配置日志
logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Ollama客户端基础异常"""

    pass


class OllamaConnectionError(OllamaError):
    """连接异常"""

    pass


class OllamaTimeoutError(OllamaError):
    """超时异常"""

    pass


class OllamaResponseError(OllamaError):
    """响应异常"""

    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

    def __str__(self) -> str:
        """返回包含状态码的错误信息"""
        msg = super().__str__()
        if self.status_code is not None:
            msg = f"[{self.status_code}] {msg}"
        return msg


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),  # 默认捕获所有异常
):
    """带指数退避的重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        backoff_factor: 退避因子
        exceptions: 需要捕获重试的异常类型（默认捕获所有Exception）
    """

    def decorator(func: Callable) -> Callable:
        """重试装饰器工厂函数

        为指定函数添加指数退避重试机制的装饰器。

        Args:
            func: 需要被装饰的函数

        Returns:
            包装后的函数，具有重试能力

        Raises:
            最后一次捕获的异常，当所有重试都失败时抛出
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """带重试机制的包装函数

            执行被装饰的函数，并在失败时根据配置进行重试。
            使用指数退避策略增加重试间隔时间。

            Args:
                *args: 被装饰函数的位置参数
                **kwargs: 被装饰函数的关键字参数

            Returns:
                被装饰函数的返回值

            Raises:
                exceptions: 当所有重试都失败后，抛出最后一次捕获的异常
            """
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} 在 {max_retries} 次重试后失败: {e}")
                        raise

                    logger.warning(
                        f"{func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{delay}秒后重试..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exception

        return wrapper

    return decorator


class OllamaClient:
    """Ollama HTTP 客户端

    用于与 Ollama 本地大模型服务进行交互，支持嵌入向量生成、
    文本生成和对话功能。支持自动重试、连接池、健康检查等特性。

    Attributes:
        model: 使用的模型名称
        url: Ollama 服务的基础 URL
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        session: requests会话对象（连接池）

    Example:
        >>> client = OllamaClient(model="llama2", url="http://localhost:11434")
        >>> embedding = client.embed("这是一个测试文本")
        >>> response = client.generate("你好，请介绍一下自己")
    """

    DEFAULT_TIMEOUT = 120
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0

    def __init__(
        self,
        model: Optional[str] = None,
        url: str = "http://localhost:11434",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """初始化 Ollama 客户端

        Args:
            model: 模型名称，如 "llama2", "mistral" 等
            url: Ollama 服务的基础 URL，默认为 "http://localhost:11434"
            timeout: 请求超时时间（秒），默认为 120
            max_retries: 最大重试次数，默认为 3
            retry_delay: 重试延迟（秒），默认为 1.0
        """
        self.model = model
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 创建会话对象以支持连接池
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        # 适配器配置（连接池）
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10, pool_maxsize=20, max_retries=0  # 我们使用自定义重试逻辑
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.debug(f"OllamaClient 初始化完成: url={url}, model={model}")

    def _make_request(
        self, method: str, endpoint: str, json_data: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        """发送HTTP请求（带重试机制）

        Args:
            method: HTTP方法
            endpoint: API端点
            json_data: JSON数据
            **kwargs: 额外的请求参数

        Returns:
            JSON响应数据

        Raises:
            OllamaConnectionError: 连接失败
            OllamaTimeoutError: 请求超时
            OllamaResponseError: 响应错误
        """
        url = f"{self.url}{endpoint}"
        delay = self.retry_delay
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method, url=url, json=json_data, timeout=self.timeout, **kwargs
                )

                # 处理HTTP错误状态码
                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f": {error_detail}"
                    except Exception:
                        error_msg += f": {response.text[:200]}"

                    # 某些错误不应该重试（如400 Bad Request）
                    if response.status_code in (400, 401, 403, 404):
                        raise OllamaResponseError(
                            error_msg, status_code=response.status_code, response_text=response.text
                        )

                    response.raise_for_status()

                return response.json()

            except requests.Timeout as e:
                last_exception = OllamaTimeoutError(f"请求超时（{self.timeout}秒）: {e}")
                logger.warning(f"请求超时，第 {attempt + 1} 次尝试")

            except requests.ConnectionError as e:
                last_exception = OllamaConnectionError(f"连接失败: {e}")
                logger.warning(f"连接失败，第 {attempt + 1} 次尝试")

            except requests.HTTPError as e:
                last_exception = OllamaResponseError(f"HTTP错误: {e}")
                logger.warning(f"HTTP错误，第 {attempt + 1} 次尝试")

            except requests.RequestException as e:
                last_exception = OllamaConnectionError(f"请求异常: {e}")
                logger.warning(f"请求异常，第 {attempt + 1} 次尝试")

            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.max_retries:
                wait_time = min(delay * (2**attempt), 30)  # 指数退避，最大30秒
                logger.info(f"{wait_time}秒后重试...")
                time.sleep(wait_time)

        # 所有重试都失败了
        logger.error(f"在 {self.max_retries} 次重试后仍然失败")
        raise last_exception

    def embed(self, text: str) -> List[float]:
        """将文本转换为向量嵌入

        调用 Ollama 的 embeddings API 将文本转换为高维向量。

        Args:
            text: 需要向量化的文本

        Returns:
            文本的向量表示（浮点数列表）

        Raises:
            OllamaError: 当请求失败时抛出
            ValueError: 当模型未指定时抛出

        Example:
            >>> client = OllamaClient(model="nomic-embed-text")
            >>> embedding = client.embed("这是一个测试文本")
            >>> print(len(embedding))  # 输出向量维度
        """
        if not self.model:
            raise ValueError("必须先指定模型名称才能生成嵌入向量")

        if not text or not text.strip():
            logger.warning("输入文本为空，返回零向量")
            return [0.0] * 768  # 假设默认维度为768

        try:
            result = self._make_request(
                "POST", "/api/embeddings", {"model": self.model, "prompt": text}
            )

            embedding = result.get("embedding")
            if not embedding:
                raise OllamaResponseError("响应中缺少 embedding 字段")

            logger.debug(f"成功生成嵌入向量，维度: {len(embedding)}")
            return embedding

        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"生成嵌入向量时发生未知错误: {e}")
            raise OllamaError(f"生成嵌入向量失败: {e}")

    def generate(self, prompt: str, **options) -> str:
        """生成文本

        调用 Ollama 的 generate API 根据提示词生成文本。

        Args:
            prompt: 提示词/输入文本
            **options: 额外的生成选项，如 temperature, top_p 等
                - temperature: 温度参数，控制随机性（0.0-1.0）
                - top_p: 核采样参数（0.0-1.0）
                - max_tokens: 最大生成 token 数

        Returns:
            生成的文本内容

        Raises:
            OllamaError: 当请求失败时抛出
            ValueError: 当模型未指定时抛出

        Example:
            >>> client = OllamaClient(model="llama2")
            >>> response = client.generate("你好", temperature=0.7)
            >>> print(response)
        """
        if not self.model:
            raise ValueError("必须先指定模型名称才能生成文本")

        if not prompt:
            logger.warning("输入提示词为空")
            return ""

        # 过滤options中的None值
        options = {k: v for k, v in options.items() if v is not None}

        try:
            result = self._make_request(
                "POST",
                "/api/generate",
                {"model": self.model, "prompt": prompt, "stream": False, "options": options},
            )

            response = result.get("response")
            if response is None:
                raise OllamaResponseError("响应中缺少 response 字段")

            logger.debug(f"成功生成文本，长度: {len(response)}")
            return response

        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"生成文本时发生未知错误: {e}")
            raise OllamaError(f"生成文本失败: {e}")

    def chat(self, messages: List[Dict[str, str]], **options) -> str:
        """进行对话

        调用 Ollama 的 chat API 进行多轮对话。

        Args:
            messages: 对话消息列表，每个消息是一个字典，包含 role 和 content
                role 可以是 "system", "user", "assistant"
                例如: [{"role": "user", "content": "你好"}]
            **options: 额外的生成选项，如 temperature, top_p 等

        Returns:
            助手的回复内容

        Raises:
            OllamaError: 当请求失败时抛出
            ValueError: 当模型未指定或消息格式不正确时抛出

        Example:
            >>> client = OllamaClient(model="llama2")
            >>> messages = [
            ...     {"role": "system", "content": "你是一个有用的助手"},
            ...     {"role": "user", "content": "你好"}
            ... ]
            >>> response = client.chat(messages, temperature=0.7)
            >>> print(response)
        """
        if not self.model:
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

        # 过滤options中的None值
        options = {k: v for k, v in options.items() if v is not None}

        try:
            result = self._make_request(
                "POST",
                "/api/chat",
                {"model": self.model, "messages": messages, "stream": False, "options": options},
            )

            message = result.get("message", {})
            content = message.get("content")

            if content is None:
                raise OllamaResponseError("响应中缺少 message.content 字段")

            logger.debug(f"成功获取对话回复，长度: {len(content)}")
            return content

        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"对话时发生未知错误: {e}")
            raise OllamaError(f"对话失败: {e}")

    def check(self) -> bool:
        """检查 Ollama 服务状态

        发送一个简单的 HTTP 请求检查 Ollama 服务是否可用。

        Returns:
            如果服务可用返回 True，否则返回 False

        Example:
            >>> client = OllamaClient()
            >>> if client.check():
            ...     print("Ollama 服务运行正常")
            ... else:
            ...     print("Ollama 服务不可用")
        """
        try:
            response = self.session.get(self.url, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.debug(f"健康检查失败: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息

        Returns:
            模型信息字典

        Raises:
            OllamaError: 当请求失败时抛出
        """
        if not self.model:
            raise ValueError("必须先指定模型名称")

        try:
            result = self._make_request("POST", "/api/show", {"name": self.model})
            return result
        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"获取模型信息时发生错误: {e}")
            raise OllamaError(f"获取模型信息失败: {e}")

    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有可用模型

        Returns:
            模型列表

        Raises:
            OllamaError: 当请求失败时抛出
        """
        try:
            result = self._make_request("GET", "/api/tags")
            return result.get("models", [])
        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"列出模型时发生错误: {e}")
            raise OllamaError(f"列出模型失败: {e}")

    def close(self):
        """关闭客户端，释放资源"""
        if hasattr(self, "session"):
            self.session.close()
            logger.debug("OllamaClient 会话已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False
