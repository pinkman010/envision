"""TCFD气候情景分析模块

该模块提供TCFD（气候相关财务披露工作组）要求的气候情景分析能力，
支持评估企业在不同温升路径下的战略韧性。

主要组件:
    - ClimateScenario: 气候情景定义数据类
    - ScenarioType: 标准NGFS情景类型枚举
    - ScenarioImpact: 情景影响分析结果
    - ClimateScenarioAnalyzer: 气候情景分析器
    - STANDARD_SCENARIOS: 预定义标准NGFS情景

标准情景:
    - NGFS Orderly (1.5°C): 有序转型，提前行动
    - NGFS Disorderly (1.5°C): 延迟行动，突然转型
    - NGFS Hot House World (4°C): 政策行动失败，高物理风险
    - NGFS Too Little, Too Late (3°C): 行动不足，转型和物理风险并存

使用示例:
    >>> from src.esg.core import ESGMetrics, SBTiTarget
    >>> from src.esg.core.climate_scenario import ClimateScenarioAnalyzer
    >>> 
    >>> metrics = ESGMetrics(company_name="示例公司", year="2024")
    >>> analyzer = ClimateScenarioAnalyzer(metrics)
    >>> 
    >>> # 分析所有标准情景
    >>> results = analyzer.analyze_all_scenarios()
    >>> 
    >>> # 生成TCFD报告
    >>> report = analyzer.generate_tcfd_report()
    >>> print(f"韧性评分范围: {report['resilience_assessment']['best_case']:.1f} - "
    ...       f"{report['resilience_assessment']['worst_case']:.1f}")

参考:
    - TCFD建议报告框架
    - NGFS（央行与监管机构绿色金融网络）情景
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from src.esg.core.models import ESGMetrics


class ScenarioType(Enum):
    """标准NGFS气候情景类型
    
    基于央行与监管机构绿色金融网络（NGFS）定义的标准气候情景。
    """
    ORDERLY_15C = "orderly_1.5c"  # 有序1.5°C转型
    DISORDERLY_15C = "disorderly_1.5c"  # 无序1.5°C转型
    HOTHOUSE_4C = "hothouse_4c"  # 温室世界4°C
    TOO_LITTLE_3C = "too_little_3c"  # 行动不足3°C


@dataclass
class ClimateScenario:
    """气候情景定义
    
    定义特定气候情景的参数和影响假设。
    
    Attributes:
        scenario_type: 情景类型
        name: 情景名称
        description: 情景描述
        temperature_rise: 温升幅度（°C）
        carbon_price_2030: 2030年碳价格（美元/tCO2e）
        carbon_price_2050: 2050年碳价格
        carbon_price_2050_high: 2050年高估值碳价格
        policy_stringency: 政策严格程度（low/medium/high）
        technology_development: 技术发展速度（slow/medium/fast）
        physical_risk_level: 物理风险等级（low/medium/high）
        renewable_energy_share_2030: 2030年可再生能源占比（%）
        renewable_energy_share_2050: 2050年可再生能源占比（%）
        fossil_fuel_phase_out_year: 化石燃料退出年份（如适用）
    """
    scenario_type: ScenarioType
    name: str
    description: str
    temperature_rise: float  # °C
    carbon_price_2030: float  # USD/tCO2e
    carbon_price_2050: float
    carbon_price_2050_high: float  # 高估值
    policy_stringency: str  # low/medium/high
    technology_development: str  # slow/medium/fast
    physical_risk_level: str  # low/medium/high
    
    # 新能源行业特定参数
    renewable_energy_share_2030: float  # %
    renewable_energy_share_2050: float
    fossil_fuel_phase_out_year: Optional[int]


# 预定义标准情景
STANDARD_SCENARIOS: Dict[ScenarioType, ClimateScenario] = {
    ScenarioType.ORDERLY_15C: ClimateScenario(
        scenario_type=ScenarioType.ORDERLY_15C,
        name="NGFS Orderly (Below 2°C)",
        description="有序转型情景，气候政策早期实施且逐步收紧，低碳技术快速发展",
        temperature_rise=1.5,
        carbon_price_2030=75.0,
        carbon_price_2050=200.0,
        carbon_price_2050_high=300.0,
        policy_stringency="high",
        technology_development="fast",
        physical_risk_level="low",
        renewable_energy_share_2030=60.0,
        renewable_energy_share_2050=90.0,
        fossil_fuel_phase_out_year=2040,
    ),
    ScenarioType.DISORDERLY_15C: ClimateScenario(
        scenario_type=ScenarioType.DISORDERLY_15C,
        name="NGFS Disorderly (Below 2°C)",
        description="无序转型情景，延迟行动导致突然转型，高转型风险",
        temperature_rise=1.5,
        carbon_price_2030=50.0,
        carbon_price_2050=300.0,
        carbon_price_2050_high=500.0,
        policy_stringency="high",
        technology_development="medium",
        physical_risk_level="medium",
        renewable_energy_share_2030=45.0,
        renewable_energy_share_2050=85.0,
        fossil_fuel_phase_out_year=2035,
    ),
    ScenarioType.HOTHOUSE_4C: ClimateScenario(
        scenario_type=ScenarioType.HOTHOUSE_4C,
        name="NGFS Hot House World (Above 3°C)",
        description="温室世界情景，政策行动失败，高物理风险",
        temperature_rise=4.0,
        carbon_price_2030=10.0,
        carbon_price_2050=30.0,
        carbon_price_2050_high=50.0,
        policy_stringency="low",
        technology_development="slow",
        physical_risk_level="high",
        renewable_energy_share_2030=35.0,
        renewable_energy_share_2050=50.0,
        fossil_fuel_phase_out_year=None,
    ),
    ScenarioType.TOO_LITTLE_3C: ClimateScenario(
        scenario_type=ScenarioType.TOO_LITTLE_3C,
        name="NGFS Too Little, Too Late (Above 3°C)",
        description="行动不足情景，转型和物理风险并存",
        temperature_rise=3.0,
        carbon_price_2030=30.0,
        carbon_price_2050=100.0,
        carbon_price_2050_high=150.0,
        policy_stringency="medium",
        technology_development="medium",
        physical_risk_level="medium",
        renewable_energy_share_2030=40.0,
        renewable_energy_share_2050=65.0,
        fossil_fuel_phase_out_year=2050,
    ),
}


@dataclass
class ScenarioImpact:
    """情景影响分析结果
    
    存储特定情景下的财务影响和战略评估。
    
    Attributes:
        scenario: 对应的气候情景
        annual_carbon_cost_2030: 2030年年度碳成本（百万元）
        annual_carbon_cost_2050: 2050年年度碳成本（百万元）
        cumulative_carbon_cost_2050: 累计碳成本至2050年（百万元）
        revenue_impact_2030: 2030年收入影响（%变化）
        revenue_impact_2050: 2050年收入影响（%变化）
        stranded_asset_risk: 资产搁浅风险（百万元）
        asset_impairment_ratio: 资产减值比例（%）
        physical_damage_annual: 年度物理风险损失（百万元）
        business_interruption_days: 年度业务中断天数
        net_financial_impact_2030: 2030年净财务影响（百万元）
        net_financial_impact_2050: 2050年净财务影响（百万元）
        resilience_score: 韧性评分（0-100）
    """
    scenario: ClimateScenario
    
    # 碳成本影响
    annual_carbon_cost_2030: float  # 百万元
    annual_carbon_cost_2050: float
    cumulative_carbon_cost_2050: float
    
    # 收入影响（新能源企业可能受益）
    revenue_impact_2030: float  # %变化
    revenue_impact_2050: float
    
    # 资产影响
    stranded_asset_risk: float  # 百万元
    asset_impairment_ratio: float  # %
    
    # 物理风险
    physical_damage_annual: float  # 百万元
    business_interruption_days: int
    
    # 总体评估
    net_financial_impact_2030: float  # 百万元
    net_financial_impact_2050: float
    resilience_score: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "scenario": {
                "type": self.scenario.scenario_type.value,
                "name": self.scenario.name,
                "temperature_rise": self.scenario.temperature_rise,
                "carbon_price_2030": self.scenario.carbon_price_2030,
                "carbon_price_2050": self.scenario.carbon_price_2050,
                "physical_risk_level": self.scenario.physical_risk_level,
            },
            "carbon_cost": {
                "annual_2030": self.annual_carbon_cost_2030,
                "annual_2050": self.annual_carbon_cost_2050,
                "cumulative_2050": self.cumulative_carbon_cost_2050,
            },
            "revenue_impact": {
                "2030": self.revenue_impact_2030,
                "2050": self.revenue_impact_2050,
            },
            "asset_risk": {
                "stranded_assets": self.stranded_asset_risk,
                "impairment_ratio": self.asset_impairment_ratio,
            },
            "physical_risk": {
                "annual_damage": self.physical_damage_annual,
                "business_interruption_days": self.business_interruption_days,
            },
            "net_financial_impact": {
                "2030": self.net_financial_impact_2030,
                "2050": self.net_financial_impact_2050,
            },
            "resilience_score": self.resilience_score,
        }


class ClimateScenarioAnalyzer:
    """气候情景分析器
    
    分析企业ESG指标在不同气候情景下的财务影响和战略韧性。
    
    Attributes:
        metrics: ESG指标数据
    
    使用示例:
        >>> analyzer = ClimateScenarioAnalyzer(metrics)
        >>> impact = analyzer.analyze_scenario(STANDARD_SCENARIOS[ScenarioType.ORDERLY_15C])
        >>> print(f"2030年碳成本: {impact.annual_carbon_cost_2030:.2f}百万元")
    """
    
    def __init__(self, metrics: "ESGMetrics"):
        """初始化分析器
        
        Args:
            metrics: ESG指标数据
        """
        self.metrics = metrics
    
    def analyze_scenario(self, scenario: ClimateScenario) -> ScenarioImpact:
        """分析特定情景的影响
        
        计算碳成本、收入影响、资产搁浅风险和物理风险等综合财务影响。
        
        Args:
            scenario: 要分析的气候情景
            
        Returns:
            情景影响分析结果
        """
        # 1. 计算碳成本影响
        scope12_emissions = self._get_scope1_2_emissions()
        annual_carbon_cost_2030 = scope12_emissions * scenario.carbon_price_2030 / 1000000  # 转换为百万元
        annual_carbon_cost_2050 = scope12_emissions * scenario.carbon_price_2050 / 1000000
        
        # 2. 计算收入影响（新能源企业受益于高碳价情景）
        base_revenue_impact = self._calculate_revenue_impact(scenario)
        
        # 3. 资产搁浅风险评估
        stranded_assets = self._calculate_stranded_assets(scenario)
        
        # 4. 物理风险评估
        physical_damage = self._calculate_physical_risk(scenario)
        
        # 5. 综合评估
        # 假设年营收1000百万元（10亿元）用于计算收入影响
        assumed_revenue = 1000.0  # 百万元
        revenue_gain_2030 = base_revenue_impact * assumed_revenue / 100  # 转换为百万元
        revenue_gain_2050 = base_revenue_impact * 1.5 * assumed_revenue / 100
        
        net_impact_2030 = annual_carbon_cost_2030 - revenue_gain_2030 + physical_damage
        net_impact_2050 = annual_carbon_cost_2050 - revenue_gain_2050 + physical_damage * 2
        
        # 6. 韧性评分
        resilience = self._calculate_resilience(scenario, net_impact_2050)
        
        return ScenarioImpact(
            scenario=scenario,
            annual_carbon_cost_2030=annual_carbon_cost_2030,
            annual_carbon_cost_2050=annual_carbon_cost_2050,
            cumulative_carbon_cost_2050=annual_carbon_cost_2050 * 20,
            revenue_impact_2030=base_revenue_impact,
            revenue_impact_2050=base_revenue_impact * 1.5,
            stranded_asset_risk=stranded_assets,
            asset_impairment_ratio=stranded_assets / 100 if stranded_assets else 0,
            physical_damage_annual=physical_damage,
            business_interruption_days=int(physical_damage / 10),
            net_financial_impact_2030=net_impact_2030,
            net_financial_impact_2050=net_impact_2050,
            resilience_score=resilience,
        )
    
    def analyze_all_scenarios(self) -> Dict[ScenarioType, ScenarioImpact]:
        """分析所有标准情景
        
        Returns:
            各情景类型到影响结果的映射字典
        """
        results = {}
        for scenario_type, scenario in STANDARD_SCENARIOS.items():
            results[scenario_type] = self.analyze_scenario(scenario)
        return results
    
    def _get_scope1_2_emissions(self) -> float:
        """获取范围1+2排放总量
        
        Returns:
            范围1+2排放总量（吨CO2e）
        """
        from src.esg.core.models import ESGMetrics
        
        if self.metrics is None:
            return 0.0
        
        scope1 = self.metrics.scope1_emissions or 0
        scope2 = (
            self.metrics.scope2_emissions_market 
            if self.metrics.scope2_emissions_market is not None 
            else self.metrics.scope2_emissions_location or 0
        )
        return scope1 + scope2
    
    def _calculate_revenue_impact(self, scenario: ClimateScenario) -> float:
        """计算收入影响
        
        新能源企业受益于高碳价情景，因为需求增长。
        
        Args:
            scenario: 气候情景
            
        Returns:
            收入变化百分比
        """
        if scenario.temperature_rise <= 2.0:
            # 1.5-2°C情景下，新能源需求强劲增长
            base_impact = (scenario.renewable_energy_share_2050 - 30) * 0.5
        else:
            # 高碳情景下，虽然需求增长但物理风险可能抵消
            base_impact = (scenario.renewable_energy_share_2050 - 30) * 0.3
        
        # 如果企业有SBTi 1.5°C目标，在有序转型情景中更具竞争力
        if (scenario == ScenarioType.ORDERLY_15C and 
            self.metrics.sbti_target is not None and
            self.metrics.sbti_target.pathway == "1.5c"):
            base_impact += 5.0  # 额外5%竞争优势
        
        return base_impact
    
    def _calculate_stranded_assets(self, scenario: ClimateScenario) -> float:
        """计算资产搁浅风险
        
        简化模型，新能源企业资产搁浅风险相对较低。
        
        Args:
            scenario: 气候情景
            
        Returns:
            资产搁浅风险金额（百万元）
        """
        base_risk = 0.0
        
        # 高碳情景下传统制造设备可能面临转型风险
        if scenario.temperature_rise > 2.0:
            base_risk = 50.0  # 基础风险50百万元
            
            # 如果企业没有转型计划，风险增加
            if self.metrics.sbti_target is None:
                base_risk += 30.0
        
        return base_risk
    
    def _calculate_physical_risk(self, scenario: ClimateScenario) -> float:
        """计算物理风险
        
        基于物理风险等级估算年度损失。
        
        Args:
            scenario: 气候情景
            
        Returns:
            年度物理风险损失（百万元）
        """
        risk_levels = {
            "low": 10.0,
            "medium": 30.0,
            "high": 80.0,
        }
        return risk_levels.get(scenario.physical_risk_level, 20.0)
    
    def _calculate_resilience(
        self, scenario: ClimateScenario, net_impact: float
    ) -> float:
        """计算韧性评分
        
        基于净财务影响和SBTi目标状态评估企业战略韧性。
        
        Args:
            scenario: 气候情景
            net_impact: 净财务影响
            
        Returns:
            韧性评分（0-100）
        """
        base_score = 50.0
        
        # 有SBTi目标的企业韧性更强
        sbti = getattr(self.metrics, 'sbti_target', None)
        if sbti:
            if sbti.pathway == "1.5c":
                base_score += 30.0
            elif sbti.pathway == "wb2c":
                base_score += 20.0
            else:
                base_score += 10.0
        
        # 有内部碳价格的企业在转型情景中更有准备
        if self.metrics.internal_carbon_price is not None:
            base_score += 5.0
        
        # 根据净影响调整
        if net_impact < 0:  # 净收益
            base_score += 20.0
        elif net_impact < 100:
            base_score += 10.0
        elif net_impact > 500:
            base_score -= 20.0
        elif net_impact > 200:
            base_score -= 10.0
        
        # 有序转型情景下表现更好
        if scenario == ScenarioType.ORDERLY_15C:
            base_score += 5.0
        
        return min(100.0, max(0.0, base_score))
    
    def generate_tcfd_report(self) -> Dict[str, Any]:
        """生成TCFD格式报告
        
        生成符合TCFD建议的情景分析披露报告。
        
        Returns:
            TCFD格式报告字典
        """
        results = self.analyze_all_scenarios()
        
        return {
            "scenarios_analyzed": [s.scenario.name for s in results.values()],
            "temperature_rise_range": {
                "min": min(s.scenario.temperature_rise for s in results.values()),
                "max": max(s.scenario.temperature_rise for s in results.values()),
            },
            "resilience_assessment": {
                "best_case": max(s.resilience_score for s in results.values()),
                "worst_case": min(s.resilience_score for s in results.values()),
                "average": sum(s.resilience_score for s in results.values()) / len(results),
            },
            "financial_impacts": {
                scenario_type.value: {
                    "carbon_cost_2030": impact.annual_carbon_cost_2030,
                    "carbon_cost_2050": impact.annual_carbon_cost_2050,
                    "revenue_impact_2030": impact.revenue_impact_2030,
                    "revenue_impact_2050": impact.revenue_impact_2050,
                    "net_impact_2030": impact.net_financial_impact_2030,
                    "net_impact_2050": impact.net_financial_impact_2050,
                    "stranded_assets": impact.stranded_asset_risk,
                    "physical_damage": impact.physical_damage_annual,
                }
                for scenario_type, impact in results.items()
            },
            "scenario_details": {
                scenario_type.value: impact.to_dict()
                for scenario_type, impact in results.items()
            },
            "strategic_implications": self._generate_implications(results),
            "tcfd_alignment": {
                "scenario_analysis_disclosed": True,
                "resilience_assessment_included": True,
                "financial_impacts_quantified": True,
            },
        }
    
    def _generate_implications(
        self, results: Dict[ScenarioType, ScenarioImpact]
    ) -> List[str]:
        """生成战略建议
        
        基于各情景下的表现生成战略建议。
        
        Args:
            results: 各情景影响结果
            
        Returns:
            战略建议列表
        """
        implications = []
        
        # 检查各情景下的表现
        orderly = results.get(ScenarioType.ORDERLY_15C)
        disorderly = results.get(ScenarioType.DISORDERLY_15C)
        hothouse = results.get(ScenarioType.HOTHOUSE_4C)
        too_little = results.get(ScenarioType.TOO_LITTLE_3C)
        
        if orderly and orderly.resilience_score > 70:
            implications.append(
                "企业在有序转型情景下表现良好，1.5°C战略准备充分"
            )
        
        if disorderly and disorderly.net_financial_impact_2050 > 200:
            implications.append(
                "无序转型情景下财务风险较高，建议制定应急转型计划"
            )
        
        if hothouse and hothouse.physical_damage_annual > 50:
            implications.append(
                "高物理风险情景下设施暴露度较高，需加强韧性建设"
            )
        
        if too_little and too_little.resilience_score < 50:
            implications.append(
                "行动不足情景下韧性评分较低，建议加速气候行动"
            )
        
        # 比较不同情景的差异
        if orderly and disorderly:
            cost_diff = (
                disorderly.net_financial_impact_2050 - orderly.net_financial_impact_2050
            )
            if cost_diff > 100:
                implications.append(
                    f"延迟行动可能导致额外{cost_diff:.0f}百万元成本，建议尽早转型"
                )
        
        # 检查是否需要设定SBTi目标
        if self.metrics.sbti_target is None:
            implications.append(
                "未设定SBTi气候目标，建议在有序转型情景下设定1.5°C目标"
            )
        
        return implications


def quick_analyze_scenarios(metrics: "ESGMetrics") -> Dict[str, Any]:
    """快速分析所有气候情景
    
    便捷函数，快速执行气候情景分析。
    
    Args:
        metrics: ESG指标数据
        
    Returns:
        TCFD格式报告
    """
    analyzer = ClimateScenarioAnalyzer(metrics)
    return analyzer.generate_tcfd_report()
