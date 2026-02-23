"""
统一 Python logging 初始化工具
区分开发/生产环境，区分应用日志/API日志，支持日志轮转
与审计日志（audit_utils.py）完全解耦
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src.core_config.settings import (
    ENVIRONMENT,
    DEBUG,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
)
from src.core_config.paths import APP_LOG_DIR, API_LOG_DIR


def init_logging() -> None:
    """
    初始化全局 logging 配置
    必须在应用启动时调用一次（main.py 和 streamlit_app.py 都要调用）
    """
    # 1. 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.handlers.clear()  # 清除默认的 StreamHandler，避免重复输出

    # 2. 定义日志格式
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # 3. 添加控制台输出（仅开发环境开启DEBUG级别，生产环境仅INFO及以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL if DEBUG else logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 4. 添加应用日志文件输出（所有环境都开启，支持轮转）
    app_log_file = APP_LOG_DIR / f"esg_app_{ENVIRONMENT}.log"
    app_file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    app_file_handler.setLevel(LOG_LEVEL)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # 5. （可选）添加API请求日志文件输出（仅FastAPI后端使用）
    # 这里先定义好，后续在FastAPI的中间件里调用
    api_logger = logging.getLogger("esg_api")
    api_logger.setLevel(LOG_LEVEL)
    api_logger.propagate = False  # 不传播到根 logger，避免重复输出
    api_log_file = API_LOG_DIR / f"esg_api_{ENVIRONMENT}.log"
    api_file_handler = RotatingFileHandler(
        api_log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    api_file_handler.setLevel(LOG_LEVEL)
    api_file_handler.setFormatter(formatter)
    api_logger.addHandler(api_file_handler)
    if DEBUG:
        api_logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取指定名称的 logger
    :param name: logger名称，默认使用调用模块的 __name__
    :return: 配置好的 logger 对象
    """
    if not name:
        # 获取调用模块的 __name__（跳过当前函数和init_logging的调用）
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "esg_unknown")
    return logging.getLogger(name)
