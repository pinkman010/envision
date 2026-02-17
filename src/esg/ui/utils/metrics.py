"""指标工具模块

提供指标创建和转换功能。
"""

from typing import Any, Dict, Optional

from src.esg.core.models import ESGMetrics


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """安全地将值转换为 float 类型

    Args:
        value: 原始值（可能是字符串、数字或None）
        default: 转换失败时的默认值

    Returns:
        转换后的 float 或 default
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """安全地将值转换为 int 类型

    Args:
        value: 原始值（可能是字符串、数字或None）
        default: 转换失败时的默认值

    Returns:
        转换后的 int 或 default
    """
    if value is None:
        return default
    try:
        return int(float(value))  # 先转 float 再转 int，处理 "123.0" 的情况
    except (ValueError, TypeError):
        return default


def _safe_bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    """安全地将值转换为 bool 类型

    Args:
        value: 原始值（可能是字符串、布尔或None）
        default: 转换失败时的默认值

    Returns:
        转换后的 bool 或 default
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "是")
    return bool(value)


def create_metrics_from_extraction(extraction_result: Dict[str, Any]) -> ESGMetrics:
    """从PDF提取结果创建ESGMetrics对象

    支持两种输入格式：
    1. MetricExtractor.extract() 返回的 Dict[str, ExtractedMetric] 格式
    2. 带有 environmental/social/governance 子字典的格式

    Args:
        extraction_result: PDF提取结果字典

    Returns:
        ESGMetrics对象
    """
    # 提取基本信息
    company_name = extraction_result.get("company_name", "未知公司")
    year = extraction_result.get("year", "2024")

    # 创建ESGMetrics对象
    metrics = ESGMetrics(
        company_name=company_name,
        year=year,
        source="PDF提取",
    )

    # 检查是否是 MetricExtractor.extract() 返回的格式（扁平字典，值为 ExtractedMetric 对象）
    # 这种格式下，key 是指标名称，value 是 ExtractedMetric 或字典
    def get_metric_value(data: Any, key: str) -> Optional[float]:
        """从提取结果中获取指标值，支持多种格式"""
        if key not in data:
            return None
        value = data[key]
        # ExtractedMetric 对象有 value 属性
        if hasattr(value, "value"):
            return float(value.value)
        # 字典格式
        if isinstance(value, dict) and "value" in value:
            return _safe_float(value["value"])
        # 直接是数值
        if isinstance(value, (int, float)):
            return float(value)
        # 字符串
        if isinstance(value, str):
            return _safe_float(value)
        return None

    # 环境指标映射
    env_mappings = {
        "carbon_emissions": "carbon_emissions",
        "carbon_intensity": "carbon_intensity",
        "renewable_energy_ratio": "renewable_energy_ratio",
        "energy_efficiency": "energy_efficiency",
        "water_consumption": "water_consumption",
        "water_intensity": "water_intensity",
        "waste_recycling_rate": "waste_recycling_rate",
    }

    # 社会指标映射
    social_mappings = {
        "employee_count": "employee_count",
        "female_ratio": "female_ratio",
        "female_executive_ratio": "female_executive_ratio",
        "training_hours": "training_hours",
        "safety_incidents": "safety_incidents",
        "trir": "trir",
        "ltifr": "ltifr",
        "community_investment": "community_investment",
    }

    # 治理指标映射
    gov_mappings = {
        "board_independence_ratio": "board_independence_ratio",
        "ethics_training_coverage": "ethics_training_coverage",
        "esg_report_quality": "esg_report_quality",
        "anti_corruption_training_coverage": "anti_corruption_training_coverage",
    }

    # 如果是嵌套格式（带 environmental/social/governance 子字典）
    if "environmental" in extraction_result:
        env = extraction_result["environmental"]
        if isinstance(env, dict):
            for src_key, dst_attr in env_mappings.items():
                if src_key in env:
                    setattr(metrics, dst_attr, _safe_float(env[src_key]))

    if "social" in extraction_result:
        social = extraction_result["social"]
        if isinstance(social, dict):
            for src_key, dst_attr in social_mappings.items():
                if src_key in social:
                    if dst_attr == "employee_count":
                        setattr(metrics, dst_attr, _safe_int(social[src_key]))
                    else:
                        setattr(metrics, dst_attr, _safe_float(social[src_key]))

    if "governance" in extraction_result:
        gov = extraction_result["governance"]
        if isinstance(gov, dict):
            for src_key, dst_attr in gov_mappings.items():
                if src_key in gov:
                    setattr(metrics, dst_attr, _safe_float(gov[src_key]))
            # 布尔类型单独处理
            if "whistleblower_protection" in gov:
                metrics.whistleblower_protection = _safe_bool(gov["whistleblower_protection"])

    # 处理扁平格式（MetricExtractor.extract() 返回的格式）
    # 直接从根级别提取指标
    for src_key, dst_attr in env_mappings.items():
        if src_key in extraction_result and getattr(metrics, dst_attr) is None:
            value = get_metric_value(extraction_result, src_key)
            if value is not None:
                setattr(metrics, dst_attr, value)

    for src_key, dst_attr in social_mappings.items():
        if src_key in extraction_result and getattr(metrics, dst_attr) is None:
            value = get_metric_value(extraction_result, src_key)
            if value is not None:
                if dst_attr == "employee_count":
                    setattr(metrics, dst_attr, int(value))
                else:
                    setattr(metrics, dst_attr, value)

    for src_key, dst_attr in gov_mappings.items():
        if src_key in extraction_result and getattr(metrics, dst_attr) is None:
            value = get_metric_value(extraction_result, src_key)
            if value is not None:
                setattr(metrics, dst_attr, value)

    return metrics


def create_metrics_from_form(form_data: Dict[str, Any], company_name: str, year: str) -> ESGMetrics:
    """从表单数据创建ESGMetrics对象

    Args:
        form_data: 表单数据字典
        company_name: 公司名称
        year: 年份

    Returns:
        ESGMetrics对象
    """
    return ESGMetrics(
        company_name=company_name,
        year=year,
        # 环境指标
        carbon_emissions=form_data.get("carbon_emissions"),
        carbon_intensity=form_data.get("carbon_intensity"),
        renewable_energy_ratio=form_data.get("renewable_energy_ratio"),
        energy_efficiency=form_data.get("energy_efficiency"),
        water_consumption=form_data.get("water_consumption"),
        water_intensity=form_data.get("water_intensity"),
        waste_recycling_rate=form_data.get("waste_recycling_rate"),
        # 社会指标
        employee_count=form_data.get("employee_count"),
        female_ratio=form_data.get("female_ratio"),
        female_executive_ratio=form_data.get("female_executive_ratio"),
        training_hours=form_data.get("training_hours"),
        safety_incidents=form_data.get("safety_incidents"),
        trir=form_data.get("trir"),
        community_investment=form_data.get("community_investment"),
        # 治理指标
        board_independence_ratio=form_data.get("board_independence_ratio"),
        ethics_training_coverage=form_data.get("ethics_training_coverage"),
        esg_report_quality=form_data.get("esg_report_quality"),
        anti_corruption_training_coverage=form_data.get("anti_corruption_training_coverage"),
        whistleblower_protection=form_data.get("whistleblower_protection"),
        # 元数据
        source="手动输入",
    )
