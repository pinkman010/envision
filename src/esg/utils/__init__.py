"""ESG 项目工具函数模块

提供 ESG 报告处理过程中常用的工具函数，包括：
- Ollama HTTP 客户端：用于与大模型服务交互
- 文件操作工具：文件保存、目录管理等
- 数据校验工具：PDF、年份、评分等数据验证
"""

# Ollama 客户端
from src.esg.utils.ollama_client import OllamaClient

# 文件操作工具
from src.esg.utils.file_utils import (
    save_uploaded_file,
    ensure_dir,
    get_file_extension,
    copy_file,
    delete_file,
    get_file_size,
)

# 数据校验工具
from src.esg.utils.validators import (
    validate_pdf,
    validate_year,
    validate_score,
    validate_company_code,
    validate_report_year_range,
    ALLOWED_PDF_EXTENSIONS,
    ALLOWED_PDF_MIME_TYPES,
    MAX_FILE_SIZE,
)

__all__ = [
    # Ollama 客户端
    "OllamaClient",
    # 文件操作
    "save_uploaded_file",
    "ensure_dir",
    "get_file_extension",
    "copy_file",
    "delete_file",
    "get_file_size",
    # 数据校验
    "validate_pdf",
    "validate_year",
    "validate_score",
    "validate_company_code",
    "validate_report_year_range",
    # 校验常量
    "ALLOWED_PDF_EXTENSIONS",
    "ALLOWED_PDF_MIME_TYPES",
    "MAX_FILE_SIZE",
]
