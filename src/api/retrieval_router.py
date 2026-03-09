"""
议题检索接口
封装RetrievalAgent的能力，供前端调用
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent import RetrievalAgent
from src.core_config import get_logger
from src.utils import ValidationException, BaseESGException

# 初始化路由和logger
router = APIRouter()
logger = get_logger(__name__)
retrieval_agent = RetrievalAgent()


# 定义请求/响应模型
class RetrievalRequest(BaseModel):
    corpus_result: Dict[str, Any] = Field(..., description="语料处理Agent的输出结果")


class RetrievalResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Dict[str, Any] = Field(..., description="议题检索结果")


@router.post("/run", response_model=RetrievalResponse)
async def run_retrieval(request: RetrievalRequest):
    """
    执行议题检索（RAG+LLM识别ESG议题）
    :param request: 包含语料处理结果的请求
    :return: 议题识别结果 + 检索到的标准条文 + 检索到的同行案例
    """
    try:
        logger.info("接收到议题检索请求")
        result = retrieval_agent.run(request.dict())
        return RetrievalResponse(
            code=200,
            message="议题检索成功",
            data=result,
        )
    except ValidationException as e:
        logger.error(f"议题检索失败: {e.message}", exc_info=True)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except BaseESGException as e:
        logger.error(f"议题检索未知错误: {e.message}", exc_info=True)
        raise HTTPException(status_code=500, detail=e.to_dict())
