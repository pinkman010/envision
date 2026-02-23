"""
API路由模块 - FastAPI RESTful接口
"""

# 直接导入各个子模块，不导入 router（避免循环导入）
from src.api import corpus_router
from src.api import extract_router
from src.api import compliance_router
from src.api import content_router

# 导出各个路由模块
__all__ = [
    "corpus_router",
    "extract_router",
    "compliance_router",
    "content_router",
]
