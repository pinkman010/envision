"""
信息抽取接口
封装ExtractAgent的能力，供前端调用
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent import ExtractAgent
from src.core_config import get_logger
from src.utils import ValidationException, BaseESGException

# 初始化路由和logger
router = APIRouter()
logger = get_logger(__name__)
extract_agent = ExtractAgent()


# 定义请求/响应模型
class ExtractRequest(BaseModel):
    corpus_result: Dict[str, Any] = Field(..., description="语料处理Agent的输出结果")


class ExtractResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Dict[str, Any] = Field(..., description="信息抽取结果")


@router.post("/run", response_model=ExtractResponse)
async def run_extraction(request: ExtractRequest):
    """
    执行信息抽取（仅按固定字段提取事实内容+字符级锚点）
    :param request: 包含语料处理结果的请求
    :return: 信息抽取结果（带相似度校验）
    """
    try:
        logger.info("接收到信息抽取请求")
        result = extract_agent.run(request.dict())
        return ExtractResponse(
            code=200,
            message="信息抽取成功",
            data=result,
        )
    except ValidationException as e:
        logger.error(f"信息抽取失败: {e.message}", exc_info=True)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except BaseESGException as e:
        logger.error(f"信息抽取未知错误: {e.message}", exc_info=True)
        raise HTTPException(status_code=500, detail=e.to_dict())
