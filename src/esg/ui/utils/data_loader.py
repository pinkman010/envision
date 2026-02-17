"""数据加载模块

提供示例数据加载功能。
"""

from src.esg.core.models import ESGMetrics


def load_demo_metrics() -> ESGMetrics:
    """加载示例ESG指标数据（绿色能源集团）

    Returns:
        ESGMetrics对象
    """
    return ESGMetrics(
        company_name="绿色能源集团",
        year="2024",
        industry_sector="wind_power",
        # 环境指标
        carbon_emissions=50000,
        scope1_emissions=20000,
        scope2_emissions_location=15000,
        scope2_emissions_market=10000,
        scope3_emissions=150000,
        carbon_intensity=0.12,
        renewable_energy_ratio=0.85,
        energy_efficiency=0.92,
        water_intensity=8.0,
        waste_recycling_rate=0.95,
        turbine_availability=0.98,
        curtailment_rate=1.5,
        # 社会指标
        employee_count=8000,
        female_ratio=0.42,
        female_executive_ratio=0.35,
        training_hours=60,
        training_investment_per_employee=800,
        trir=0.3,
        ltifr=0.1,
        safety_investment_ratio=0.025,
        local_employment_ratio=0.80,
        community_investment=8000000,
        community_investment_per_revenue=0.015,
        # 治理指标
        board_independence_ratio=0.55,
        esg_committee_independence=0.90,
        ethics_training_coverage=0.98,
        anti_corruption_training_coverage=0.95,
        esg_report_quality=92,
        whistleblower_protection=True,
        # 元数据
        source="示例数据",
    )