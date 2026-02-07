"""ISSB/GRI标准配置

披露标准、合规状态等配置项。
"""

from typing import Dict, List, Any

# 要求类型枚举
REQUIREMENT_MANDATORY = "强制"
REQUIREMENT_RECOMMENDED = "建议"

# ISSB S1 - 可持续发展相关财务信息披露（8条）
ISSB_S1_CLAUSES = [
    {
        "standard_id": "ISSB-S1-01",
        "clause_name": "治理",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["治理架构描述", "管理角色指定", "董事会监督机制"],
        "description": "披露负责监督可持续发展相关风险和机遇的治理机构（如董事会、委员会或高管）的信息",
        "related_metrics": ["board_independence_ratio", "ethics_training_coverage"]
    },
    {
        "standard_id": "ISSB-S1-02",
        "clause_name": "战略整合",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["战略描述", "商业模式影响", "财务规划整合"],
        "description": "披露可持续发展相关风险和机遇如何影响企业战略和商业模式",
        "related_metrics": ["esg_report_quality"]
    },
    {
        "standard_id": "ISSB-S1-03",
        "clause_name": "风险管理",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["风险识别流程", "风险评估方法", "风险管理整合"],
        "description": "披露识别、评估和管理可持续发展相关风险的过程",
        "related_metrics": []
    },
    {
        "standard_id": "ISSB-S1-04",
        "clause_name": "指标与目标",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["定量指标披露", "目标设定", "绩效追踪机制"],
        "description": "披露用于评估和管理可持续发展相关风险和机遇的指标和目标",
        "related_metrics": ["carbon_emissions", "renewable_energy_ratio", "employee_count", "training_hours"]
    },
    {
        "standard_id": "ISSB-S1-05",
        "clause_name": "行业特定披露",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["行业标准对照", "行业指标适用", "同行比较数据"],
        "description": "参照适用的行业特定指南披露可持续发展相关风险和机遇",
        "related_metrics": []
    },
    {
        "standard_id": "ISSB-S1-06",
        "clause_name": "时间范围披露",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["短期风险识别", "中长期风险描述", "时间维度分析"],
        "description": "披露可持续发展相关风险和机遇的预期时间范围（短期、中期、长期）",
        "related_metrics": []
    },
    {
        "standard_id": "ISSB-S1-07",
        "clause_name": "价值链影响",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["上游影响评估", "下游影响评估", "价值链风险识别"],
        "description": "披露可持续发展相关风险和机遇对企业价值链的影响",
        "related_metrics": []
    },
    {
        "standard_id": "ISSB-S1-08",
        "clause_name": "韧性评估",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["情景分析", "战略韧性评估", "适应能力描述"],
        "description": "披露企业战略对不同可持续发展情景的韧性分析",
        "related_metrics": []
    },
]

# ISSB S2 - 气候相关披露（10条）
ISSB_S2_CLAUSES = [
    {
        "standard_id": "ISSB-S2-01",
        "clause_name": "气候治理",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["气候治理架构", "董事会气候监督", "管理层气候职责"],
        "description": "披露负责监督气候相关风险和机遇的治理机构的信息",
        "related_metrics": ["board_independence_ratio"]
    },
    {
        "standard_id": "ISSB-S2-02",
        "clause_name": "气候战略",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["气候风险描述", "气候机遇识别", "战略调整说明"],
        "description": "披露气候相关风险和机遇对组织战略和决策的影响",
        "related_metrics": ["renewable_energy_ratio", "energy_efficiency"]
    },
    {
        "standard_id": "ISSB-S2-03",
        "clause_name": "范围1+2排放",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["范围1排放数据", "范围2排放数据", "排放计算方法"],
        "description": "披露范围1和范围2温室气体排放的绝对值和强度",
        "related_metrics": ["carbon_emissions"]
    },
    {
        "standard_id": "ISSB-S2-04",
        "clause_name": "范围3排放",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["范围3排放数据", "价值链排放", "重大排放类别"],
        "description": "披露范围3温室气体排放的绝对值，包括与下游和上游活动相关的排放",
        "related_metrics": ["carbon_emissions"]
    },
    {
        "standard_id": "ISSB-S2-05",
        "clause_name": "转型计划",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["减排目标", "转型路径", "资金计划"],
        "description": "披露向低碳经济转型的计划，包括减排目标和时间表",
        "related_metrics": ["renewable_energy_ratio"]
    },
    {
        "standard_id": "ISSB-S2-06",
        "clause_name": "气候韧性",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["气候情景分析", "韧性评估结果", "适应措施"],
        "description": "披露对气候变化的韧性分析，包括使用气候情景分析的结果",
        "related_metrics": []
    },
    {
        "standard_id": "ISSB-S2-07",
        "clause_name": "碳价格应用",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["内部碳定价", "碳价格水平", "应用范围"],
        "description": "披露是否在决策中使用内部碳价格",
        "related_metrics": []
    },
    {
        "standard_id": "ISSB-S2-08",
        "clause_name": "能源使用披露",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["总能耗数据", "可再生能源占比", "能源效率指标"],
        "description": "披露能源消耗总量、可再生能源使用比例和能源效率改进",
        "related_metrics": ["renewable_energy_ratio", "energy_efficiency"]
    },
    {
        "standard_id": "ISSB-S2-09",
        "clause_name": "物理风险",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["急性风险识别", "慢性风险识别", "资产风险评估"],
        "description": "披露与气候变化相关的物理风险（急性和慢性）及其潜在影响",
        "related_metrics": []
    },
    {
        "standard_id": "ISSB-S2-10",
        "clause_name": "转型风险",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["政策风险", "技术风险", "市场风险", "声誉风险"],
        "description": "披露与向低碳经济转型相关的风险（政策、技术、市场、声誉）",
        "related_metrics": []
    },
]

