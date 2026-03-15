"""
代码级固定配置（不可随意修改，与外置业务规则解耦）
所有配置项均从 .env 文件读取，无默认兜底值
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Literal, Any, Callable


# 加载.env环境变量（优先加载项目根目录的.env）
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")


def get_required_env(key: str, var_type: type = str, converter: Callable[[str], Any] = None) -> Any:
    """
    获取必需的环境变量，不存在则抛出异常
    
    Args:
        key: 环境变量名称
        var_type: 期望的类型（用于错误提示）
        converter: 自定义转换函数
    
    Returns:
        转换后的值
    
    Raises:
        ValueError: 环境变量不存在时抛出
    """
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"缺少必需的环境变量: {key}，请在 .env 文件中配置")
    
    try:
        if converter:
            return converter(value)
        if var_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        if var_type == int:
            return int(value)
        if var_type == float:
            return float(value)
        if var_type == str:
            return value
        return value
    except (ValueError, TypeError) as e:
        raise ValueError(f"环境变量 {key} 的值 '{value}' 无法转换为 {var_type.__name__}: {e}")


def parse_list(value: str, separator: str = ",") -> List[str]:
    """解析逗号分隔的列表"""
    return [item.strip() for item in value.split(separator) if item.strip()]


# ------------------------------
# 项目基础配置
# ------------------------------
PROJECT_NAME: str = get_required_env("PROJECT_NAME")
PROJECT_DESCRIPTION: str = get_required_env("PROJECT_DESCRIPTION")
VERSION: str = get_required_env("VERSION")
API_PREFIX: str = get_required_env("API_PREFIX")

# ------------------------------
# 运行环境配置
# ------------------------------
ENVIRONMENT: Literal["development", "testing", "production"] = get_required_env("ENVIRONMENT")
DEBUG: bool = ENVIRONMENT == "development"

# 服务器绑定配置（后端使用）
HOST: str = get_required_env("HOST")
PORT: int = get_required_env("PORT", int)

# API访问地址（前端/UI连接后端使用）
API_BASE_URL: str = get_required_env("API_BASE_URL")

# ------------------------------
# 跨域配置（CORS）
# ------------------------------
ALLOWED_ORIGINS: List[str] = get_required_env("ALLOWED_ORIGINS", converter=parse_list)

# ------------------------------
# 大模型配置（仅保留网络层重试，无业务逻辑）
# ------------------------------
LLM_API_KEY: str = get_required_env("LLM_API_KEY")
LLM_BASE_URL: str = get_required_env("LLM_BASE_URL")
LLM_MODEL: str = get_required_env("LLM_MODEL")
LLM_TEMPERATURE: float = get_required_env("LLM_TEMPERATURE", float)
LLM_MAX_TOKENS: int = get_required_env("LLM_MAX_TOKENS", int)
LLM_TIMEOUT: int = get_required_env("LLM_TIMEOUT", int)
LLM_MAX_RETRIES: int = get_required_env("LLM_MAX_RETRIES", int)
LLM_RETRY_DELAY: float = get_required_env("LLM_RETRY_DELAY", float)
# 可选配置：禁用推理模型思考能力（如 kimi-k2.5, DeepSeek-R1）
LLM_THINKING_DISABLED: bool = os.getenv("LLM_THINKING_DISABLED", "false").lower() in ("true", "1", "yes", "on")

# ------------------------------
# 硬规则校验阈值（ESG合规核心）
# ------------------------------
# 注意：SIMILARITY_THRESHOLD仅保留用于兼容性（src/utils/similarity_utils.py使用）
# 新的RetrievalAgent/AnalystAgent/AdvisorAgent不再使用此配置
SIMILARITY_THRESHOLD: float = get_required_env("SIMILARITY_THRESHOLD", float)
MAX_FILE_SIZE: int = get_required_env("MAX_FILE_SIZE", int)
CHUNK_SIZE: int = get_required_env("CHUNK_SIZE", int)
CHUNK_OVERLAP: int = get_required_env("CHUNK_OVERLAP", int)

# ------------------------------
# 日志配置（区分普通运行日志和审计日志）
# ------------------------------
LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = get_required_env("LOG_LEVEL")
LOG_FORMAT: str = get_required_env("LOG_FORMAT")
LOG_DATE_FORMAT: str = get_required_env("LOG_DATE_FORMAT")
LOG_MAX_BYTES: int = get_required_env("LOG_MAX_BYTES", int)
LOG_BACKUP_COUNT: int = get_required_env("LOG_BACKUP_COUNT", int)

# ------------------------------
# 数据库配置（SQLite轻量级，适合单人开发和企业小范围使用）
# ------------------------------
SQLITE_DB_NAME: str = get_required_env("SQLITE_DB_NAME")
CHROMA_DB_PERSIST_DIR: str = get_required_env("CHROMA_DB_PERSIST_DIR")

# ------------------------------
# 嵌入模型配置（硅基流动 API）
# ------------------------------
SILICONFLOW_API_KEY: str = get_required_env("SILICONFLOW_API_KEY")
EMBEDDING_MODEL: str = get_required_env("EMBEDDING_MODEL")
EMBEDDING_DIMENSION: int = get_required_env("EMBEDDING_DIMENSION", int)
EMBEDDING_BATCH_SIZE: int = get_required_env("EMBEDDING_BATCH_SIZE", int)
EMBEDDING_MAX_WORKERS: int = get_required_env("EMBEDDING_MAX_WORKERS", int)
EMBEDDING_TIMEOUT: int = get_required_env("EMBEDDING_TIMEOUT", int)

# ------------------------------
# RAG增强提取配置
# ------------------------------
USE_RAG_ENHANCEMENT: bool = os.getenv("USE_RAG_ENHANCEMENT", "true").lower() in ("true", "1", "yes", "on")
RAG_EXTRACTION_TOP_K: int = int(os.getenv("RAG_EXTRACTION_TOP_K", "3"))
RAG_EXTRACTION_THRESHOLD: float = float(os.getenv("RAG_EXTRACTION_THRESHOLD", "0.6"))


class Settings:
    """统一配置访问入口"""
    # 项目基础
    PROJECT_NAME = PROJECT_NAME
    PROJECT_DESCRIPTION = PROJECT_DESCRIPTION
    VERSION = VERSION
    API_PREFIX = API_PREFIX
    
    # 运行环境
    ENVIRONMENT = ENVIRONMENT
    DEBUG = DEBUG
    HOST = HOST
    PORT = PORT
    API_BASE_URL = API_BASE_URL
    
    # CORS
    ALLOWED_ORIGINS = ALLOWED_ORIGINS
    
    # 大模型
    LLM_API_KEY = LLM_API_KEY
    LLM_BASE_URL = LLM_BASE_URL
    LLM_MODEL = LLM_MODEL
    LLM_TEMPERATURE = LLM_TEMPERATURE
    LLM_MAX_TOKENS = LLM_MAX_TOKENS
    LLM_TIMEOUT = LLM_TIMEOUT
    LLM_MAX_RETRIES = LLM_MAX_RETRIES
    LLM_RETRY_DELAY = LLM_RETRY_DELAY
    LLM_THINKING_DISABLED = LLM_THINKING_DISABLED
    
    # 硬规则
    SIMILARITY_THRESHOLD = SIMILARITY_THRESHOLD
    MAX_FILE_SIZE = MAX_FILE_SIZE
    CHUNK_SIZE = CHUNK_SIZE
    CHUNK_OVERLAP = CHUNK_OVERLAP
    
    # 日志
    LOG_LEVEL = LOG_LEVEL
    LOG_FORMAT = LOG_FORMAT
    LOG_DATE_FORMAT = LOG_DATE_FORMAT
    LOG_MAX_BYTES = LOG_MAX_BYTES
    LOG_BACKUP_COUNT = LOG_BACKUP_COUNT
    
    # 数据库
    SQLITE_DB_NAME = SQLITE_DB_NAME
    CHROMA_DB_PERSIST_DIR = CHROMA_DB_PERSIST_DIR
    
    # 嵌入模型
    SILICONFLOW_API_KEY = SILICONFLOW_API_KEY
    EMBEDDING_MODEL = EMBEDDING_MODEL
    EMBEDDING_DIMENSION = EMBEDDING_DIMENSION
    EMBEDDING_BATCH_SIZE = EMBEDDING_BATCH_SIZE
    EMBEDDING_MAX_WORKERS = EMBEDDING_MAX_WORKERS
    EMBEDDING_TIMEOUT = EMBEDDING_TIMEOUT
    
    # RAG增强提取
    USE_RAG_ENHANCEMENT = USE_RAG_ENHANCEMENT
    RAG_EXTRACTION_TOP_K = RAG_EXTRACTION_TOP_K
    RAG_EXTRACTION_THRESHOLD = RAG_EXTRACTION_THRESHOLD


# 关键：创建实例，这样才能 import settings
settings = Settings()
