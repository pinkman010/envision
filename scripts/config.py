# -*- coding: utf-8 -*-
"""
【配置中心】集中管理所有可调参数（带验证）
修改原因：消除硬编码，便于不同环境部署
"""
import os
from dataclasses import dataclass
from typing import Literal

# ==================== 路径配置 ====================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(PROJECT_ROOT, "data")
VECTOR_DB_PATH = os.path.join(PROJECT_ROOT, "vector_db")

# ==================== Ollama 配置 ====================
OLLAMA_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 60  # 单次请求超时（秒）
OLLAMA_PULL_TIMEOUT = 1800  # 模型下载超时（30分钟）

# ==================== 模型配置 ====================
MODELS = {
    "llm": "deepseek-r1:7b",
    "embedding": "nomic-embed-text"
}
EMBEDDING_DIM = 768  # nomic-embed-text 的向量维度

# ==================== RAG 配置 ====================
CHUNK_SIZE = 500       # 文本切片大小
CHUNK_OVERLAP = 100    # 切片重叠窗口
RETRIEVER_TOP_K = 4    # 召回文档数量

# ==================== 并发配置 ====================
EMBEDDING_BATCH_SIZE = 10     # 批量 Embedding 并发数
EMBEDDING_MAX_WORKERS = 4     # 线程池大小
MAX_RETRIES = 3               # API 请求重试次数
RETRY_DELAY = 1               # 重试间隔（秒）


# ==================== 类型安全配置类（新增）====================
@dataclass(frozen=True)
class RAGConfig:
    """
    类型安全的 RAG 配置类
    使用 frozen=True 防止运行时修改
    """
    ollama_url: str
    llm_model: Literal["deepseek-r1:1.5b", "deepseek-r1:7b", "deepseek-r1:14b"]
    embedding_model: Literal["nomic-embed-text"]
    chunk_size: int
    chunk_overlap: int
    retriever_top_k: int
    embedding_dim: int = 768
    max_retries: int = 3
    
    def __post_init__(self):
        # 运行时验证
        if not self.ollama_url.startswith(("http://", "https://")):
            raise ValueError(f"ollama_url 必须是有效的 HTTP URL: {self.ollama_url}")
        
        if not (100 <= self.chunk_size <= 2000):
            raise ValueError(f"chunk_size 必须在 100-2000 之间: {self.chunk_size}")
        
        if not (0 <= self.chunk_overlap < self.chunk_size):
            raise ValueError(f"chunk_overlap 必须在 0-chunk_size 之间: {self.chunk_overlap}")
        
        if not (1 <= self.retriever_top_k <= 20):
            raise ValueError(f"retriever_top_k 必须在 1-20 之间: {self.retriever_top_k}")
        
        if self.max_retries < 0:
            raise ValueError(f"max_retries 不能为负数: {self.max_retries}")


# 默认配置实例
DEFAULT_CONFIG = RAGConfig(
    ollama_url=OLLAMA_URL,
    llm_model="deepseek-r1:7b",
    embedding_model="nomic-embed-text",
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    retriever_top_k=RETRIEVER_TOP_K,
    max_retries=MAX_RETRIES
)


def get_config_from_env() -> RAGConfig:
    """
    从环境变量读取配置（便于容器化部署）
    
    支持的环境变量：
    - OLLAMA_URL
    - LLM_MODEL
    - CHUNK_SIZE
    - RETRIEVER_TOP_K
    """
    def safe_int(value, default, name):
        """[ADDED] 安全地转换环境变量为整数"""
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            import logging
            logging.warning(f"环境变量 {name} 值 '{value}' 无效，使用默认值 {default}")
            return default
    
    return RAGConfig(
        ollama_url=os.getenv("OLLAMA_URL", OLLAMA_URL),
        llm_model=os.getenv("LLM_MODEL", MODELS["llm"]),
        embedding_model=MODELS["embedding"],
        chunk_size=safe_int(os.getenv("CHUNK_SIZE"), CHUNK_SIZE, "CHUNK_SIZE"),  # [FIXED] 安全转换
        chunk_overlap=safe_int(os.getenv("CHUNK_OVERLAP"), CHUNK_OVERLAP, "CHUNK_OVERLAP"),  # [FIXED]
        retriever_top_k=safe_int(os.getenv("RETRIEVER_TOP_K"), RETRIEVER_TOP_K, "RETRIEVER_TOP_K"),  # [FIXED]
        max_retries=safe_int(os.getenv("MAX_RETRIES"), MAX_RETRIES, "MAX_RETRIES")  # [FIXED]
    )
