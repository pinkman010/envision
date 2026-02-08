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


# ============================================================================
# 以下内容来自原 esg_features/standards.py
# ============================================================================

"""ESG国际标准支持模块

提供SASB、TCFD、ISSB、GRI等ESG标准的合规性检查和报告支持。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any

# 配置日志
logger = logging.getLogger(__name__)


class StandardType(Enum):
    """ESG标准类型"""
    SASB = "sasb"
    TCFD = "tcfd"
    ISSB_S1 = "issb_s1"
    ISSB_S2 = "issb_s2"
    GRI = "gri"
    CSRD = "csrd"
    HKEX = "hkex"


@dataclass
class StandardRequirement:
    """标准要求"""
    code: str
    name: str
    description: str
    category: str
    mandatory: bool = True
    guidance: str = ""
    examples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'mandatory': self.mandatory,
            'guidance': self.guidance,
            'examples': self.examples
        }


@dataclass
class ComplianceCheckResult:
    """合规检查结果"""
    requirement: StandardRequirement
    is_compliant: bool
    evidence: Optional[str] = None
    gap_description: Optional[str] = None
    recommendation: Optional[str] = None
    priority: str = "medium"  # high, medium, low
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'requirement': self.requirement.to_dict(),
            'is_compliant': self.is_compliant,
            'evidence': self.evidence,
            'gap_description': self.gap_description,
            'recommendation': self.recommendation,
            'priority': self.priority
        }


class SASBStandards:
    """SASB标准
    
    可持续发展会计准则委员会（SASB）标准，针对新能源行业的特定指标。
    """
    
    # 新能源行业SASB标准代码
    INDUSTRY_CODE = "NR0302"  # 可再生能源发电
    
    # SASB标准要求
    REQUIREMENTS: List[StandardRequirement] = [
        StandardRequirement(
            code="NR0302-01",
            name="可再生能源发电量",
            description="报告期内生产的可再生能源总量",
            category="环境绩效",
            guidance="以兆瓦时(MWh)为单位报告总发电量"
        ),
        StandardRequirement(
            code="NR0302-02",
            name="能源组合",
            description="按能源类型划分的装机容量",
            category="战略",
            guidance="报告各类可再生能源（风能、太阳能、水能等）的装机容量占比"
        ),
        StandardRequirement(
            code="NR0302-03",
            name="电网稳定性贡献",
            description="对电网稳定性和可靠性的贡献",
            category="环境绩效",
            guidance="报告调峰服务、储能能力等"
        ),
        StandardRequirement(
            code="NR0302-04",
            name="土地使用和生物多样性",
            description="土地使用对生物多样性的影响",
            category="环境绩效",
            mandatory=True,
            guidance="报告受保护区域的选址情况、栖息地保护措施"
        ),
        StandardRequirement(
            code="NR0302-05",
            name="社区关系",
            description="与项目所在地社区的关系管理",
            category="社会绩效",
            guidance="报告社区参与、投诉处理机制"
        ),
        StandardRequirement(
            code="NR0302-06",
            name="温室气体排放强度",
            description="每单位发电量的温室气体排放量",
            category="环境绩效",
            guidance="以kgCO2e/MWh为单位"
        ),
        StandardRequirement(
            code="NR0302-07",
            name="水资源管理",
            description="水资源使用和回收",
            category="环境绩效",
            guidance="报告取水量、回收率、干旱地区用水情况"
        ),
        StandardRequirement(
            code="NR0302-08",
            name="职业健康与安全",
            description="员工和承包商的安全绩效",
            category="社会绩效",
            guidance="报告可记录事故率、死亡率、安全培训"
        ),
        StandardRequirement(
            code="NR0302-09",
            name="供应链管理",
            description="供应链的环境和社会影响",
            category="社会绩效",
            guidance="报告供应商审核、冲突矿产政策"
        ),
        StandardRequirement(
            code="NR0302-10",
            name="董事会ESG监督",
            description="董事会对ESG事务的监督",
            category="治理",
            guidance="报告ESG委员会设置、董事会培训"
        )
    ]
    
    @classmethod
    def get_requirements(cls, category: Optional[str] = None) -> List[StandardRequirement]:
        """获取标准要求"""
        if category:
            return [r for r in cls.REQUIREMENTS if r.category == category]
        return cls.REQUIREMENTS
    
    @classmethod
    def get_requirement_by_code(cls, code: str) -> Optional[StandardRequirement]:
        """通过代码获取要求"""
        return next((r for r in cls.REQUIREMENTS if r.code == code), None)


class TCFDStandards:
    """TCFD标准
    
    气候相关财务披露工作组（TCFD）建议框架。
    """
    
    # TCFD四大支柱
    PILLARS = {
        'governance': '治理',
        'strategy': '战略',
        'risk_management': '风险管理',
        'metrics_targets': '指标和目标'
    }
    
    REQUIREMENTS: List[StandardRequirement] = [
        # 治理支柱
        StandardRequirement(
            code="TCFD-G-01",
            name="气候相关风险的董事会监督",
            description="描述董事会对气候相关风险和机遇的监督",
            category="governance",
            guidance="包括董事会评估气候风险的频率和方式"
        ),
        StandardRequirement(
            code="TCFD-G-02",
            name="管理层在气候风险管理中的角色",
            description="描述管理层在评估和管理气候风险中的角色",
            category="governance",
            guidance="包括具体的职责分工和汇报关系"
        ),
        # 战略支柱
        StandardRequirement(
            code="TCFD-S-01",
            name="气候相关风险和机遇",
            description="描述识别出的短期、中期和长期气候风险和机遇",
            category="strategy",
            guidance="包括对不同情景下影响的评估"
        ),
        StandardRequirement(
            code="TCFD-S-02",
            name="气候风险对业务的影响",
            description="描述气候风险对业务战略和财务规划的影响",
            category="strategy",
            guidance="包括战略韧性评估"
        ),
        StandardRequirement(
            code="TCFD-S-03",
            name="气候情景分析",
            description="描述组织的气候韧性情景分析",
            category="strategy",
            guidance="包括2°C或更低情景的考虑"
        ),
        # 风险管理支柱
        StandardRequirement(
            code="TCFD-R-01",
            name="识别和评估气候风险",
            description="描述识别和评估气候风险的流程",
            category="risk_management",
            guidance="与整体风险管理框架的整合"
        ),
        StandardRequirement(
            code="TCFD-R-02",
            name="管理气候风险",
            description="描述管理气候风险的流程",
            category="risk_management",
            guidance="包括风险缓解策略"
        ),
        # 指标和目标支柱
        StandardRequirement(
            code="TCFD-M-01",
            name="气候相关指标",
            description="披露用于评估气候相关风险和机遇的指标",
            category="metrics_targets",
            guidance="包括范围1、2、3温室气体排放"
        ),
        StandardRequirement(
            code="TCFD-M-02",
            name="温室气体排放",
            description="披露范围1、2、3温室气体排放和相关风险",
            category="metrics_targets",
            guidance="按GHG Protocol标准披露"
        ),
        StandardRequirement(
            code="TCFD-M-03",
            name="气候相关目标",
            description="描述用于管理气候相关风险和机遇的目标",
            category="metrics_targets",
            guidance="包括目标实现进展"
        )
    ]
    
    @classmethod
    def get_requirements_by_pillar(cls, pillar: str) -> List[StandardRequirement]:
        """按支柱获取要求"""
        return [r for r in cls.REQUIREMENTS if r.category == pillar]
    
    @classmethod
    def get_all_requirements(cls) -> List[StandardRequirement]:
        """获取所有要求"""
        return cls.REQUIREMENTS


class StandardsManager:
    """标准管理器
    
    统一管理多个ESG标准的要求和合规性检查。
    
    Example:
        >>> manager = StandardsManager()
        >>> 
        >>> # 获取SASB要求
        >>> sasb_reqs = manager.get_requirements(StandardType.SASB)
        >>> 
        >>> # 检查合规性
        >>> results = manager.check_compliance(
        ...     standard=StandardType.SASB,
        ...     disclosure_data={"NR0302-01": "100000 MWh"}
        ... )
    """
    
    def __init__(self):
        """初始化标准管理器"""
        self._standards: Dict[StandardType, Any] = {
            StandardType.SASB: SASBStandards,
            StandardType.TCFD: TCFDStandards,
        }
    
    def get_requirements(
        self,
        standard: StandardType,
        category: Optional[str] = None
    ) -> List[StandardRequirement]:
        """获取标准要求
        
        Args:
            standard: 标准类型
            category: 可选的类别过滤
            
        Returns:
            标准要求列表
        """
        std = self._standards.get(standard)
        if not std:
            return []
        
        if hasattr(std, 'get_requirements'):
            return std.get_requirements(category)
        return []
    
    def check_compliance(
        self,
        standard: StandardType,
        disclosure_data: Dict[str, Any]
    ) -> List[ComplianceCheckResult]:
        """检查合规性
        
        Args:
            standard: 标准类型
            disclosure_data: 披露数据，键为要求代码
            
        Returns:
            合规性检查结果列表
        """
        requirements = self.get_requirements(standard)
        results = []
        
        for req in requirements:
            # 检查是否提供了披露数据
            has_disclosure = req.code in disclosure_data
            
            if req.mandatory and not has_disclosure:
                result = ComplianceCheckResult(
                    requirement=req,
                    is_compliant=False,
                    gap_description=f"缺少强制性披露项: {req.name}",
                    recommendation=f"请提供{req.name}的相关数据",
                    priority="high"
                )
            elif has_disclosure:
                result = ComplianceCheckResult(
                    requirement=req,
                    is_compliant=True,
                    evidence=str(disclosure_data[req.code]),
                    priority="low"
                )
            else:
                result = ComplianceCheckResult(
                    requirement=req,
                    is_compliant=True,  # 非强制性，可以合规
                    gap_description=f"可选披露项未提供: {req.name}",
                    priority="low"
                )
            
            results.append(result)
        
        return results
    
    def generate_compliance_report(
        self,
        standard: StandardType,
        disclosure_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成合规性报告
        
        Args:
            standard: 标准类型
            disclosure_data: 披露数据
            
        Returns:
            合规性报告
        """
        results = self.check_compliance(standard, disclosure_data)
        
        total = len(results)
        compliant = sum(1 for r in results if r.is_compliant)
        non_compliant = total - compliant
        
        mandatory_non_compliant = [
            r for r in results
            if not r.is_compliant and r.requirement.mandatory
        ]
        
        high_priority_gaps = [
            r for r in results
            if r.priority == "high" and not r.is_compliant
        ]
        
        return {
            'standard': standard.value,
            'summary': {
                'total_requirements': total,
                'compliant': compliant,
                'non_compliant': non_compliant,
                'compliance_rate': compliant / total if total > 0 else 0,
                'mandatory_gaps': len(mandatory_non_compliant),
                'high_priority_gaps': len(high_priority_gaps)
            },
            'gaps': [r.to_dict() for r in results if not r.is_compliant],
            'compliant_items': [r.to_dict() for r in results if r.is_compliant],
            'recommendations': [
                r.recommendation for r in high_priority_gaps
                if r.recommendation
            ]
        }
    
    def get_supported_standards(self) -> List[str]:
        """获取支持的标准列表"""
        return [s.value for s in self._standards.keys()]


class ComplianceChecker:
    """合规检查器
    
    检查ESG报告对多个标准的合规性。
    """
    
    def __init__(self):
        """初始化合规检查器"""
        self.standards_manager = StandardsManager()
    
    def comprehensive_check(
        self,
        disclosure_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """综合合规性检查
        
        Args:
            disclosure_data: 按标准组织的数据
                {"sasb": {"NR0302-01": "..."}, "tcfd": {...}}
                
        Returns:
            综合合规性报告
        """
        reports = {}
        
        for std_type in StandardType:
            if std_type.value in disclosure_data:
                reports[std_type.value] = self.standards_manager.generate_compliance_report(
                    std_type,
                    disclosure_data[std_type.value]
                )
        
        # 计算整体合规率
        total_requirements = sum(
            r['summary']['total_requirements'] for r in reports.values()
        )
        total_compliant = sum(
            r['summary']['compliant'] for r in reports.values()
        )
        
        overall_rate = total_compliant / total_requirements if total_requirements > 0 else 0
        
        return {
            'overall_compliance_rate': overall_rate,
            'total_requirements': total_requirements,
            'total_compliant': total_compliant,
            'standards': reports
        }
