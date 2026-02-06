"""ESG数据模型"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.config import DEFAULT_SCORE


@dataclass
class ESGMetrics:
    """ESG指标数据"""
    company_name: str
    year: str
    
    # 环境指标
    carbon_emissions: Optional[float] = None
    renewable_energy_ratio: Optional[float] = None
    energy_efficiency: Optional[float] = None
    water_consumption: Optional[float] = None
    waste_recycling_rate: Optional[float] = None
    
    # 社会指标
    employee_count: Optional[int] = None
    female_ratio: Optional[float] = None
    training_hours: Optional[float] = None
    safety_incidents: Optional[int] = None
    community_investment: Optional[float] = None
    
    # 治理指标
    board_independence_ratio: Optional[float] = None
    ethics_training_coverage: Optional[float] = None
    esg_report_quality: Optional[float] = None
    
    # 元数据
    source: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: Dict[str, float] = field(default_factory=dict)
    data_sources: Dict[str, str] = field(default_factory=dict)
    
    def get_dimension_score(self, dimension: str) -> float:
        """计算维度得分"""
        scores = []
        
        if dimension == 'E':
            scores = [
                self._safe_score(self.renewable_energy_ratio, 100),
                self._safe_score(self.energy_efficiency, 100),
                self._safe_score(self.waste_recycling_rate, 100)
            ]
        elif dimension == 'S':
            scores = [
                self._safe_score(self.female_ratio, 100, multiplier=100),
                self._safe_score(self.training_hours, 40, multiplier=100/40),
                self._safe_score(self.community_investment, 50000000, multiplier=100/50000000)
            ]
        elif dimension == 'G':
            scores = [
                self._safe_score(self.board_independence_ratio, 100),
                self._safe_score(self.ethics_training_coverage, 100),
                self._safe_score(self.esg_report_quality, 100)
            ]
        
        valid_scores = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else DEFAULT_SCORE
    
    def _safe_score(self, value: Optional[float], max_val: float, multiplier: float = 1.0) -> Optional[float]:
        """安全地计算分数"""
        if value is None:
            return None
        return min(value * multiplier, max_val) if multiplier != 1 else min(value, max_val)
    
    def calculate_overall_confidence(self) -> str:
        """计算整体置信度"""
        if not self.confidence:
            return "极低"
        avg = sum(self.confidence.values()) / len(self.confidence)
        if avg < 0.3: return "低"
        if avg < 0.6: return "中"
        if avg < 0.8: return "较高"
        return "高"
    
    def has_dimension_data(self, dimension: str) -> bool:
        """检查维度是否有数据"""
        checks = {
            'E': [self.carbon_emissions, self.renewable_energy_ratio, 
                  self.energy_efficiency, self.water_consumption, self.waste_recycling_rate],
            'S': [self.employee_count, self.female_ratio, self.training_hours, 
                  self.safety_incidents, self.community_investment],
            'G': [self.board_independence_ratio, self.ethics_training_coverage, self.esg_report_quality]
        }
        return any(v is not None for v in checks.get(dimension, []))


@dataclass
class AnalysisResult:
    """分析结果"""
    metrics: ESGMetrics
    weights: Dict[str, float]
    gap_analysis: Dict[str, Any]
    strategies: List[Dict[str, Any]]
    overall_score: float = 0.0
    confidence_level: str = "中"
    data_quality_warnings: List[str] = field(default_factory=list)


@dataclass
class BenchmarkData:
    """行业基准数据"""
    industry: str
    year: str
    
    avg_renewable_energy_ratio: Optional[float] = None
    avg_energy_efficiency: Optional[float] = None
    avg_female_ratio: Optional[float] = None
    avg_training_hours: Optional[float] = None
    avg_board_independence_ratio: Optional[float] = None
    
    source: str = ""
    sample_size: int = 0
