"""
API路由模块

提供FastAPI路由定义，包括：
- corpus_router: 语料库管理路由
- retrieval_router: 议题检索路由
- analyst_router: 差距分析路由
- advisor_router: 优化建议路由
- api_router: 全局总路由
"""

from src.api.router import api_router
from src.api.corpus_router import router as corpus_router
from src.api.retrieval_router import router as retrieval_router
from src.api.analyst_router import router as analyst_router
from src.api.advisor_router import router as advisor_router

__all__ = [
    "api_router",
    "corpus_router",
    "retrieval_router",
    "analyst_router",
    "advisor_router",
]
