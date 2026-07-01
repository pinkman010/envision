"""
核心配置模块

提供项目核心配置功能：
- settings: 统一配置访问入口（Settings类实例）
- paths: 全局路径配置
- logging_utils: 日志工具（get_logger, init_logging）
"""

from src.config.logging_utils import get_logger, init_logging
from src.config.settings import settings
from src.config.paths import (
    ROOT_DIR,
    SRC_DIR,
    CONFIG_DIR,
    PROMPT_TEMPLATES_DIR,
    RULE_TEMPLATES_DIR,
    DATA_DIR,
    CHROMA_DB_DIR,
    SQLITE_DB_DIR,
    RAW_CORPUS_DIR,
    EXPORT_RESULTS_DIR,
    UI_PAGES_DIR,
    LOGS_DIR,
    APP_LOG_DIR,
    API_LOG_DIR,
    ensure_all_paths,
)

__all__ = [
    # 日志工具
    "get_logger",
    "init_logging",
    # 配置实例
    "settings",
    # 路径
    "ROOT_DIR",
    "SRC_DIR",
    "CONFIG_DIR",
    "PROMPT_TEMPLATES_DIR",
    "RULE_TEMPLATES_DIR",
    "DATA_DIR",
    "CHROMA_DB_DIR",
    "SQLITE_DB_DIR",
    "RAW_CORPUS_DIR",
    "EXPORT_RESULTS_DIR",
    "UI_PAGES_DIR",
    "LOGS_DIR",
    "APP_LOG_DIR",
    "API_LOG_DIR",
    "ensure_all_paths",
]
