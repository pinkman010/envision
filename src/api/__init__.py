"""
API路由模块

提供FastAPI路由定义，包括：
- corpus_router: 语料库管理路由
- extract_router: 指标提取路由
- compliance_router: 合规检查路由
- content_router: 内容生成路由
- api_router: 全局总路由
"""

from src.api.router import api_router
from src.api.corpus_router import router as corpus_router
from src.api.extract_router import router as extract_router
from src.api.compliance_router import router as compliance_router
from src.api.content_router import router as content_router

__all__ = [
    "api_router",
    "corpus_router",
    "extract_router",
    "compliance_router",
    "content_router",
]
