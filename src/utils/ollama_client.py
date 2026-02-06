"""Ollama HTTP 客户端模块

提供与 Ollama 本地大模型服务的交互功能，包括文本向量化、文本生成、对话等功能。
"""

import requests
from typing import List, Optional, Dict, Any, Union


class OllamaClient:
    """Ollama HTTP 客户端
    
    用于与 Ollama 本地大模型服务进行交互，支持嵌入向量生成、
    文本生成和对话功能。
    
    Attributes:
        model: 使用的模型名称
        url: Ollama 服务的基础 URL
        timeout: 请求超时时间（秒）
    
    Example:
        >>> client = OllamaClient(model="llama2", url="http://localhost:11434")
        >>> embedding = client.embed("这是一个测试文本")
        >>> response = client.generate("你好，请介绍一下自己")
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        url: str = "http://localhost:11434",
        timeout: int = 120
    ):
        """初始化 Ollama 客户端
        
        Args:
            model: 模型名称，如 "llama2", "mistral" 等
            url: Ollama 服务的基础 URL，默认为 "http://localhost:11434"
            timeout: 请求超时时间（秒），默认为 120
        """
        self.model = model
        self.url = url.rstrip("/")
        self.timeout = timeout
    
    def embed(self, text: str) -> List[float]:
        """将文本转换为向量嵌入
        
        调用 Ollama 的 embeddings API 将文本转换为高维向量。
        
        Args:
            text: 需要向量化的文本
            
        Returns:
            文本的向量表示（浮点数列表）
            
        Raises:
            requests.RequestException: 当请求失败时抛出
            KeyError: 当响应格式不正确时抛出
            
        Example:
            >>> client = OllamaClient(model="nomic-embed-text")
            >>> embedding = client.embed("这是一个测试文本")
            >>> print(len(embedding))  # 输出向量维度
        """
        resp = requests.post(
            f"{self.url}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    
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
            requests.RequestException: 当请求失败时抛出
            KeyError: 当响应格式不正确时抛出
            
        Example:
            >>> client = OllamaClient(model="llama2")
            >>> response = client.generate("你好", temperature=0.7)
            >>> print(response)
        """
        resp = requests.post(
            f"{self.url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": options
            },
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()["response"]
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **options
    ) -> str:
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
            requests.RequestException: 当请求失败时抛出
            KeyError: 当响应格式不正确时抛出
            ValueError: 当消息格式不正确时抛出
            
        Example:
            >>> client = OllamaClient(model="llama2")
            >>> messages = [
            ...     {"role": "system", "content": "你是一个有用的助手"},
            ...     {"role": "user", "content": "你好"}
            ... ]
            >>> response = client.chat(messages, temperature=0.7)
            >>> print(response)
        """
        # 验证消息格式
        for msg in messages:
            if not isinstance(msg, dict):
                raise ValueError("每条消息必须是字典类型")
            if "role" not in msg or "content" not in msg:
                raise ValueError("消息必须包含 'role' 和 'content' 字段")
        
        resp = requests.post(
            f"{self.url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": options
            },
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    
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
            resp = requests.get(self.url, timeout=3)
            return resp.status_code == 200
        except requests.RequestException:
            return False
