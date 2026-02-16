"""数据加载工具模块

提供示例数据加载功能。
"""

from typing import Any, Dict

from src.esg.core.models import ESGMetrics


def load_demo_metrics(case_type: str) -> ESGMetrics:
    """加载示例指标数据

    Args:
        case_type: 案例类型 (excellent/average/poor)

    Returns:
        ESGMetrics对象
    """
    demo_data: Dict[str, Dict[str, Any]] = {
        "excellent": {
            "name": "绿色能源集团",
            "carbon": 50000,
            "renewable": 0.85,
            "efficiency": 92,
            "employees": 5000,
            "female": 0.45,
            "training": 50,
            "board": 0.60,
            "ethics": 0.90,
            "report": 90,
        },
        "average": {
            "name": "新能源科技有限公司",
            "carbon": 150000,
            "renewable": 0.45,
            "efficiency": 75,
            "employees": 3000,
            "female": 0.35,
            "training": 30,
            "board": 0.40,
            "ethics": 0.70,
            "report": 75,
        },
        "poor": {
            "name": "传统能源企业",
            "carbon": 500000,
            "renewable": 0.15,
            "efficiency": 55,
            "employees": 2000,
            "female": 0.25,
            "training": 15,
            "board": 0.25,
            "ethics": 0.50,
            "report": 60,
        },
    }

    data = demo_data.get(case_type, demo_data["average"])

    return ESGMetrics(
        company_name=data["name"],
        year="2024",
        carbon_emissions=data["carbon"],
        renewable_energy_ratio=data["renewable"],
        energy_efficiency=data["efficiency"],
        waste_recycling_rate=0.7,
        employee_count=data["employees"],
        female_ratio=data["female"],
        training_hours=data["training"],
        safety_incidents=2,
        community_investment=5000000,
        board_independence_ratio=data["board"],
        ethics_training_coverage=data["ethics"],
        esg_report_quality=data["report"],
        source="示例数据",
    )
