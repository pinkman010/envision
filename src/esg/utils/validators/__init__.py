"""数据验证器模块

提供各种数据校验功能，用于验证文件类型、年份、评分等数据的合法性。
主要用于 ESG 报告处理场景。

子模块:
    - base: 基础验证（PDF、文件）
    - fields: 字段验证（年份、评分、公司名称）
    - esg_metrics: ESG指标验证

常量:
    - ALLOWED_PDF_EXTENSIONS: 允许的PDF扩展名
    - ALLOWED_PDF_MIME_TYPES: 允许的PDF MIME类型
    - MAX_FILE_SIZE: 最大文件大小
"""

from src.esg.utils.validators.base import (
    ALLOWED_PDF_EXTENSIONS,
    ALLOWED_PDF_MIME_TYPES,
    MAX_FILE_SIZE,
    validate_pdf,
    validate_report_year_range,
    validate_year,
)
from src.esg.utils.validators.esg_metrics import (
    validate_carbon_intensity,
    validate_emissions_value,
    validate_esg_metrics,
    validate_non_negative_number,
    validate_training_hours,
    validate_water_intensity,
)
from src.esg.utils.validators.fields import (
    validate_company_code,
    validate_company_name,
    validate_percentage,
    validate_positive_int,
    validate_ratio,
    validate_score,
)

__all__ = [
    # 常量
    "ALLOWED_PDF_EXTENSIONS",
    "ALLOWED_PDF_MIME_TYPES",
    "MAX_FILE_SIZE",
    # 基础验证
    "validate_pdf",
    "validate_year",
    "validate_report_year_range",
    # 字段验证
    "validate_score",
    "validate_company_code",
    "validate_percentage",
    "validate_ratio",
    "validate_positive_int",
    "validate_company_name",
    # ESG指标验证
    "validate_esg_metrics",
    "validate_emissions_value",
    "validate_carbon_intensity",
    "validate_water_intensity",
    "validate_training_hours",
    "validate_non_negative_number",
]
