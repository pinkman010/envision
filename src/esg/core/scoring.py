"""ESG评分计算器

提供ESG各维度指标的评分计算功能。
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from src.esg.core.constants import (
    BATTERY_CYCLE_LIFE_BENCHMARK,
    BATTERY_RECYCLING_RATE_BENCHMARK,
    BIODIVERSITY_IMPACT_BENCHMARK,
    CARBON_INTENSITY_BENCHMARKS,
    CURTAILMENT_RATE_BENCHMARK,
    DEFAULT_SCORE,
    ELECTROLYSIS_EFFICIENCY_BENCHMARK,
    ENERGY_STORAGE_SAFETY_BENCHMARK,
    G_DIMENSION_WEIGHTS,
    LTIFR_BENCHMARKS,
    SAFETY_INVESTMENT_BENCHMARKS,
    SCOPE3_COVERAGE_BENCHMARK_HIGH,
    SCOPE3_COVERAGE_BENCHMARK_LOW,
    SCOPE3_RATIO_ACCEPTABLE_MAX,
    SCOPE3_RATIO_IDEAL_MAX,
    SCOPE3_RATIO_IDEAL_MIN,
    SCORE_MAX,
    TRIR_BENCHMARKS,
    TURBINE_AVAILABILITY_BENCHMARK,
    WATER_INTENSITY_BENCHMARK_HIGH,
    WATER_INTENSITY_BENCHMARK_LOW,
)
from src.esg.core.models import (
    ClimateDisclosureQuality,
    ClimateGovernance,
    SBTiTarget,
    TCFDDisclosure,
)

if TYPE_CHECKING:
    from src.esg.core.scope3_emissions import Scope3Inventory

# E维度指标权重配置（含范围3评分）
# 一级指标（45%）：碳强度15% + 范围3覆盖率10% + 范围3/1+2比例5% + SBTi目标15%
# 二级指标（30%）：可再生能源、能源效率、废弃物回收、水资源（各7.5%）
# 三级指标（25%）：新能源特色指标
E_DIMENSION_WEIGHTS = {
    # 一级指标 - 排放相关（45%）
    "carbon_intensity": 0.15,  # 范围1+2碳强度
    "scope3_coverage": 0.10,  # 范围3覆盖率（新增）
    "scope3_ratio": 0.05,  # 范围3/1+2比例（新增）
    "sbti_target": 0.15,  # SBTi目标
    # 二级指标 - 运营效率（30%）
    "renewable_energy_ratio": 0.075,
    "energy_efficiency": 0.075,
    "waste_recycling_rate": 0.075,
    "water_intensity": 0.075,
    # 三级指标 - 新能源特色（25%）
    "turbine_availability": 0.05,
    "curtailment_rate": 0.05,
    "battery_cycle_life": 0.05,
    "battery_recycling_rate": 0.025,
    "electrolysis_efficiency": 0.025,
    "energy_storage_safety": 0.05,
}

# S维度指标权重配置
# 人力资本（40%）：女性员工比例、高管层女性比例、培训时长、本地雇佣
# 安全健康（40%）：TRIR、LTIFR、安全投入占比
# 社区关系（20%）：社区投资占营收比例
S_DIMENSION_WEIGHTS = {
    # 人力资本（40%）
    "female_ratio": 0.10,
    "female_executive_ratio": 0.10,
    "training_hours": 0.10,
    "local_employment_ratio": 0.10,
    # 安全健康（40%）- 新增重点
    "trir": 0.15,
    "ltifr": 0.15,
    "safety_investment_ratio": 0.10,
    # 社区关系（20%）
    "community_investment_per_revenue": 0.20,
}


def _calculate_weighted_score(
    scores: List[Optional[float]], weights: List[float], default_score: float = DEFAULT_SCORE
) -> float:
    """计算加权得分，支持权重归一化

    当某些指标为None时，将其权重重新分配给其他有效指标。

    Args:
        scores: 得分列表（可能包含None）
        weights: 权重列表（与scores对应）
        default_score: 无有效数据时的默认得分

    Returns:
        加权得分
    """
    valid_items = [(s, w) for s, w in zip(scores, weights) if s is not None]

    if not valid_items:
        return default_score

    valid_scores, valid_weights = zip(*valid_items)
    total_weight = sum(valid_weights)

    if total_weight == 0:
        return default_score

    # 权重归一化并计算加权得分
    normalized_weights = [w / total_weight for w in valid_weights]
    return sum(s * nw for s, nw in zip(valid_scores, normalized_weights))


class ScoreCalculator:
    """ESG评分计算器

    提供各种ESG指标的评分计算方法，支持自定义阈值和基准。
    支持按新能源子行业细分的碳强度评分。
    """

    @staticmethod
    def calculate_scope3_coverage_score(
        scope3_inventory: Optional["Scope3Inventory"],
    ) -> Optional[float]:
        """计算范围3覆盖率评分

        基于行业重要性权重计算范围3覆盖率评分。
        - 100分：所有重要类别（权重>0.05）都有数据
        - 线性递减：按缺失的重要类别数量扣分

        Args:
            scope3_inventory: 范围3排放清单对象

        Returns:
            覆盖率评分(0-100)或None
        """
        if scope3_inventory is None:
            return None

        # 导入在此处避免循环导入
        from src.esg.core.scope3_emissions import NEW_ENERGY_SECTOR_RELEVANCE

        relevance_map = NEW_ENERGY_SECTOR_RELEVANCE.get(
            scope3_inventory.sector, NEW_ENERGY_SECTOR_RELEVANCE.get("wind_power")
        )

        if not relevance_map:
            return None

        covered_weight = 0.0
        total_weight = 0.0

        for cat, weight in relevance_map.items():
            total_weight += weight
            cat_data = scope3_inventory.categories.get(cat)
            if cat_data and cat_data.emissions is not None:
                covered_weight += weight

        if total_weight == 0:
            return None

        # 计算覆盖率并映射到0-100分
        coverage = covered_weight / total_weight

        # 覆盖率>80%得满分，<40%得0分，中间线性插值
        if coverage >= SCOPE3_COVERAGE_BENCHMARK_HIGH:
            return SCORE_MAX
        if coverage <= SCOPE3_COVERAGE_BENCHMARK_LOW:
            return 0.0

        # 线性插值
        ratio = (coverage - SCOPE3_COVERAGE_BENCHMARK_LOW) / (
            SCOPE3_COVERAGE_BENCHMARK_HIGH - SCOPE3_COVERAGE_BENCHMARK_LOW
        )
        return SCORE_MAX * ratio

    @staticmethod
    def calculate_scope3_ratio_score(
        scope3_inventory: Optional["Scope3Inventory"], scope12_emissions: Optional[float]
    ) -> Optional[float]:
        """计算范围3/范围1+2比例评分

        评分逻辑：
        - 范围3/1+2比例越高，说明企业意识到供应链排放重要性
        - 但比例过高(>50)可能说明范围1+2控制不佳
        - 理想区间：5-20倍（新能源制造业典型范围）

        评分：
        - 0-5倍：50分（范围3意识不足）
        - 5-20倍：100分（理想区间）
        - 20-50倍：75分（范围3较高但可接受）
        - >50倍：50分（范围1+2控制可能不佳）

        Args:
            scope3_inventory: 范围3排放清单对象
            scope12_emissions: 范围1+2排放总量

        Returns:
            比例评分(0-100)或None
        """
        if scope3_inventory is None or scope12_emissions is None:
            return None

        scope3_total = scope3_inventory.get_total_emissions()
        if scope3_total is None or scope12_emissions <= 0:
            return None

        ratio = scope3_total / scope12_emissions

        if SCOPE3_RATIO_IDEAL_MIN <= ratio <= SCOPE3_RATIO_IDEAL_MAX:
            # 理想区间：满分
            return 100.0
        elif ratio < SCOPE3_RATIO_IDEAL_MIN:
            # 0-5倍：映射到50-100分
            return 50.0 + (ratio / SCOPE3_RATIO_IDEAL_MIN) * 50.0
        elif ratio <= SCOPE3_RATIO_ACCEPTABLE_MAX:
            # 20-50倍：映射到100-75分
            return 100.0 - (ratio - SCOPE3_RATIO_IDEAL_MAX) / 30.0 * 25.0
        else:
            # >50倍：递减到50分
            return max(50.0, 75.0 - (ratio - SCOPE3_RATIO_ACCEPTABLE_MAX) / 50.0 * 25.0)

    @staticmethod
    def calculate_carbon_intensity_score(
        intensity: Optional[float], industry_sector: str = "new_energy_composite"
    ) -> Optional[float]:
        """计算碳强度得分（越低越好）

        使用行业特定基准进行评分。

        Args:
            intensity: 碳强度（吨CO2e/百万元营收）
            industry_sector: 新能源子行业

        Returns:
            碳强度得分(0-100)或None
        """
        if intensity is None:
            return None

        benchmark = CARBON_INTENSITY_BENCHMARKS.get(
            industry_sector, CARBON_INTENSITY_BENCHMARKS["new_energy_composite"]
        )

        excellent = benchmark["excellent"]
        poor = benchmark["poor"]

        # 低于优秀阈值得满分
        if intensity <= excellent:
            return SCORE_MAX
        # 高于较差阈值得0分
        if intensity >= poor:
            return 0.0

        # 线性插值计算得分
        ratio = (intensity - excellent) / (poor - excellent)
        return SCORE_MAX * (1 - ratio)

    @staticmethod
    def calculate_sbti_score(sbti_target: Optional[SBTiTarget]) -> Optional[float]:
        """计算SBTi目标评分

        综合SBTi状态评分和减排进度评分。

        Args:
            sbti_target: SBTi目标对象

        Returns:
            SBTi综合评分(0-100)或None
        """
        if sbti_target is None:
            return None
        return sbti_target.get_overall_score()

    @staticmethod
    def calculate_water_intensity_score(intensity: Optional[float]) -> Optional[float]:
        """计算水资源强度得分（越低越好）

        Args:
            intensity: 水资源强度（立方米/百万元营收）

        Returns:
            水资源强度得分(0-100)或None
        """
        if intensity is None:
            return None

        # 低于优秀阈值得满分
        if intensity <= WATER_INTENSITY_BENCHMARK_LOW:
            return SCORE_MAX
        # 高于较差阈值得0分
        if intensity >= WATER_INTENSITY_BENCHMARK_HIGH:
            return 0.0

        # 线性插值
        ratio = (intensity - WATER_INTENSITY_BENCHMARK_LOW) / (
            WATER_INTENSITY_BENCHMARK_HIGH - WATER_INTENSITY_BENCHMARK_LOW
        )
        return SCORE_MAX * (1 - ratio)

    @staticmethod
    def calculate_curtailment_score(curtailment_rate: Optional[float]) -> Optional[float]:
        """计算弃风/弃光率得分（越低越好）

        Args:
            curtailment_rate: 弃电率(%)

        Returns:
            得分(0-100)或None
        """
        if curtailment_rate is None:
            return None

        # 弃电率<2%得满分，>10%得0分
        if curtailment_rate <= 2.0:
            return SCORE_MAX
        if curtailment_rate >= 10.0:
            return 0.0

        ratio = (curtailment_rate - 2.0) / 8.0
        return SCORE_MAX * (1 - ratio)

    @staticmethod
    def calculate_trir_score(trir: Optional[float]) -> Optional[float]:
        """计算TRIR评分（越低越好）

        TRIR (Total Recordable Injury Rate): 总可记录伤害率
        行业标准：优秀<1.0，一般<2.0，较差>3.0

        Args:
            trir: 总可记录伤害率（每百万工时）

        Returns:
            TRIR评分(0-100)或None
        """
        if trir is None:
            return None

        excellent = TRIR_BENCHMARKS["excellent"]
        poor = TRIR_BENCHMARKS["poor"]

        # 低于优秀阈值得满分
        if trir <= excellent:
            return SCORE_MAX
        # 高于较差阈值得0分
        if trir >= poor:
            return 0.0

        # 线性插值计算得分
        ratio = (trir - excellent) / (poor - excellent)
        return SCORE_MAX * (1 - ratio)

    @staticmethod
    def calculate_ltifr_score(ltifr: Optional[float]) -> Optional[float]:
        """计算LTIFR评分（越低越好）

        LTIFR (Lost Time Injury Frequency Rate): 失时工伤率
        行业标准：优秀<0.2，一般<0.5，较差>1.0

        Args:
            ltifr: 失时工伤率（每百万工时）

        Returns:
            LTIFR评分(0-100)或None
        """
        if ltifr is None:
            return None

        excellent = LTIFR_BENCHMARKS["excellent"]
        poor = LTIFR_BENCHMARKS["poor"]

        # 低于优秀阈值得满分
        if ltifr <= excellent:
            return SCORE_MAX
        # 高于较差阈值得0分
        if ltifr >= poor:
            return 0.0

        # 线性插值计算得分
        ratio = (ltifr - excellent) / (poor - excellent)
        return SCORE_MAX * (1 - ratio)

    @staticmethod
    def calculate_safety_investment_score(ratio: Optional[float]) -> Optional[float]:
        """计算安全投入占比评分（越高越好）

        安全投入占总运营成本的比例
        行业标准：优秀>2%，一般>1%，较差<0.5%

        Args:
            ratio: 安全投入占比(%)

        Returns:
            安全投入评分(0-100)或None
        """
        if ratio is None:
            return None

        # 2%得100分，线性比例
        return min(SCORE_MAX, ratio * 50.0)

    @staticmethod
    def safe_score(
        value: Optional[float], max_val: float = SCORE_MAX, multiplier: float = 1.0
    ) -> Optional[float]:
        """安全地计算分数

        Args:
            value: 原始值
            max_val: 最大值限制
            multiplier: 乘数

        Returns:
            计算后的分数或None
        """
        if value is None:
            return None
        if multiplier != 1.0:
            return min(value * multiplier, max_val)
        return min(value, max_val)

    @staticmethod
    def calculate_percentage_score(value: Optional[float]) -> Optional[float]:
        """计算百分比得分（原始值即为百分比）

        Args:
            value: 百分比值（0-100）

        Returns:
            得分或None
        """
        if value is None:
            return None
        return min(value, SCORE_MAX)

    def calculate_dimension_scores(self, metrics, dimension: str) -> List[Optional[float]]:
        """计算指定维度的所有指标得分

        Args:
            metrics: ESGMetrics对象
            dimension: 维度代码 ('E', 'S', 或 'G')

        Returns:
            得分列表
        """
        scores: List[Optional[float]] = []

        if dimension == "E":
            # 环境维度评分（分层加权结构，含范围3评分）
            # 一级指标（45%）：碳强度15% + 范围3覆盖率10% + 范围3比例5% + SBTi目标15%
            # 二级指标（30%）：可再生能源、能源效率、废弃物回收、水资源
            # 三级指标（25%）：新能源特色指标
            scores = [
                # 一级指标
                self.calculate_carbon_intensity_score(
                    metrics.carbon_intensity,
                    getattr(metrics, "industry_sector", "new_energy_composite"),
                ),
                self.calculate_scope3_coverage_score(getattr(metrics, "scope3_inventory", None)),
                self.calculate_scope3_ratio_score(
                    getattr(metrics, "scope3_inventory", None),
                    getattr(metrics, "get_scope1_2_emissions", lambda: None)(),
                ),
                self.calculate_sbti_score(getattr(metrics, "sbti_target", None)),
                # 二级指标
                self.safe_score(metrics.renewable_energy_ratio, SCORE_MAX),
                self.safe_score(metrics.energy_efficiency, SCORE_MAX),
                self.safe_score(metrics.waste_recycling_rate, SCORE_MAX),
                self.calculate_water_intensity_score(metrics.water_intensity),
                # 三级指标：新能源特色
                self.safe_score(
                    getattr(metrics, "turbine_availability", None),
                    SCORE_MAX,
                    multiplier=SCORE_MAX / TURBINE_AVAILABILITY_BENCHMARK,
                ),
                self.calculate_curtailment_score(getattr(metrics, "curtailment_rate", None)),
                self.safe_score(
                    getattr(metrics, "battery_cycle_life", None),
                    SCORE_MAX,
                    multiplier=SCORE_MAX / BATTERY_CYCLE_LIFE_BENCHMARK,
                ),
                self.safe_score(getattr(metrics, "battery_recycling_rate", None), SCORE_MAX),
                self.safe_score(
                    getattr(metrics, "electrolysis_efficiency", None),
                    SCORE_MAX,
                    multiplier=SCORE_MAX / ELECTROLYSIS_EFFICIENCY_BENCHMARK,
                ),
                self.safe_score(getattr(metrics, "energy_storage_safety_score", None), SCORE_MAX),
            ]
        elif dimension == "S":
            scores = [
                self.safe_score(metrics.female_ratio, SCORE_MAX, multiplier=SCORE_MAX),
                self.safe_score(getattr(metrics, "female_executive_ratio", None), SCORE_MAX),
                self.safe_score(
                    getattr(metrics, "training_hours", None), 40.0, multiplier=SCORE_MAX / 40.0
                ),
                self.safe_score(getattr(metrics, "local_employment_ratio", None), SCORE_MAX),
                self.safe_score(
                    getattr(metrics, "community_investment_per_revenue", None),
                    1.0,
                    multiplier=SCORE_MAX,
                ),
            ]
        elif dimension == "G":
            # G维度评分（分层加权结构）
            # 传统治理（40%）：董事会独立性、ESG委员会独立性、道德培训、反腐败培训
            # 气候治理（40%）：气候治理架构、TCFD披露
            # 信息披露（20%）：ESG报告质量、举报人保护

            # 传统治理指标
            traditional_scores = [
                self.safe_score(metrics.board_independence_ratio, SCORE_MAX),
                self.safe_score(getattr(metrics, "esg_committee_independence", None), SCORE_MAX),
                self.safe_score(getattr(metrics, "ethics_training_coverage", None), SCORE_MAX),
                self.safe_score(
                    getattr(metrics, "anti_corruption_training_coverage", None), SCORE_MAX
                ),
            ]

            # 气候治理指标
            climate_gov = getattr(metrics, "climate_governance", None)
            tcfd = getattr(metrics, "tcfd_disclosure", None)
            climate_governance_score = climate_gov.get_score() if climate_gov else None
            tcfd_score = tcfd.get_score() if tcfd else None

            # 信息披露指标
            disclosure_scores = [
                self.safe_score(metrics.esg_report_quality, SCORE_MAX),
                (
                    100.0
                    if getattr(metrics, "whistleblower_protection", None)
                    else (
                        0.0
                        if getattr(metrics, "whistleblower_protection", None) is not None
                        else None
                    )
                ),
            ]

            # 返回所有子维度分数列表
            # 顺序：传统治理(4) + 气候治理(2) + 信息披露(2)
            scores = traditional_scores + [climate_governance_score, tcfd_score] + disclosure_scores

        return scores

    def calculate_dimension_score(self, metrics, dimension: str) -> float:
        """计算指定维度的综合得分

        Args:
            metrics: ESGMetrics对象
            dimension: 维度代码 ('E', 'S', 或 'G')

        Returns:
            维度得分 (0-100)
        """
        if dimension == "E":
            # 环境维度使用加权平均
            scores = self.calculate_dimension_scores(metrics, dimension)
            weights = list(E_DIMENSION_WEIGHTS.values())
            return _calculate_weighted_score(scores, weights, DEFAULT_SCORE)
        elif dimension == "S":
            # S维度使用加权平均
            scores = self.calculate_dimension_scores(metrics, dimension)
            weights = list(S_DIMENSION_WEIGHTS.values())
            return _calculate_weighted_score(scores, weights, DEFAULT_SCORE)
        elif dimension == "G":
            # G维度使用分层加权平均
            # 传统治理（40%）：4个指标各10%
            # 气候治理（40%）：气候治理架构20% + TCFD披露20%
            # 信息披露（20%）：ESG报告质量10% + 举报人保护10%
            scores = self.calculate_dimension_scores(metrics, dimension)
            weights = [
                # 传统治理（40%）
                0.10,
                0.10,
                0.10,
                0.10,
                # 气候治理（40%）
                0.20,
                0.20,
                # 信息披露（20%）
                0.10,
                0.10,
            ]
            return _calculate_weighted_score(scores, weights, DEFAULT_SCORE)
        else:
            # 其他维度使用简单平均
            scores = self.calculate_dimension_scores(metrics, dimension)
            valid_scores = [s for s in scores if s is not None]
            if not valid_scores:
                return DEFAULT_SCORE
            return sum(valid_scores) / len(valid_scores)


# 全局评分计算器实例
_calculator = ScoreCalculator()


def get_score_calculator() -> ScoreCalculator:
    """获取全局评分计算器实例"""
    return _calculator


def calculate_carbon_intensity_score(
    intensity: Optional[float], industry_sector: str = "new_energy_composite"
) -> Optional[float]:
    """便捷函数：计算碳强度得分"""
    return _calculator.calculate_carbon_intensity_score(intensity, industry_sector)


def calculate_sbti_score(sbti_target: Optional[SBTiTarget]) -> Optional[float]:
    """便捷函数：计算SBTi评分"""
    return _calculator.calculate_sbti_score(sbti_target)


def calculate_water_intensity_score(intensity: Optional[float]) -> Optional[float]:
    """便捷函数：计算水资源强度得分"""
    return _calculator.calculate_water_intensity_score(intensity)


def calculate_scope3_coverage_score(
    scope3_inventory: Optional["Scope3Inventory"],
) -> Optional[float]:
    """便捷函数：计算范围3覆盖率评分"""
    return _calculator.calculate_scope3_coverage_score(scope3_inventory)


def calculate_scope3_ratio_score(
    scope3_inventory: Optional["Scope3Inventory"], scope12_emissions: Optional[float]
) -> Optional[float]:
    """便捷函数：计算范围3/范围1+2比例评分"""
    return _calculator.calculate_scope3_ratio_score(scope3_inventory, scope12_emissions)


def calculate_climate_governance_score(climate_gov: Optional[ClimateGovernance]) -> Optional[float]:
    """计算气候治理架构评分

    评估企业在气候治理架构方面的建设情况。

    Args:
        climate_gov: ClimateGovernance对象

    Returns:
        气候治理架构得分(0-100)或None
    """
    if climate_gov is None:
        return None
    return climate_gov.get_score()


def calculate_tcfd_score(tcfd: Optional[TCFDDisclosure]) -> Optional[float]:
    """计算TCFD披露完整度评分

    评估企业TCFD四支柱披露的完整度。

    Args:
        tcfd: TCFDDisclosure对象

    Returns:
        TCFD披露完整度得分(0-100)或None
    """
    if tcfd is None:
        return None
    return tcfd.get_score()


def calculate_climate_disclosure_quality_score(
    quality: Optional[ClimateDisclosureQuality],
) -> Optional[float]:
    """计算气候信息披露质量评分

    评估企业气候信息披露的质量和完整性。

    Args:
        quality: ClimateDisclosureQuality对象

    Returns:
        气候信息披露质量得分(0-100)或None
    """
    if quality is None:
        return None
    return quality.get_score()
