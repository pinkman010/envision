"""ESG核心数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.esg.core.scope3_emissions import Scope3Inventory


@dataclass
class ClimateGovernance:
    """气候治理架构
    
    评估企业在气候治理方面的架构建设情况，
    符合TCFD/ISSB要求的气候治理评估标准。
    
    Attributes:
        board_climate_committee: 董事会气候委员会设立
        exec_comp_linked_to_climate: 高管薪酬与气候目标挂钩
        climate_risk_identification_process: 气候风险识别流程
        regular_climate_reporting_to_board: 定期向董事会汇报气候议题
    """
    board_climate_committee: bool = False  # 董事会气候委员会
    exec_comp_linked_to_climate: bool = False  # 高管薪酬与气候目标挂钩
    climate_risk_identification_process: bool = False  # 气候风险识别流程
    regular_climate_reporting_to_board: bool = False  # 定期向董事会汇报
    
    def get_score(self) -> float:
        """计算气候治理架构评分（0-100）
        
        Returns:
            气候治理架构得分
        """
        score = 0.0
        if self.board_climate_committee:
            score += 30.0
        if self.exec_comp_linked_to_climate:
            score += 30.0
        if self.climate_risk_identification_process:
            score += 20.0
        if self.regular_climate_reporting_to_board:
            score += 20.0
        return score


@dataclass
class TCFDDisclosure:
    """TCFD披露评估
    
    评估企业TCFD（气候相关财务披露工作组）
    四支柱披露完整度。
    
    Attributes:
        governance_disclosed: 治理支柱已披露
        strategy_disclosed: 战略支柱已披露
        risk_management_disclosed: 风险管理支柱已披露
        metrics_targets_disclosed: 指标与目标支柱已披露
    """
    governance_disclosed: bool = False
    strategy_disclosed: bool = False
    risk_management_disclosed: bool = False
    metrics_targets_disclosed: bool = False
    
    def get_score(self) -> float:
        """计算TCFD披露完整度评分（0-100）
        
        Returns:
            TCFD披露完整度得分
        """
        score = 0.0
        if self.governance_disclosed:
            score += 25.0
        if self.strategy_disclosed:
            score += 25.0
        if self.risk_management_disclosed:
            score += 25.0
        if self.metrics_targets_disclosed:
            score += 25.0
        return score


@dataclass
class ClimateDisclosureQuality:
    """气候信息披露质量
    
    评估企业气候信息披露的质量和完整性。
    
    Attributes:
        scope123_full_disclosure: 范围1+2+3完整披露
        third_party_verification: 第三方核证
        historical_data_comparability: 历史数据可比性
        forward_looking_targets: 前瞻性目标披露
    """
    scope123_full_disclosure: bool = False  # 范围1+2+3完整披露
    third_party_verification: bool = False  # 第三方核证
    historical_data_comparability: bool = False  # 历史数据可比性
    forward_looking_targets: bool = False  # 前瞻性目标披露
    
    def get_score(self) -> float:
        """计算气候信息披露质量评分（0-100）
        
        Returns:
            气候信息披露质量得分
        """
        score = 0.0
        if self.scope123_full_disclosure:
            score += 40.0
        if self.third_party_verification:
            score += 30.0
        if self.historical_data_comparability:
            score += 20.0
        if self.forward_looking_targets:
            score += 10.0
        return score

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
    "carbon_intensity": 0.15,          # 范围1+2碳强度
    "scope3_coverage": 0.10,           # 范围3覆盖率
    "scope3_ratio": 0.05,              # 范围3/1+2比例
    "sbti_target": 0.15,               # SBTi目标
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
SCOPE3_RATIO_IDEAL_MIN = 5.0   # 理想区间最小值
SCOPE3_RATIO_IDEAL_MAX = 20.0  # 理想区间最大值
SCOPE3_RATIO_ACCEPTABLE_MAX = 50.0  # 可接受区间最大值

# 范围3覆盖率评分基准
SCOPE3_COVERAGE_BENCHMARK_HIGH = 0.80  # 高覆盖率基准（80%）
SCOPE3_COVERAGE_BENCHMARK_LOW = 0.40   # 低覆盖率基准（40%）

# SBTi状态评分
SBTI_STATUS_SCORES = {
    "committed": 20,
    "target_set": 60,
    "validated": 80,
    "validated_1.5c": 100,
    "validated_wb2c": 90,
    "validated_2c": 80,
    "not_committed": 0,
    "removed": 0,
}

def _calculate_weighted_score(
    scores: List[Optional[float]],
    weights: List[float],
    default_score: float = DEFAULT_SCORE
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
    
    存储企业SBTi承诺状态、减排目标和进度追踪。
    
    Attributes:
        status: SBTi状态（committed/target_set/validated等）
        target_type: 目标类型（absolute/intensity/renewable）
        baseline_year: 基准年
        target_year: 目标年
        baseline_emissions: 基准年排放量（吨CO2e）
        target_emissions: 目标排放量（吨CO2e）
        reduction_rate: 目标减排率（0-1）
        current_emissions: 当前排放量
        current_year: 当前年份
        validation_date: SBTi验证日期
        pathway: 温升路径（1.5c/wb2c/2c）
        scope_coverage: 覆盖范围（1+2/1+2+3）
    """
    
    status: str = "not_committed"  # SBTi状态
    target_type: str = ""  # 目标类型
    baseline_year: int = 0  # 基准年
    target_year: int = 0  # 目标年
    baseline_emissions: Optional[float] = None  # 基准年排放量
    target_emissions: Optional[float] = None  # 目标排放量
    reduction_rate: Optional[float] = None  # 目标减排率（0-1）
    current_emissions: Optional[float] = None  # 当前排放量
    current_year: Optional[int] = None  # 当前年份
    validation_date: Optional[str] = None  # SBTi验证日期
    pathway: str = ""  # 温升路径
    scope_coverage: str = "1+2"  # 覆盖范围
    
    def get_progress_rate(self) -> Optional[float]:
        """计算当前减排进度
        
        Returns:
            当前减排率（相对于基准年），范围0-1
        """
        if (self.baseline_emissions is None or 
            self.current_emissions is None or
            self.baseline_emissions == 0):
            return None
        
        reduction = self.baseline_emissions - self.current_emissions
        return reduction / self.baseline_emissions
    
    def get_progress_score(self) -> float:
        """计算减排进度评分（0-100）
        
        基于当前减排进度与目标减排率的比值评分。
        
        Returns:
            进度评分（0-100）
        """
        progress = self.get_progress_rate()
        if progress is None or self.reduction_rate is None or self.reduction_rate == 0:
            return 0.0
        
        # 计算完成度（当前减排率 / 目标减排率）
        completion = progress / self.reduction_rate
        
        # 计算年份进度
        if self.baseline_year and self.target_year and self.current_year:
            year_progress = (self.current_year - self.baseline_year) / (self.target_year - self.baseline_year)
            # 如果减排进度超前于年份进度，给予奖励
            if completion >= year_progress and year_progress > 0:
                completion = min(1.0, completion * 1.1)  # 10%奖励系数
        
        return min(100.0, completion * 100)
    
    def get_status_score(self) -> float:
        """获取SBTi状态评分
        
        Returns:
            SBTi状态对应的基础评分（0-100）
        """
        return SBTI_STATUS_SCORES.get(self.status, 0)
    
    def get_overall_score(self) -> float:
        """获取SBTi综合评分
        
        综合状态评分（40%）和进度评分（60%）
        
        Returns:
            综合评分（0-100）
        """
        status_score = self.get_status_score()
        progress_score = self.get_progress_score()
        
        # 如果未承诺，直接返回0
        if self.status in ("not_committed", "removed"):
            return 0.0
        
        # 如果已设定目标但未验证，只考虑进度
        if self.status == "target_set":
            return progress_score * 0.6 + status_score * 0.4
        
        # 已验证：状态40% + 进度60%
        return status_score * 0.4 + progress_score * 0.6
    
    def is_on_track(self) -> Optional[bool]:
        """判断是否按进度推进
        
        Returns:
            True: 按计划推进，False: 落后，None: 无法判断
        """
        if not all([self.baseline_year, self.target_year, self.current_year, self.reduction_rate]):
            return None
        
        progress = self.get_progress_rate()
        if progress is None:
            return None
        
        # 计算应达到的减排率（线性插值）
        year_progress = (self.current_year - self.baseline_year) / (self.target_year - self.baseline_year)
        expected_reduction = self.reduction_rate * year_progress
        
        # 允许10%的偏差
        return progress >= expected_reduction * 0.9
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status,
            "target_type": self.target_type,
            "baseline_year": self.baseline_year,
            "target_year": self.target_year,
            "baseline_emissions": self.baseline_emissions,
            "target_emissions": self.target_emissions,
            "reduction_rate": self.reduction_rate,
            "current_emissions": self.current_emissions,
            "current_year": self.current_year,
            "validation_date": self.validation_date,
            "pathway": self.pathway,
            "scope_coverage": self.scope_coverage,
            "progress_rate": self.get_progress_rate(),
            "progress_score": self.get_progress_score(),
            "status_score": self.get_status_score(),
            "overall_score": self.get_overall_score(),
            "on_track": self.is_on_track(),
        }


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
    
    # 范围3完整核算
    scope3_inventory: Optional[Any] = None  # Scope3Inventory对象
    scope3_data_quality_score: Optional[float] = None  # 范围3数据质量评分
    scope3_coverage_percentage: Optional[float] = None  # 范围3数据覆盖率
    
    # SBTi目标
    sbti_target: Optional[SBTiTarget] = None

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
    
    # 治理指标 (G) - 气候治理
    climate_governance: Optional[ClimateGovernance] = None
    tcfd_disclosure: Optional[TCFDDisclosure] = None
    climate_disclosure_quality: Optional[ClimateDisclosureQuality] = None
    climate_disclosure_quality_score: Optional[float] = None  # 0-100

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
        如果scope3_inventory存在，优先使用其完整核算数据。

        Args:
            include_scope3: 是否包含范围3排放

        Returns:
            总碳排放量或None
        """
        # 优先使用scope3_inventory的完整核算数据
        if include_scope3 and self.scope3_inventory is not None:
            scope3 = self.scope3_inventory.get_total_emissions()
            scope1 = self.scope1_emissions or 0
            scope2 = (
                self.scope2_emissions_market
                if self.scope2_emissions_market is not None
                else self.scope2_emissions_location or 0
            )
            if scope1 > 0 or scope2 > 0:
                return scope1 + scope2 + (scope3 or 0)
        
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
            self.industry_sector, 
            CARBON_INTENSITY_BENCHMARKS["new_energy_composite"]
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

    def _calculate_sbti_score(self) -> Optional[float]:
        """计算SBTi目标评分
        
        Returns:
            SBTi综合评分(0-100)或None（如未设置目标）
        """
        if self.sbti_target is None:
            return None
        return self.sbti_target.get_overall_score()

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

    def _calculate_scope3_coverage_score(self) -> Optional[float]:
        """计算范围3覆盖率评分

        基于行业重要性权重计算范围3覆盖率评分。
        - 100分：所有重要类别都有数据
        - 线性递减：按缺失的重要类别数量扣分

        Returns:
            覆盖率评分(0-100)或None
        """
        if self.scope3_inventory is None:
            return None
        
        from src.esg.core.scope3_emissions import NEW_ENERGY_SECTOR_RELEVANCE
        
        relevance_map = NEW_ENERGY_SECTOR_RELEVANCE.get(
            self.scope3_inventory.sector,
            NEW_ENERGY_SECTOR_RELEVANCE.get("wind_power")
        )
        
        if not relevance_map:
            return None
        
        covered_weight = 0.0
        total_weight = 0.0
        
        for cat, weight in relevance_map.items():
            total_weight += weight
            cat_data = self.scope3_inventory.categories.get(cat)
            if cat_data and cat_data.emissions is not None:
                covered_weight += weight
        
        if total_weight == 0:
            return None
        
        # 计算覆盖率并映射到0-100分
        coverage = covered_weight / total_weight
        
        # 覆盖率>80%得满分，<40%得0分，中间线性插值
        if coverage >= SCOPE3_COVERAGE_BENCHMARK_HIGH:
            return 100.0
        if coverage <= SCOPE3_COVERAGE_BENCHMARK_LOW:
            return 0.0
        
        # 线性插值
        ratio = (coverage - SCOPE3_COVERAGE_BENCHMARK_LOW) / (
            SCOPE3_COVERAGE_BENCHMARK_HIGH - SCOPE3_COVERAGE_BENCHMARK_LOW
        )
        return 100.0 * ratio

    def _calculate_scope3_ratio_score(self) -> Optional[float]:
        """计算范围3/范围1+2比例评分

        评分逻辑：
        - 范围3/1+2比例越高，说明企业意识到供应链排放重要性
        - 但比例过高(>50)可能说明范围1+2控制不佳
        - 理想区间：5-20倍（新能源制造业典型范围）

        Returns:
            比例评分(0-100)或None
        """
        if self.scope3_inventory is None:
            return None
        
        scope3_total = self.scope3_inventory.get_total_emissions()
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
            scope3_coverage_score = self._calculate_scope3_coverage_score()
            scope3_ratio_score = self._calculate_scope3_ratio_score()
            sbti_score = self._calculate_sbti_score()
            
            scores = [
                # 一级指标
                carbon_score,
                scope3_coverage_score,
                scope3_ratio_score,
                sbti_score,
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
            scores = [
                self._safe_score(self.female_ratio, 100.0, multiplier=100.0),
                self._safe_score(self.female_executive_ratio, 100.0),
                self._safe_score(self.training_hours, 40.0, multiplier=100.0 / 40.0),
                self._safe_score(self.local_employment_ratio, 100.0),
                self._safe_score(
                    self.community_investment_per_revenue, 1.0, multiplier=100.0
                ),
            ]
            valid_scores: List[float] = [s for s in scores if s is not None]
            return sum(valid_scores) / len(valid_scores) if valid_scores else DEFAULT_SCORE
        elif dimension == "G":
            # G维度评分（分层加权）
            # 传统治理（40%）：董事会独立性10% + ESG委员会独立性10% + 
            #                  道德培训10% + 反腐败培训10%
            # 气候治理（40%）：气候治理架构20% + TCFD披露20%
            # 信息披露（20%）：ESG报告质量10% + 举报人保护10%
            
            # 传统治理指标
            traditional_governance_scores = [
                self._safe_score(self.board_independence_ratio, 100.0),
                self._safe_score(self.esg_committee_independence, 100.0),
                self._safe_score(self.ethics_training_coverage, 100.0),
                self._safe_score(self.anti_corruption_training_coverage, 100.0),
            ]
            
            # 气候治理指标
            climate_governance_score = (
                self.climate_governance.get_score() 
                if self.climate_governance is not None else None
            )
            tcfd_score = (
                self.tcfd_disclosure.get_score() 
                if self.tcfd_disclosure is not None else None
            )
            
            # 信息披露指标
            disclosure_scores = [
                self._safe_score(self.esg_report_quality, 100.0),
                100.0 if self.whistleblower_protection else 0.0 if self.whistleblower_protection is not None else None,
            ]
            
            # 计算各子维度平均分
            valid_traditional = [s for s in traditional_governance_scores if s is not None]
            traditional_avg = sum(valid_traditional) / len(valid_traditional) if valid_traditional else None
            
            valid_disclosure = [s for s in disclosure_scores if s is not None]
            disclosure_avg = sum(valid_disclosure) / len(valid_disclosure) if valid_disclosure else None
            
            # 加权计算最终得分
            all_scores = [
                traditional_avg,    # 传统治理（40%权重）
                climate_governance_score,  # 气候治理架构（20%权重）
                tcfd_score,         # TCFD披露（20%权重）
                disclosure_avg,     # 信息披露（20%权重）
            ]
            weights = [0.40, 0.20, 0.20, 0.20]
            
            return _calculate_weighted_score(all_scores, weights, DEFAULT_SCORE)
        
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
                self.scope3_inventory is not None,
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
                self.climate_governance is not None,
                self.tcfd_disclosure is not None,
                self.climate_disclosure_quality is not None,
                self.climate_disclosure_quality_score,
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
        
        # 如果存在scope3_inventory，添加详细分解
        if self.scope3_inventory is not None:
            breakdown["scope3_detail"] = {
                "total": self.scope3_inventory.get_total_emissions(),
                "upstream": self.scope3_inventory.get_upstream_emissions(),
                "downstream": self.scope3_inventory.get_downstream_emissions(),
                "data_quality_score": self.scope3_inventory.get_data_quality_score(),
                "coverage_percentage": self.scope3_inventory.get_coverage_percentage(),
                "significant_categories": [
                    {
                        "id": cat.value,
                        "name": cat.name,
                        "emissions": self.scope3_inventory.categories[cat].emissions if cat in self.scope3_inventory.categories else None,
                    }
                    for cat in self.scope3_inventory.get_significant_categories(threshold=0.05)
                ],
            }
            
            # 添加CDP对齐评分
            cdp_score = self.scope3_inventory.get_cdp_alignment_score()
            breakdown["scope3_detail"]["cdp_alignment"] = cdp_score
        
        return breakdown

    def get_climate_scenario_analysis(self) -> Optional[Dict[str, Any]]:
        """获取TCFD气候情景分析
        
        执行标准NGFS情景分析，评估企业在不同温升路径下的战略韧性。
        
        Returns:
            TCFD格式气候情景分析报告，或None（如果分析失败）
            
        报告结构:
            - scenarios_analyzed: 分析的情景列表
            - temperature_rise_range: 温升范围
            - resilience_assessment: 韧性评估（最佳/最差/平均）
            - financial_impacts: 各情景财务影响
            - scenario_details: 详细情景分析
            - strategic_implications: 战略建议
            - tcfd_alignment: TCFD对齐情况
            
        使用示例:
            >>> metrics = ESGMetrics(company_name="示例公司", year="2024")
            >>> report = metrics.get_climate_scenario_analysis()
            >>> print(f"韧性评分范围: {report['resilience_assessment']['best_case']:.1f} - "
            ...       f"{report['resilience_assessment']['worst_case']:.1f}")
        """
        try:
            # 延迟导入以避免循环依赖
            from src.esg.core.climate_scenario import ClimateScenarioAnalyzer
            
            analyzer = ClimateScenarioAnalyzer(self)
            return analyzer.generate_tcfd_report()
        except Exception:
            return None


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
