"""ESG分析核心引擎"""

from typing import Dict, List, Any, Optional
from core.data_models import ESGMetrics, AnalysisResult


class ESGAnalysisEngine:
    """ESG分析引擎"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.weights = {'E': 0.4, 'S': 0.3, 'G': 0.3}
        self.warnings = []
    
    def analyze(self, metrics: ESGMetrics, 
                benchmark: Optional[Any] = None) -> AnalysisResult:
        """执行分析"""
        self.warnings = []
        self._validate_data_quality(metrics)
        
        e_score = metrics.get_dimension_score('E')
        s_score = metrics.get_dimension_score('S')
        g_score = metrics.get_dimension_score('G')
        
        overall = (e_score * self.weights['E'] + 
                  s_score * self.weights['S'] + 
                  g_score * self.weights['G'])
        
        gap_analysis = self._analyze_gap(metrics)
        strategies = self._generate_strategies(gap_analysis)
        
        return AnalysisResult(
            metrics=metrics,
            weights=self.weights,
            gap_analysis=gap_analysis,
            strategies=strategies,
            overall_score=round(overall, 1),
            confidence_level=metrics.calculate_overall_confidence(),
            data_quality_warnings=self.warnings
        )
    
    def _validate_data_quality(self, metrics: ESGMetrics):
        """数据质量校验"""
        if metrics.carbon_emissions:
            if metrics.carbon_emissions < 1000:
                self.warnings.append(
                    f"碳排放数值过小({metrics.carbon_emissions})，疑似单位错误"
                )
            elif metrics.employee_count and metrics.carbon_emissions < 50000:
                self.warnings.append(
                    "碳排放与员工规模不匹配，请核实"
                )
        
        if metrics.employee_count and metrics.employee_count < 100:
            self.warnings.append("员工数异常偏低")
    
    def _analyze_gap(self, metrics: ESGMetrics) -> Dict[str, Any]:
        """差距分析"""
        gaps = {}
        for dim in ['E', 'S', 'G']:
            current = metrics.get_dimension_score(dim)
            target = 80.0
            gaps[dim] = {
                'current': round(current, 1),
                'target': target,
                'gap': round(target - current, 1),
                'status': '需改进' if target - current > 10 else '正常'
            }
        
        return {
            'dimensions': gaps,
            'overall': {
                'current': round(sum(gaps[d]['current'] * self.weights[d] for d in ['E','S','G']), 1),
                'target': 80.0,
                'gap': round(80.0 - sum(gaps[d]['current'] * self.weights[d] for d in ['E','S','G']), 1)
            }
        }
    
    def _generate_strategies(self, gap_analysis: Dict) -> List[Dict[str, Any]]:
        """生成策略"""
        strategies = []
        gaps = gap_analysis.get('dimensions', {})
        
        priority_map = {
            'E': {
                'title': '提升环境绩效',
                'actions': ['完善碳排放核算', '制定可再生能源目标', '建立监测机制'],
                'standards': ['GRI 305', 'TCFD']
            },
            'S': {
                'title': '加强社会责任',
                'actions': ['完善员工多元化', '建立供应商审核', '增加社区投资'],
                'standards': ['GRI 400', 'SA8000']
            },
            'G': {
                'title': '优化公司治理',
                'actions': ['提升董事会独立性', '完善ESG披露', '建立沟通机制'],
                'standards': ['GRI 200', 'ISO 37000']
            }
        }
        
        for dim in ['E', 'S', 'G']:
            gap = gaps.get(dim, {}).get('gap', 0)
            if gap > 5:
                template = priority_map.get(dim, {})
                strategies.append({
                    'dimension': dim,
                    'title': template.get('title', ''),
                    'priority': '高' if gap > 15 else '中',
                    'gap': round(gap, 1),
                    'actions': template.get('actions', []),
                    'standards': template.get('standards', [])
                })
        
        return strategies