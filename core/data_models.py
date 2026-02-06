"""数据模型定义

定义ESG分析相关的数据模型，使用dataclass提供类型安全和默认值处理。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from core.constants import (
    DEFAULT_DIMENSION_SCORE,
    CONFIDENCE_THRESHOLDS
)


@dataclass
class ESGMetrics:
    """ESG指标数据模型
    
    包含环境(E)、社会(S)、治理(G)三个维度的指标数据。
    所有数值字段均为Optional，表示可能缺失。
    """
    company_name: str
    year: str
    
    # E环境指标
    carbon_emissions: Optional[float] = None
    renewable_energy_ratio: Optional[float] = None
    energy_efficiency: Optional[float] = None
    water_consumption: Optional[float] = None
    waste_recycling_rate: Optional[float] = None
    
    # S社会指标
    employee_count: Optional[int] = None
    female_ratio: Optional[float] = None
    training_hours: Optional[float] = None
    safety_incidents: Optional[int] = None
    community_investment: Optional[float] = None
    
    # G治理指标
    board_independence_ratio: Optional[float] = None
    ethics_training_coverage: Optional[float] = None
    esg_report_quality: Optional[float] = None
    
    # 元数据
    source: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: Dict[str, float] = field(default_factory=dict)
    data_sources: Dict[str, str] = field(default_factory=dict)
    
    def get_dimension_score(self, dimension: str) -> float:
        """计算维度得分
        
        根据维度类型计算得分，处理缺失数据情况。
        如果所有指标都缺失，返回默认值而非0。
        
        Args:
            dimension: 维度标识，'E'/'S'/'G'
            
        Returns:
            维度得分(0-100)，无数据时返回默认值
        """
        scores: List[float] = []
        
        if dimension == 'E':
            scores = self._calculate_e_scores()
        elif dimension == 'S':
            scores = self._calculate_s_scores()
        elif dimension == 'G':
            scores = self._calculate_g_scores()
        
        valid_scores = [s for s in scores if s is not None and s > 0]
        
        if not valid_scores:
            return DEFAULT_DIMENSION_SCORE
        
        return sum(valid_scores) / len(valid_scores)
    
    def _calculate_e_scores(self) -> List[Optional[float]]:
        """计算环境维度各指标得分"""
        return [
            min(self.renewable_energy_ratio, 100) if self.renewable_energy_ratio is not None else None,
            min(self.energy_efficiency, 100) if self.energy_efficiency is not None else None,
            min(self.waste_recycling_rate, 100) if self.waste_recycling_rate is not None else None
        ]
    
    def _calculate_s_scores(self) -> List[Optional[float]]:
        """计算社会维度各指标得分"""
        scores = []
        
        if self.female_ratio is not None:
            scores.append(min(self.female_ratio * 100, 100))
        else:
            scores.append(None)
        
        if self.training_hours is not None:
            scores.append(min(self.training_hours / 40 * 100, 100))
        else:
            scores.append(None)
        
        if self.community_investment is not None:
            investment_score = min(self.community_investment / 50000000 * 100, 100)
            scores.append(investment_score)
        else:
            scores.append(None)
        
        return scores
    
    def _calculate_g_scores(self) -> List[Optional[float]]:
        """计算治理维度各指标得分"""
        return [
            min(self.board_independence_ratio, 100) if self.board_independence_ratio is not None else None,
            min(self.ethics_training_coverage, 100) if self.ethics_training_coverage is not None else None,
            min(self.esg_report_quality, 100) if self.esg_report_quality is not None else None
        ]
    
    def calculate_overall_confidence(self) -> str:
        """计算整体置信度等级
        
        基于各指标提取的置信度，计算整体等级。
        
        Returns:
            置信度等级（极低/低/中/较高/高）
        """
        if not self.confidence:
            return "极低"
        
        avg_conf = sum(self.confidence.values()) / len(self.confidence)
        
        if avg_conf < CONFIDENCE_THRESHOLDS["低"]:
            return "低"
        elif avg_conf < CONFIDENCE_THRESHOLDS["中"]:
            return "中"
        elif avg_conf < CONFIDENCE_THRESHOLDS["较高"]:
            return "较高"
        else:
            return "高"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            按E/S/G维度组织的字典
        """
        return {
            "E": {
                "carbon_emissions": self.carbon_emissions,
                "renewable_energy_ratio": self.renewable_energy_ratio,
                "energy_efficiency": self.energy_efficiency,
                "water_consumption": self.water_consumption,
                "waste_recycling_rate": self.waste_recycling_rate
            },
            "S": {
                "employee_count": self.employee_count,
                "female_ratio": self.female_ratio,
                "training_hours": self.training_hours,
                "safety_incidents": self.safety_incidents,
                "community_investment": self.community_investment
            },
            "G": {
                "board_independence_ratio": self.board_independence_ratio,
                "ethics_training_coverage": self.ethics_training_coverage,
                "esg_report_quality": self.esg_report_quality
            }
        }
    
    def has_dimension_data(self, dimension: str) -> bool:
        """检查指定维度是否有数据
        
        Args:
            dimension: 维度标识，'E'/'S'/'G'
            
        Returns:
            该维度是否有任何有效数据
        """
        if dimension == 'E':
            return any([
                self.carbon_emissions is not None,
                self.renewable_energy_ratio is not None,
                self.energy_efficiency is not None,
                self.water_consumption is not None,
                self.waste_recycling_rate is not None
            ])
        elif dimension == 'S':
            return any([
                self.employee_count is not None,
                self.female_ratio is not None,
                self.training_hours is not None,
                self.safety_incidents is not None,
                self.community_investment is not None
            ])
        elif dimension == 'G':
            return any([
                self.board_independence_ratio is not None,
                self.ethics_training_coverage is not None,
                self.esg_report_quality is not None
            ])
        return False
    
    def get_missing_indicators(self, dimension: Optional[str] = None) -> List[str]:
        """获取缺失的指标列表
        
        Args:
            dimension: 可选，指定维度，不指定则检查所有
            
        Returns:
            缺失的指标名称列表
        """
        all_indicators = {
            'E': ['carbon_emissions', 'renewable_energy_ratio', 'energy_efficiency', 
                  'water_consumption', 'waste_recycling_rate'],
            'S': ['employee_count', 'female_ratio', 'training_hours', 
                  'safety_incidents', 'community_investment'],
            'G': ['board_independence_ratio', 'ethics_training_coverage', 'esg_report_quality']
        }
        
        missing = []
        dimensions = [dimension] if dimension else ['E', 'S', 'G']
        
        for dim in dimensions:
            for indicator in all_indicators.get(dim, []):
                value = getattr(self, indicator, None)
                if value is None:
                    missing.append(f"{dim}.{indicator}")
        
        return missing


