"""
合规提示接口
封装ComplianceAgent的能力，供前端调用
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent import ComplianceAgent
from src.core_config import get_logger
from src.utils import ValidationException, BaseESGException

# 初始化路由和logger
router = APIRouter()
logger = get_logger(__name__)
compliance_agent = ComplianceAgent()


# 定义请求/响应模型
class ComplianceRequest(BaseModel):
    extract_result: Dict[str, Any] = Field(..., description="信息抽取Agent的输出结果")


class ComplianceResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Dict[str, Any] = Field(..., description="合规提示结果（仅标注，无决策）")


@router.post("/hint", response_model=ComplianceResponse)
async def get_compliance_hint(request: ComplianceRequest):
    """
    获取合规风险提示（仅做标注，无任何拦截/决策权限）
    :param request: 包含信息抽取结果的请求
    :return: 合规提示结果
    """
    try:
        logger.info("接收到合规提示请求")
        result = compliance_agent.run(request.dict())
        return ComplianceResponse(
            code=200,
            message="合规提示生成成功",
            data=result,
        )
    except ValidationException as e:
        logger.error(f"合规提示失败: {e.message}", exc_info=True)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except BaseESGException as e:
        logger.error(f"合规提示未知错误: {e.message}", exc_info=True)
        raise HTTPException(status_code=500, detail=e.to_dict())
