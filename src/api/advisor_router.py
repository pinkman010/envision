"""
优化建议接口
封装AdvisorAgent的能力，供前端调用
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent import AdvisorAgent
from src.core_config import get_logger
from src.utils import ValidationException, BaseESGException

# 初始化路由和logger
router = APIRouter()
logger = get_logger(__name__)
advisor_agent = AdvisorAgent()


# 定义请求/响应模型
class AdvisorRequest(BaseModel):
    analyst_result: Dict[str, Any] = Field(..., description="差距分析Agent的输出结果")


class AdvisorResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Dict[str, Any] = Field(..., description="优化建议结果")


@router.post("/recommend", response_model=AdvisorResponse)
async def run_recommendation(request: AdvisorRequest):
    """
    执行优化建议生成（生成可操作的改进建议）
    :param request: 包含差距分析结果的请求
    :return: 改进建议列表 + 优先行动项 + 完整建议文本
    """
    try:
        logger.info("接收到优化建议请求")
        result = advisor_agent.run(request.dict())
        return AdvisorResponse(
            code=200,
            message="优化建议生成成功",
            data=result,
        )
    except ValidationException as e:
        logger.error(f"优化建议生成失败: {e.message}", exc_info=True)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except BaseESGException as e:
        logger.error(f"优化建议生成未知错误: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=500, detail={"error_code": "E5001", "message": e.message}
        )
    except Exception as e:
        logger.critical(f"优化建议生成系统未知错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail={"error_code": "E5001", "message": str(e)}
        )
