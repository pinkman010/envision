"""ESG指标提取"""

import re
from typing import Dict, List, Tuple, Optional

from src.models.esg import ESGMetrics


class MetricsExtractor:
    """指标提取器"""
    
    PATTERNS = {
        "carbon_emissions": [
            r"(?:carbon|碳)排放[：:]?\s*([0-9,]+\.?\d*)\s*(?:吨|t)",
            r"温室气体.*?排放[：:]?\s*([0-9,]+\.?\d*)"
        ],
        "renewable_energy_ratio": [
            r"可再生能源.*?(?:占比)?[：:]?\s*([0-9.]+)\s*%"
        ],
        "employee_count": [
            r"(?:total|over)?\s*([0-9,]+)\s*employees?",
            r"员工[总]?数[：:]?\s*([0-9,]+)"
        ],
        "female_ratio": [
            r"female.*?([0-9.]+)\s*%",
            r"女性员工.*?([0-9.]+)\s*%"
        ],
        "board_independence_ratio": [
            r"independent.*?([0-9.]+)\s*%",
            r"独立董事.*?([0-9.]+)\s*%"
        ]
    }
    
    def extract(self, text: str, company: str = "未知", year: str = "2023") -> ESGMetrics:
        """提取ESG指标"""
        metrics = ESGMetrics(company_name=company, year=year)
        confidence = {}
        sources = {}
        
        for field, patterns in self.PATTERNS.items():
            value, conf, source = self._extract_field(text, patterns)
            if value is not None:
                setattr(metrics, field, value)
                confidence[field] = conf
                sources[field] = source[:100] if source else ""
        
        metrics.confidence = confidence
        metrics.data_sources = sources
        return metrics
    
    def _extract_field(self, text: str, patterns: List[str]) -> Tuple[Optional[float], float, str]:
        """提取单个字段"""
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    raw = match.group(1).replace(",", "")
                    value = float(raw)
                    
                    # 单位转换
                    if "female" in pattern or "女性" in pattern:
                        if value > 1:
                            value /= 100
                    
                    conf = 0.7 if len(match.group(0)) > 20 else 0.5
                    return value, conf, match.group(0)
                    
                except (ValueError, IndexError):
                    continue
        
        return None, 0.0, ""
