"""UI相关配置

分析年份、标杆企业、评估视角、沟通日历等UI配置。
"""

from typing import Any, Dict, List

# ========== UI 配置 ==========
ANALYSIS_YEARS: List[str] = ["2025", "2024", "2023"]
BENCHMARK_COMPANIES: List[str] = ["维斯塔斯", "西门子歌美飒", "行业平均"]

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

# ========== ESG沟通日历配置 ==========
COMMUNICATION_CALENDAR = [
    {
        "event_name": "COP29联合国气候变化大会",
        "date": "2024-11",
        "suitable_topics": ["carbon_management", "renewable_energy", "climate_strategy"],
        "audience": "国际投资者/监管机构",
        "opportunity": "国际媒体关注度高，适合发布气候承诺",
        "preparation_advice": "建议10月准备：碳中和进展报告",
    },
    {
        "event_name": "年报披露季",
        "date": "2024-03",
        "suitable_topics": ["governance", "board", "esg_disclosure", "financial_performance"],
        "audience": "投资者/分析师",
        "opportunity": "年报发布期关注度高，适合全面展示ESG成果",
        "preparation_advice": "建议2月准备：年度ESG报告",
    },
    {
        "event_name": "MSCI ESG评级窗口期",
        "date": "2024-06",
        "suitable_topics": ["governance", "carbon_management", "diversity"],
        "audience": "评级机构/投资者",
        "opportunity": "MSCI评级更新期，影响ESG评级结果",
        "preparation_advice": "建议5月准备：ESG评级回复材料",
    },
    {
        "event_name": "可持续发展目标峰会",
        "date": "2024-09",
        "suitable_topics": ["community_investment", "sdg_alignment", "social_impact"],
        "audience": "国际组织/NGO",
        "opportunity": "联合国SDG峰会，展示可持续发展贡献",
        "preparation_advice": "建议8月准备：SDG贡献报告",
    },
    {
        "event_name": "世界环境日",
        "date": "2024-06",
        "suitable_topics": ["environmental_protection", "carbon_management", "circular_economy"],
        "audience": "公众/媒体",
        "opportunity": "全球性环保主题日，适合发布环保举措",
        "preparation_advice": "建议5月准备：环境保护行动计划",
    },
    {
        "event_name": "Q3财报发布",
        "date": "2024-10",
        "suitable_topics": ["financial_performance", "esg_disclosure", "governance"],
        "audience": "投资者/分析师",
        "opportunity": "季度财报期，可同步更新ESG进展",
        "preparation_advice": "建议9月准备：季度ESG亮点总结",
    },
    {
        "event_name": "国际生物多样性日",
        "date": "2024-05",
        "suitable_topics": ["biodiversity", "environmental_protection", "ecosystem"],
        "audience": "环保组织/公众",
        "opportunity": "生物多样性主题，适合发布生态保护项目",
        "preparation_advice": "建议4月准备：生物多样性保护报告",
    },
    {
        "event_name": "全球气候行动峰会",
        "date": "2024-12",
        "suitable_topics": ["climate_strategy", "net_zero", "carbon_management"],
        "audience": "国际组织/政府",
        "opportunity": "年末气候行动总结，展示年度减排成果",
        "preparation_advice": "建议11月准备：年度碳减排成绩单",
    },
    {
        "event_name": "国际劳工日",
        "date": "2024-05",
        "suitable_topics": ["employee_safety", "diversity", "employee_development"],
        "audience": "员工/工会",
        "opportunity": "劳工权益主题，展示员工关怀举措",
        "preparation_advice": "建议4月准备：员工福利与权益报告",
    },
    {
        "event_name": "国际反腐败日",
        "date": "2024-12",
        "suitable_topics": ["business_ethics", "compliance", "governance"],
        "audience": "监管机构/投资者",
        "opportunity": "反贪腐主题日，展示合规管理体系",
        "preparation_advice": "建议11月准备：合规与伦理报告",
    },
    {
        "event_name": "年报披露季",
        "date": "2025-03",
        "suitable_topics": ["governance", "board", "esg_disclosure", "financial_performance"],
        "audience": "投资者/分析师",
        "opportunity": "年报发布期关注度高，适合全面展示ESG成果",
        "preparation_advice": "建议2月准备：年度ESG报告",
    },
    {
        "event_name": "COP30联合国气候变化大会",
        "date": "2025-11",
        "suitable_topics": ["carbon_management", "renewable_energy", "climate_strategy"],
        "audience": "国际投资者/监管机构",
        "opportunity": "国际媒体关注度高，适合发布气候承诺",
        "preparation_advice": "建议10月准备：碳中和进展报告",
    },
]
