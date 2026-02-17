"""ESG 项目工具函数模块

提供 ESG 报告处理过程中常用的工具函数：
- Ollama HTTP 客户端：用于与大模型服务交互
"""

# Ollama 客户端 (从 llm 模块导入)
from src.esg.llm.ollama_client import OllamaClient

__all__ = [
    # Ollama 客户端
    "OllamaClient",
]
