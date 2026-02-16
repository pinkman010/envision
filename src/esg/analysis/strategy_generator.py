"""策略生成器

基于差距分析结果生成改进策略，计算AI置信度。
"""

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from src.esg.analysis.gap_analyzer import GapAnalyzer, GapResult
from src.esg.config import ESG_DIMENSION_NAMES, GAP_THRESHOLD_HIGH, GAP_THRESHOLD_MEDIUM
from src.esg.core.models import ESGMetrics


class StrategyPriority(Enum):
    """策略优先级"""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class Strategy:
    """改进策略"""

    id: str
    title: str
    description: str
    dimension: str
    actions: List[str]
    priority: StrategyPriority
    confidence: float
    expected_impact: float
    timeframe: str
    resources_needed: List[str]
    target_audiences: List[str] = None
    communication_style: str = "正式"
    recommended_channels: List[Dict[str, str]] = None

    def __post_init__(self):
        """初始化默认值"""
        if self.target_audiences is None:
            self.target_audiences = []
        if self.recommended_channels is None:
            self.recommended_channels = []

    def to_dict(self) -> Dict[str, Any]:
        """将策略转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "dimension": self.dimension,
            "actions": self.actions,
            "priority": (
                self.priority.value
                if isinstance(self.priority, StrategyPriority)
                else self.priority
            ),
            "confidence": self.confidence,
            "expected_impact": self.expected_impact,
            "timeframe": self.timeframe,
            "resources_needed": self.resources_needed,
            "target_audiences": self.target_audiences,
            "communication_style": self.communication_style,
            "recommended_channels": self.recommended_channels,
        }


class StrategyGenerator:
    """ESG改进策略生成器

    基于差距分析结果生成针对性的改进策略，并提供AI置信度评估。

    Attributes:
        gap_analyzer: 差距分析器实例
        strategy_templates: 策略模板库
    """

    # 策略模板库
    STRATEGY_TEMPLATES = {
        "E": {
            "carbon_management": {
                "title": "加强碳排放管理",
                "description": "建立完善的碳核算体系，制定科学碳目标",
                "actions": [
                    "完善碳排放数据收集与核算体系",
                    "制定科学碳目标(SBTi)并定期披露进展",
                    "实施内部碳定价机制",
                    "推动供应链碳排放管理",
                ],
                "timeframe": "6-12个月",
                "resources": ["碳管理专员", "碳核算软件", "第三方核查"],
                "target_audiences": ["监管机构", "投资者", "评级机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "年报适合详细碳排放数据披露和减排目标进展汇报",
                    },
                    {
                        "channel_name": "官网ESG专栏",
                        "priority": "主渠道",
                        "reason": "实时展示碳管理数据和可视化进展",
                    },
                    {
                        "channel_name": "ESG评级回复",
                        "priority": "辅助渠道",
                        "reason": "回应评级机构对碳管理的专业问询",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "辅助渠道",
                        "reason": "向投资者阐述碳中和战略和投资价值",
                    },
                ],
            },
            "scope3_management": {
                "title": "加强范围3排放管理",
                "description": "建立价值链碳排放核算体系，推动供应链减排",
                "actions": [
                    "识别并核算15类范围3排放源",
                    "与重点供应商建立碳数据共享机制",
                    "制定供应链减排目标和激励机制",
                    "优先采购低碳产品和服务",
                ],
                "timeframe": "12-24个月",
                "resources": ["供应链碳管理团队", "供应商管理平台", "核算工具"],
                "target_audiences": ["供应链伙伴", "投资者", "监管机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "供应商大会",
                        "priority": "主渠道",
                        "reason": "向供应商宣导范围3管理要求和合作机制",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露范围3排放数据和供应链减排进展",
                    },
                    {
                        "channel_name": "供应商通讯",
                        "priority": "辅助渠道",
                        "reason": "定期更新碳管理要求和最佳实践",
                    },
                    {
                        "channel_name": "CDP供应链",
                        "priority": "辅助渠道",
                        "reason": "通过CDP平台收集供应商环境数据",
                    },
                ],
            },
            "sbti_target_setting": {
                "title": "设定科学碳目标(SBTi)",
                "description": "承诺SBTi并制定1.5°C温控路径的减排目标",
                "actions": [
                    "承诺加入SBTi并提交目标设定申请",
                    "开展全价值链碳盘查和情景分析",
                    "制定1.5°C路径的短期和长期减排目标",
                    "定期披露目标进展并获取第三方验证",
                ],
                "timeframe": "6-18个月",
                "resources": ["碳管理团队", "SBTi顾问", "第三方核查"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "新闻发布会",
                        "priority": "主渠道",
                        "reason": "宣布SBTi承诺和目标，提升品牌影响",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露SBTi目标、进展和减排路径",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "辅助渠道",
                        "reason": "阐述SBTi目标对长期价值的影响",
                    },
                    {
                        "channel_name": "SBTi官网",
                        "priority": "辅助渠道",
                        "reason": "在SBTi平台展示承诺和进展",
                    },
                ],
            },
            "renewable_energy": {
                "title": "提升可再生能源使用比例",
                "description": "通过自发自用和绿电采购提高可再生能源占比",
                "actions": [
                    "评估屋顶光伏和储能可行性",
                    "签订长期绿电采购协议(PPA)",
                    "参与绿电交易市场",
                    "建立可再生能源使用追踪体系",
                ],
                "timeframe": "12-24个月",
                "resources": ["能源管理团队", "项目资金", "技术供应商"],
                "target_audiences": ["投资者", "社区/公众", "监管机构"],
                "communication_style": "营销",
                "recommended_channels": [
                    {
                        "channel_name": "官网ESG专栏",
                        "priority": "主渠道",
                        "reason": "展示可再生能源项目进展和实时数据",
                    },
                    {
                        "channel_name": "社交媒体",
                        "priority": "主渠道",
                        "reason": "传播绿色能源成就，提升品牌形象",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "辅助渠道",
                        "reason": "汇总披露可再生能源使用比例和目标",
                    },
                    {
                        "channel_name": "新闻发布会",
                        "priority": "辅助渠道",
                        "reason": "重大项目签约或并网时对外发布",
                    },
                ],
            },
            "turbine_performance": {
                "title": "提升风机运营效率",
                "description": "提高风机可利用率，降低弃风率，优化发电性能",
                "actions": [
                    "实施预测性维护减少故障停机",
                    "优化风机控制策略提升发电效率",
                    "升级电网接入设施降低弃风率",
                    "开展风机性能监测和数据分析",
                ],
                "timeframe": "6-18个月",
                "resources": ["运维团队", "技术升级预算", "数据分析平台"],
                "target_audiences": ["投资者", "电网公司", "监管机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露风机可利用率、弃风率等关键指标",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "主渠道",
                        "reason": "展示运营效率提升对收益的影响",
                    },
                    {
                        "channel_name": "行业会议",
                        "priority": "辅助渠道",
                        "reason": "分享风机优化最佳实践",
                    },
                    {
                        "channel_name": "技术白皮书",
                        "priority": "辅助渠道",
                        "reason": "发布风机性能优化研究成果",
                    },
                ],
            },
            "battery_lifecycle": {
                "title": "优化电池全生命周期管理",
                "description": "提升电池循环寿命，建立回收和梯次利用体系",
                "actions": [
                    "改进电池管理系统延长循环寿命",
                    "建立电池健康状态监测和评估体系",
                    "开展退役电池梯次利用试点项目",
                    "与回收企业合作建立闭环回收体系",
                ],
                "timeframe": "12-36个月",
                "resources": ["研发团队", "回收合作伙伴", "试点项目资金"],
                "target_audiences": ["投资者", "监管机构", "供应链伙伴"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露电池循环寿命、回收率和梯次利用进展",
                    },
                    {
                        "channel_name": "行业论坛",
                        "priority": "主渠道",
                        "reason": "分享电池循环经济最佳实践",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "辅助渠道",
                        "reason": "阐述电池生命周期管理对成本的影响",
                    },
                    {
                        "channel_name": "技术白皮书",
                        "priority": "辅助渠道",
                        "reason": "发布电池回收和梯次利用技术成果",
                    },
                ],
            },
            "hydrogen_production": {
                "title": "提升绿氢生产效率",
                "description": "提高电解效率，降低绿氢生产成本",
                "actions": [
                    "采用高效电解槽技术提升电解效率",
                    "优化电解槽运行参数降低电耗",
                    "利用可再生能源直供降低制氢成本",
                    "开展电解槽核心材料研发",
                ],
                "timeframe": "12-36个月",
                "resources": ["研发团队", "技术升级预算", "示范项目资金"],
                "target_audiences": ["投资者", "政府", "下游客户"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露电解效率、氢气纯度和成本数据",
                    },
                    {
                        "channel_name": "行业峰会",
                        "priority": "主渠道",
                        "reason": "展示绿氢技术突破和商业化进展",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "辅助渠道",
                        "reason": "阐述绿氢业务的市场前景和投资价值",
                    },
                    {
                        "channel_name": "技术发布会",
                        "priority": "辅助渠道",
                        "reason": "发布新一代电解槽技术成果",
                    },
                ],
            },
            "circular_economy": {
                "title": "推进循环经济实践",
                "description": "实施废弃物减量、回收和再利用",
                "actions": [
                    "开展全生命周期环境影响评估",
                    "设计可回收、可再利用产品",
                    "建立废弃物分类和回收体系",
                    "与回收企业建立合作关系",
                ],
                "timeframe": "12-18个月",
                "resources": ["循环经济专员", "设计团队", "合作伙伴"],
                "target_audiences": ["社区/公众", "供应链伙伴", "投资者"],
                "communication_style": "亲和",
                "recommended_channels": [
                    {
                        "channel_name": "社交媒体",
                        "priority": "主渠道",
                        "reason": "分享循环经济案例，增强公众参与感",
                    },
                    {
                        "channel_name": "供应商大会",
                        "priority": "主渠道",
                        "reason": "推动供应链伙伴参与循环经济计划",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "辅助渠道",
                        "reason": "披露废弃物管理和资源利用数据",
                    },
                    {
                        "channel_name": "社区活动",
                        "priority": "辅助渠道",
                        "reason": "组织回收活动，提升社区参与度",
                    },
                ],
            },
        },
        "S": {
            "diversity_inclusion": {
                "title": "促进员工多元与包容",
                "description": "提升员工多样性，营造包容性工作环境",
                "actions": [
                    "制定多元化招聘目标和政策",
                    "开展无意识偏见培训",
                    "建立员工资源小组(ERG)",
                    "定期进行薪酬公平性审计",
                ],
                "timeframe": "6-12个月",
                "resources": ["HR团队", "培训预算", "DEI专员"],
                "target_audiences": ["员工", "投资者", "社区/公众"],
                "communication_style": "亲和",
                "recommended_channels": [
                    {
                        "channel_name": "员工大会",
                        "priority": "主渠道",
                        "reason": "向全员宣导多元化政策和员工资源小组",
                    },
                    {
                        "channel_name": "社交媒体",
                        "priority": "主渠道",
                        "reason": "分享多元文化故事，展示包容性文化",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "辅助渠道",
                        "reason": "披露员工多样性数据和薪酬公平性",
                    },
                    {
                        "channel_name": "招聘网站",
                        "priority": "辅助渠道",
                        "reason": "展示多元化承诺，吸引多样化人才",
                    },
                ],
            },
            "executive_diversity": {
                "title": "提升高管层多元化",
                "description": "增加女性和少数群体在高管层和董事会的代表性",
                "actions": [
                    "制定高管继任计划中的多元化目标",
                    "建立导师计划和领导力发展项目",
                    "评估并优化高管招聘流程以减少偏见",
                    "定期披露高管层多元化进展",
                ],
                "timeframe": "12-36个月",
                "resources": ["董事会", "HR团队", "高管教练", "猎头公司"],
                "target_audiences": ["投资者", "监管机构", "员工"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露高管层多元化数据和目标进展",
                    },
                    {
                        "channel_name": "公司治理报告",
                        "priority": "主渠道",
                        "reason": "说明董事会和高管层多元化政策",
                    },
                    {
                        "channel_name": "股东大会",
                        "priority": "辅助渠道",
                        "reason": "汇报高管继任和多元化进展",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "辅助渠道",
                        "reason": "阐述多元化如何提升决策质量",
                    },
                ],
            },
            "employee_development": {
                "title": "加强员工培训与发展",
                "description": "提升员工技能和职业发展机会",
                "actions": [
                    "建立系统化培训体系",
                    "制定个人发展计划(IDP)",
                    "提供内部轮岗和晋升机会",
                    "开展ESG意识和技能培训",
                ],
                "timeframe": "3-6个月",
                "resources": ["培训团队", "学习平台", "培训预算"],
                "target_audiences": ["员工", "投资者"],
                "communication_style": "亲和",
                "recommended_channels": [
                    {
                        "channel_name": "员工培训",
                        "priority": "主渠道",
                        "reason": "直接开展技能培训和ESG意识课程",
                    },
                    {
                        "channel_name": "内部通讯",
                        "priority": "主渠道",
                        "reason": "发布培训机会和员工发展成功案例",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "辅助渠道",
                        "reason": "披露培训投入和覆盖率数据",
                    },
                    {
                        "channel_name": "员工内网",
                        "priority": "辅助渠道",
                        "reason": "提供在线学习资源和个人发展工具",
                    },
                ],
            },
            "safety_performance": {
                "title": "提升安全绩效",
                "description": "降低工伤率，建立零伤害安全文化",
                "actions": [
                    "建立安全管理体系（ISO 45001）",
                    "开展全员安全培训和意识提升",
                    "实施安全隐患排查和整改闭环",
                    "加强承包商和供应商安全管理",
                ],
                "timeframe": "6-12个月",
                "resources": ["安全团队", "培训预算", "第三方认证"],
                "target_audiences": ["员工", "监管机构", "投资者"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "员工安全培训",
                        "priority": "主渠道",
                        "reason": "直接开展安全操作规程和应急演练培训",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露TRIR、LTIFR等安全指标和改进进展",
                    },
                    {
                        "channel_name": "内部通讯",
                        "priority": "辅助渠道",
                        "reason": "分享安全案例和表彰安全行为",
                    },
                    {
                        "channel_name": "安全月活动",
                        "priority": "辅助渠道",
                        "reason": "集中开展安全宣传和主题活动",
                    },
                ],
            },
            "community_engagement": {
                "title": "深化社区参与和投资",
                "description": "提升社区投资占营收比例，建立互利共赢的社区关系",
                "actions": [
                    "制定社区投资战略和重点领域",
                    "开展社区需求评估和利益相关方沟通",
                    "建立社区投资项目监测和评估机制",
                    "定期披露社区投资进展和影响",
                ],
                "timeframe": "6-12个月",
                "resources": ["CSR团队", "项目预算", "社区伙伴"],
                "target_audiences": ["社区/公众", "投资者", "监管机构"],
                "communication_style": "亲和",
                "recommended_channels": [
                    {
                        "channel_name": "社区活动",
                        "priority": "主渠道",
                        "reason": "直接参与社区建设和公益活动",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露社区投资额、项目和受益人数",
                    },
                    {
                        "channel_name": "社交媒体",
                        "priority": "辅助渠道",
                        "reason": "分享社区活动故事和员工志愿者经历",
                    },
                    {
                        "channel_name": "官网社区专栏",
                        "priority": "辅助渠道",
                        "reason": "展示社区项目地图和影响评估报告",
                    },
                ],
            },
            "supply_chain_human_rights": {
                "title": "强化供应链人权尽职调查",
                "description": "识别和 mitigate 供应链中的人权风险",
                "actions": [
                    "开展供应链人权风险评估",
                    "制定供应商行为准则",
                    "建立供应商审核机制",
                    "与供应商合作改善工作条件",
                ],
                "timeframe": "12-18个月",
                "resources": ["供应链团队", "审核预算", "第三方机构"],
                "target_audiences": ["监管机构", "供应链伙伴", "社区/公众"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "供应商大会",
                        "priority": "主渠道",
                        "reason": "宣导供应商行为准则和审核要求",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露供应链人权尽职调查进展",
                    },
                    {
                        "channel_name": "供应商培训",
                        "priority": "辅助渠道",
                        "reason": "帮助供应商理解和改善人权表现",
                    },
                    {
                        "channel_name": "官网供应商门户",
                        "priority": "辅助渠道",
                        "reason": "发布行为准则和审核标准",
                    },
                ],
            },
        },
        "G": {
            "board_independence": {
                "title": "提升董事会独立性和多元化",
                "description": "优化董事会结构，增强独立性和多样性",
                "actions": [
                    "评估当前董事会构成",
                    "制定董事多元化政策",
                    "引入具有ESG专业背景的独立董事",
                    "建立董事会ESG委员会",
                ],
                "timeframe": "12-24个月",
                "resources": ["董事会", "猎头公司", "治理顾问"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露董事会构成和多元化政策详情",
                    },
                    {
                        "channel_name": "股东大会",
                        "priority": "主渠道",
                        "reason": "向股东汇报治理结构和董事变更",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "辅助渠道",
                        "reason": "阐述董事会ESG监督能力提升",
                    },
                    {
                        "channel_name": "公司治理公告",
                        "priority": "辅助渠道",
                        "reason": "发布董事会委员会设立和调整",
                    },
                ],
            },
            "esg_governance_structure": {
                "title": "完善ESG治理架构",
                "description": "建立独立的ESG委员会，提升ESG监督效能",
                "actions": [
                    "设立董事会层面的ESG委员会",
                    "明确ESG委员会职责和议事规则",
                    "确保ESG委员会独立性（独立董事占比≥50%）",
                    "建立ESG指标与高管薪酬挂钩机制",
                ],
                "timeframe": "6-12个月",
                "resources": ["董事会", "治理顾问", "薪酬委员会"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露ESG委员会构成、职责和年度工作",
                    },
                    {
                        "channel_name": "公司章程修订公告",
                        "priority": "主渠道",
                        "reason": "正式公告ESG委员会设立和职责范围",
                    },
                    {
                        "channel_name": "股东大会",
                        "priority": "辅助渠道",
                        "reason": "向股东说明ESG治理架构升级",
                    },
                    {
                        "channel_name": "投资者路演",
                        "priority": "辅助渠道",
                        "reason": "阐述ESG治理如何提升长期价值",
                    },
                ],
            },
            "climate_governance": {
                "title": "强化气候治理架构",
                "description": "建立董事会气候委员会，将气候风险纳入治理核心",
                "actions": [
                    "设立董事会气候委员会或明确ESG委员会气候职责",
                    "将气候指标纳入高管薪酬考核体系",
                    "建立气候风险识别和管理流程",
                    "定期向董事会汇报气候议题进展",
                ],
                "timeframe": "6-18个月",
                "resources": ["董事会", "气候专家", "薪酬委员会"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "TCFD报告",
                        "priority": "主渠道",
                        "reason": "披露气候治理架构和风险管理",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "详细说明气候治理进展和目标",
                    },
                    {
                        "channel_name": "股东大会",
                        "priority": "辅助渠道",
                        "reason": "汇报气候治理战略和重大决策",
                    },
                    {
                        "channel_name": "投资者气候专项沟通",
                        "priority": "辅助渠道",
                        "reason": "针对气候投资者的专业交流",
                    },
                ],
            },
            "tcfd_disclosure": {
                "title": "完善TCFD四支柱披露",
                "description": "全面披露治理、战略、风险管理、指标与目标四支柱",
                "actions": [
                    "披露气候治理架构（董事会和管理层职责）",
                    "分析气候相关风险和机遇对业务战略的影响",
                    "披露气候风险识别、评估和管理流程",
                    "设定并披露气候相关指标和目标（含范围3）",
                ],
                "timeframe": "12-24个月",
                "resources": ["ESG团队", "气候专家", "第三方鉴证"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "TCFD专项报告",
                        "priority": "主渠道",
                        "reason": "完整呈现TCFD四支柱披露",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "整合TCFD披露到ESG报告体系",
                    },
                    {
                        "channel_name": "官网TCFD专栏",
                        "priority": "辅助渠道",
                        "reason": "提供TCFD报告下载和数据可视化",
                    },
                    {
                        "channel_name": "投资者说明会",
                        "priority": "辅助渠道",
                        "reason": "解读TCFD战略和财务影响分析",
                    },
                ],
            },
            "esg_disclosure": {
                "title": "完善ESG信息披露",
                "description": "提升ESG报告质量和透明度",
                "actions": [
                    "对标TCFD、GRI等国际标准",
                    "开展双重重要性评估",
                    "建立ESG数据管理系统",
                    "获取第三方ESG报告鉴证",
                ],
                "timeframe": "6-12个月",
                "resources": ["ESG团队", "披露平台", "咨询顾问"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "核心披露载体，包含完整ESG数据和分析",
                    },
                    {
                        "channel_name": "官网ESG专栏",
                        "priority": "主渠道",
                        "reason": "实时更新ESG进展和下载中心",
                    },
                    {
                        "channel_name": "ESG评级回复",
                        "priority": "辅助渠道",
                        "reason": "回应MSCI、Sustainalytics等评级问询",
                    },
                    {
                        "channel_name": "投资者说明会",
                        "priority": "辅助渠道",
                        "reason": "解读ESG报告亮点和应对投资者问题",
                    },
                ],
            },
            "ethics_compliance": {
                "title": "强化商业伦理与合规",
                "description": "建立完善的合规管理体系",
                "actions": [
                    "制定商业行为准则",
                    "建立举报机制和保护政策",
                    "开展全员伦理培训",
                    "定期进行合规风险评估",
                ],
                "timeframe": "3-9个月",
                "resources": ["合规团队", "培训资源", "举报系统"],
                "target_audiences": ["员工", "监管机构", "投资者"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "员工培训",
                        "priority": "主渠道",
                        "reason": "全员伦理培训和商业行为准则宣导",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露合规管理体系和举报机制",
                    },
                    {
                        "channel_name": "内部举报热线",
                        "priority": "辅助渠道",
                        "reason": "提供匿名举报渠道和保护机制",
                    },
                    {
                        "channel_name": "官网合规专栏",
                        "priority": "辅助渠道",
                        "reason": "公开商业行为准则和合规承诺",
                    },
                ],
            },
            "anti_corruption": {
                "title": "强化反腐败与反贿赂体系",
                "description": "建立全面的反腐败合规体系，覆盖全体员工和供应链",
                "actions": [
                    "制定反腐败政策和供应商行为准则",
                    "对高风险岗位和供应商开展专项培训",
                    "建立礼品申报和利益冲突管理制度",
                    "定期开展反腐败风险评估和尽职调查",
                ],
                "timeframe": "6-12个月",
                "resources": ["合规团队", "法务部门", "第三方审核"],
                "target_audiences": ["员工", "监管机构", "投资者", "供应链伙伴"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露反腐败政策、培训和风险评估",
                    },
                    {
                        "channel_name": "供应商大会",
                        "priority": "主渠道",
                        "reason": "宣导供应商行为准则和审核要求",
                    },
                    {
                        "channel_name": "员工培训",
                        "priority": "辅助渠道",
                        "reason": "高风险岗位专项反腐败培训",
                    },
                    {
                        "channel_name": "官网合规专栏",
                        "priority": "辅助渠道",
                        "reason": "公开反腐败承诺和举报渠道",
                    },
                ],
            },
            "whistleblower_protection": {
                "title": "完善举报人保护机制",
                "description": "建立安全、保密的举报渠道和全面的举报人保护体系",
                "actions": [
                    "建立多渠道举报平台（热线、邮箱、在线）",
                    "制定举报人保护政策，明确禁止报复行为",
                    "确保举报调查的独立性和保密性",
                    "定期向董事会汇报举报受理和处理情况",
                ],
                "timeframe": "3-6个月",
                "resources": ["合规团队", "IT部门", "外部供应商"],
                "target_audiences": ["员工", "监管机构", "投资者"],
                "communication_style": "正式",
                "recommended_channels": [
                    {
                        "channel_name": "内部举报平台",
                        "priority": "主渠道",
                        "reason": "直接提供安全、匿名的举报入口",
                    },
                    {
                        "channel_name": "年度ESG报告",
                        "priority": "主渠道",
                        "reason": "披露举报机制和保护政策",
                    },
                    {
                        "channel_name": "员工培训",
                        "priority": "辅助渠道",
                        "reason": "宣导举报渠道和保护政策",
                    },
                    {
                        "channel_name": "内部通讯",
                        "priority": "辅助渠道",
                        "reason": "定期宣传举报渠道更新和典型案例",
                    },
                ],
            },
        },
    }

    def __init__(self, gap_analyzer: Optional[GapAnalyzer] = None):
        """初始化策略生成器

        Args:
            gap_analyzer: 可选的差距分析器实例
        """
        self.gap_analyzer = gap_analyzer or GapAnalyzer()

    def generate_strategies(
        self, metrics: ESGMetrics, benchmark_company: str = "行业平均", max_strategies: int = 6
    ) -> List[Strategy]:
        """基于差距生成改进策略

        Args:
            metrics: 当前企业ESG指标
            benchmark_company: 标杆企业名称
            max_strategies: 最大策略数量

        Returns:
            策略列表，按优先级排序
        """
        # 分析维度差距
        dim_gaps = self.gap_analyzer.analyze_dimension_gap(metrics, benchmark_company)

        strategies = []

        # 为每个有差距的维度生成策略
        for dim, gap_result in dim_gaps.items():
            if gap_result.gap <= 0:
                continue

            # 根据差距大小选择策略
            dim_strategies = self._select_strategies_for_dimension(dim, gap_result, metrics)
            strategies.extend(dim_strategies)

        # 按优先级和置信度排序
        strategies.sort(
            key=lambda s: (
                (
                    0
                    if s.priority == StrategyPriority.HIGH
                    else (1 if s.priority == StrategyPriority.MEDIUM else 2)
                ),
                -s.confidence,
            )
        )

        return strategies[:max_strategies]

    def generate_strategy_for_area(
        self, area: str, metrics: ESGMetrics, gap_value: float
    ) -> Optional[Strategy]:
        """为特定领域生成策略

        Args:
            area: 策略领域ID
            metrics: 当前ESG指标
            gap_value: 差距值

        Returns:
            策略对象或None
        """
        # 查找对应的模板
        template = None
        dimension = None

        for dim, templates in self.STRATEGY_TEMPLATES.items():
            if area in templates:
                template = templates[area]
                dimension = dim
                break

        if not template:
            return None

        # 计算置信度和预期影响
        confidence = self._calculate_confidence(area, metrics, gap_value)
        impact = self._calculate_expected_impact(gap_value, confidence)

        # 生成策略ID
        strategy_id = self._generate_strategy_id(area, metrics.company_name)

        return Strategy(
            id=strategy_id,
            title=template["title"],
            description=template["description"],
            dimension=dimension,
            actions=template["actions"],
            priority=self._gap_to_priority(gap_value),
            confidence=round(confidence, 2),
            expected_impact=round(impact, 1),
            timeframe=template["timeframe"],
            resources_needed=template["resources"],
            target_audiences=template.get("target_audiences", []),
            communication_style=template.get("communication_style", "正式"),
            recommended_channels=template.get("recommended_channels", []),
        )

    def fine_tune_strategy(self, strategy: Strategy, adjustments: Dict[str, Any]) -> Strategy:
        """微调策略

        Args:
            strategy: 原始策略
            adjustments: 调整参数

        Returns:
            调整后的策略
        """
        # 创建策略副本
        new_strategy = Strategy(
            id=strategy.id,
            title=adjustments.get("title", strategy.title),
            description=adjustments.get("description", strategy.description),
            dimension=adjustments.get("dimension", strategy.dimension),
            actions=adjustments.get("actions", strategy.actions.copy()),
            priority=adjustments.get("priority", strategy.priority),
            confidence=strategy.confidence,
            expected_impact=strategy.expected_impact,
            timeframe=adjustments.get("timeframe", strategy.timeframe),
            resources_needed=adjustments.get("resources", strategy.resources_needed.copy()),
            target_audiences=adjustments.get(
                "target_audiences",
                list(strategy.target_audiences) if strategy.target_audiences else [],
            ),
            communication_style=adjustments.get(
                "communication_style", strategy.communication_style
            ),
            recommended_channels=adjustments.get(
                "recommended_channels",
                list(strategy.recommended_channels) if strategy.recommended_channels else [],
            ),
        )

        # 如果有行动项调整，重新计算置信度
        if "actions" in adjustments:
            # 行动项越多，置信度略有下降（复杂度增加）
            action_count = len(new_strategy.actions)
            complexity_factor = max(0.9, 1.0 - (action_count - 4) * 0.02)
            new_strategy.confidence = round(strategy.confidence * complexity_factor, 2)

        # 调整预期影响
        if "priority" in adjustments:
            priority_multipliers = {
                StrategyPriority.HIGH: 1.2,
                StrategyPriority.MEDIUM: 1.0,
                StrategyPriority.LOW: 0.8,
            }
            multiplier = priority_multipliers.get(new_strategy.priority, 1.0)
            new_strategy.expected_impact = round(
                strategy.expected_impact
                * multiplier
                / priority_multipliers.get(strategy.priority, 1.0),
                1,
            )

        return new_strategy

    def explain_confidence(self, strategy: Strategy) -> Dict[str, Any]:
        """解释AI置信度的计算依据

        Args:
            strategy: 策略对象

        Returns:
            置信度解释
        """
        confidence = strategy.confidence

        # 置信度等级
        if confidence >= 0.85:
            level = "高"
            explanation = "差距明显，策略模板匹配度高，实施路径清晰"
        elif confidence >= 0.70:
            level = "较高"
            explanation = "差距适中，有成熟的行业实践可参考"
        elif confidence >= 0.55:
            level = "中等"
            explanation = "差距较小或策略需要一定定制化"
        else:
            level = "待提升"
            explanation = "差距较小或数据不足，建议进一步分析"

        return {
            "confidence_score": confidence,
            "confidence_level": level,
            "explanation": explanation,
            "factors": {
                "gap_magnitude": (
                    "差距越大，策略针对性越强" if strategy.expected_impact > 10 else "差距适中"
                ),
                "data_quality": "基于完整ESG数据" if confidence > 0.7 else "部分数据缺失",
                "industry_benchmark": "有明确行业标杆可参考",
                "template_maturity": "使用经过验证的策略模板",
            },
        }

    def _select_strategies_for_dimension(
        self, dimension: str, gap_result: GapResult, metrics: ESGMetrics
    ) -> List[Strategy]:
        """为指定维度选择策略"""
        templates = self.STRATEGY_TEMPLATES.get(dimension, {})
        strategies = []

        # 根据差距大小选择策略数量
        num_strategies = (
            1
            if gap_result.gap < GAP_THRESHOLD_MEDIUM
            else (2 if gap_result.gap < GAP_THRESHOLD_HIGH else 3)
        )

        # 选择前N个模板
        selected_templates = list(templates.items())[:num_strategies]

        for area_id, template in selected_templates:
            confidence = self._calculate_confidence(area_id, metrics, gap_result.gap)
            impact = self._calculate_expected_impact(gap_result.gap, confidence)

            strategy = Strategy(
                id=self._generate_strategy_id(area_id, metrics.company_name),
                title=template["title"],
                description=template["description"],
                dimension=dimension,
                actions=template["actions"],
                priority=self._gap_to_priority(gap_result.gap),
                confidence=round(confidence, 2),
                expected_impact=round(impact, 1),
                timeframe=template["timeframe"],
                resources_needed=template["resources"],
                target_audiences=template.get("target_audiences", []),
                communication_style=template.get("communication_style", "正式"),
                recommended_channels=template.get("recommended_channels", []),
            )
            strategies.append(strategy)

        return strategies

    def _calculate_confidence(self, area: str, metrics: ESGMetrics, gap: float) -> float:
        """计算AI置信度（基于规则）

        置信度基于以下因素计算：
        1. 差距大小 (40%): 差距越大，策略针对性越强
        2. 数据完整度 (30%): 数据越完整，置信度越高
        3. 模板匹配度 (20%): 预设模板的成熟度
        4. 行业可比性 (10%): 与行业标杆的可比性
        """
        # 差距因子 (0-1)
        gap_factor = min(gap / 30.0, 1.0) * 0.4

        # 数据完整度 (0-1)
        data_completeness = self._calculate_data_completeness(metrics) * 0.3

        # 模板匹配度 (0-1) - 预设值
        template_match = 0.85 * 0.2

        # 行业可比性 (0-1)
        industry_comparability = 0.8 * 0.1

        # 基础置信度 + 各因子
        base_confidence = 0.5
        confidence = (
            base_confidence
            + gap_factor
            + data_completeness
            + template_match
            + industry_comparability
        )

        # 确保在0.35-0.95范围内
        return min(0.95, max(0.35, confidence))

    def _calculate_data_completeness(self, metrics: ESGMetrics) -> float:
        """计算数据完整度

        基于models.py中修复后的E/S/G维度权重配置，检查所有核心指标。
        与E_DIMENSION_WEIGHTS、S_DIMENSION_WEIGHTS、G_DIMENSION_WEIGHTS对齐。

        Returns:
            数据完整度 (0-1)
        """
        # ===== 环境维度 (E) - 对应E_DIMENSION_WEIGHTS的16个指标 =====
        e_checks = [
            # 一级指标：排放与气候（45%）
            metrics.carbon_intensity,
            metrics.scope3_coverage_percentage,
            metrics.sbti_target,
            # 二级指标：运营效率（30%）
            metrics.renewable_energy_ratio,
            metrics.energy_efficiency,
            metrics.waste_recycling_rate,
            metrics.water_intensity,
            # 三级指标：新能源特色（25%）
            metrics.turbine_availability,
            metrics.curtailment_rate,
            metrics.battery_cycle_life,
            metrics.battery_recycling_rate,
            metrics.electrolysis_efficiency,
            metrics.energy_storage_safety_score,
            # 基础排放数据（向后兼容）
            metrics.carbon_emissions,
            metrics.scope1_emissions,
            metrics.scope2_emissions_location,
        ]

        # ===== 社会维度 (S) - 对应S_DIMENSION_WEIGHTS的7个指标 =====
        s_checks = [
            # 一级指标：员工发展与多元化（45%）
            metrics.female_ratio,
            metrics.female_executive_ratio,
            metrics.training_hours,
            metrics.training_investment_per_employee,
            metrics.employee_count,
            # 二级指标：安全与福祉（30%）
            metrics.trir,
            metrics.ltifr if metrics.ltifr is not None else metrics.lost_time_injury_rate,
            metrics.safety_investment_ratio,
            metrics.safety_incidents,
            # 三级指标：社区责任（25%）
            metrics.community_investment_per_revenue,
            metrics.local_employment_ratio,
            metrics.community_investment,
        ]

        # ===== 治理维度 (G) - 对应G_DIMENSION_WEIGHTS的10个指标 =====
        g_checks = [
            # 第一层：董事会与治理结构（35%）
            metrics.board_independence_ratio,
            metrics.esg_committee_independence,
            # 第二层：合规与商业道德（30%）
            metrics.ethics_training_coverage,
            metrics.anti_corruption_training_coverage,
            metrics.whistleblower_protection,
            # 第三层：气候治理（20%）- 添加hasattr检查
            getattr(metrics, "climate_governance", None),
            getattr(metrics, "tcfd_disclosure", None),
            # 第四层：透明度与问责（15%）
            metrics.esg_report_quality,
            metrics.esg_committee_independence,  # 同时作为ESG治理指标
        ]

        checks = {
            "E": e_checks,
            "S": s_checks,
            "G": g_checks,
        }

        total_fields = sum(len(fields) for fields in checks.values())
        filled_fields = sum(
            1 for fields in checks.values() for field in fields if field is not None
        )

        return filled_fields / total_fields if total_fields > 0 else 0.5

    def _calculate_expected_impact(self, gap: float, confidence: float) -> float:
        """计算预期改进效果"""
        # 预期影响 = 差距 * 置信度 * 实现系数
        achievement_ratio = 0.6  # 假设能实现60%的差距改进
        return gap * confidence * achievement_ratio

    def _gap_to_priority(self, gap: float) -> StrategyPriority:
        """差距转优先级"""
        if gap >= GAP_THRESHOLD_HIGH:
            return StrategyPriority.HIGH
        elif gap >= GAP_THRESHOLD_MEDIUM:
            return StrategyPriority.MEDIUM
        else:
            return StrategyPriority.LOW

    def _generate_strategy_id(self, area: str, company: str) -> str:
        """生成策略ID"""
        # 使用area和company生成确定性ID
        hash_input = f"{area}_{company}_{id(self)}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"STR-{area.upper()}-{hash_value.upper()}"

    def to_dict(self, strategy: Strategy) -> Dict[str, Any]:
        """将策略转换为字典"""
        return {
            "id": strategy.id,
            "title": strategy.title,
            "description": strategy.description,
            "dimension": strategy.dimension,
            "dimension_name": ESG_DIMENSION_NAMES.get(strategy.dimension, "未知"),
            "actions": strategy.actions,
            "priority": (
                strategy.priority.value
                if isinstance(strategy.priority, StrategyPriority)
                else strategy.priority
            ),
            "confidence": strategy.confidence,
            "confidence_level": self._confidence_level(strategy.confidence),
            "expected_impact": strategy.expected_impact,
            "timeframe": strategy.timeframe,
            "resources_needed": strategy.resources_needed,
            "target_audiences": strategy.target_audiences if strategy.target_audiences else [],
            "communication_style": strategy.communication_style,
            "recommended_channels": (
                strategy.recommended_channels if strategy.recommended_channels else []
            ),
        }

    def filter_by_audience(self, strategies: List[Strategy], audience: str) -> List[Strategy]:
        """按目标受众筛选策略

        Args:
            strategies: 策略列表
            audience: 目标受众名称

        Returns:
            包含该受众的策略列表
        """
        if not audience:
            return strategies
        return [s for s in strategies if audience in (s.target_audiences or [])]

    def _confidence_level(self, confidence: float) -> str:
        """置信度数值转等级"""
        if confidence >= 0.85:
            return "高"
        elif confidence >= 0.70:
            return "较高"
        elif confidence >= 0.55:
            return "中等"
        else:
            return "待提升"

    @staticmethod
    def get_all_audiences() -> List[str]:
        """获取所有可用的目标受众选项"""
        return ["投资者", "监管机构", "员工", "社区/公众", "供应链伙伴", "评级机构"]
