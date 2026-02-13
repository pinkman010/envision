"""ESG指标验证模块

提供ESG相关指标的验证功能。
"""

import math
from typing import Any, Dict, List, Tuple, Union

from src.esg.utils.validators.base import validate_year
from src.esg.utils.validators.fields import (
    validate_company_name,
    validate_percentage,
    validate_positive_int,
    validate_score,
)


def validate_non_negative_number(
    value: Union[int, float, str], 
    field_name: str = "数值"
) -> Tuple[bool, str]:
    """验证非负数值的合法性
    
    检查给定的值是否为非负数（大于等于 0）。
    
    Args:
        value: 数值
        field_name: 字段名称
    
    Returns:
        (is_valid, message) 元组
    """
    try:
        value_float = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name}必须是有效的数字，收到: {value}"
    
    # 检查是否为有效数值
    if math.isnan(value_float):
        return False, f"{field_name}不能为 NaN"
    
    if math.isinf(value_float):
        return False, f"{field_name}不能为无穷大"
    
    # 检查是否为非负数
    if value_float < 0:
        return False, f"{field_name}不能为负数，收到: {value_float}"
    
    return True, "验证通过"


def validate_emissions_value(
    value: Union[int, float, str], 
    field_name: str = "排放量"
) -> Tuple[bool, str]:
    """验证碳排放量的合法性
    
    检查碳排放量值是否合法（非负）。
    
    Args:
        value: 排放量值
        field_name: 字段名称
    
    Returns:
        (is_valid, message) 元组
    """
    return validate_non_negative_number(value, field_name)


def validate_carbon_intensity(value: Union[int, float, str]) -> Tuple[bool, str]:
    """验证碳强度的合法性
    
    检查碳强度值（吨CO2e/万元营收）是否合法。
    
    Args:
        value: 碳强度值
    
    Returns:
        (is_valid, message) 元组
    """
    return validate_non_negative_number(value, "碳强度")


def validate_water_intensity(value: Union[int, float, str]) -> Tuple[bool, str]:
    """验证水资源强度的合法性
    
    检查水资源强度值（立方米/万元营收）是否合法。
    
    Args:
        value: 水资源强度值
    
    Returns:
        (is_valid, message) 元组
    """
    return validate_non_negative_number(value, "水资源强度")


def validate_training_hours(value: Union[int, float, str]) -> Tuple[bool, str]:
    """验证培训时长的合法性
    
    检查人均培训时长是否合法（非负，且不超过合理上限）。
    
    Args:
        value: 培训时长（小时）
    
    Returns:
        (is_valid, message) 元组
    """
    # 先验证是否为非负数
    valid, msg = validate_non_negative_number(value, "人均培训时长")
    if not valid:
        return valid, msg
    
    # 检查合理上限（一年最多 8760 小时）
    value_float = float(value)
    if value_float > 8760:
        return False, f"培训时长不合理，超过 8760 小时（一年总小时数），收到: {value_float}"
    
    return True, "验证通过"


def validate_esg_metrics(metrics) -> Tuple[bool, List[str]]:
    """验证 ESGMetrics 对象的完整性
    
    检查 ESGMetrics 对象的所有字段是否符合规范。
    
    Args:
        metrics: ESGMetrics 对象
    
    Returns:
        (is_valid, errors) 元组
    """
    errors: List[str] = []
    
    # 验证必填字段
    if not metrics.company_name:
        errors.append("公司名称不能为空")
    else:
        valid, msg = validate_company_name(metrics.company_name)
        if not valid:
            errors.append(f"公司名称无效: {msg}")
    
    if not metrics.year:
        errors.append("年份不能为空")
    else:
        valid, msg = validate_year(metrics.year)
        if not valid:
            errors.append(f"年份无效: {msg}")
    
    # 验证百分比字段（0-100）
    percentage_fields: Dict[str, str] = {
        "renewable_energy_ratio": "可再生能源占比",
        "energy_efficiency": "能源效率",
        "waste_recycling_rate": "废物回收率",
        "female_ratio": "女性员工比例",
        "board_independence_ratio": "董事会独立董事比例",
        "ethics_training_coverage": "道德培训覆盖率",
        "turbine_availability": "风机可利用率",
        "battery_recycling_rate": "电池回收率",
        "electrolysis_efficiency": "电解效率",
    }
    
    for field_name, display_name in percentage_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_percentage(value, display_name)
            if not valid:
                errors.append(msg)
    
    # 验证 0-100 评分字段
    score_fields: Dict[str, str] = {
        "biodiversity_impact_score": "生物多样性影响评分",
        "energy_storage_safety_score": "储能安全评分",
        "esg_report_quality": "ESG报告质量评分",
    }
    
    for field_name, display_name in score_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_score(value)
            if not valid:
                errors.append(f"{display_name}: {msg}")
    
    # 验证正整数字段
    positive_int_fields: Dict[str, str] = {
        "employee_count": "员工数量",
        "battery_cycle_life": "电池循环寿命",
    }
    
    for field_name, display_name in positive_int_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_positive_int(value, display_name)
            if not valid:
                errors.append(msg)
    
    # 验证非负整数字段（安全事故数可以为0）
    if metrics.safety_incidents is not None:
        if metrics.safety_incidents < 0:
            errors.append("安全事故数不能为负数")
    
    # 验证排放量字段（非负）
    emissions_fields: Dict[str, str] = {
        "carbon_emissions": "总碳排放量",
        "scope1_emissions": "范围1排放",
        "scope2_emissions_location": "范围2排放（位置法）",
        "scope2_emissions_market": "范围2排放（市场法）",
        "scope3_emissions": "范围3排放",
    }
    
    for field_name, display_name in emissions_fields.items():
        value = getattr(metrics, field_name, None)
        if value is not None:
            valid, msg = validate_emissions_value(value, display_name)
            if not valid:
                errors.append(msg)
    
    # 验证强度字段
    if metrics.carbon_intensity is not None:
        valid, msg = validate_carbon_intensity(metrics.carbon_intensity)
        if not valid:
            errors.append(msg)
    
    if metrics.water_intensity is not None:
        valid, msg = validate_water_intensity(metrics.water_intensity)
        if not valid:
            errors.append(msg)
    
    # 验证用水量（非负）
    if metrics.water_consumption is not None:
        valid, msg = validate_non_negative_number(metrics.water_consumption, "用水量")
        if not valid:
            errors.append(msg)
    
    # 验证社区投资金额（非负）
    if metrics.community_investment is not None:
        valid, msg = validate_non_negative_number(metrics.community_investment, "社区投资金额")
        if not valid:
            errors.append(msg)
    
    # 验证培训时长
    if metrics.training_hours is not None:
        valid, msg = validate_training_hours(metrics.training_hours)
        if not valid:
            errors.append(msg)
    
    return len(errors) == 0, errors
