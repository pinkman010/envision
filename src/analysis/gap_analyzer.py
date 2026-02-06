"""差距分析器

对标行业标杆，计算维度差距和指标差距。
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from src.config import MOCK_DATA_DIR, DEFAULT_SCORE, ESG_DIMENSION_NAMES
from src.core.models import ESGMetrics


@dataclass
class GapResult:
    """差距分析结果"""
    dimension: str
    current: float
    benchmark: float
    gap: float
    gap_percentage: float
    priority: str


@dataclass
class IndicatorGap:
    """指标差距"""
    indicator_id: str
    indicator_name: str
    current_score: float
    benchmark_score: float
    gap: float
    disclosure_level: str


class GapAnalyzer:
    """ESG差距分析器
    
    对标行业标杆企业，计算维度差距和指标差距。
    
    Attributes:
        benchmark_data: 标杆数据字典
        indicator_names: 指标名称映射
    """
    
    DEFAULT_DATA_SOURCE = MOCK_DATA_DIR / "benchmark_data.json"
    
    # 指标映射：从ESGMetrics字段到benchmark指标ID
    INDICATOR_MAPPING = {
        "renewable_energy_ratio": "renewable_energy",
        "carbon_emissions": "carbon_emissions",
        "female_ratio": "employee_diversity",
        "board_independence_ratio": "board_independence",
    }
    
    def __init__(self, data_source: Optional[Path] = None):
        """初始化分析器
        
        Args:
            data_source: 自定义标杆数据源路径
        """
        self.data_source = data_source or self.DEFAULT_DATA_SOURCE
        self.benchmark_data: Dict[str, Any] = {}
        self.indicator_names: Dict[str, str] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """加载标杆数据"""
        try:
            with open(self.data_source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.benchmark_data = data.get("companies", {})
            self.indicator_names = data.get("indicator_names", {})
        except FileNotFoundError:
            raise FileNotFoundError(f"标杆数据源文件不存在: {self.data_source}")
        except json.JSONDecodeError as e:
            raise ValueError(f"标杆数据JSON解析错误: {e}")
    
    def analyze_dimension_gap(
        self, 
        metrics: ESGMetrics,
        benchmark_company: str = "行业平均"
    ) -> Dict[str, GapResult]:
        """分析维度差距
        
        Args:
            metrics: 当前企业ESG指标
            benchmark_company: 标杆企业名称
            
        Returns:
            各维度差距分析结果
        """
        benchmark = self._get_benchmark(benchmark_company)
        if not benchmark:
            raise ValueError(f"未找到标杆企业: {benchmark_company}")
        
        results = {}
        for dim in ["E", "S", "G"]:
            current = metrics.get_dimension_score(dim)
            target = benchmark["dimensions"].get(dim, DEFAULT_SCORE)
            gap = target - current
            
            # 计算差距百分比
            gap_percentage = (gap / target * 100) if target > 0 else 0.0
            
            # 确定优先级
            priority = self._calculate_priority(abs(gap))
            
            results[dim] = GapResult(
                dimension=dim,
                current=round(current, 1),
                benchmark=round(target, 1),
                gap=round(gap, 1),
                gap_percentage=round(gap_percentage, 1),
                priority=priority
            )
        
        return results
    
    def analyze_indicator_gap(
        self,
        metrics: ESGMetrics,
        benchmark_company: str = "行业平均"
    ) -> List[IndicatorGap]:
        """分析指标级差距
        
        Args:
            metrics: 当前企业ESG指标
            benchmark_company: 标杆企业名称
            
        Returns:
            指标差距列表
        """
        benchmark = self._get_benchmark(benchmark_company)
        if not benchmark:
            raise ValueError(f"未找到标杆企业: {benchmark_company}")
        
        results = []
        benchmark_indicators = benchmark.get("indicators", {})
        
        # 计算当前指标分数
        current_indicators = self._calculate_indicator_scores(metrics)
        
        for indicator_id, current_score in current_indicators.items():
            bench_data = benchmark_indicators.get(indicator_id, {})
            bench_score = bench_data.get("score", DEFAULT_SCORE) if isinstance(bench_data, dict) else bench_data
            
            gap = IndicatorGap(
                indicator_id=indicator_id,
                indicator_name=self.indicator_names.get(indicator_id, indicator_id),
                current_score=round(current_score, 1),
                benchmark_score=round(bench_score, 1),
                gap=round(bench_score - current_score, 1),
                disclosure_level=bench_data.get("disclosure", "未知") if isinstance(bench_data, dict) else "未知"
            )
            results.append(gap)
        
        # 按差距从大到小排序
        results.sort(key=lambda x: abs(x.gap), reverse=True)
        return results
    
    def compare_with_multiple(
        self,
        metrics: ESGMetrics,
        benchmark_companies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """与多家标杆企业对比
        
        Args:
            metrics: 当前企业ESG指标
            benchmark_companies: 标杆企业列表，默认使用所有可用标杆
            
        Returns:
            多标杆对比结果
        """
        if benchmark_companies is None:
            benchmark_companies = list(self.benchmark_data.keys())
        
        comparisons = []
        for company in benchmark_companies:
            benchmark = self._get_benchmark(company)
            if not benchmark:
                continue
            
            dim_gaps = self.analyze_dimension_gap(metrics, company)
            total_gap = sum(abs(g.gap) for g in dim_gaps.values())
            
            comparisons.append({
                "company": company,
                "overall_score": benchmark.get("overall_score", 0),
                "dimension_scores": {
                    dim: {
                        "benchmark": g.benchmark,
                        "current": g.current,
                        "gap": g.gap
                    }
                    for dim, g in dim_gaps.items()
                },
                "total_gap": round(total_gap, 1)
            })
        
        # 按总差距排序
        comparisons.sort(key=lambda x: x["total_gap"])
        
        # 计算最佳标杆
        best_benchmark = comparisons[0]["company"] if comparisons else None
        
        return {
            "comparisons": comparisons,
            "best_benchmark": best_benchmark,
            "overall_ranking": self._calculate_ranking(metrics)
        }
    
    def get_improvement_areas(
        self,
        metrics: ESGMetrics,
        top_n: int = 3,
        benchmark_company: str = "行业平均"
    ) -> List[Dict[str, Any]]:
        """获取优先改进领域
        
        Args:
            metrics: 当前企业ESG指标
            top_n: 返回前N个改进领域
            benchmark_company: 标杆企业名称
            
        Returns:
            优先改进领域列表
        """
        dim_gaps = self.analyze_dimension_gap(metrics, benchmark_company)
        indicator_gaps = self.analyze_indicator_gap(metrics, benchmark_company)
        
        # 合并维度和指标差距
        all_gaps = []
        
        # 添加维度差距
        for dim, gap in dim_gaps.items():
            if gap.gap > 0:
                all_gaps.append({
                    "type": "dimension",
                    "id": dim,
                    "name": ESG_DIMENSION_NAMES.get(dim, dim),
                    "gap": gap.gap,
                    "priority": gap.priority
                })
        
        # 添加指标差距（前N个）
        for ind_gap in indicator_gaps[:top_n * 2]:
            if ind_gap.gap > 0:
                all_gaps.append({
                    "type": "indicator",
                    "id": ind_gap.indicator_id,
                    "name": ind_gap.indicator_name,
                    "gap": ind_gap.gap,
                    "priority": self._calculate_priority(ind_gap.gap)
                })
        
        # 按差距排序并去重
        all_gaps.sort(key=lambda x: x["gap"], reverse=True)
        
        # 返回前N个
        return all_gaps[:top_n]
    
    def get_available_benchmarks(self) -> List[str]:
        """获取可用的标杆企业列表"""
        return list(self.benchmark_data.keys())
    
    def _get_benchmark(self, company: str) -> Optional[Dict[str, Any]]:
        """获取指定企业的标杆数据"""
        return self.benchmark_data.get(company)
    
    def _calculate_indicator_scores(self, metrics: ESGMetrics) -> Dict[str, float]:
        """计算各项指标分数"""
        scores = {}
        
        # 环境指标
        if metrics.renewable_energy_ratio is not None:
            scores["renewable_energy"] = metrics.renewable_energy_ratio
        if metrics.carbon_emissions is not None:
            # 碳排放分数：假设排放越低越好，基于行业基准反推
            scores["carbon_emissions"] = max(0, 100 - metrics.carbon_emissions / 10000)
        
        # 社会指标
        if metrics.female_ratio is not None:
            scores["employee_diversity"] = metrics.female_ratio * 100
        
        # 治理指标
        if metrics.board_independence_ratio is not None:
            scores["board_independence"] = metrics.board_independence_ratio * 100
        
        return scores
    
    def _calculate_priority(self, gap: float) -> str:
        """根据差距计算优先级"""
        if gap >= 15:
            return "高"
        elif gap >= 8:
            return "中"
        else:
            return "低"
    
    def _calculate_ranking(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """计算在所有标杆中的相对排名"""
        # 计算当前企业总体分数
        current_scores = {
            "E": metrics.get_dimension_score("E"),
            "S": metrics.get_dimension_score("S"),
            "G": metrics.get_dimension_score("G")
        }
        current_overall = sum(current_scores.values()) / 3
        
        # 收集所有标杆分数
        all_scores = [("当前企业", current_overall)]
        for company, data in self.benchmark_data.items():
            all_scores.append((company, data.get("overall_score", 0)))
        
        # 排序
        all_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 查找排名
        rank = next(i for i, (name, _) in enumerate(all_scores, 1) if name == "当前企业")
        total = len(all_scores)
        
        return {
            "rank": rank,
            "total": total,
            "percentile": round((total - rank + 1) / total * 100, 1),
            "overall_score": round(current_overall, 1)
        }
