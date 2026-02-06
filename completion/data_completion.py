"""数据补全"""

from typing import Dict, List, Tuple
from core.data_models import ESGMetrics


class SimpleCompletionEngine:
    """简单补全引擎"""
    
    def complete(self, metrics: ESGMetrics) -> Tuple[ESGMetrics, List[Dict]]:
        """补全缺失值"""
        completed = ESGMetrics(
            company_name=metrics.company_name,
            year=metrics.year
        )
        
        # 复制已有数据
        for field in ['carbon_emissions', 'renewable_energy_ratio', 'employee_count',
                      'female_ratio', 'training_hours', 'safety_incidents',
                      'board_independence_ratio']:
            value = getattr(metrics, field, None)
            setattr(completed, field, value)
        
        completed.confidence = metrics.confidence.copy()
        completed.data_sources = metrics.data_sources.copy()
        
        log = []
        
        # 高置信度推导
        if completed.training_hours and completed.employee_count:
            per_capita = completed.training_hours / completed.employee_count
            log.append({
                'field': 'training_per_capita',
                'value': per_capita,
                'method': 'calculated'
            })
        
        # 数据质量警告
        if completed.carbon_emissions and completed.carbon_emissions < 10000:
            log.append({
                'type': 'warning',
                'field': 'carbon_emissions',
                'message': f'数值{completed.carbon_emissions}过小，请检查单位'
            })
        
        return completed, log