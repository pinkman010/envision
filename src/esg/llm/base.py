"""LLM客户端抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMConfig:
    """LLM配置"""

    provider: str = "ollama"  # "ollama" 或 "kimi"
    model_name: str = "qwen2.5:14b"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class LLMClient(ABC):
    """LLM客户端抽象基类"""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """通用文本生成"""
        pass

    @abstractmethod
    def extract_structured(self, text: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """结构化数据提取"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """获取LLM客户端实例"""
    if config is None:
        config = LLMConfig()

    if config.provider == "ollama":
        from .ollama_client import OllamaClient

        return OllamaClient(config)
    elif config.provider == "kimi":
        from .kimi_client import KimiClient

        return KimiClient(config)
    else:
        raise ValueError(f"不支持的LLM提供商: {config.provider}")
