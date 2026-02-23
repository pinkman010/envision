"""
代码级固定配置（不可随意修改，与外置业务规则解耦）
所有配置项均有默认值，可通过.env覆盖
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Literal

# 加载.env环境变量（优先加载项目根目录的.env）
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

# ------------------------------
# 项目基础配置
# ------------------------------
PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ESG AI Expert System")
PROJECT_DESCRIPTION: str = os.getenv(
    "PROJECT_DESCRIPTION",
    "新能源行业ESG披露与沟通智能分析系统（规则驱动为主、AI辅助为辅的强合规工具）",
)
VERSION: str = os.getenv("VERSION", "1.0.0")
API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")

# ------------------------------
# 运行环境配置
# ------------------------------
ENVIRONMENT: Literal["development", "testing", "production"] = os.getenv(
    "ENVIRONMENT", "development"
).lower()
DEBUG: bool = ENVIRONMENT == "development"

# 服务器绑定配置（后端使用）
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", 8000))

# API访问地址（前端/UI连接后端使用，默认127.0.0.1，可通过.env覆盖）
API_BASE_URL: str = os.getenv("API_BASE_URL", f"http://127.0.0.1:{PORT}")

# ------------------------------
# 跨域配置（CORS）
# ------------------------------
ALLOWED_ORIGINS: List[str] = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000"
).split(",")

# ------------------------------
# 大模型配置（仅保留网络层重试，无业务逻辑）
# ------------------------------
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")  # MVP用小模型，成本低、速度快
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))  # 0温度，输出稳定无随机性
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))
LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_RETRY_DELAY: float = float(os.getenv("LLM_RETRY_DELAY", "2.0"))  # 基础重试延迟（秒），指数退避

# ------------------------------
# 硬规则校验阈值（ESG合规核心）
# ------------------------------
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.98"))  # 文本相似度阈值，低于直接拦截
MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 最大文件大小（字节），默认50MB
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))  # 文本分块大小（字符数）
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))  # 文本分块重叠大小（字符数）

# ------------------------------
# 日志配置（区分普通运行日志和审计日志）
# ------------------------------
LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = os.getenv(
    "LOG_LEVEL", "DEBUG" if DEBUG else "INFO"
).upper()
LOG_FORMAT: str = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)
LOG_DATE_FORMAT: str = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 单个日志文件最大大小（字节），默认10MB
LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # 保留的日志文件备份数

# ------------------------------
# 数据库配置（SQLite轻量级，适合单人开发和企业小范围使用）
# ------------------------------
SQLITE_DB_NAME: str = os.getenv("SQLITE_DB_NAME", "esg_system.db")
CHROMA_DB_PERSIST_DIR: str = os.getenv("CHROMA_DB_PERSIST_DIR", "chroma_db")

# ------------------------------
# Ollama 嵌入模型配置（向量数据库用）
# ------------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:v1.5")
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))
EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
EMBEDDING_MAX_WORKERS: int = int(os.getenv("EMBEDDING_MAX_WORKERS", "4"))
EMBEDDING_TIMEOUT: int = int(os.getenv("EMBEDDING_TIMEOUT", "60"))


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
    
    # Ollama 嵌入模型
    OLLAMA_BASE_URL = OLLAMA_BASE_URL
    EMBEDDING_MODEL = EMBEDDING_MODEL
    EMBEDDING_DIMENSION = EMBEDDING_DIMENSION
    EMBEDDING_BATCH_SIZE = EMBEDDING_BATCH_SIZE
    EMBEDDING_MAX_WORKERS = EMBEDDING_MAX_WORKERS
    EMBEDDING_TIMEOUT = EMBEDDING_TIMEOUT


# 关键：创建实例，这样才能 import settings
settings = Settings()
