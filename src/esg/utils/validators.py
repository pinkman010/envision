"""数据验证模块

提供各类数据验证功能，包括ESG指标验证、文件验证等。
"""

import math
import os
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

# 验证结果类型
ValidationResult = Tuple[bool, str]


def validate_pdf(
    file_path: Union[str, Path], max_size: int = 100 * 1024 * 1024  # 默认100MB
) -> ValidationResult:
    """验证PDF文件是否有效

    Args:
        file_path: PDF文件路径
        max_size: 最大文件大小（字节）

    Returns:
        (是否有效, 消息)
    """
    path = Path(file_path)

    # 检查文件是否存在
    if not path.exists():
        return (False, f"文件不存在: {file_path}")

    # 检查是否为文件
    if not path.is_file():
        return (False, f"路径不是文件: {file_path}")

    # 检查扩展名
    if path.suffix.lower() != ".pdf":
        return (False, f"不支持的文件类型: {path.suffix}，仅支持 .pdf")

    # 检查文件大小
    if path.stat().st_size > max_size:
        return (
            False,
            f"文件大小超过限制: {path.stat().st_size / (1024*1024):.1f}MB > {max_size/(1024*1024):.0f}MB",
        )

    # 检查文件是否为空
    if path.stat().st_size == 0:
        return (False, "文件为空")

    # 检查PDF头
    try:
        with open(path, "rb") as f:
            header = f.read(5)
            if not header.startswith(b"%PDF-"):
                return (False, "不是有效的 PDF 格式")
    except Exception as e:
        return (False, f"读取文件失败: {str(e)}")

    return (True, "验证通过")


def validate_year(year: Any) -> ValidationResult:
    """验证年份是否有效

    Args:
        year: 年份值，可以是int或str

    Returns:
        (是否有效, 消息)
    """
    import datetime

    if year is None:
        return (False, "年份不能为空")

    # 尝试转换为整数
    try:
        if isinstance(year, str):
            year = int(year.strip())
        elif isinstance(year, float):
            if math.isnan(year) or math.isinf(year):
                return (False, "年份必须是有效的数字")
            year = int(year)
    except (ValueError, TypeError):
        return (False, "年份必须是有效的数字")

    current_year = datetime.datetime.now().year

    if year < 2000:
        return (False, f"年份必须大于等于 2000，当前: {year}")

    if year > current_year + 1:
        return (False, f"年份必须小于等于 {current_year + 1}，当前: {year}")

    return (True, "验证通过")


def validate_score(score: Any) -> ValidationResult:
    """验证评分是否有效（0-100）

    Args:
        score: 评分值

    Returns:
        (是否有效, 消息)
    """
    if score is None:
        return (False, "评分不能为空")

    try:
        if isinstance(score, str):
            score = float(score.strip())
        else:
            score = float(score)
    except (ValueError, TypeError):
        return (False, "评分必须是有效的数字")

    if math.isnan(score):
        return (False, "评分不能为 NaN")

    if math.isinf(score):
        return (False, "评分不能为无穷大")

    if score < 0:
        return (False, f"评分不能小于 0，当前: {score}")

    if score > 100:
        return (False, f"评分不能大于 100，当前: {score}")

    return (True, "验证通过")


def validate_company_code(code: Any) -> ValidationResult:
    """验证公司代码是否有效

    Args:
        code: 公司代码

    Returns:
        (是否有效, 消息)
    """
    if code is None:
        return (False, "公司代码不能为空")

    if isinstance(code, str):
        code = code.strip()

    if not code:
        return (False, "公司代码不能为空")

    if len(code) < 4 or len(code) > 10:
        return (False, f"公司代码长度应在 4-10 个字符，当前: {len(code)}")

    return (True, "验证通过")


def validate_report_year_range(start_year: int, end_year: int) -> ValidationResult:
    """验证报告年份范围是否有效

    Args:
        start_year: 起始年份
        end_year: 结束年份

    Returns:
        (是否有效, 消息)
    """
    # 验证起始年份
    is_valid, msg = validate_year(start_year)
    if not is_valid:
        return (False, f"起始年份无效: {msg}")

    # 验证结束年份
    is_valid, msg = validate_year(end_year)
    if not is_valid:
        return (False, f"结束年份无效: {msg}")

    if start_year > end_year:
        return (False, "起始年份不能大于结束年份")

    if end_year - start_year > 20:
        return (False, "年份范围不能超过 20 年")

    return (True, "验证通过")


