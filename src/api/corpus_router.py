"""
语料处理接口
封装CorpusAgent的能力，供前端调用
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field

from src.agent import CorpusAgent
from src.core_config import get_logger
from src.utils import (
    FileProcessingException, 
    BaseESGException,
    get_corpus_list,
    get_corpus_detail,
    get_esg_metrics,
)

# 初始化路由和logger
router = APIRouter()
logger = get_logger(__name__)
corpus_agent = CorpusAgent()


# 定义请求/响应模型（Pydantic，自动生成API文档）
class CorpusProcessResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Dict[str, Any] = Field(..., description="语料处理结果")


class CorpusListItem(BaseModel):
    """语料列表项"""
    corpus_id: str = Field(..., description="语料唯一ID")
    file_name: str = Field(..., description="文件名")
    file_suffix: str = Field(..., description="文件后缀")
    file_size: int = Field(..., description="文件大小(字节)")
    text_length: int = Field(..., description="文本长度(字符)")
    chunk_count: int = Field(..., description="分块数量")
    processed_at: str = Field(..., description="处理时间")
    has_esg_extraction: bool = Field(False, description="是否已提取ESG指标")
    raw_text_path: Optional[str] = Field(None, description="原始文本存储路径")


class CorpusListResponse(BaseModel):
    """语料列表响应"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: List[CorpusListItem] = Field(..., description="语料列表")


class CorpusChunk(BaseModel):
    """语料分块"""
    chunk_index: int = Field(..., description="分块索引")
    start: int = Field(..., description="起始位置")
    end: int = Field(..., description="结束位置")
    text: str = Field(..., description="分块文本内容")


class CorpusDetail(BaseModel):
    """语料详情"""
    corpus_id: str = Field(..., description="语料唯一ID")
    file_name: str = Field(..., description="文件名")
    file_suffix: str = Field(..., description="文件后缀")
    file_size: int = Field(..., description="文件大小(字节)")
    text_length: int = Field(..., description="文本长度(字符)")
    chunk_count: int = Field(..., description="分块数量")
    processed_at: str = Field(..., description="处理时间")
    has_esg_extraction: bool = Field(False, description="是否已提取ESG指标")
    raw_text: str = Field(..., description="原始文本内容")
    fixed_text: str = Field(..., description="修复后文本内容")
    chunks: List[CorpusChunk] = Field(..., description="分块列表")


class CorpusDetailResponse(BaseModel):
    """语料详情响应"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[CorpusDetail] = Field(None, description="语料详情")


class ESGMetricItem(BaseModel):
    """ESG指标项"""
    metric_key: str = Field(..., description="指标键名")
    metric_name: str = Field(..., description="指标名称")
    original_value: float = Field(..., description="原始数值")
    original_unit: str = Field(..., description="原始单位")
    normalized_value: float = Field(..., description="归一化数值")
    normalized_unit: str = Field(..., description="归一化单位")
    confidence: float = Field(..., description="置信度")
    original_text: str = Field(..., description="原文片段")


class ESGMetricsResponse(BaseModel):
    """ESG指标响应"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: List[ESGMetricItem] = Field(..., description="ESG指标列表")


@router.post("/process", response_model=CorpusProcessResponse)
async def process_corpus(file: UploadFile = File(...)):
    """
    上传并处理ESG语料文件（PDF/Word）
    :param file: 上传的文件
    :return: 语料处理结果（文本、分块、元数据）
    """
    try:
        # 1. 保存上传的文件到临时目录
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        logger.info(f"接收到语料处理请求: {file.filename}")
        
        # 2. 调用CorpusAgent处理
        task_input = {"file_path": str(tmp_path)}
        result = corpus_agent.run(task_input)
        
        # 3. 返回结果
        return CorpusProcessResponse(
            code=200,
            message="语料处理成功",
            data=result,
        )
    
    except FileProcessingException as e:
        logger.error(f"语料处理失败: {e.message}", exc_info=True)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except BaseESGException as e:
        logger.error(f"语料处理未知错误: {e.message}", exc_info=True)
        raise HTTPException(status_code=500, detail=e.to_dict())
    except Exception as e:
        logger.critical(f"语料处理系统错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error_code": "E0001", "message": str(e)})


@router.get("/list", response_model=CorpusListResponse)
async def list_corpus(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    获取历史语料列表
    :param limit: 返回数量限制（默认100，最大1000）
    :param offset: 偏移量（分页用）
    :return: 语料列表
    """
    try:
        logger.info(f"查询语料列表: limit={limit}, offset={offset}")
        corpus_list = get_corpus_list(limit=limit, offset=offset)
        return CorpusListResponse(
            code=200,
            message="查询成功",
            data=corpus_list,
        )
    except Exception as e:
        logger.error(f"语料列表查询失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error_code": "E0002", "message": str(e)})


@router.get("/detail/{corpus_id}", response_model=CorpusDetailResponse)
async def get_corpus(corpus_id: str):
    """
    获取语料详情
    :param corpus_id: 语料唯一ID
    :return: 语料详情（包含完整文本和分块）
    """
    try:
        logger.info(f"查询语料详情: {corpus_id}")
        corpus_detail = get_corpus_detail(corpus_id)
        if corpus_detail is None:
            raise HTTPException(status_code=404, detail={"error_code": "E0003", "message": "语料不存在"})
        return CorpusDetailResponse(
            code=200,
            message="查询成功",
            data=corpus_detail,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"语料详情查询失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error_code": "E0004", "message": str(e)})


@router.get("/esg-metrics/{corpus_id}", response_model=ESGMetricsResponse)
async def get_corpus_esg_metrics(corpus_id: str):
    """
    获取语料的ESG指标
    :param corpus_id: 语料唯一ID
    :return: ESG指标列表
    """
    try:
        logger.info(f"查询ESG指标: {corpus_id}")
        metrics = get_esg_metrics(corpus_id)
        return ESGMetricsResponse(
            code=200,
            message="查询成功",
            data=metrics,
        )
    except Exception as e:
        logger.error(f"ESG指标查询失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error_code": "E0005", "message": str(e)})
