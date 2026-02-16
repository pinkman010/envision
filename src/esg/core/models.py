"""ESG核心数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# 常量定义
DEFAULT_SCORE: float = 50.0
DEFAULT_TARGET_SCORE: float = 80.0
GAP_THRESHOLD_HIGH: float = 15.0
GAP_THRESHOLD_MEDIUM: float = 8.0

# 碳强度评分参考值（吨CO2e/百万元营收）- 按新能源子行业细分
CARBON_INTENSITY_BENCHMARKS = {
    "wind_power": {"excellent": 0.15, "good": 0.25, "poor": 0.50},
    "solar_pv": {"excellent": 0.20, "good": 0.35, "poor": 0.70},
    "energy_storage": {"excellent": 0.40, "good": 0.65, "poor": 1.20},
    "green_hydrogen": {"excellent": 0.30, "good": 0.50, "poor": 0.90},
    "new_energy_composite": {"excellent": 0.25, "good": 0.45, "poor": 0.85},
}

# 新能源特色指标评分参考值
TURBINE_AVAILABILITY_BENCHMARK = 97.0  # 风机可利用率基准
BATTERY_CYCLE_LIFE_BENCHMARK = 6000  # 电池循环寿命基准
BATTERY_RECYCLING_RATE_BENCHMARK = 95.0  # 电池回收率基准
ELECTROLYSIS_EFFICIENCY_BENCHMARK = 70.0  # 电解效率基准

# 行业指标评分参考值
BIODIVERSITY_IMPACT_BENCHMARK = 80.0  # 生物多样性影响基准
ENERGY_STORAGE_SAFETY_BENCHMARK = 90.0  # 储能安全评分基准
WATER_INTENSITY_BENCHMARK_LOW = 15.0  # 水资源强度优秀阈值（立方米/百万元营收）
WATER_INTENSITY_BENCHMARK_HIGH = 100.0  # 水资源强度较差阈值

# E维度评分权重配置（含范围3评分）
E_DIMENSION_WEIGHTS = {
    # 一级指标 - 排放相关（45%）
    "carbon_intensity": 0.15,  # 范围1+2碳强度
    "scope3_coverage": 0.10,  # 范围3覆盖率
    "scope3_ratio": 0.05,  # 范围3/1+2比例
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

# 范围3比例评分参考值
SCOPE3_RATIO_IDEAL_MIN = 5.0  # 理想区间最小值
SCOPE3_RATIO_IDEAL_MAX = 20.0  # 理想区间最大值
SCOPE3_RATIO_ACCEPTABLE_MAX = 50.0  # 可接受区间最大值

# 范围3覆盖率评分基准
SCOPE3_COVERAGE_BENCHMARK_HIGH = 0.80  # 高覆盖率基准（80%）
SCOPE3_COVERAGE_BENCHMARK_LOW = 0.40  # 低覆盖率基准（40%）

# S维度评分权重配置（分层加权，与E维度对齐）
S_DIMENSION_WEIGHTS = {
    # 一级指标 - 员工发展与多元化（45%）
    "diversity_inclusion": 0.20,  # 性别多元化（女性员工比例+高管女性比例）
    "training_development": 0.15,  # 培训与发展（人均培训时长+人均培训投入）
    "employee_scale": 0.10,  # 员工规模（相对行业基准）
    # 二级指标 - 安全与福祉（30%）
    "safety_performance": 0.20,  # 安全绩效（TRIR/LTIFR/安全事故综合）
    "safety_investment": 0.10,  # 安全投入占比
    # 三级指标 - 社区责任（25%）
    "community_investment": 0.15,  # 社区投资（占营收比例）
    "local_employment": 0.10,  # 本地雇佣比例
}

# G维度评分权重配置（分层加权，与E/S维度对齐）
G_DIMENSION_WEIGHTS = {
    # 第一层：董事会与治理结构（35%）
    "board_effectiveness": 0.15,  # 董事会效能（独立性+多元化）
    "esg_governance": 0.10,  # ESG治理架构
    "audit_independence": 0.10,  # 审计独立性（新增）
    # 第二层：合规与商业道德（30%）
    "compliance_maturity": 0.15,  # 合规成熟度（道德+反腐败综合）
    "whistleblower_protection": 0.05,  # 举报人保护机制
    "business_ethics": 0.10,  # 商业道德体系（新增）
    # 第三层：透明度与问责（15%）
    "esg_report_quality": 0.08,  # ESG报告质量
    "stakeholder_engagement": 0.07,  # 利益相关方参与（新增）
}

# S维度行业基准值
DIVERSITY_BENCHMARK_EXCELLENT = 40.0  # 女性比例优秀值（%）
DIVERSITY_BENCHMARK_GOOD = 35.0  # 女性比例良好值（%）
TRAINING_HOURS_BENCHMARK = 40.0  # 人均培训时长基准（小时）
TRIR_BENCHMARK_EXCELLENT = 0.5  # 总可记录伤害率优秀值
TRIR_BENCHMARK_POOR = 3.0  # 总可记录伤害率较差值
EMPLOYEE_SCALE_BENCHMARK = 5000  # 员工规模基准值（用于归一化）

# G维度行业基准值
BOARD_INDEPENDENCE_BENCHMARK = 50.0  # 董事会独立性优秀值（%）
BOARD_DIVERSITY_BENCHMARK = 30.0  # 董事会多元化优秀值（%）
AUDIT_INDEPENDENCE_BENCHMARK = 80.0  # 审计独立性优秀值（%）
ETHICS_TRAINING_BENCHMARK = 95.0  # 道德培训覆盖率优秀值（%）
ANTI_CORRUPTION_BENCHMARK = 90.0  # 反腐败培训覆盖率优秀值（%）


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


@dataclass
class SBTiTarget:
    """SBTi气候目标数据类

    存储科学碳目标倡议(SBTi)相关信息。

    Attributes:
        target_type: 目标类型（如 'absolute', 'intensity'）
        target_year: 目标年份
        reduction_percentage: 减排百分比
        baseline_year: 基准年份
        verification_status: 验证状态
    """

    target_type: Optional[str] = None
    target_year: Optional[int] = None
    reduction_percentage: Optional[float] = None
    baseline_year: Optional[int] = None
    verification_status: Optional[str] = None


@dataclass
class ESGMetrics:
    """ESG指标数据类

    包含环境(E)、社会(S)、治理(G)三个维度的指标数据，
    支持计算各维度得分。

    Attributes:
        company_name: 公司名称
        year: 报告年份
        industry_sector: 新能源子行业（wind_power/solar_pv/energy_storage/green_hydrogen/new_energy_composite）

        # 碳排放指标（范围1/2/3分离）
        carbon_emissions: 总碳排放量（向后兼容，可为范围1+2+3总和）
        scope1_emissions: 范围1排放（直接排放）
        scope2_emissions_location: 范围2排放（基于位置法）
        scope2_emissions_market: 范围2排放（基于市场法）
        scope3_emissions: 范围3排放（价值链间接排放）
        carbon_intensity: 碳强度（吨CO2e/百万元营收）

        # SBTi目标追踪
        sbti_target: SBTi气候目标

        # 能源指标
        renewable_energy_ratio: 可再生能源使用比例(%)
        energy_efficiency: 能源效率指标
        internal_carbon_price: 内部碳价格（美元/吨CO2e）

        # 水资源指标
        water_consumption: 用水量
        water_intensity: 水资源强度（立方米/百万元营收）

        # 废弃物指标
        waste_recycling_rate: 废物回收率(%)

        # 生物多样性
        biodiversity_impact_score: 生物多样性影响评分(0-100)

        # 社会指标 (S)
        employee_count: 员工数量
        female_ratio: 女性员工比例(%)
        female_executive_ratio: 高管层女性比例(%)
        training_hours: 人均培训时长(小时)
        training_investment_per_employee: 人均培训投入（美元/人）
        safety_incidents: 安全事故数量
        trir: 总可记录伤害率（每百万工时）
        lost_time_injury_rate: 失时工伤率
        local_employment_ratio: 本地雇佣比例(%)
        community_investment: 社区投资金额
        community_investment_per_revenue: 社区投资占营收比例(%)

        # 治理指标 (G)
        board_independence_ratio: 董事会独立董事比例(%)
        ethics_training_coverage: 道德培训覆盖率(%)
        esg_report_quality: ESG报告质量评分
        esg_committee_independence: ESG委员会独立性（0-100）
        anti_corruption_training_coverage: 反腐败培训覆盖率(%)
        whistleblower_protection: 举报人保护机制（True/False）

        # 新能源特色指标
        turbine_availability: 风机可利用率(%)
        curtailment_rate: 弃风/弃光率(%)
        solar_degradation_rate: 光伏组件年衰减率(%)
        battery_cycle_life: 电池循环寿命(次)
        battery_recycling_rate: 电池回收率(%)
        battery_second_life_utilization: 电池梯次利用率(%)
        electrolysis_efficiency: 电解效率(%)
        green_hydrogen_ratio: 绿氢占比(%)
        energy_storage_safety_score: 储能安全评分(0-100)

        # 元数据
        source: 数据来源
        extracted_at: 数据提取时间
        confidence: 各字段置信度
        data_sources: 数据来源详情
    """

    company_name: str
    year: str
    industry_sector: str = "new_energy_composite"  # 默认综合新能源

    # 环境指标 (E) - 碳排放
    carbon_emissions: Optional[float] = None  # 总碳排放（向后兼容）
    scope1_emissions: Optional[float] = None  # 范围1：直接排放
    scope2_emissions_location: Optional[float] = None  # 范围2：基于位置
    scope2_emissions_market: Optional[float] = None  # 范围2：基于市场
    scope3_emissions: Optional[float] = None  # 范围3：价值链排放（汇总值）
    carbon_intensity: Optional[float] = None  # 碳强度（范围1+2+3 / 营收）
    carbon_intensity_scope12: Optional[float] = None  # 仅范围1+2的碳强度

    # 范围3数据质量
    scope3_data_quality_score: Optional[float] = None  # 范围3数据质量评分
    scope3_coverage_percentage: Optional[float] = None  # 范围3数据覆盖率

    # SBTi目标
    sbti_target: Optional["SBTiTarget"] = None

    # 环境指标 (E) - 能源
    renewable_energy_ratio: Optional[float] = None
    energy_efficiency: Optional[float] = None
    internal_carbon_price: Optional[float] = None

    # 环境指标 (E) - 水资源
    water_consumption: Optional[float] = None
    water_intensity: Optional[float] = None

    # 环境指标 (E) - 废弃物
    waste_recycling_rate: Optional[float] = None

    # 环境指标 (E) - 生物多样性
    biodiversity_impact_score: Optional[float] = None

    # 社会指标 (S)
    employee_count: Optional[int] = None
    female_ratio: Optional[float] = None
    female_executive_ratio: Optional[float] = None
    training_hours: Optional[float] = None
    training_investment_per_employee: Optional[float] = None
    safety_incidents: Optional[int] = None
    trir: Optional[float] = None  # 总可记录伤害率（每百万工时）
    ltifr: Optional[float] = None  # 失时工伤率（每百万工时）
    lost_time_injury_rate: Optional[float] = None  # 向后兼容的失时工伤率字段
    safety_investment_ratio: Optional[float] = None  # 安全投入占比(%)
    local_employment_ratio: Optional[float] = None
    community_investment: Optional[float] = None
    community_investment_per_revenue: Optional[float] = None

    # 治理指标 (G)
    board_independence_ratio: Optional[float] = None
    ethics_training_coverage: Optional[float] = None
    esg_report_quality: Optional[float] = None
    esg_committee_independence: Optional[float] = None
    anti_corruption_training_coverage: Optional[float] = None
    whistleblower_protection: Optional[bool] = None

    # 新能源特色指标
    turbine_availability: Optional[float] = None
    curtailment_rate: Optional[float] = None
    solar_degradation_rate: Optional[float] = None
    battery_cycle_life: Optional[float] = None
    battery_recycling_rate: Optional[float] = None
    battery_second_life_utilization: Optional[float] = None
    electrolysis_efficiency: Optional[float] = None
    green_hydrogen_ratio: Optional[float] = None
    energy_storage_safety_score: Optional[float] = None

    # 元数据
    source: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: Dict[str, float] = field(default_factory=dict)
    data_sources: Dict[str, str] = field(default_factory=dict)

    def get_total_emissions(self, include_scope3: bool = True) -> Optional[float]:
        """计算总碳排放量

        优先使用分离的范围1/2/3排放数据，如不存在则使用carbon_emissions字段。

        Args:
            include_scope3: 是否包含范围3排放

        Returns:
            总碳排放量或None
        """
        # 如果scope1和scope2（任一方法）存在，计算总和
        if self.scope1_emissions is not None:
            total = self.scope1_emissions
            # 范围2使用市场法优先，否则使用位置法
            scope2 = (
                self.scope2_emissions_market
                if self.scope2_emissions_market is not None
                else self.scope2_emissions_location
            )
            if scope2 is not None:
                total += scope2
            if include_scope3 and self.scope3_emissions is not None:
                total += self.scope3_emissions
            return total

        # 回退到carbon_emissions字段
        return self.carbon_emissions

    def get_scope1_2_emissions(self) -> Optional[float]:
        """获取范围1+2排放总量

        Returns:
            范围1+2排放总量或None
        """
        if self.scope1_emissions is not None:
            scope2 = (
                self.scope2_emissions_market
                if self.scope2_emissions_market is not None
                else self.scope2_emissions_location
            )
            if scope2 is not None:
                return self.scope1_emissions + scope2
            return self.scope1_emissions
        return self.carbon_emissions

    def _get_carbon_intensity_benchmark(self) -> Dict[str, float]:
        """获取当前行业的碳强度基准

        Returns:
            包含excellent/good/poor阈值的字典
        """
        return CARBON_INTENSITY_BENCHMARKS.get(
            self.industry_sector, CARBON_INTENSITY_BENCHMARKS["new_energy_composite"]
        )

    def _calculate_carbon_intensity_score(self) -> Optional[float]:
        """计算碳强度得分（越低越好）

        使用行业特定基准进行评分，支持分段线性插值。

        Returns:
            碳强度得分(0-100)或None
        """
        intensity = self.carbon_intensity
        if intensity is None:
            return None

        benchmark = self._get_carbon_intensity_benchmark()
        excellent = benchmark["excellent"]
        poor = benchmark["poor"]

        # 低于优秀阈值得满分
        if intensity <= excellent:
            return 100.0
        # 高于较差阈值得0分
        if intensity >= poor:
            return 0.0

        # 线性插值计算得分
        ratio = (intensity - excellent) / (poor - excellent)
        return 100.0 * (1 - ratio)

    def _calculate_water_intensity_score(self) -> Optional[float]:
        """计算水资源强度得分（越低越好）

        Returns:
            水资源强度得分(0-100)或None
        """
        intensity = self.water_intensity
        if intensity is None:
            return None

        # 低于优秀阈值得满分
        if intensity <= WATER_INTENSITY_BENCHMARK_LOW:
            return 100.0
        # 高于较差阈值得0分
        if intensity >= WATER_INTENSITY_BENCHMARK_HIGH:
            return 0.0

        # 线性插值
        ratio = (intensity - WATER_INTENSITY_BENCHMARK_LOW) / (
            WATER_INTENSITY_BENCHMARK_HIGH - WATER_INTENSITY_BENCHMARK_LOW
        )
        return 100.0 * (1 - ratio)

    def _calculate_scope3_ratio_score(self) -> Optional[float]:
        """计算范围3/范围1+2比例评分

        评分逻辑：
        - 范围3/1+2比例越高，说明企业意识到供应链排放重要性
        - 但比例过高(>50)可能说明范围1+2控制不佳
        - 理想区间：5-20倍（新能源制造业典型范围）

        Returns:
            比例评分(0-100)或None
        """
        scope3_total = self.scope3_emissions
        scope12_emissions = self.get_scope1_2_emissions()

        if scope3_total is None or scope12_emissions is None or scope12_emissions <= 0:
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

    def _calculate_curtailment_score(self) -> Optional[float]:
        """计算弃风/弃光率得分（越低越好）

        Returns:
            得分(0-100)或None
        """
        if self.curtailment_rate is None:
            return None

        # 弃电率<2%得满分，>10%得0分
        if self.curtailment_rate <= 2.0:
            return 100.0
        if self.curtailment_rate >= 10.0:
            return 0.0

        ratio = (self.curtailment_rate - 2.0) / 8.0
        return 100.0 * (1 - ratio)

    def get_dimension_score(self, dimension: str) -> float:
        """计算指定维度的得分

        Args:
            dimension: 维度代码 ('E', 'S', 或 'G')

        Returns:
            维度得分 (0-100)
        """
        scores: List[Optional[float]] = []

        if dimension == "E":
            # 环境维度评分（分层加权，含范围3评分）
            # 一级指标（45%）：碳强度15% + 范围3覆盖率10% + 范围3/1+2比例5% + SBTi目标15%
            # 二级指标（30%）：可再生能源、能源效率、废弃物回收、水资源
            # 三级指标（25%）：新能源特色指标

            carbon_score = self._calculate_carbon_intensity_score()
            scope3_ratio_score = self._calculate_scope3_ratio_score()
            scores = [
                # 一级指标
                carbon_score,
                None,  # scope3_coverage_score 已移除
                scope3_ratio_score,
                # 二级指标
                self._safe_score(self.renewable_energy_ratio, 100.0),
                self._safe_score(self.energy_efficiency, 100.0),
                self._safe_score(self.waste_recycling_rate, 100.0),
                self._calculate_water_intensity_score(),
                # 三级指标：新能源特色
                self._safe_score(
                    self.turbine_availability,
                    100.0,
                    multiplier=100.0 / TURBINE_AVAILABILITY_BENCHMARK,
                ),
                self._calculate_curtailment_score(),
                self._safe_score(
                    self.battery_cycle_life, 100.0, multiplier=100.0 / BATTERY_CYCLE_LIFE_BENCHMARK
                ),
                self._safe_score(self.battery_recycling_rate, 100.0),
                self._safe_score(
                    self.electrolysis_efficiency,
                    100.0,
                    multiplier=100.0 / ELECTROLYSIS_EFFICIENCY_BENCHMARK,
                ),
                self._safe_score(self.energy_storage_safety_score, 100.0),
            ]
            # 使用加权平均算法
            weights = list(E_DIMENSION_WEIGHTS.values())
            return _calculate_weighted_score(scores, weights, DEFAULT_SCORE)
        elif dimension == "S":
            # S维度评分（分层加权，与E维度对齐）
            # 一级指标（45%）：员工发展与多元化
            diversity_score = self._calculate_diversity_score()
            training_score = self._calculate_training_score()
            employee_scale_score = self._calculate_employee_scale_score()

            # 二级指标（30%）：安全与福祉
            safety_score = self._calculate_safety_score()
            safety_investment_score = self._safe_score(self.safety_investment_ratio, 100.0)

            # 三级指标（25%）：社区责任
            community_score = self._safe_score(
                self.community_investment_per_revenue, 1.0, multiplier=100.0
            )
            local_employment_score = self._safe_score(self.local_employment_ratio, 100.0)

            scores = [
                # 一级指标
                diversity_score,
                training_score,
                employee_scale_score,
                # 二级指标
                safety_score,
                safety_investment_score,
                # 三级指标
                community_score,
                local_employment_score,
            ]
            # 使用加权平均算法（与E维度一致）
            weights = list(S_DIMENSION_WEIGHTS.values())
            return _calculate_weighted_score(scores, weights, DEFAULT_SCORE)
        elif dimension == "G":
            # G维度评分（分层加权，与E/S维度对齐）
            # 第一层（35%）：董事会与治理结构
            # 第二层（30%）：合规与商业道德
            # 第三层（20%）：气候治理（新能源特色）
            # 第四层（15%）：透明度与问责

            # 第一层：董事会与治理结构
            board_effectiveness = self._calculate_board_effectiveness()
            esg_governance = self._calculate_esg_governance_score()
            audit_score = self._safe_score(
                self.board_independence_ratio, 100.0, multiplier=1.0
            )  # 作为代理

            # 第二层：合规与商业道德
            compliance_maturity = self._calculate_compliance_maturity()
            whistleblower_score = (
                100.0
                if self.whistleblower_protection
                else 0.0 if self.whistleblower_protection is not None else None
            )
            business_ethics = self._calculate_business_ethics_score()

            # 第三层：透明度与问责
            report_quality = self._safe_score(self.esg_report_quality, 100.0)
            stakeholder_score = self._calculate_stakeholder_engagement_score()

            scores = [
                # 第一层
                board_effectiveness,
                esg_governance,
                audit_score,
                # 第二层
                compliance_maturity,
                whistleblower_score,
                business_ethics,
                # 第三层
                report_quality,
                stakeholder_score,
            ]
            # 使用加权平均算法（与E/S维度一致）
            weights = list(G_DIMENSION_WEIGHTS.values())
            return _calculate_weighted_score(scores, weights, DEFAULT_SCORE)

        return DEFAULT_SCORE

    def _safe_score(
        self, value: Optional[float], max_val: float, multiplier: float = 1.0
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
        return min(value * multiplier, max_val) if multiplier != 1.0 else min(value, max_val)

    def _calculate_diversity_score(self) -> Optional[float]:
        """计算员工多元化得分（0-100）

        综合评估女性员工比例和高管层女性比例。
        女性员工比例权重60%，高管女性比例权重40%。

        Returns:
            多元化得分(0-100)或None
        """
        if self.female_ratio is None and self.female_executive_ratio is None:
            return None

        scores = []
        weights = []

        # 女性员工比例评分
        if self.female_ratio is not None:
            # 理想区间35-50%，低于20%或高于60%需要关注
            if self.female_ratio >= DIVERSITY_BENCHMARK_EXCELLENT:
                score = 100.0
            elif self.female_ratio >= DIVERSITY_BENCHMARK_GOOD:
                score = 80.0 + (self.female_ratio - DIVERSITY_BENCHMARK_GOOD) / 5.0 * 20.0
            elif self.female_ratio >= 20.0:
                score = 60.0 + (self.female_ratio - 20.0) / 15.0 * 20.0
            else:
                score = max(0.0, self.female_ratio / 20.0 * 60.0)
            scores.append(score)
            weights.append(0.6)

        # 高管层女性比例评分（更严格的标准）
        if self.female_executive_ratio is not None:
            # 高管层30%为优秀，20%为良好
            if self.female_executive_ratio >= 30.0:
                score = 100.0
            elif self.female_executive_ratio >= 20.0:
                score = 70.0 + (self.female_executive_ratio - 20.0) / 10.0 * 30.0
            elif self.female_executive_ratio >= 10.0:
                score = 50.0 + (self.female_executive_ratio - 10.0) / 10.0 * 20.0
            else:
                score = max(0.0, self.female_executive_ratio / 10.0 * 50.0)
            scores.append(score)
            weights.append(0.4)

        if not scores:
            return None

        # 加权平均
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        return sum(s * nw for s, nw in zip(scores, normalized_weights))

    def _calculate_training_score(self) -> Optional[float]:
        """计算培训与发展得分（0-100）

        综合评估人均培训时长和人均培训投入。

        Returns:
            培训得分(0-100)或None
        """
        if self.training_hours is None and self.training_investment_per_employee is None:
            return None

        scores = []

        # 人均培训时长评分
        if self.training_hours is not None:
            if self.training_hours >= TRAINING_HOURS_BENCHMARK:
                score = 100.0
            else:
                score = (self.training_hours / TRAINING_HOURS_BENCHMARK) * 100.0
            scores.append(score)

        # 人均培训投入评分（如果有数据）
        if self.training_investment_per_employee is not None:
            # 假设500美元/人为基准
            benchmark_investment = 500.0
            score = min(
                100.0, (self.training_investment_per_employee / benchmark_investment) * 100.0
            )
            scores.append(score)

        if not scores:
            return None

        return sum(scores) / len(scores)

    def _calculate_employee_scale_score(self) -> Optional[float]:
        """计算员工规模得分（0-100）

        评估企业规模，鼓励创造就业。
        使用对数尺度避免大企业过度优势。

        Returns:
            规模得分(0-100)或None
        """
        if self.employee_count is None:
            return None

        import math

        # 使用对数尺度：1000人=60分，5000人=80分，20000人=100分
        if self.employee_count <= 0:
            return 0.0

        log_score = 20.0 * math.log10(self.employee_count / 100.0)
        return min(100.0, max(0.0, log_score))

    def _calculate_safety_score(self) -> Optional[float]:
        """计算安全绩效得分（0-100）

        综合评估TRIR（总可记录伤害率）、LTIFR（失时工伤率）和安全事故数量。
        分数越高表示安全性越好。

        Returns:
            安全得分(0-100)或None
        """
        has_trir = self.trir is not None
        has_ltifr = self.ltifr is not None or self.lost_time_injury_rate is not None
        has_incidents = self.safety_incidents is not None

        if not (has_trir or has_ltifr or has_incidents):
            return None

        scores = []
        weights = []

        # TRIR评分（最权威的安全指标）
        trir_value = self.trir
        if trir_value is not None:
            if trir_value <= TRIR_BENCHMARK_EXCELLENT:
                score = 100.0
            elif trir_value >= TRIR_BENCHMARK_POOR:
                score = 0.0
            else:
                ratio = (trir_value - TRIR_BENCHMARK_EXCELLENT) / (
                    TRIR_BENCHMARK_POOR - TRIR_BENCHMARK_EXCELLENT
                )
                score = 100.0 * (1 - ratio)
            scores.append(score)
            weights.append(0.5)

        # LTIFR评分
        ltifr_value = self.ltifr if self.ltifr is not None else self.lost_time_injury_rate
        if ltifr_value is not None:
            # LTIFR基准值比TRIR更严格
            ltifr_excellent = TRIR_BENCHMARK_EXCELLENT * 0.6
            ltifr_poor = TRIR_BENCHMARK_POOR * 0.6
            if ltifr_value <= ltifr_excellent:
                score = 100.0
            elif ltifr_value >= ltifr_poor:
                score = 0.0
            else:
                ratio = (ltifr_value - ltifr_excellent) / (ltifr_poor - ltifr_excellent)
                score = 100.0 * (1 - ratio)
            scores.append(score)
            weights.append(0.3)

        # 安全事故数量评分（相对指标，需要员工规模）
        if (
            self.safety_incidents is not None
            and self.employee_count is not None
            and self.employee_count > 0
        ):
            # 计算事故率（每千人）
            incident_rate = (self.safety_incidents / self.employee_count) * 1000
            if incident_rate == 0:
                score = 100.0
            elif incident_rate <= 1.0:
                score = 80.0 + (1.0 - incident_rate) / 1.0 * 20.0
            elif incident_rate <= 5.0:
                score = 60.0 + (5.0 - incident_rate) / 4.0 * 20.0
            else:
                score = max(0.0, 60.0 - (incident_rate - 5.0) / 5.0 * 60.0)
            scores.append(score)
            weights.append(0.2)

        if not scores:
            return None

        # 加权平均
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        return sum(s * nw for s, nw in zip(scores, normalized_weights))

    def _calculate_board_effectiveness(self) -> Optional[float]:
        """计算董事会效能得分（0-100）

        综合评估董事会独立性和多元化。
        独立性权重60%，多元化权重40%。

        Returns:
            董事会效能得分(0-100)或None
        """
        has_independence = self.board_independence_ratio is not None

        # 检查是否有董事会多元化数据（使用现有字段作为代理）
        # 在实际应用中，可以添加 board_diversity_score 字段
        has_diversity = False  # 当前模型中暂无此字段

        if not has_independence and not has_diversity:
            return None

        scores = []
        weights = []

        # 董事会独立性评分
        if self.board_independence_ratio is not None:
            if self.board_independence_ratio >= BOARD_INDEPENDENCE_BENCHMARK:
                score = 100.0
            elif self.board_independence_ratio >= 33.0:  # 最低合规标准
                score = (
                    60.0
                    + (self.board_independence_ratio - 33.0)
                    / (BOARD_INDEPENDENCE_BENCHMARK - 33.0)
                    * 40.0
                )
            else:
                score = max(0.0, self.board_independence_ratio / 33.0 * 60.0)
            scores.append(score)
            weights.append(0.6)

        # 董事会多元化评分（使用ESG委员会独立性作为代理）
        if self.esg_committee_independence is not None:
            # ESG委员会独立性反映了董事会对ESG的重视
            if self.esg_committee_independence >= BOARD_DIVERSITY_BENCHMARK:
                score = 100.0
            else:
                score = (self.esg_committee_independence / BOARD_DIVERSITY_BENCHMARK) * 100.0
            scores.append(score)
            weights.append(0.4)

        if not scores:
            return None

        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        return sum(s * nw for s, nw in zip(scores, normalized_weights))

    def _calculate_esg_governance_score(self) -> Optional[float]:
        """计算ESG治理架构得分（0-100）

        评估ESG委员会独立性和ESG报告质量。

        Returns:
            ESG治理得分(0-100)或None
        """
        has_committee = self.esg_committee_independence is not None
        has_report_quality = self.esg_report_quality is not None

        if not has_committee and not has_report_quality:
            return None

        scores = []

        if self.esg_committee_independence is not None:
            if self.esg_committee_independence >= 50.0:
                score = 100.0
            else:
                score = (self.esg_committee_independence / 50.0) * 100.0
            scores.append(score)

        if self.esg_report_quality is not None:
            scores.append(self.esg_report_quality)

        if not scores:
            return None

        return sum(scores) / len(scores)

    def _calculate_compliance_maturity(self) -> Optional[float]:
        """计算合规成熟度得分（0-100）

        综合评估道德培训和反腐败培训覆盖率。

        Returns:
            合规成熟度得分(0-100)或None
        """
        has_ethics = self.ethics_training_coverage is not None
        has_anti_corruption = self.anti_corruption_training_coverage is not None

        if not has_ethics and not has_anti_corruption:
            return None

        scores = []
        weights = []

        # 道德培训覆盖率（权重60%）
        if self.ethics_training_coverage is not None:
            if self.ethics_training_coverage >= ETHICS_TRAINING_BENCHMARK:
                score = 100.0
            else:
                score = (self.ethics_training_coverage / ETHICS_TRAINING_BENCHMARK) * 100.0
            scores.append(score)
            weights.append(0.6)

        # 反腐败培训覆盖率（权重40%）
        if self.anti_corruption_training_coverage is not None:
            if self.anti_corruption_training_coverage >= ANTI_CORRUPTION_BENCHMARK:
                score = 100.0
            else:
                score = (self.anti_corruption_training_coverage / ANTI_CORRUPTION_BENCHMARK) * 100.0
            scores.append(score)
            weights.append(0.4)

        if not scores:
            return None

        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        return sum(s * nw for s, nw in zip(scores, normalized_weights))

    def _calculate_business_ethics_score(self) -> Optional[float]:
        """计算商业道德体系得分（0-100）

        基于道德培训覆盖率和举报人保护机制评估商业道德体系成熟度。

        Returns:
            商业道德得分(0-100)或None
        """
        has_ethics = self.ethics_training_coverage is not None
        has_whistleblower = self.whistleblower_protection is not None

        if not has_ethics and not has_whistleblower:
            return None

        scores = []
        weights = []

        # 道德培训（权重70%）
        if self.ethics_training_coverage is not None:
            if self.ethics_training_coverage >= ETHICS_TRAINING_BENCHMARK:
                score = 100.0
            else:
                score = (self.ethics_training_coverage / ETHICS_TRAINING_BENCHMARK) * 100.0
            scores.append(score)
            weights.append(0.7)

        # 举报人保护（权重30%）
        if self.whistleblower_protection is not None:
            score = 100.0 if self.whistleblower_protection else 0.0
            scores.append(score)
            weights.append(0.3)

        if not scores:
            return None

        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        return sum(s * nw for s, nw in zip(scores, normalized_weights))

    def _calculate_stakeholder_engagement_score(self) -> Optional[float]:
        """计算利益相关方参与得分（0-100）

        基于ESG报告质量和社区投资评估利益相关方参与度。

        Returns:
            利益相关方参与得分(0-100)或None
        """
        has_report = self.esg_report_quality is not None
        has_community = self.community_investment_per_revenue is not None

        if not has_report and not has_community:
            return None

        scores = []
        weights = []

        # ESG报告质量（权重60%）
        if self.esg_report_quality is not None:
            scores.append(self.esg_report_quality)
            weights.append(0.6)

        # 社区投资占营收比例（权重40%）
        if self.community_investment_per_revenue is not None:
            # 1%为优秀标准
            benchmark = 1.0
            if self.community_investment_per_revenue >= benchmark:
                score = 100.0
            else:
                score = (self.community_investment_per_revenue / benchmark) * 100.0
            scores.append(score)
            weights.append(0.4)

        if not scores:
            return None

        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        return sum(s * nw for s, nw in zip(scores, normalized_weights))

    def calculate_overall_confidence(self) -> str:
        """计算整体置信度等级

        Returns:
            置信度等级: "极低", "低", "中", "较高", "高"
        """
        if not self.confidence:
            return "极低"
        avg: float = sum(self.confidence.values()) / len(self.confidence)
        if avg < 0.3:
            return "低"
        if avg < 0.6:
            return "中"
        if avg < 0.8:
            return "较高"
        return "高"

    def has_dimension_data(self, dimension: str) -> bool:
        """检查指定维度是否有数据

        Args:
            dimension: 维度代码 ('E', 'S', 或 'G')

        Returns:
            该维度是否有任何数据
        """
        checks: Dict[str, List[Optional[Any]]] = {
            "E": [
                self.carbon_emissions,
                self.scope1_emissions,
                self.scope2_emissions_location,
                self.scope2_emissions_market,
                self.scope3_emissions,
                self.carbon_intensity,
                self.renewable_energy_ratio,
                self.energy_efficiency,
                self.water_consumption,
                self.water_intensity,
                self.waste_recycling_rate,
                self.biodiversity_impact_score,
                self.turbine_availability,
                self.battery_cycle_life,
                self.battery_recycling_rate,
                self.electrolysis_efficiency,
                self.energy_storage_safety_score,
            ],
            "S": [
                self.employee_count,
                self.female_ratio,
                self.female_executive_ratio,
                self.training_hours,
                self.safety_incidents,
                self.trir,
                self.ltifr,
                self.safety_investment_ratio,
                self.local_employment_ratio,
                self.community_investment,
            ],
            "G": [
                self.board_independence_ratio,
                self.ethics_training_coverage,
                self.esg_report_quality,
                self.esg_committee_independence,
                self.anti_corruption_training_coverage,
                self.whistleblower_protection,
            ],
        }
        return any(v is not None and v is not False for v in checks.get(dimension, []))

    def get_all_dimension_scores(self) -> Dict[str, float]:
        """获取所有维度的得分

        Returns:
            包含E/S/G三个维度得分的字典
        """
        return {
            "E": self.get_dimension_score("E"),
            "S": self.get_dimension_score("S"),
            "G": self.get_dimension_score("G"),
        }

    def get_emissions_breakdown(self) -> Dict[str, Any]:
        """获取碳排放分解数据

        Returns:
            包含各范围排放的详细字典
        """
        # 基础排放数据
        breakdown = {
            "scope1": self.scope1_emissions,
            "scope2_location": self.scope2_emissions_location,
            "scope2_market": self.scope2_emissions_market,
            "scope2_used": (
                self.scope2_emissions_market
                if self.scope2_emissions_market is not None
                else self.scope2_emissions_location
            ),
            "scope3_summary": self.scope3_emissions,
            "total_calculated": self.get_total_emissions(),
            "total_reported": self.carbon_emissions,
        }

        return breakdown


@dataclass
class BenchmarkData:
    """行业基准数据类

    存储特定行业的平均ESG指标，用于差距分析。

    Attributes:
        industry: 行业名称
        year: 年份
        avg_renewable_energy_ratio: 平均可再生能源比例
        avg_energy_efficiency: 平均能源效率
        avg_female_ratio: 平均女性员工比例
        avg_training_hours: 平均培训时长
        avg_board_independence_ratio: 平均董事会独立比例
        avg_esg_report_quality: 平均ESG报告质量
        avg_carbon_intensity: 平均碳强度
        avg_water_intensity: 平均水资源强度
        source: 数据来源
        sample_size: 样本数量
    """

    industry: str
    year: str

    avg_renewable_energy_ratio: Optional[float] = None
    avg_energy_efficiency: Optional[float] = None
    avg_female_ratio: Optional[float] = None
    avg_training_hours: Optional[float] = None
    avg_board_independence_ratio: Optional[float] = None
    avg_esg_report_quality: Optional[float] = None
    avg_carbon_intensity: Optional[float] = None
    avg_water_intensity: Optional[float] = None

    source: str = ""
    sample_size: int = 0

    def to_metrics(self) -> "ESGMetrics":
        """转换为ESGMetrics对象用于对比

        Returns:
            包含基准数据的ESGMetrics对象
        """
        return ESGMetrics(
            company_name=f"{self.industry}_基准",
            year=self.year,
            renewable_energy_ratio=self.avg_renewable_energy_ratio,
            energy_efficiency=self.avg_energy_efficiency,
            female_ratio=self.avg_female_ratio,
            training_hours=self.avg_training_hours,
            board_independence_ratio=self.avg_board_independence_ratio,
            esg_report_quality=self.avg_esg_report_quality,
            carbon_intensity=self.avg_carbon_intensity,
            water_intensity=self.avg_water_intensity,
            source=self.source,
        )


@dataclass
class AnalysisResult:
    """ESG分析结果类

    存储ESG分析的完整结果，包括得分、差距分析和改进策略。

    Attributes:
        metrics: 原始ESG指标数据
        weights: 各维度权重
        gap_analysis: 差距分析结果
        strategies: 改进策略列表
        overall_score: 总体得分
        confidence_level: 置信度等级
        data_quality_warnings: 数据质量警告
        analyzed_at: 分析时间
    """

    metrics: ESGMetrics
    weights: Dict[str, float] = field(default_factory=lambda: {"E": 0.4, "S": 0.3, "G": 0.3})
    gap_analysis: Dict[str, Any] = field(default_factory=dict)
    strategies: List[Dict[str, Any]] = field(default_factory=list)
    overall_score: float = 0.0
    confidence_level: str = "中"
    data_quality_warnings: List[str] = field(default_factory=list)
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_dimension_gap(self, dimension: str) -> Optional[float]:
        """获取指定维度的差距

        Args:
            dimension: 维度代码 ('E', 'S', 或 'G')

        Returns:
            差距值或None
        """
        gaps = self.gap_analysis.get("dimensions", {})
        dim_data = gaps.get(dimension, {})
        return dim_data.get("gap")

    def get_high_priority_strategies(self) -> List[Dict[str, Any]]:
        """获取高优先级策略

        Returns:
            高优先级策略列表
        """
        return [s for s in self.strategies if s.get("priority") == "高"]

    def has_data_quality_issues(self) -> bool:
        """检查是否存在数据质量问题

        Returns:
            是否存在警告
        """
        return len(self.data_quality_warnings) > 0
