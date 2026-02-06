"""ESG分析服务"""

from typing import Dict, List, Any, Optional

from src.models.esg import ESGMetrics, AnalysisResult
from src.config import DEFAULT_SCORE


class ESGAnalysisService:
    """ESG分析服务"""
    
    def __init__(self):
        self.weights = {"E": 0.4, "S": 0.3, "G": 0.3}
        self.warnings = []
    
    def analyze(self, metrics: ESGMetrics, benchmark: Any = None) -> AnalysisResult:
        """执行ESG分析"""
        self.warnings = []
        self._validate(metrics)
        
        e_score = metrics.get_dimension_score("E")
        s_score = metrics.get_dimension_score("S")
        g_score = metrics.get_dimension_score("G")
        
        overall = (
            e_score * self.weights["E"] +
            s_score * self.weights["S"] +
            g_score * self.weights["G"]
        )
        
        gaps = self._analyze_gaps(metrics)
        strategies = self._generate_strategies(gaps)
        
        return AnalysisResult(
            metrics=metrics,
            weights=self.weights,
            gap_analysis=gaps,
            strategies=strategies,
            overall_score=round(overall, 1),
            confidence_level=metrics.calculate_overall_confidence(),
            data_quality_warnings=self.warnings
        )
    
    def _validate(self, metrics: ESGMetrics):
        """数据质量校验"""
        if metrics.carbon_emissions and metrics.carbon_emissions < 1000:
            self.warnings.append(f"碳排放数值({metrics.carbon_emissions})疑似单位错误")
        
        if metrics.employee_count and metrics.employee_count < 100:
            self.warnings.append("员工数异常偏低")
    
    def _analyze_gaps(self, metrics: ESGMetrics) -> Dict:
        """差距分析"""
        gaps = {}
        for dim in ["E", "S", "G"]:
            current = metrics.get_dimension_score(dim)
            target = 80.0
            gaps[dim] = {
                "current": round(current, 1),
                "target": target,
                "gap": round(target - current, 1)
            }
        return {"dimensions": gaps}
    
    def _generate_strategies(self, gaps: Dict) -> List[Dict]:
        """生成改进策略"""
        strategies = []
        templates = {
            "E": {"title": "提升环境绩效", "actions": ["完善碳核算", "制定可再生能源目标"]},
            "S": {"title": "加强社会责任", "actions": ["完善员工多元化", "增加社区投资"]},
            "G": {"title": "优化公司治理", "actions": ["提升董事会独立性", "完善ESG披露"]}
        }
        
        for dim in ["E", "S", "G"]:
            gap = gaps["dimensions"].get(dim, {}).get("gap", 0)
            if gap > 5:
                strategies.append({
                    "dimension": dim,
                    "title": templates[dim]["title"],
                    "priority": "高" if gap > 15 else "中",
                    "actions": templates[dim]["actions"]
                })
        
        return strategies
