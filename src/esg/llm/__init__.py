"""LLM客户端模块

提供与本地大模型服务和API服务的交互功能。
"""

from src.esg.llm.ollama_client import LLMClient, OllamaClient

__all__ = [
    "OllamaClient",
    "LLMClient",
]
