"""ESG 项目工具函数模块

提供 ESG 报告处理过程中常用的工具函数：
- Ollama HTTP 客户端：用于与大模型服务交互
"""

# Ollama 客户端
from src.esg.utils.ollama_client import OllamaClient

__all__ = [
    # Ollama 客户端
    "OllamaClient",
]
