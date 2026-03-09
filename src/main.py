"""
FastAPI后端服务入口
功能：全局配置加载、API路由注册、CORS配置、健康检查
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.config.paths import ensure_all_paths
from src.api.router import api_router

# 1. 确保所有必要的目录存在（data/、tmp/等）
ensure_all_paths()

# 2. 初始化FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/api/docs",  # 自动生成API文档
    redoc_url="/api/redoc",
)

# 3. 配置CORS（允许Streamlit前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 注册全局API路由
app.include_router(api_router, prefix=settings.API_PREFIX)

# 5. 全局异常处理器：将 Pydantic 请求验证错误(422)转换为 400
# 注：测试期望请求参数验证失败返回 400，而 FastAPI 默认返回 422
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors(), "message": "请求参数验证失败"},
    )

# 6. 健康检查接口（用于Docker部署、监控）
@app.get("/health", tags=["系统监控"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "project_name": settings.PROJECT_NAME,
    }

# 7. 本地启动入口（仅用于开发调试，生产环境用uvicorn命令或Docker）
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # 开发环境开启热重载
        log_level=settings.LOG_LEVEL.lower(),
    )