# GRI Standards - 可持续发展报告标准（10条）
GRI_STANDARDS_CLAUSES = [
    {
        "standard_id": "GRI-2-01",
        "clause_name": "组织概况",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["组织规模", "所有制结构", "运营地点", "服务市场"],
        "description": "披露组织的规模、所有制结构、运营地点和服务市场等基本信息",
        "related_metrics": ["employee_count"]
    },
    {
        "standard_id": "GRI-2-02",
        "clause_name": "可持续发展报告披露",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["报告周期", "报告边界", "报告标准", "联系信息"],
        "description": "披露可持续发展报告的编制基础、报告周期和应用的标准",
        "related_metrics": ["esg_report_quality"]
    },
    {
        "standard_id": "GRI-2-03",
        "clause_name": "报告实践",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["披露项列表", "数据来源说明", "重述政策"],
        "description": "披露报告期内所涵盖的GRI披露项列表和报告实践",
        "related_metrics": []
    },
    {
        "standard_id": "GRI-3-01",
        "clause_name": "实质性议题确定过程",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["议题识别过程", "利益相关方参与", "实质性评估方法"],
        "description": "披露确定实质性议题的过程，包括利益相关方参与和实质性评估",
        "related_metrics": []
    },
    {
        "standard_id": "GRI-305-01",
        "clause_name": "直接温室气体排放(范围1)",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["范围1排放数据", "计算方法", "排放源分解"],
        "description": "披露范围1（直接）温室气体排放总量",
        "related_metrics": ["carbon_emissions"]
    },
    {
        "standard_id": "GRI-305-02",
        "clause_name": "能源间接排放(范围2)",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["范围2排放数据", "计算方法", "位置法/市场法"],
        "description": "披露范围2（能源间接）温室气体排放总量",
        "related_metrics": ["carbon_emissions"]
    },
    {
        "standard_id": "GRI-302-01",
        "clause_name": "组织内部的能源消耗",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["能源消耗总量", "可再生能源用量", "能源强度"],
        "description": "披露组织内部的能源消耗总量和可再生能源使用比例",
        "related_metrics": ["renewable_energy_ratio", "energy_efficiency"]
    },
    {
        "standard_id": "GRI-303-01",
        "clause_name": "水资源管理",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["用水总量", "水资源压力区", "循环用水量"],
        "description": "披露与水相关的相互影响和取用水情况",
        "related_metrics": ["water_consumption"]
    },
    {
        "standard_id": "GRI-306-01",
        "clause_name": "废弃物产生与管理",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["废弃物总量", "危险废弃物", "废弃物回收率"],
        "description": "披露废弃物产生总量和管理方式",
        "related_metrics": ["waste_recycling_rate"]
    },
    {
        "standard_id": "GRI-401-01",
        "clause_name": "员工雇佣",
        "requirement_type": REQUIREMENT_MANDATORY,
        "check_items": ["员工总数", "按性别分类", "按地区分类", "雇佣类型"],
        "description": "披露员工总数、新员工雇佣和员工流失总数",
        "related_metrics": ["employee_count", "female_ratio"]
    },
    {
        "standard_id": "GRI-404-01",
        "clause_name": "员工培训",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["人均培训时长", "培训覆盖率", "培训类型"],
        "description": "披露每名员工每年接受培训的平均小时数",
        "related_metrics": ["training_hours"]
    },
    {
        "standard_id": "GRI-413-01",
        "clause_name": "社区参与",
        "requirement_type": REQUIREMENT_RECOMMENDED,
        "check_items": ["社区投资金额", "社区项目数", "利益相关方沟通"],
        "description": "披露社区参与活动、影响评估和发展计划",
        "related_metrics": ["community_investment"]
    },
]

# 合并所有披露标准
DISCLOSURE_STANDARDS = {
    "ISSB-S1": {
        "name": "ISSB S1 - 可持续发展相关财务信息披露",
        "description": "国际可持续发展准则理事会发布的可持续发展相关财务信息披露一般要求",
        "version": "2023年6月",
        "clauses": ISSB_S1_CLAUSES,
    },
    "ISSB-S2": {
        "name": "ISSB S2 - 气候相关披露",
        "description": "国际可持续发展准则理事会发布的气候相关披露标准",
        "version": "2023年6月",
        "clauses": ISSB_S2_CLAUSES,
    },
    "GRI": {
        "name": "GRI Standards - 全球报告倡议组织标准",
        "description": "全球最广泛使用的可持续发展报告标准",
        "version": "2021版",
        "clauses": GRI_STANDARDS_CLAUSES,
    },
}

# 合规状态枚举
COMPLIANCE_STATUS_COMPLIANT = "已合规"
COMPLIANCE_STATUS_NON_COMPLIANT = "未合规"
COMPLIANCE_STATUS_PARTIAL = "部分合规"
