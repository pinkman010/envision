"""数据处理工具"""

import re
from typing import Dict, List, Any, Optional


def validate_esg_data(data: Dict[str, Any]) -> tuple:
    """验证ESG数据完整性"""
    required_fields = ['company_name', 'year']
    missing = [f for f in required_fields if f not in data or not data[f]]
    
    if missing:
        return False, f"缺失必填字段: {missing}"
    
    return True, "数据有效"


def calculate_gap_score(yuanjing_score: float, benchmark_score: float) -> Dict:
    """计算差距得分"""
    gap = benchmark_score - yuanjing_score
    
    return {
        'yuanjing_score': round(yuanjing_score, 1),
        'benchmark_score': round(benchmark_score, 1),
        'gap': round(gap, 1),
        'gap_pct': round(gap / benchmark_score * 100 if benchmark_score > 0 else 0, 1),
        'status': '落后' if gap > 0 else '领先',
        'priority': '高' if abs(gap) > 20 else '中' if abs(gap) > 10 else '低'
    }


def extract_number_from_text(text: str, patterns: List[str]) -> Optional[float]:
    """从文本中提取数字"""
    if not text:
        return None
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                return float(matches[0].replace(',', ''))
            except:
                continue
    return None


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """安全除法"""
    if denominator == 0:
        return default
    return numerator / denominator