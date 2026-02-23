"""
全局总路由注册入口
统一管理所有业务路由的前缀、标签
"""

from fastapi import APIRouter

# 直接从子模块导入，不经过 src.api（避免循环导入）
from src.api.corpus_router import router as corpus_router
from src.api.extract_router import router as extract_router
from src.api.compliance_router import router as compliance_router
from src.api.content_router import router as content_router

# 初始化全局总路由
api_router = APIRouter()

# 注册各业务路由
api_router.include_router(
    corpus_router,
    prefix="/corpus",
    tags=["语料处理"],
)
api_router.include_router(
    extract_router,
    prefix="/extract",
    tags=["信息抽取"],
)
api_router.include_router(
    compliance_router,
    prefix="/compliance",
    tags=["合规提示"],
)
api_router.include_router(
    content_router,
    prefix="/content",
    tags=["内容生成"],
)
