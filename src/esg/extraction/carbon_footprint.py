"""碳足迹计算模块

提供碳排放计算、范围1/2/3排放估算、碳强度分析等功能。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

# 配置日志
logger = logging.getLogger(__name__)


class EmissionScope(Enum):
    """排放范围枚举"""

    SCOPE_1 = "scope_1"  # 直接排放
    SCOPE_2_LOCATION = "scope_2_location"  # 范围2基于位置
    SCOPE_2_MARKET = "scope_2_market"  # 范围2基于市场
    SCOPE_3 = "scope_3"  # 价值链间接排放


class EmissionCategory(Enum):
    """排放类别"""

    STATIONARY_COMBUSTION = "stationary_combustion"
    MOBILE_COMBUSTION = "mobile_combustion"
    PROCESS_EMISSIONS = "process_emissions"
    FUGITIVE_EMISSIONS = "fugitive_emissions"
    PURCHASED_ELECTRICITY = "purchased_electricity"
    PURCHASED_HEAT = "purchased_heat"
    PURCHASED_STEAM = "purchased_steam"
    PURCHASED_COOLING = "purchased_cooling"
    UPSTREAM_TRANSPORT = "upstream_transport"
    BUSINESS_TRAVEL = "business_travel"
    EMPLOYEE_COMMUTING = "employee_commuting"
    DOWNSTREAM_TRANSPORT = "downstream_transport"
    USE_OF_SOLD_PRODUCTS = "use_of_sold_products"
    END_OF_LIFE_TREATMENT = "end_of_life_treatment"
    INVESTMENTS = "investments"


# 排放因子（吨CO2e/单位）
EMISSION_FACTORS = {
    # 燃料排放因子
    "diesel": 2.68,  # 升
    "gasoline": 2.31,  # 升
    "natural_gas": 2.02,  # 立方米
    "coal": 2.62,  # 千克
    "lpg": 1.51,  # 千克
    "fuel_oil": 3.15,  # 升
    # 电力排放因子（区域平均）
    "electricity_grid": 0.5703,  # 千克CO2e/kWh（中国2022年）
    "electricity_renewable": 0.0,  # 可再生电力
    # 交通排放因子
    "air_travel_domestic": 0.255,  # 千克CO2e/乘客公里
    "air_travel_international": 0.195,  # 千克CO2e/乘客公里
    "rail": 0.041,  # 千克CO2e/乘客公里
    "taxi": 0.210,  # 千克CO2e/公里
    "bus": 0.105,  # 千克CO2e/乘客公里
}

# 范围3排放估算系数
SCOPE_3_ESTIMATION_FACTORS = {
    "purchased_goods": 0.15,  # 占采购金额比例
    "capital_goods": 0.10,
    "fuel_energy_related": 0.05,
    "upstream_transport": 0.08,
    "waste": 0.02,
    "business_travel": 0.03,
    "employee_commuting": 0.04,
    "upstream_leased": 0.02,
    "downstream_transport": 0.06,
    "processing_sold": 0.07,
    "use_of_sold": 0.20,
    "end_of_life": 0.04,
    "downstream_leased": 0.01,
    "franchises": 0.00,
    "investments": 0.13,
}


@dataclass
class EmissionSource:
    """排放源数据类"""

    category: EmissionCategory
    source_name: str
    quantity: float
    unit: str
    emission_factor: float  # 吨CO2e/单位
    calculation_method: str = "default"

    def calculate_emissions(self) -> float:
        """计算排放量"""
        return self.quantity * self.emission_factor


@dataclass
class CarbonFootprintResult:
    """碳足迹计算结果"""

    total_emissions: float  # 总排放（吨CO2e）
    scope1_emissions: float
    scope2_location_emissions: float
    scope2_market_emissions: Optional[float]
    scope3_emissions: float

    # 按类别细分
    emissions_by_category: Dict[EmissionCategory, float] = field(default_factory=dict)

    # 时间范围
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # 业务指标
    revenue: Optional[float] = None  # 万元
    employee_count: Optional[int] = None
    production_volume: Optional[float] = None

    # 强度指标
    carbon_intensity_revenue: Optional[float] = None  # 吨CO2e/万元
    carbon_intensity_production: Optional[float] = None  # 吨CO2e/单位产量
    carbon_intensity_employee: Optional[float] = None  # 吨CO2e/员工

    # 计算信息
    calculation_date: datetime = field(default_factory=datetime.now)
    methodology: str = "GHG Protocol"

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "total_emissions": self.total_emissions,
            "scope1_emissions": self.scope1_emissions,
            "scope2_location_emissions": self.scope2_location_emissions,
            "scope2_market_emissions": self.scope2_market_emissions,
            "scope3_emissions": self.scope3_emissions,
            "emissions_by_category": {k.value: v for k, v in self.emissions_by_category.items()},
            "scope1_2_total": self.scope1_emissions + self.scope2_location_emissions,
            "scope1_2_3_total": self.total_emissions,
            "carbon_intensity": {
                "per_revenue": self.carbon_intensity_revenue,
                "per_production": self.carbon_intensity_production,
                "per_employee": self.carbon_intensity_employee,
            },
            "methodology": self.methodology,
            "calculation_date": self.calculation_date.isoformat(),
        }


class CarbonFootprintCalculator:
    """碳足迹计算器

    计算企业碳排放足迹，支持范围1/2/3。

    Example:
        >>> calculator = CarbonFootprintCalculator()
        >>>
        >>> # 添加排放源
        >>> calculator.add_emission_source(
        ...     category=EmissionCategory.STATIONARY_COMBUSTION,
        ...     source_name="天然气锅炉",
        ...     quantity=10000,  # 立方米
        ...     unit="m3",
        ...     emission_factor=2.02  # kgCO2e/m3
        ... )
        >>>
        >>> # 计算碳足迹
        >>> result = calculator.calculate(
        ...     revenue=100000,  # 万元
        ...     employee_count=500
        ... )
    """

    def __init__(self):
        """初始化碳足迹计算器"""
        self.emission_sources: List[EmissionSource] = []
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None

    def add_emission_source(
        self,
        category: EmissionCategory,
        source_name: str,
        quantity: float,
        unit: str,
        emission_factor: Optional[float] = None,
        calculation_method: str = "default",
    ):
        """添加排放源

        Args:
            category: 排放类别
            source_name: 排放源名称
            quantity: 数量
            unit: 单位
            emission_factor: 排放因子，None则从默认因子查找
            calculation_method: 计算方法
        """
        if emission_factor is None:
            # 尝试从默认因子查找
            factor_key = source_name.lower().replace(" ", "_")
            emission_factor = EMISSION_FACTORS.get(factor_key, 0)

        source = EmissionSource(
            category=category,
            source_name=source_name,
            quantity=quantity,
            unit=unit,
            emission_factor=emission_factor,
            calculation_method=calculation_method,
        )

        self.emission_sources.append(source)
        logger.debug(f"添加排放源: {source_name} ({quantity} {unit})")

    def calculate(
        self,
        revenue: Optional[float] = None,
        employee_count: Optional[int] = None,
        production_volume: Optional[float] = None,
        scope3_estimation_factor: float = 0.5,
    ) -> CarbonFootprintResult:
        """计算碳足迹

        Args:
            revenue: 营业收入（万元）
            employee_count: 员工数量
            production_volume: 产量
            scope3_estimation_factor: 范围3估算系数

        Returns:
            碳足迹计算结果
        """
        # 按范围分类计算
        scope1_sources = [
            s
            for s in self.emission_sources
            if s.category
            in [
                EmissionCategory.STATIONARY_COMBUSTION,
                EmissionCategory.MOBILE_COMBUSTION,
                EmissionCategory.PROCESS_EMISSIONS,
                EmissionCategory.FUGITIVE_EMISSIONS,
            ]
        ]

        scope2_sources = [
            s
            for s in self.emission_sources
            if s.category
            in [
                EmissionCategory.PURCHASED_ELECTRICITY,
                EmissionCategory.PURCHASED_HEAT,
                EmissionCategory.PURCHASED_STEAM,
                EmissionCategory.PURCHASED_COOLING,
            ]
        ]

        scope3_sources = [
            s
            for s in self.emission_sources
            if s.category
            not in [
                EmissionCategory.STATIONARY_COMBUSTION,
                EmissionCategory.MOBILE_COMBUSTION,
                EmissionCategory.PROCESS_EMISSIONS,
                EmissionCategory.FUGITIVE_EMISSIONS,
                EmissionCategory.PURCHASED_ELECTRICITY,
                EmissionCategory.PURCHASED_HEAT,
                EmissionCategory.PURCHASED_STEAM,
                EmissionCategory.PURCHASED_COOLING,
            ]
        ]

        # 计算各范围排放
        scope1_emissions = sum(s.calculate_emissions() for s in scope1_sources)
        scope2_location_emissions = sum(s.calculate_emissions() for s in scope2_sources)
        scope3_emissions_calculated = sum(s.calculate_emissions() for s in scope3_sources)

        # 估算缺失的范围3排放
        scope3_estimated = self._estimate_scope3(
            scope1_emissions, scope2_location_emissions, scope3_estimation_factor
        )

        total_scope3 = scope3_emissions_calculated + scope3_estimated

        # 计算总排放
        total_emissions = scope1_emissions + scope2_location_emissions + total_scope3

        # 按类别统计
        emissions_by_category: Dict[EmissionCategory, float] = {}
        for source in self.emission_sources:
            if source.category not in emissions_by_category:
                emissions_by_category[source.category] = 0
            emissions_by_category[source.category] += source.calculate_emissions()

        # 计算强度指标
        carbon_intensity_revenue = None
        carbon_intensity_production = None
        carbon_intensity_employee = None

        if revenue and revenue > 0:
            carbon_intensity_revenue = total_emissions / revenue

        if production_volume and production_volume > 0:
            carbon_intensity_production = total_emissions / production_volume

        if employee_count and employee_count > 0:
            carbon_intensity_employee = total_emissions / employee_count

        return CarbonFootprintResult(
            total_emissions=total_emissions,
            scope1_emissions=scope1_emissions,
            scope2_location_emissions=scope2_location_emissions,
            scope2_market_emissions=None,  # 需要额外数据
            scope3_emissions=total_scope3,
            emissions_by_category=emissions_by_category,
            start_date=self.start_date,
            end_date=self.end_date,
            revenue=revenue,
            employee_count=employee_count,
            production_volume=production_volume,
            carbon_intensity_revenue=carbon_intensity_revenue,
            carbon_intensity_production=carbon_intensity_production,
            carbon_intensity_employee=carbon_intensity_employee,
        )

    def _estimate_scope3(self, scope1: float, scope2: float, factor: float) -> float:
        """估算范围3排放"""
        return (scope1 + scope2) * factor

    def clear_sources(self):
        """清除所有排放源"""
        self.emission_sources.clear()


def calculate_carbon_intensity(total_emissions: float, revenue: float, unit: str = "万元") -> float:
    """计算碳强度

    Args:
        total_emissions: 总排放量（吨CO2e）
        revenue: 营业收入
        unit: 收入单位

    Returns:
        碳强度（吨CO2e/单位收入）
    """
    if revenue == 0:
        return 0.0
    return total_emissions / revenue


def estimate_scope3_emissions(
    scope1_emissions: float,
    scope2_emissions: float,
    category_breakdown: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """估算范围3排放细分

    Args:
        scope1_emissions: 范围1排放
        scope2_emissions: 范围2排放
        category_breakdown: 类别细分比例

    Returns:
        各类别估算排放
    """
    base_scope3 = (scope1_emissions + scope2_emissions) * 0.5

    if category_breakdown is None:
        category_breakdown = SCOPE_3_ESTIMATION_FACTORS

    estimates = {}
    for category, factor in category_breakdown.items():
        estimates[category] = base_scope3 * factor

    return estimates


# 行业基准数据
INDUSTRY_BENCHMARKS = {
    "renewable_energy": {
        "carbon_intensity_median": 0.5,  # 吨CO2e/万元
        "carbon_intensity_best": 0.1,
        "scope3_ratio": 0.6,
    },
    "manufacturing": {
        "carbon_intensity_median": 2.5,
        "carbon_intensity_best": 1.0,
        "scope3_ratio": 0.5,
    },
    "technology": {
        "carbon_intensity_median": 0.8,
        "carbon_intensity_best": 0.2,
        "scope3_ratio": 0.7,
    },
    "finance": {"carbon_intensity_median": 0.3, "carbon_intensity_best": 0.05, "scope3_ratio": 0.8},
}


def compare_to_benchmark(carbon_intensity: float, industry: str) -> Dict[str, Union[float, str]]:
    """与行业基准比较

    Args:
        carbon_intensity: 碳强度
        industry: 行业类型

    Returns:
        比较结果
    """
    benchmark = INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["manufacturing"])

    median = benchmark["carbon_intensity_median"]
    best = benchmark["carbon_intensity_best"]

    vs_median = ((carbon_intensity - median) / median * 100) if median > 0 else 0
    vs_best = ((carbon_intensity - best) / best * 100) if best > 0 else 0

    if carbon_intensity <= best:
        performance = "excellent"
    elif carbon_intensity <= median:
        performance = "good"
    elif carbon_intensity <= median * 1.5:
        performance = "average"
    else:
        performance = "poor"

    return {
        "carbon_intensity": carbon_intensity,
        "industry_median": median,
        "industry_best": best,
        "vs_median_percent": vs_median,
        "vs_best_percent": vs_best,
        "performance_rating": performance,
    }
