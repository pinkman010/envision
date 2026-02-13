"""日志配置模块

提供统一的日志配置，支持控制台输出和文件输出。
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 默认日志级别
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 文件日志配置
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


def setup_logging(
    name: str = None,
    level: str = None,
    log_to_file: bool = True,
) -> logging.Logger:
    """配置日志记录器

    Args:
        name: 日志记录器名称，None则配置根日志
        level: 日志级别，默认为环境变量LOG_LEVEL
        log_to_file: 是否输出到文件

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    log_level = getattr(logging, (level or DEFAULT_LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(log_level)

    # 控制台Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件Handler
    if log_to_file:
        log_file = LOG_DIR / f"{name or 'esg'}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器

    如果已配置则返回现有记录器，否则创建新记录器。

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)


# 初始化根日志配置
def init_root_logger():
    """初始化根日志记录器"""
    setup_logging(name=None, level=DEFAULT_LOG_LEVEL, log_to_file=True)
    
    # 设置第三方库日志级别，减少噪音
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("streamlit").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


# 导出常用日志级别常量
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