def validate_percentage(value: Any, field_name: str = "百分比") -> ValidationResult:
    """验证百分比值是否有效（0-100）

    Args:
        value: 百分比值
        field_name: 字段名称（用于错误消息）

    Returns:
        (是否有效, 消息)
    """
    if value is None:
        return (False, f"{field_name}不能为空")

    try:
        if isinstance(value, str):
            value = float(value.strip())
        else:
            value = float(value)
    except (ValueError, TypeError):
        return (False, f"{field_name}必须是有效的数字")

    if math.isnan(value):
        return (False, f"{field_name}不能为 NaN")

    if math.isinf(value):
        return (False, f"{field_name}不能为无穷大")

    if value < 0:
        return (False, f"{field_name}不能小于 0，当前: {value}")

    if value > 100:
        return (False, f"{field_name}不能大于 100，当前: {value}")

    return (True, "验证通过")


def validate_ratio(value: Any, field_name: str = "比例") -> ValidationResult:
    """验证比例值是否有效（0-1）

    Args:
        value: 比例值
        field_name: 字段名称（用于错误消息）

    Returns:
        (是否有效, 消息)
    """
    if value is None:
        return (False, f"{field_name}不能为空")

    try:
        if isinstance(value, str):
            value = float(value.strip())
        else:
            value = float(value)
    except (ValueError, TypeError):
        return (False, f"{field_name}必须是有效的数字")

    if math.isnan(value):
        return (False, f"{field_name}不能为 NaN")

    if math.isinf(value):
        return (False, f"{field_name}不能为无穷大")

    if value < 0:
        return (False, f"{field_name}不能小于 0，当前: {value}")

    if value > 1:
        return (False, f"{field_name}不能大于 1，当前: {value}")

    return (True, "验证通过")


def validate_positive_int(value: Any, field_name: str = "正整数") -> ValidationResult:
    """验证正整数是否有效

    Args:
        value: 整数值
        field_name: 字段名称（用于错误消息）

    Returns:
        (是否有效, 消息)
    """
    if value is None:
        return (False, f"{field_name}不能为空")

    try:
        if isinstance(value, str):
            value = int(value.strip())
        else:
            value = int(value)
    except (ValueError, TypeError):
        return (False, f"{field_name}必须是有效的整数")

    if value <= 0:
        return (False, f"{field_name}必须是正整数，当前: {value}")

    return (True, "验证通过")


def validate_non_negative_number(value: Any, field_name: str = "数值") -> ValidationResult:
    """验证非负数是否有效

    Args:
        value: 数值
        field_name: 字段名称（用于错误消息）

    Returns:
        (是否有效, 消息)
    """
    if value is None:
        return (False, f"{field_name}不能为空")

    try:
        if isinstance(value, str):
            value = float(value.strip())
        else:
            value = float(value)
    except (ValueError, TypeError):
        return (False, f"{field_name}必须是有效的数字")

    if math.isnan(value):
        return (False, f"{field_name}不能为 NaN")

    if math.isinf(value):
        return (False, f"{field_name}不能为无穷大")

    if value < 0:
        return (False, f"{field_name}不能为负数，当前: {value}")

    return (True, "验证通过")


def validate_company_name(name: Any) -> ValidationResult:
    """验证公司名称是否有效

    Args:
        name: 公司名称

    Returns:
        (是否有效, 消息)
    """
    if name is None:
        return (False, "公司名称不能为空")

    if isinstance(name, str):
        name = name.strip()

    if not name:
        return (False, "公司名称不能为空或仅包含空白字符")

    if len(name) > 100:
        return (False, f"公司名称长度不能超过 100 个字符，当前: {len(name)}")

    # 检查非法字符
    illegal_patterns = ["<script", "javascript:", "onerror=", "onclick="]
    name_lower = name.lower()
    for pattern in illegal_patterns:
        if pattern in name_lower:
            return (False, f"公司名称包含非法字符")

    return (True, "验证通过")


def validate_emissions_value(value: Any, field_name: str = "排放量") -> ValidationResult:
    """验证排放量值是否有效（非负数）

    Args:
        value: 排放量值
        field_name: 字段名称（用于错误消息）

    Returns:
        (是否有效, 消息)
    """
    if value is None:
        return (False, f"{field_name}不能为空")

    try:
        if isinstance(value, str):
            value = float(value.strip())
        else:
            value = float(value)
    except (ValueError, TypeError):
        return (False, f"{field_name}必须是有效的数字")

    if math.isnan(value):
        return (False, f"{field_name}不能为 NaN")

    if math.isinf(value):
        return (False, f"{field_name}不能为无穷大")

    if value < 0:
        return (False, f"{field_name}不能为负数，当前: {value}")

    return (True, "验证通过")


def validate_carbon_intensity(value: Any) -> ValidationResult:
    """验证碳强度值是否有效（非负数）

    Args:
        value: 碳强度值

    Returns:
        (是否有效, 消息)
    """
    return validate_non_negative_number(value, "碳强度")


def validate_water_intensity(value: Any) -> ValidationResult:
    """验证水资源强度值是否有效（非负数）

    Args:
        value: 水资源强度值

    Returns:
        (是否有效, 消息)
    """
    return validate_non_negative_number(value, "水资源强度")


