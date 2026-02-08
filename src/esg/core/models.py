"""ESG核心数据模型"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


# 常量定义
DEFAULT_SCORE: float = 50.0
DEFAULT_TARGET_SCORE: float = 80.0
GAP_THRESHOLD_HIGH: float = 15.0
GAP_THRESHOLD_MEDIUM: float = 8.0

# 碳强度评分参考值（吨CO2e/万元营收）
# 低于此值为优秀，高于此值为差
CARBON_INTENSITY_BENCHMARK_LOW = 0.5   # 优秀阈值
CARBON_INTENSITY_BENCHMARK_HIGH = 2.0  # 较差阈值

# 新能源特色指标评分参考值
TURBINE_AVAILABILITY_BENCHMARK = 97.0      # 风机可利用率基准
BATTERY_CYCLE_LIFE_BENCHMARK = 6000        # 电池循环寿命基准
BATTERY_RECYCLING_RATE_BENCHMARK = 95.0    # 电池回收率基准
ELECTROLYSIS_EFFICIENCY_BENCHMARK = 70.0   # 电解效率基准

# 行业指标评分参考值
BIODIVERSITY_IMPACT_BENCHMARK = 80.0       # 生物多样性影响基准
ENERGY_STORAGE_SAFETY_BENCHMARK = 90.0     # 储能安全评分基准
WATER_INTENSITY_BENCHMARK_LOW = 10.0       # 水资源强度优秀阈值（立方米/万元营收）
WATER_INTENSITY_BENCHMARK_HIGH = 50.0      # 水资源强度较差阈值


@dataclass
class ESGMetrics:
    """ESG指标数据类
    
    包含环境(E)、社会(S)、治理(G)三个维度的指标数据，
    支持计算各维度得分。
    
    Attributes:
        company_name: 公司名称
        year: 报告年份
        
        # 碳排放指标（范围1/2/3分离）
        carbon_emissions: 总碳排放量（向后兼容，可为范围1+2+3总和）
        scope1_emissions: 范围1排放（直接排放）
        scope2_emissions_location: 范围2排放（基于位置法）
        scope2_emissions_market: 范围2排放（基于市场法）
        scope3_emissions: 范围3排放（价值链间接排放）
        carbon_intensity: 碳强度（吨CO2e/万元营收）
        
        # 能源指标
        renewable_energy_ratio: 可再生能源使用比例(%)
        energy_efficiency: 能源效率指标
        
        # 水资源指标
        water_consumption: 用水量
        water_intensity: 水资源强度（立方米/万元营收）
        
        # 废弃物指标
        waste_recycling_rate: 废物回收率(%)
        
        # 生物多样性
        biodiversity_impact_score: 生物多样性影响评分(0-100)
        
        # 社会指标 (S)
        employee_count: 员工数量
        female_ratio: 女性员工比例(%)
        training_hours: 人均培训时长(小时)
        safety_incidents: 安全事故数量
        community_investment: 社区投资金额
        
        # 治理指标 (G)
        board_independence_ratio: 董事会独立董事比例(%)
        ethics_training_coverage: 道德培训覆盖率(%)
        esg_report_quality: ESG报告质量评分
        
        # 新能源特色指标
        turbine_availability: 风机可利用率(%)
        battery_cycle_life: 电池循环寿命(次)
        battery_recycling_rate: 电池回收率(%)
        electrolysis_efficiency: 电解效率(%)
        energy_storage_safety_score: 储能安全评分(0-100)
        
        # 元数据
        source: 数据来源
        extracted_at: 数据提取时间
        confidence: 各字段置信度
        data_sources: 数据来源详情
    """
    company_name: str
    year: str
    
    # 环境指标 (E) - 碳排放
    carbon_emissions: Optional[float] = None
    scope1_emissions: Optional[float] = None
    scope2_emissions_location: Optional[float] = None
    scope2_emissions_market: Optional[float] = None
    scope3_emissions: Optional[float] = None
    carbon_intensity: Optional[float] = None
    
    # 环境指标 (E) - 能源
    renewable_energy_ratio: Optional[float] = None
    energy_efficiency: Optional[float] = None
    
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
    training_hours: Optional[float] = None
    safety_incidents: Optional[int] = None
    community_investment: Optional[float] = None
    
    # 治理指标 (G)
    board_independence_ratio: Optional[float] = None
    ethics_training_coverage: Optional[float] = None
    esg_report_quality: Optional[float] = None
    
    # 新能源特色指标
    turbine_availability: Optional[float] = None
    battery_cycle_life: Optional[float] = None
    battery_recycling_rate: Optional[float] = None
    electrolysis_efficiency: Optional[float] = None
    energy_storage_safety_score: Optional[float] = None
    
    # 元数据
    source: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: Dict[str, float] = field(default_factory=dict)
    data_sources: Dict[str, str] = field(default_factory=dict)
    
    def get_total_emissions(self) -> Optional[float]:
        """计算总碳排放量
        
        优先使用分离的范围1/2/3排放数据，如不存在则使用carbon_emissions字段。
        
        Returns:
            总碳排放量或None
        """
        # 如果scope1和scope2（任一方法）存在，计算总和
        if self.scope1_emissions is not None:
            total = self.scope1_emissions
            # 范围2使用市场法优先，否则使用位置法
            scope2 = self.scope2_emissions_market if self.scope2_emissions_market is not None else self.scope2_emissions_location
            if scope2 is not None:
                total += scope2
            if self.scope3_emissions is not None:
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
            scope2 = self.scope2_emissions_market if self.scope2_emissions_market is not None else self.scope2_emissions_location
            if scope2 is not None:
                return self.scope1_emissions + scope2
            return self.scope1_emissions
        return self.carbon_emissions
    
    def _calculate_carbon_intensity_score(self) -> Optional[float]:
        """计算碳强度得分（越低越好）
        
        使用反向计分：碳强度越低得分越高
        
        Returns:
            碳强度得分(0-100)或None
        """
        intensity = self.carbon_intensity
        if intensity is None:
            return None
        
        # 低于优秀阈值得满分
        if intensity <= CARBON_INTENSITY_BENCHMARK_LOW:
            return 100.0
        # 高于较差阈值得0分
        if intensity >= CARBON_INTENSITY_BENCHMARK_HIGH:
            return 0.0
        
        # 线性插值计算得分
        # 得分 = 100 - (强度 - 低阈值) / (高阈值 - 低阈值) * 100
        ratio = (intensity - CARBON_INTENSITY_BENCHMARK_LOW) / \
                (CARBON_INTENSITY_BENCHMARK_HIGH - CARBON_INTENSITY_BENCHMARK_LOW)
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
        ratio = (intensity - WATER_INTENSITY_BENCHMARK_LOW) / \
                (WATER_INTENSITY_BENCHMARK_HIGH - WATER_INTENSITY_BENCHMARK_LOW)
        return 100.0 * (1 - ratio)
    
    def get_dimension_score(self, dimension: str) -> float:
        """计算指定维度的得分
        
        Args:
            dimension: 维度代码 ('E', 'S', 或 'G')
            
        Returns:
            维度得分 (0-100)
        """
        scores: List[Optional[float]] = []
        
        if dimension == 'E':
            # 环境维度评分：包含碳强度、可再生能源、能源效率、废弃物回收、
            # 水资源强度、生物多样性、新能源特色指标
            scores = [
                # 碳强度（越低越好）
                self._calculate_carbon_intensity_score(),
                # 可再生能源比例
                self._safe_score(self.renewable_energy_ratio, 100.0),
                # 能源效率
                self._safe_score(self.energy_efficiency, 100.0),
                # 废弃物回收率
                self._safe_score(self.waste_recycling_rate, 100.0),
                # 水资源强度（越低越好）
                self._calculate_water_intensity_score(),
                # 生物多样性影响评分
                self._safe_score(self.biodiversity_impact_score, 100.0),
                # 新能源特色指标
                self._safe_score(self.turbine_availability, 100.0, 
                                multiplier=100.0 / TURBINE_AVAILABILITY_BENCHMARK),
                self._safe_score(self.battery_cycle_life, 100.0,
                                multiplier=100.0 / BATTERY_CYCLE_LIFE_BENCHMARK),
                self._safe_score(self.battery_recycling_rate, 100.0),
                self._safe_score(self.electrolysis_efficiency, 100.0,
                                multiplier=100.0 / ELECTROLYSIS_EFFICIENCY_BENCHMARK),
                self._safe_score(self.energy_storage_safety_score, 100.0),
            ]
        elif dimension == 'S':
            scores = [
                self._safe_score(self.female_ratio, 100.0, multiplier=100.0),
                self._safe_score(self.training_hours, 40.0, multiplier=100.0 / 40.0),
                self._safe_score(self.community_investment, 50000000.0, multiplier=100.0 / 50000000.0)
            ]
        elif dimension == 'G':
            scores = [
                self._safe_score(self.board_independence_ratio, 100.0),
                self._safe_score(self.ethics_training_coverage, 100.0),
                self._safe_score(self.esg_report_quality, 100.0)
            ]
        
        valid_scores: List[float] = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else DEFAULT_SCORE
    
    def _safe_score(self, value: Optional[float], max_val: float, multiplier: float = 1.0) -> Optional[float]:
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
            'E': [
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
            'S': [
                self.employee_count,
                self.female_ratio,
                self.training_hours,
                self.safety_incidents,
                self.community_investment
            ],
            'G': [
                self.board_independence_ratio,
                self.ethics_training_coverage,
                self.esg_report_quality
            ]
        }
        return any(v is not None for v in checks.get(dimension, []))
    
    def get_all_dimension_scores(self) -> Dict[str, float]:
        """获取所有维度的得分
        
        Returns:
            包含E/S/G三个维度得分的字典
        """
        return {
            'E': self.get_dimension_score('E'),
            'S': self.get_dimension_score('S'),
            'G': self.get_dimension_score('G')
        }
    
    def get_emissions_breakdown(self) -> Dict[str, Optional[float]]:
        """获取碳排放分解数据
        
        Returns:
            包含各范围排放的字典
        """
        return {
            'scope1': self.scope1_emissions,
            'scope2_location': self.scope2_emissions_location,
            'scope2_market': self.scope2_emissions_market,
            'scope2_used': self.scope2_emissions_market if self.scope2_emissions_market is not None else self.scope2_emissions_location,
            'scope3': self.scope3_emissions,
            'total_calculated': self.get_total_emissions(),
            'total_reported': self.carbon_emissions,
        }


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
    
    def to_metrics(self) -> 'ESGMetrics':
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
            source=self.source
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
