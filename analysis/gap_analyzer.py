"""模块三：披露差距诊断与对标分析器
技术：向量相似度计算 + 行业对标分析
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from core.constants import (
    MOCK_BENCHMARK_FILE,
    GAP_THRESHOLD_HIGH,
    GAP_THRESHOLD_MEDIUM,
    DEFAULT_DIMENSION_SCORE
)


class GapAnalyzer:
    """ESG披露差距分析器"""
    
    def __init__(self, company_data: Optional[Dict] = None, 
                 benchmark_file: Optional[str] = None):
        """初始化分析器
        
        Args:
            company_data: 公司ESG数据
            benchmark_file: 标杆数据文件路径，默认使用mock数据
        """
        self.company_data = company_data or {}
        self.benchmark_file = benchmark_file or MOCK_BENCHMARK_FILE
        self.gaps = {}
        self._benchmark_cache: Optional[Dict] = None
        self._indicator_names: Dict[str, str] = {}
        self._load_benchmark_data()
    
    def _load_benchmark_data(self) -> None:
        """加载标杆数据"""
        if Path(self.benchmark_file).exists():
            try:
                with open(self.benchmark_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._benchmark_cache = data.get("companies", {})
                    self._indicator_names = data.get("indicator_names", {})
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载标杆数据失败: {e}，使用默认数据")
                self._benchmark_cache = self._get_default_benchmark()
                self._indicator_names = self._get_default_indicator_names()
        else:
            self._benchmark_cache = self._get_default_benchmark()
            self._indicator_names = self._get_default_indicator_names()
    
    def _get_default_benchmark(self) -> Dict:
        """获取默认标杆数据"""
        return {
            "维斯塔斯": {
                "overall_score": 88.2,
                "dimensions": {"E": 90.5, "S": 86.8, "G": 87.3},
                "indicators": {
                    "carbon_emissions": {"score": 92, "disclosure": "详细"},
                    "renewable_energy": {"score": 95, "disclosure": "详细"},
                    "supply_chain": {"score": 88, "disclosure": "详细"}
                }
            },
            "行业平均": {
                "overall_score": 78.5,
                "dimensions": {"E": 78.0, "S": 78.8, "G": 78.7},
                "indicators": {
                    "carbon_emissions": {"score": 78, "disclosure": "中等"},
                    "renewable_energy": {"score": 82, "disclosure": "中等"},
                    "supply_chain": {"score": 75, "disclosure": "基础"}
                }
            }
        }
    
    def _get_default_indicator_names(self) -> Dict[str, str]:
        """获取默认指标名称映射"""
        return {
            "carbon_emissions": "碳排放管理",
            "renewable_energy": "可再生能源使用",
            "supply_chain": "供应链透明度",
            "employee_diversity": "员工多样性",
            "board_independence": "董事会独立性",
            "scope3_data": "Scope 3数据披露"
        }
    
    def analyze_gap(self, benchmark_company: str = "维斯塔斯",
                    company_score: Optional[float] = None) -> Dict:
        """执行差距分析
        
        Args:
            benchmark_company: 对标企业名称
            company_score: 公司得分，如果未提供则使用模拟数据或从company_data计算
            
        Returns:
            差距分析结果字典
        """
        benchmark = self._benchmark_cache.get(benchmark_company, 
                                              self._benchmark_cache.get("维斯塔斯", {}))
        
        # 使用提供的得分或尝试从数据计算，最后使用默认值
        if company_score is not None:
            actual_company_score = company_score
        elif self.company_data:
            actual_company_score = self._calculate_company_score()
        else:
            actual_company_score = DEFAULT_DIMENSION_SCORE  # 使用常量而非硬编码
        
        analysis_result = {
            "company_score": round(actual_company_score, 1),
            "benchmark_score": benchmark.get("overall_score", DEFAULT_DIMENSION_SCORE),
            "gap": round(benchmark.get("overall_score", DEFAULT_DIMENSION_SCORE) - actual_company_score, 1),
            "status": "落后" if actual_company_score < benchmark.get("overall_score", 0) else "领先",
            "dimension_gaps": {},
            "indicator_gaps": []
        }
        
        # 维度差距
        benchmark_dims = benchmark.get("dimensions", {})
        for dim in ["E", "S", "G"]:
            benchmark_dim = benchmark_dims.get(dim, DEFAULT_DIMENSION_SCORE)
            # 模拟公司维度得分（实际应从真实数据计算）
            company_dim = actual_company_score * 0.98
            
            analysis_result["dimension_gaps"][dim] = {
                "company": round(company_dim, 1),
                "benchmark": benchmark_dim,
                "gap": round(benchmark_dim - company_dim, 1)
            }
        
        # 指标级差距分析
        benchmark_indicators = benchmark.get("indicators", {})
        for indicator_id, indicator_info in benchmark_indicators.items():
            benchmark_score = indicator_info.get("score", 0)
            # 模拟公司指标得分（实际应从分析结果获取）
            company_indicator = self._get_company_indicator_score(indicator_id, benchmark_score)
            gap_score = benchmark_score - company_indicator
            
            # 使用常量判断严重程度
            severity = self._calculate_severity(gap_score)
            
            analysis_result["indicator_gaps"].append({
                "id": indicator_id,
                "name": self._indicator_names.get(indicator_id, indicator_id),
                "company_score": round(company_indicator, 1),
                "benchmark_score": benchmark_score,
                "gap": round(gap_score, 1),
                "severity": severity,
                "disclosure_level": indicator_info.get("disclosure", "未知")
            })
        
        # 按差距排序
        analysis_result["indicator_gaps"].sort(key=lambda x: x["gap"], reverse=True)
        
        return analysis_result
    
    def _calculate_company_score(self) -> float:
        """从company_data计算公司得分"""
        # 实际应根据company_data中的各项指标计算
        # 这里返回一个默认值
        return self.company_data.get("overall_score", DEFAULT_DIMENSION_SCORE)
    
    def _get_company_indicator_score(self, indicator_id: str, benchmark_score: float) -> float:
        """获取公司特定指标得分
        
        Args:
            indicator_id: 指标ID
            benchmark_score: 标杆得分
            
        Returns:
            公司指标得分
        """
        # 尝试从company_data获取真实数据
        if self.company_data and "indicators" in self.company_data:
            indicator_data = self.company_data["indicators"].get(indicator_id, {})
            if isinstance(indicator_data, dict):
                return indicator_data.get("score", benchmark_score * 0.85)
            elif isinstance(indicator_data, (int, float)):
                return float(indicator_data)
        
        # 模拟数据：基于标杆分数和随机差距
        gap = random.uniform(5, 20)
        return max(0, benchmark_score - gap)
    
    def _calculate_severity(self, gap_score: float) -> str:
        """计算差距严重程度
        
        Args:
            gap_score: 差距分数
            
        Returns:
            严重程度等级（高/中/低）
        """
        if gap_score > GAP_THRESHOLD_HIGH:
            return "高"
        elif gap_score > GAP_THRESHOLD_MEDIUM:
            return "中"
        return "低"
    
    def get_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度（模拟）
        
        TODO: 实际应使用Word2Vec或BERT计算
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数(0-1)
        """
        # 临时模拟实现
        return round(random.uniform(0.6, 0.95), 3)
    
    def get_missing_keywords(self, company_text: str, benchmark_text: str) -> List[str]:
        """识别公司文本中缺失的关键关键词
        
        TODO: 实际应使用NLP技术提取和比较
        
        Args:
            company_text: 公司文本
            benchmark_text: 标杆文本
            
        Returns:
            缺失的关键词列表
        """
        # 模拟缺失的关键词
        common_missing = [
            "Scope 3 排放核算",
            "供应链碳盘查",
            "生物多样性保护",
            "TCFD气候信息披露",
            "SBTi科学碳目标"
        ]
        return random.sample(common_missing, min(3, len(common_missing)))