@dataclass
class AnalysisResult:
    """分析结果模型"""
    metrics: ESGMetrics
    weights: Dict[str, float]
    gap_analysis: Dict[str, Any]
    strategies: List[Dict[str, Any]]
    overall_score: float = 0.0
    confidence_level: str = "中"
    data_quality_warnings: List[str] = field(default_factory=list)
    
    def get_dimension_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """获取各维度详细分解
        
        Returns:
            各维度得分和权重的详细信息
        """
        breakdown = {}
        for dim in ['E', 'S', 'G']:
            score = self.metrics.get_dimension_score(dim)
            weight = self.weights.get(dim, 0.33)
            breakdown[dim] = {
                'score': score,
                'weight': weight,
                'weighted_score': score * weight,
                'has_data': self.metrics.has_dimension_data(dim)
            }
        return breakdown


@dataclass
class BenchmarkData:
    """行业基准数据模型"""
    industry: str
    year: str
    
    # E维度基准
    avg_carbon_emissions: Optional[float] = None
    avg_renewable_energy_ratio: Optional[float] = None
    avg_energy_efficiency: Optional[float] = None
    
    # S维度基准
    avg_female_ratio: Optional[float] = None
    avg_training_hours: Optional[float] = None
    
    # G维度基准
    avg_board_independence_ratio: Optional[float] = None
    
    # 元数据
    source: str = ""
    sample_size: int = 0
    
    def get_benchmark_score(self, dimension: str) -> float:
        """获取维度基准得分
        
        Args:
            dimension: 维度标识，'E'/'S'/'G'
            
        Returns:
            维度基准得分，无数据时返回默认值
        """
        scores: List[float] = []
        
        if dimension == 'E':
            if self.avg_renewable_energy_ratio is not None:
                scores.append(self.avg_renewable_energy_ratio)
            if self.avg_energy_efficiency is not None:
                scores.append(self.avg_energy_efficiency)
        elif dimension == 'S':
            if self.avg_female_ratio is not None:
                scores.append(self.avg_female_ratio * 100)
            if self.avg_training_hours is not None:
                scores.append(self.avg_training_hours / 40 * 100)
        elif dimension == 'G':
            if self.avg_board_independence_ratio is not None:
                scores.append(self.avg_board_independence_ratio)
        
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else DEFAULT_DIMENSION_SCORE
    
    def to_metrics(self) -> Dict[str, Any]:
        """转换为指标字典"""
        return {
            'renewable_energy_ratio': self.avg_renewable_energy_ratio,
            'energy_efficiency': self.avg_energy_efficiency,
            'female_ratio': self.avg_female_ratio,
            'training_hours': self.avg_training_hours,
            'board_independence_ratio': self.avg_board_independence_ratio
        }
