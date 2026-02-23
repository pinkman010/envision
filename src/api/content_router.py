"""
内容生成接口
封装ContentAgent的能力，供前端调用
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent import ContentAgent
from src.core_config import get_logger
from src.utils import ValidationException, BaseESGException

# 初始化路由和logger
router = APIRouter()
logger = get_logger(__name__)
content_agent = ContentAgent()


# 定义请求/响应模型
class ContentRequest(BaseModel):
    confirmed_data: Dict[str, Any] = Field(..., description="人工确认后的结构化数据")
    template_type: str = Field("analysis_report", description="模板类型（analysis_report/benchmark_report）")


class ContentResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Dict[str, Any] = Field(..., description="内容生成结果（仅模板填充）")


@router.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """
    生成标准化文本（仅按固定模板填充人工确认后的结构化数据）
    :param request: 包含人工确认数据的请求
    :return: 内容生成结果
    """
    try:
        logger.info(f"接收到内容生成请求，模板类型: {request.template_type}")
        result = content_agent.run(request.dict())
        return ContentResponse(
            code=200,
            message="内容生成成功",
            data=result,
        )
    except ValidationException as e:
        logger.error(f"内容生成失败: {e.message}", exc_info=True)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except BaseESGException as e:
        logger.error(f"内容生成未知错误: {e.message}", exc_info=True)
        raise HTTPException(status_code=500, detail=e.to_dict())
