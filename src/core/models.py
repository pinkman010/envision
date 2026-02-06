"""ESG核心数据模型"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


# 常量定义
DEFAULT_SCORE: float = 50.0
GAP_THRESHOLD_HIGH: float = 15.0
GAP_THRESHOLD_MEDIUM: float = 8.0


@dataclass
class ESGMetrics:
    """ESG指标数据类
    
    包含环境(E)、社会(S)、治理(G)三个维度的指标数据，
    支持计算各维度得分。
    
    Attributes:
        company_name: 公司名称
        year: 报告年份
        carbon_emissions: 碳排放量
        renewable_energy_ratio: 可再生能源使用比例(%)
        energy_efficiency: 能源效率指标
        water_consumption: 用水量
        waste_recycling_rate: 废物回收率(%)
        employee_count: 员工数量
        female_ratio: 女性员工比例(%)
        training_hours: 人均培训时长(小时)
        safety_incidents: 安全事故数量
        community_investment: 社区投资金额
        board_independence_ratio: 董事会独立董事比例(%)
        ethics_training_coverage: 道德培训覆盖率(%)
        esg_report_quality: ESG报告质量评分
        source: 数据来源
        extracted_at: 数据提取时间
        confidence: 各字段置信度
        data_sources: 数据来源详情
    """
    company_name: str
    year: str
    
    # 环境指标 (E)
    carbon_emissions: Optional[float] = None
    renewable_energy_ratio: Optional[float] = None
    energy_efficiency: Optional[float] = None
    water_consumption: Optional[float] = None
    waste_recycling_rate: Optional[float] = None
    
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
    
    # 元数据
    source: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: Dict[str, float] = field(default_factory=dict)
    data_sources: Dict[str, str] = field(default_factory=dict)
    
    def get_dimension_score(self, dimension: str) -> float:
        """计算指定维度的得分
        
        Args:
            dimension: 维度代码 ('E', 'S', 或 'G')
            
        Returns:
            维度得分 (0-100)
        """
        scores: List[Optional[float]] = []
        
        if dimension == 'E':
            scores = [
                self._safe_score(self.renewable_energy_ratio, 100.0),
                self._safe_score(self.energy_efficiency, 100.0),
                self._safe_score(self.waste_recycling_rate, 100.0)
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
                self.renewable_energy_ratio,
                self.energy_efficiency,
                self.water_consumption,
                self.waste_recycling_rate
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
