"""指标处理工具模块

提供从PDF提取结果创建ESG指标对象的功能。
"""

from typing import Any, Dict, Optional

from src.esg.core.models import ESGMetrics


def create_metrics_from_extraction(result: Any) -> ESGMetrics:
    """从提取结果创建ESGMetrics对象

    Args:
        result: PDF提取结果对象

    Returns:
        ESGMetrics对象
    """
    metrics_dict: Dict[str, Any] = result.metrics

    def get_value(name: str, default: Optional[float] = None) -> Optional[float]:
        """从指标字典中获取值

        安全地从提取结果字典中获取指定指标的值，
        如果指标不存在则返回默认值。

        Args:
            name: 指标名称
            default: 默认值，当指标不存在时返回

        Returns:
            指标值或默认值
        """
        # 边界条件检查：参数有效性
        if not isinstance(name, str) or not name.strip():
            return default

        metric = metrics_dict.get(name)

        # 边界条件检查：确保metric有value属性
        if metric is None:
            return default

        # 返回指标值
        return metric.value if hasattr(metric, "value") else default

    return ESGMetrics(
        company_name=result.company_name,
        year=result.year,
        carbon_emissions=get_value("carbon_emissions"),
        renewable_energy_ratio=get_value("renewable_energy_ratio"),
        energy_efficiency=get_value("energy_efficiency"),
        water_consumption=get_value("water_consumption"),
        waste_recycling_rate=get_value("waste_recycling_rate"),
        employee_count=int(get_value("employee_count", 0)) if get_value("employee_count") else None,
        female_ratio=get_value("female_ratio"),
        training_hours=get_value("training_hours"),
        safety_incidents=(
            int(get_value("safety_incidents", 0)) if get_value("safety_incidents") else None
        ),
        community_investment=get_value("community_investment"),
        board_independence_ratio=get_value("board_independence_ratio"),
        ethics_training_coverage=get_value("ethics_training_coverage"),
        esg_report_quality=get_value("esg_report_quality"),
        source="PDF提取",
        confidence={k: v.confidence for k, v in metrics_dict.items() if v is not None},
    )
