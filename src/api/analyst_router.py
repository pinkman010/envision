"""
差距分析接口
封装AnalystAgent的能力，供前端调用
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent import AnalystAgent
from src.core_config import get_logger
from src.utils import ValidationException, BaseESGException

# 初始化路由和logger
router = APIRouter()
logger = get_logger(__name__)
analyst_agent = AnalystAgent()


# 定义请求/响应模型
class AnalystRequest(BaseModel):
    retrieval_result: Dict[str, Any] = Field(..., description="议题检索Agent的输出结果")


class AnalystResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Dict[str, Any] = Field(..., description="差距分析结果")


@router.post("/analyze", response_model=AnalystResponse)
async def run_analysis(request: AnalystRequest):
    """
    执行差距分析（对照标准+同行对比找差距）
    :param request: 包含议题检索结果的请求
    :return: 差距分析结果 + 同行对比结果
    """
    try:
        logger.info("接收到差距分析请求")
        result = analyst_agent.run(request.dict())
        return AnalystResponse(
            code=200,
            message="差距分析成功",
            data=result,
        )
    except ValidationException as e:
        logger.error(f"差距分析失败: {e.message}", exc_info=True)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except BaseESGException as e:
        logger.error(f"差距分析未知错误: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=500, detail={"error_code": "E5001", "message": e.message}
        )
    except Exception as e:
        logger.critical(f"差距分析系统未知错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail={"error_code": "E5001", "message": str(e)}
        )
