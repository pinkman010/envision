"""指标提取器"""

import re
from typing import Dict, List, Optional, Any
from core.data_models import ESGMetrics


class MetricExtractor:
    """ESG指标提取器"""
    
    PATTERNS = {
        'carbon_emissions': [
            r'(?:carbon|碳)排放[：:]?\s*([0-9,]+\.?\d*)\s*(?:吨|t)',
            r'Scope 1[^0-9]*?([0-9,]+\.?\d*)\s*Mt',
            r'温室气体.*?(?:排放)?[：:]?\s*([0-9,]+\.?\d*)'
        ],
        'renewable_energy_ratio': [
            r'可再生能源.*?(?:占比)?[：:]?\s*([0-9\.]+)\s*%',
            r'renewable energy.*?([0-9\.]+)\s*%'
        ],
        'employee_count': [
            r'(?:total|over)?\s*([0-9,]+)\s*employees?',
            r'员工[总]?数[：:]?\s*([0-9,]+)',
            r'从业人员[：:]?\s*([0-9,]+)'
        ],
        'female_ratio': [
            r'female.*?([0-9\.]+)\s*%',
            r'女性员工.*?([0-9\.]+)\s*%'
        ],
        'training_hours': [
            r'training.*?([0-9,]+)\s*hours?',
            r'培训.*?([0-9,]+)\s*小时'
        ],
        'safety_incidents': [
            r'(?:major|重大).*?(?:accidents?|事故).*?([0-9]+)',
            r'safety.*?([0-9]+)\s*(?:incidents|accidents)'
        ],
        'board_independence_ratio': [
            r'independent.*?([0-9\.]+)\s*%',
            r'独立董事.*?([0-9\.]+)\s*%'
        ]
    }
    
    def extract(self, text: str, company_name: str = "未知", year: str = "2023") -> ESGMetrics:
        """提取指标"""
        metrics = ESGMetrics(company_name=company_name, year=year)
        confidence = {}
        sources = {}
        
        for field, patterns in self.PATTERNS.items():
            value, conf, source = self._extract_field(text, field, patterns)
            if value is not None:
                setattr(metrics, field, value)
                confidence[field] = conf
                sources[field] = source[:100] if source else ""
        
        metrics.confidence = confidence
        metrics.data_sources = sources
        return metrics
    
    def _extract_field(self, text: str, field: str, patterns: List[str]) -> tuple:
        """提取单个字段"""
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    raw_value = match.group(1).replace(',', '')
                    value = float(raw_value)
                    
                    # 单位转换
                    if field == 'carbon_emissions' and 'Mt' in match.group(0):
                        value *= 1000
                    
                    if field == 'female_ratio' and value > 1:
                        value /= 100
                    
                    conf = 0.7 if len(match.group(0)) > 20 else 0.5
                    
                    return value, conf, match.group(0)
                except (ValueError, IndexError, AttributeError) as e:
                    # 数值转换失败、正则分组不存在或属性访问错误，继续尝试下一个匹配
                    continue
        return None, 0.0, ""