def validate_training_hours(hours: Any) -> ValidationResult:
    """验证培训时长是否有效

    Args:
        hours: 培训小时数

    Returns:
        (是否有效, 消息)
    """
    if hours is None:
        return (False, "培训时长不能为空")

    try:
        if isinstance(hours, str):
            hours = float(hours.strip())
        else:
            hours = float(hours)
    except (ValueError, TypeError):
        return (False, "培训时长必须是有效的数字")

    if math.isnan(hours) or math.isinf(hours):
        return (False, "培训时长不能为 NaN 或无穷大")

    if hours < 0:
        return (False, f"培训时长不能为负数，当前: {hours}")

    if hours > 8760:  # 一年的小时数
        return (False, f"培训时长超过 8760 小时（一年），当前: {hours}")

    return (True, "验证通过")


# ============================================================================
# ESG指标验证规则配置 (配置驱动模式)
# ============================================================================
# 使用配置驱动代替硬编码的if分支，降低圈复杂度

ESG_METRICS_VALIDATION_RULES = [
    # 必填字段验证
    {
        "field": "company_name",
        "validator": validate_company_name,
        "required": True,
        "label": "公司名称",
    },
    {"field": "year", "validator": validate_year, "required": True, "label": "年份"},
    # 百分比字段验证 (0-100)
    {
        "field": "renewable_energy_ratio",
        "validator": validate_percentage,
        "label": "可再生能源占比",
    },
    {"field": "energy_efficiency", "validator": validate_percentage, "label": "能源效率"},
    {"field": "waste_recycling_rate", "validator": validate_percentage, "label": "废物回收率"},
    {
        "field": "ethics_training_coverage",
        "validator": validate_percentage,
        "label": "道德培训覆盖率",
    },
    {"field": "esg_report_quality", "validator": validate_percentage, "label": "ESG报告质量"},
    # 比例字段验证 (0-1)
    {"field": "female_ratio", "validator": validate_ratio, "label": "女性员工比例"},
    {"field": "board_independence_ratio", "validator": validate_ratio, "label": "独立董事比例"},
    # 正整数字段验证
    {"field": "employee_count", "validator": validate_positive_int, "label": "员工数量"},
    # 非负数字段验证
    {"field": "carbon_emissions", "validator": validate_non_negative_number, "label": "碳排放量"},
    {"field": "safety_incidents", "validator": validate_non_negative_number, "label": "安全事故数"},
    # 强度字段验证
    {"field": "carbon_intensity", "validator": validate_carbon_intensity, "label": "碳强度"},
    {"field": "water_intensity", "validator": validate_water_intensity, "label": "水资源强度"},
    # 培训时长验证
    {"field": "training_hours", "validator": validate_training_hours, "label": "培训时长"},
]


def _validate_field(metrics: Any, rule: dict) -> Optional[str]:
    """验证单个字段

    Args:
        metrics: ESG指标对象
        rule: 验证规则字典

    Returns:
        错误消息，如果验证通过则返回None
    """
    field = rule["field"]
    validator = rule["validator"]
    label = rule["label"]

    # 获取字段值
    value = getattr(metrics, field, None)

    # 处理特殊字段映射
    if value is None and field == "safety_incidents":
        value = getattr(metrics, "incident_count", None)

    # 必填字段验证
    if rule.get("required", False):
        if value is None:
            return f"{label}不能为空"
        is_valid, msg = validator(value)
        if not is_valid:
            return f"{label}: {msg}"
        return None

    # 可选字段验证（仅当值不为None时）
    if value is not None:
        is_valid, msg = validator(value)
        if not is_valid:
            return f"{label}: {msg}"

    return None


def validate_esg_metrics(metrics: Any) -> Tuple[bool, List[str]]:
    """验证ESG指标对象是否有效

    Args:
        metrics: ESGMetrics对象

    Returns:
        (是否有效, 错误列表)
    """
    from src.esg.core.models import ESGMetrics

    if not isinstance(metrics, ESGMetrics):
        return (False, ["无效的ESG指标对象"])

    # 使用配置驱动的验证方式，替代30个独立if分支
    errors = []
    for rule in ESG_METRICS_VALIDATION_RULES:
        error_msg = _validate_field(metrics, rule)
        if error_msg:
            errors.append(error_msg)

    return (len(errors) == 0, errors)


# 导出所有验证函数
__all__ = [
    "validate_pdf",
    "validate_year",
    "validate_score",
    "validate_company_code",
    "validate_report_year_range",
    "validate_percentage",
    "validate_ratio",
    "validate_positive_int",
    "validate_non_negative_number",
    "validate_company_name",
    "validate_emissions_value",
    "validate_carbon_intensity",
    "validate_water_intensity",
    "validate_training_hours",
    "validate_esg_metrics",
]
