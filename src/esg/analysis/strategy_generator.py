"""策略生成器

基于差距分析结果生成改进策略，计算AI置信度。
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

from src.esg.config import ESG_DIMENSION_NAMES, GAP_THRESHOLD_HIGH, GAP_THRESHOLD_MEDIUM
from src.esg.analysis.gap_analyzer import GapResult, GapAnalyzer
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
            "priority": self.priority.value if isinstance(self.priority, StrategyPriority) else self.priority,
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
                    "推动供应链碳排放管理"
                ],
                "timeframe": "6-12个月",
                "resources": ["碳管理专员", "碳核算软件", "第三方核查"],
                "target_audiences": ["监管机构", "投资者", "评级机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "年报适合详细碳排放数据披露和减排目标进展汇报"},
                    {"channel_name": "官网ESG专栏", "priority": "主渠道", "reason": "实时展示碳管理数据和可视化进展"},
                    {"channel_name": "ESG评级回复", "priority": "辅助渠道", "reason": "回应评级机构对碳管理的专业问询"},
                    {"channel_name": "投资者路演", "priority": "辅助渠道", "reason": "向投资者阐述碳中和战略和投资价值"}
                ]
            },
            "renewable_energy": {
                "title": "提升可再生能源使用比例",
                "description": "通过自发自用和绿电采购提高可再生能源占比",
                "actions": [
                    "评估屋顶光伏和储能可行性",
                    "签订长期绿电采购协议(PPA)",
                    "参与绿电交易市场",
                    "建立可再生能源使用追踪体系"
                ],
                "timeframe": "12-24个月",
                "resources": ["能源管理团队", "项目资金", "技术供应商"],
                "target_audiences": ["投资者", "社区/公众", "监管机构"],
                "communication_style": "营销",
                "recommended_channels": [
                    {"channel_name": "官网ESG专栏", "priority": "主渠道", "reason": "展示可再生能源项目进展和实时数据"},
                    {"channel_name": "社交媒体", "priority": "主渠道", "reason": "传播绿色能源成就，提升品牌形象"},
                    {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "汇总披露可再生能源使用比例和目标"},
                    {"channel_name": "新闻发布会", "priority": "辅助渠道", "reason": "重大项目签约或并网时对外发布"}
                ]
            },
            "circular_economy": {
                "title": "推进循环经济实践",
                "description": "实施废弃物减量、回收和再利用",
                "actions": [
                    "开展全生命周期环境影响评估",
                    "设计可回收、可再利用产品",
                    "建立废弃物分类和回收体系",
                    "与回收企业建立合作关系"
                ],
                "timeframe": "12-18个月",
                "resources": ["循环经济专员", "设计团队", "合作伙伴"],
                "target_audiences": ["社区/公众", "供应链伙伴", "投资者"],
                "communication_style": "亲和",
                "recommended_channels": [
                    {"channel_name": "社交媒体", "priority": "主渠道", "reason": "分享循环经济案例，增强公众参与感"},
                    {"channel_name": "供应商大会", "priority": "主渠道", "reason": "推动供应链伙伴参与循环经济计划"},
                    {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "披露废弃物管理和资源利用数据"},
                    {"channel_name": "社区活动", "priority": "辅助渠道", "reason": "组织回收活动，提升社区参与度"}
                ]
            }
        },
        "S": {
            "diversity_inclusion": {
                "title": "促进员工多元与包容",
                "description": "提升员工多样性，营造包容性工作环境",
                "actions": [
                    "制定多元化招聘目标和政策",
                    "开展无意识偏见培训",
                    "建立员工资源小组(ERG)",
                    "定期进行薪酬公平性审计"
                ],
                "timeframe": "6-12个月",
                "resources": ["HR团队", "培训预算", "DEI专员"],
                "target_audiences": ["员工", "投资者", "社区/公众"],
                "communication_style": "亲和",
                "recommended_channels": [
                    {"channel_name": "员工大会", "priority": "主渠道", "reason": "向全员宣导多元化政策和员工资源小组"},
                    {"channel_name": "社交媒体", "priority": "主渠道", "reason": "分享多元文化故事，展示包容性文化"},
                    {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "披露员工多样性数据和薪酬公平性"},
                    {"channel_name": "招聘网站", "priority": "辅助渠道", "reason": "展示多元化承诺，吸引多样化人才"}
                ]
            },
            "employee_development": {
                "title": "加强员工培训与发展",
                "description": "提升员工技能和职业发展机会",
                "actions": [
                    "建立系统化培训体系",
                    "制定个人发展计划(IDP)",
                    "提供内部轮岗和晋升机会",
                    "开展ESG意识和技能培训"
                ],
                "timeframe": "3-6个月",
                "resources": ["培训团队", "学习平台", "培训预算"],
                "target_audiences": ["员工", "投资者"],
                "communication_style": "亲和",
                "recommended_channels": [
                    {"channel_name": "员工培训", "priority": "主渠道", "reason": "直接开展技能培训和ESG意识课程"},
                    {"channel_name": "内部通讯", "priority": "主渠道", "reason": "发布培训机会和员工发展成功案例"},
                    {"channel_name": "年度ESG报告", "priority": "辅助渠道", "reason": "披露培训投入和覆盖率数据"},
                    {"channel_name": "员工内网", "priority": "辅助渠道", "reason": "提供在线学习资源和个人发展工具"}
                ]
            },
            "supply_chain_human_rights": {
                "title": "强化供应链人权尽职调查",
                "description": "识别和 mitigate 供应链中的人权风险",
                "actions": [
                    "开展供应链人权风险评估",
                    "制定供应商行为准则",
                    "建立供应商审核机制",
                    "与供应商合作改善工作条件"
                ],
                "timeframe": "12-18个月",
                "resources": ["供应链团队", "审核预算", "第三方机构"],
                "target_audiences": ["监管机构", "供应链伙伴", "社区/公众"],
                "communication_style": "正式",
                "recommended_channels": [
                    {"channel_name": "供应商大会", "priority": "主渠道", "reason": "宣导供应商行为准则和审核要求"},
                    {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露供应链人权尽职调查进展"},
                    {"channel_name": "供应商培训", "priority": "辅助渠道", "reason": "帮助供应商理解和改善人权表现"},
                    {"channel_name": "官网供应商门户", "priority": "辅助渠道", "reason": "发布行为准则和审核标准"}
                ]
            }
        },
        "G": {
            "board_independence": {
                "title": "提升董事会独立性和多元化",
                "description": "优化董事会结构，增强独立性和多样性",
                "actions": [
                    "评估当前董事会构成",
                    "制定董事多元化政策",
                    "引入具有ESG专业背景的独立董事",
                    "建立董事会ESG委员会"
                ],
                "timeframe": "12-24个月",
                "resources": ["董事会", "猎头公司", "治理顾问"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "正式",
                "recommended_channels": [
                    {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露董事会构成和多元化政策详情"},
                    {"channel_name": "股东大会", "priority": "主渠道", "reason": "向股东汇报治理结构和董事变更"},
                    {"channel_name": "投资者路演", "priority": "辅助渠道", "reason": "阐述董事会ESG监督能力提升"},
                    {"channel_name": "公司治理公告", "priority": "辅助渠道", "reason": "发布董事会委员会设立和调整"}
                ]
            },
            "esg_disclosure": {
                "title": "完善ESG信息披露",
                "description": "提升ESG报告质量和透明度",
                "actions": [
                    "对标TCFD、GRI等国际标准",
                    "开展双重重要性评估",
                    "建立ESG数据管理系统",
                    "获取第三方ESG报告鉴证"
                ],
                "timeframe": "6-12个月",
                "resources": ["ESG团队", "披露平台", "咨询顾问"],
                "target_audiences": ["投资者", "监管机构", "评级机构"],
                "communication_style": "技术",
                "recommended_channels": [
                    {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "核心披露载体，包含完整ESG数据和分析"},
                    {"channel_name": "官网ESG专栏", "priority": "主渠道", "reason": "实时更新ESG进展和下载中心"},
                    {"channel_name": "ESG评级回复", "priority": "辅助渠道", "reason": "回应MSCI、Sustainalytics等评级问询"},
                    {"channel_name": "投资者说明会", "priority": "辅助渠道", "reason": "解读ESG报告亮点和应对投资者问题"}
                ]
            },
            "ethics_compliance": {
                "title": "强化商业伦理与合规",
                "description": "建立完善的合规管理体系",
                "actions": [
                    "制定商业行为准则",
                    "建立举报机制和保护政策",
                    "开展全员伦理培训",
                    "定期进行合规风险评估"
                ],
                "timeframe": "3-9个月",
                "resources": ["合规团队", "培训资源", "举报系统"],
                "target_audiences": ["员工", "监管机构", "投资者"],
                "communication_style": "正式",
                "recommended_channels": [
                    {"channel_name": "员工培训", "priority": "主渠道", "reason": "全员伦理培训和商业行为准则宣导"},
                    {"channel_name": "年度ESG报告", "priority": "主渠道", "reason": "披露合规管理体系和举报机制"},
                    {"channel_name": "内部举报热线", "priority": "辅助渠道", "reason": "提供匿名举报渠道和保护机制"},
                    {"channel_name": "官网合规专栏", "priority": "辅助渠道", "reason": "公开商业行为准则和合规承诺"}
                ]
            }
        }
    }
    
    def __init__(self, gap_analyzer: Optional[GapAnalyzer] = None):
        """初始化策略生成器
        
        Args:
            gap_analyzer: 可选的差距分析器实例
        """
        self.gap_analyzer = gap_analyzer or GapAnalyzer()
    
    def generate_strategies(
        self,
        metrics: ESGMetrics,
        benchmark_company: str = "行业平均",
        max_strategies: int = 6
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
            dim_strategies = self._select_strategies_for_dimension(
                dim, gap_result, metrics
            )
            strategies.extend(dim_strategies)
        
        # 按优先级和置信度排序
        strategies.sort(key=lambda s: (
            0 if s.priority == StrategyPriority.HIGH else (
                1 if s.priority == StrategyPriority.MEDIUM else 2
            ),
            -s.confidence
        ))
        
        return strategies[:max_strategies]
    
    def generate_strategy_for_area(
        self,
        area: str,
        metrics: ESGMetrics,
        gap_value: float
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
            recommended_channels=template.get("recommended_channels", [])
        )
    
    def fine_tune_strategy(
        self,
        strategy: Strategy,
        adjustments: Dict[str, Any]
    ) -> Strategy:
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
            target_audiences=adjustments.get("target_audiences", list(strategy.target_audiences) if strategy.target_audiences else []),
            communication_style=adjustments.get("communication_style", strategy.communication_style),
            recommended_channels=adjustments.get("recommended_channels", list(strategy.recommended_channels) if strategy.recommended_channels else [])
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
                StrategyPriority.LOW: 0.8
            }
            multiplier = priority_multipliers.get(new_strategy.priority, 1.0)
            new_strategy.expected_impact = round(
                strategy.expected_impact * multiplier / priority_multipliers.get(strategy.priority, 1.0),
                1
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
                "gap_magnitude": "差距越大，策略针对性越强" if strategy.expected_impact > 10 else "差距适中",
                "data_quality": "基于完整ESG数据" if confidence > 0.7 else "部分数据缺失",
                "industry_benchmark": "有明确行业标杆可参考",
                "template_maturity": "使用经过验证的策略模板"
            }
        }
    
    def _select_strategies_for_dimension(
        self,
        dimension: str,
        gap_result: GapResult,
        metrics: ESGMetrics
    ) -> List[Strategy]:
        """为指定维度选择策略"""
        templates = self.STRATEGY_TEMPLATES.get(dimension, {})
        strategies = []
        
        # 根据差距大小选择策略数量
        num_strategies = 1 if gap_result.gap < GAP_THRESHOLD_MEDIUM else (
            2 if gap_result.gap < GAP_THRESHOLD_HIGH else 3
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
                recommended_channels=template.get("recommended_channels", [])
            )
            strategies.append(strategy)
        
        return strategies
    
    def _calculate_confidence(
        self,
        area: str,
        metrics: ESGMetrics,
        gap: float
    ) -> float:
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
        confidence = base_confidence + gap_factor + data_completeness + template_match + industry_comparability
        
        # 确保在0.35-0.95范围内
        return min(0.95, max(0.35, confidence))
    
    def _calculate_data_completeness(self, metrics: ESGMetrics) -> float:
        """计算数据完整度"""
        # 检查各维度数据是否存在
        checks = {
            "E": [
                metrics.carbon_emissions,
                metrics.renewable_energy_ratio,
                metrics.energy_efficiency,
                metrics.water_consumption,
                metrics.waste_recycling_rate
            ],
            "S": [
                metrics.employee_count,
                metrics.female_ratio,
                metrics.training_hours,
                metrics.safety_incidents,
                metrics.community_investment
            ],
            "G": [
                metrics.board_independence_ratio,
                metrics.ethics_training_coverage,
                metrics.esg_report_quality
            ]
        }
        
        total_fields = sum(len(fields) for fields in checks.values())
        filled_fields = sum(
            1 for fields in checks.values() 
            for field in fields if field is not None
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
            "priority": strategy.priority.value if isinstance(strategy.priority, StrategyPriority) else strategy.priority,
            "confidence": strategy.confidence,
            "confidence_level": self._confidence_level(strategy.confidence),
            "expected_impact": strategy.expected_impact,
            "timeframe": strategy.timeframe,
            "resources_needed": strategy.resources_needed,
            "target_audiences": strategy.target_audiences if strategy.target_audiences else [],
            "communication_style": strategy.communication_style,
            "recommended_channels": strategy.recommended_channels if strategy.recommended_channels else [],
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
