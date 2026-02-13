"""评估配置

ESG分析师用的评分标准配置。
包含评估视角、标杆企业等配置。
"""

from typing import Dict, List

# ========== 标杆企业配置 ==========
BENCHMARK_COMPANIES: List[str] = ["维斯塔斯", "西门子歌美飒", "行业平均"]

# ========== 评估视角配置 ==========
EVALUATION_PERSPECTIVES: Dict[str, Dict] = {
    "financial": {
        "name": "财务稳健性（投资者视角）",
        "weights": {"E": 0.25, "S": 0.30, "G": 0.45},
    },
    "compliance": {
        "name": "合规与风险（监管视角）",
        "weights": {"E": 0.40, "S": 0.25, "G": 0.35},
    },
    "brand": {
        "name": "品牌影响力（公众视角）",
        "weights": {"E": 0.30, "S": 0.45, "G": 0.25},
    },
    "balanced": {
        "name": "均衡配置",
        "weights": {"E": 0.333, "S": 0.333, "G": 0.334},
    },
}
