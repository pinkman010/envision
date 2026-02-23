"""
核心配置模块 - 全局设置、路径、日志
"""
from src.core_config.settings import settings, Settings
from src.core_config.paths import (
    ROOT_DIR, SRC_DIR, CONFIG_DIR, DATA_DIR, LOGS_DIR,
    ensure_all_paths,
)
from src.core_config.logging_utils import init_logging, get_logger

__all__ = [
    "settings",
    "Settings",
    "ROOT_DIR",
    "SRC_DIR", 
    "CONFIG_DIR",
    "DATA_DIR",
    "LOGS_DIR",
    "ensure_all_paths",
    "init_logging",
    "get_logger",
]
