"""
全局总路由注册入口
统一管理所有业务路由的前缀、标签
"""

from fastapi import APIRouter

# 直接从子模块导入，不经过 src.api（避免循环导入）
from src.api.corpus_router import router as corpus_router
from src.api.retrieval_router import router as retrieval_router
from src.api.analyst_router import router as analyst_router
from src.api.advisor_router import router as advisor_router

# 初始化全局总路由
api_router = APIRouter()

# 注册各业务路由
api_router.include_router(
    corpus_router,
    prefix="/corpus",
    tags=["语料处理"],
)
api_router.include_router(
    retrieval_router,
    prefix="/retrieval",
    tags=["议题检索"],
)
api_router.include_router(
    analyst_router,
    prefix="/analyst",
    tags=["差距分析"],
)
api_router.include_router(
    advisor_router,
    prefix="/advisor",
    tags=["优化建议"],
)
