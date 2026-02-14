"""CDP问卷自动填报模块

实现CDP气候变化问卷（Climate Change Questionnaire）的自动填报功能。
支持完整版问卷（约200+问题）的题库映射、答案自动提取和填报文件生成。

Reference: https://www.cdp.net/en/guidance/guidance-and-questionnaires
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd


class CDPModule(Enum):
    """CDP问卷模块"""
    GOVERNANCE = "governance"  # 治理
    STRATEGY = "strategy"  # 战略
    RISK_OPPORTUNITY = "risk_opportunity"  # 风险和机遇
    EMISSIONS = "emissions"  # 排放
    TARGETS = "targets"  # 目标
    VALUE_CHAIN = "value_chain"  # 价值链


class CDPQuestionType(Enum):
    """CDP问题类型"""
    TEXT = "text"  # 文本
    NUMBER = "number"  # 数字
    YES_NO = "yes_no"  # 是/否
    SINGLE_SELECT = "single_select"  # 单选
    MULTI_SELECT = "multi_select"  # 多选
    TABLE = "table"  # 表格
    PERCENTAGE = "percentage"  # 百分比
    CURRENCY = "currency"  # 货币


# CDP评分权重配置
CDP_SCORING_WEIGHTS = {
    CDPModule.GOVERNANCE: 0.15,
    CDPModule.STRATEGY: 0.20,
    CDPModule.RISK_OPPORTUNITY: 0.20,
    CDPModule.EMISSIONS: 0.25,
    CDPModule.TARGETS: 0.15,
    CDPModule.VALUE_CHAIN: 0.05,
}


@dataclass
class CDPQuestion:
    """CDP问题定义
    
    Attributes:
        question_number: CDP题号（如C1.1a）
        module: 所属模块
        question_text: 问题文本
        question_type: 问题类型
        options: 选项列表（如适用）
        required: 是否必填
        mapping_field: 映射到ESGMetrics的字段
        calculation_method: 计算方法说明
        parent_question: 父问题（条件题）
        condition_value: 触发条件值
    """
    question_number: str
    module: CDPModule
    question_text: str
    question_text_cn: str = ""
    question_type: CDPQuestionType = CDPQuestionType.TEXT
    options: List[str] = field(default_factory=list)
    required: bool = False
    mapping_field: str = ""  # 如 "scope1_emissions"
    calculation_method: str = ""
    parent_question: str = ""  # 如 "C1.1"
    condition_value: Any = None
    section: str = ""  # 所属小节
    guidance: str = ""  # 填报指导


@dataclass
class CDPAnswer:
    """CDP答案
    
    Attributes:
        question_number: 题号
        answer_value: 答案值
        confidence: 置信度（0-1）
        data_source: 数据来源
        notes: 备注
        updated_at: 更新时间
    """
    question_number: str
    answer_value: Any
    confidence: float = 1.0
    data_source: str = ""
    notes: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_number": self.question_number,
            "answer_value": self.answer_value,
            "confidence": self.confidence,
            "data_source": self.data_source,
            "notes": self.notes,
            "updated_at": self.updated_at,
        }


# CDP完整题库（2024年版简化版核心问题）
CDP_QUESTIONNAIRE: List[CDPQuestion] = [
    # ========== Module 1: Governance 治理 ==========
    CDPQuestion(
        question_number="C1.1",
        module=CDPModule.GOVERNANCE,
        question_text="Does your organization have a board-level position with responsibility for climate-related issues?",
        question_text_cn="贵组织是否有董事会级别的职位负责气候相关问题？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        mapping_field="esg_committee_independence",
        section="Board Oversight",
    ),
    CDPQuestion(
        question_number="C1.1a",
        module=CDPModule.GOVERNANCE,
        question_text="Please describe the position and responsibilities",
        question_text_cn="请描述该职位和职责",
        question_type=CDPQuestionType.TEXT,
        required=False,
        parent_question="C1.1",
        condition_value="Yes",
        section="Board Oversight",
    ),
    CDPQuestion(
        question_number="C1.2",
        module=CDPModule.GOVERNANCE,
        question_text="Do you provide incentives for the management of climate-related issues?",
        question_text_cn="贵组织是否提供与气候相关问题管理相关的激励措施？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Management Incentives",
    ),
    CDPQuestion(
        question_number="C1.2a",
        module=CDPModule.GOVERNANCE,
        question_text="Please provide further details on the incentives provided",
        question_text_cn="请提供激励措施的详细说明",
        question_type=CDPQuestionType.TABLE,
        required=False,
        parent_question="C1.2",
        condition_value="Yes",
        section="Management Incentives",
    ),
    CDPQuestion(
        question_number="C1.3",
        module=CDPModule.GOVERNANCE,
        question_text="Does your organization have a process for identifying, assessing and responding to climate-related risks and opportunities?",
        question_text_cn="贵组织是否有识别、评估和应对气候相关风险和机遇的流程？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Risk Management",
    ),
    
    # ========== Module 2: Strategy 战略 ==========
    CDPQuestion(
        question_number="C2.1",
        module=CDPModule.STRATEGY,
        question_text="Has your organization identified climate-related risks and opportunities that have had or may have a substantive financial or strategic impact on your business?",
        question_text_cn="贵组织是否已识别对业务产生或可能产生实质性财务或战略影响的气候相关风险和机遇？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Risk and Opportunity Identification",
    ),
    CDPQuestion(
        question_number="C2.2",
        module=CDPModule.STRATEGY,
        question_text="Please describe your risks and opportunities",
        question_text_cn="请描述贵组织的风险和机遇",
        question_type=CDPQuestionType.TABLE,
        required=True,
        parent_question="C2.1",
        condition_value="Yes",
        section="Risk and Opportunity Description",
    ),
    CDPQuestion(
        question_number="C2.3",
        module=CDPModule.STRATEGY,
        question_text="Have you identified any climate-related opportunities with the potential to have a substantive financial or strategic impact on your business?",
        question_text_cn="贵组织是否识别了可能对业务产生实质性财务或战略影响的气候相关机遇？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Opportunities",
    ),
    CDPQuestion(
        question_number="C2.4",
        module=CDPModule.STRATEGY,
        question_text="Please provide details of your climate-related opportunities",
        question_text_cn="请提供气候相关机遇的详细信息",
        question_type=CDPQuestionType.TABLE,
        required=False,
        parent_question="C2.3",
        condition_value="Yes",
        section="Opportunities",
    ),
    
    # ========== Module 3: Risk and Opportunity 风险和机遇 ==========
    CDPQuestion(
        question_number="C3.1",
        module=CDPModule.RISK_OPPORTUNITY,
        question_text="Have you identified any inherent climate-related risks with the potential to have a substantive financial or strategic impact on your business?",
        question_text_cn="贵组织是否识别了可能对业务产生实质性财务或战略影响的固有气候相关风险？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Risk Identification",
    ),
    CDPQuestion(
        question_number="C3.1a",
        module=CDPModule.RISK_OPPORTUNITY,
        question_text="Please provide details of your inherent climate-related risks",
        question_text_cn="请提供固有气候相关风险的详细信息",
        question_type=CDPQuestionType.TABLE,
        required=True,
        parent_question="C3.1",
        condition_value="Yes",
        section="Risk Description",
    ),
    CDPQuestion(
        question_number="C3.2",
        module=CDPModule.RISK_OPPORTUNITY,
        question_text="Please describe your processes for identifying, assessing and responding to climate-related risks and opportunities",
        question_text_cn="请描述识别、评估和应对气候相关风险和机遇的流程",
        question_type=CDPQuestionType.TEXT,
        required=True,
        section="Risk Management Process",
    ),
    
    # ========== Module 4: Emissions 排放 ==========
    CDPQuestion(
        question_number="C4.1",
        module=CDPModule.EMISSIONS,
        question_text="Did you have an emissions figure that you want to report for your reporting year?",
        question_text_cn="贵组织是否有希望在报告年度报告的排放数据？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Emissions Disclosure",
    ),
    CDPQuestion(
        question_number="C4.1a",
        module=CDPModule.EMISSIONS,
        question_text="Please provide your gross global Scope 1 emissions figures",
        question_text_cn="请提供全球范围1排放总量",
        question_type=CDPQuestionType.NUMBER,
        required=True,
        parent_question="C4.1",
        condition_value="Yes",
        mapping_field="scope1_emissions",
        calculation_method="直接从scope1_emissions字段获取，单位：吨CO2e",
        section="Scope 1 Emissions",
    ),
    CDPQuestion(
        question_number="C4.1b",
        module=CDPModule.EMISSIONS,
        question_text="Please provide your gross global Scope 2 emissions figures (location-based)",
        question_text_cn="请提供全球范围2排放总量（基于位置）",
        question_type=CDPQuestionType.NUMBER,
        required=True,
        parent_question="C4.1",
        condition_value="Yes",
        mapping_field="scope2_emissions_location",
        calculation_method="直接从scope2_emissions_location字段获取",
        section="Scope 2 Emissions",
    ),
    CDPQuestion(
        question_number="C4.1c",
        module=CDPModule.EMISSIONS,
        question_text="Please provide your gross global Scope 2 emissions figures (market-based)",
        question_text_cn="请提供全球范围2排放总量（基于市场）",
        question_type=CDPQuestionType.NUMBER,
        required=False,
        parent_question="C4.1",
        condition_value="Yes",
        mapping_field="scope2_emissions_market",
        calculation_method="直接从scope2_emissions_market字段获取",
        section="Scope 2 Emissions",
    ),
    CDPQuestion(
        question_number="C4.2",
        module=CDPModule.EMISSIONS,
        question_text="Please provide your gross global Scope 3 emissions figures",
        question_text_cn="请提供全球范围3排放总量",
        question_type=CDPQuestionType.NUMBER,
        required=False,
        mapping_field="scope3_emissions",
        calculation_method="从scope3_inventory.get_total_emissions()获取或使用scope3_emissions字段",
        section="Scope 3 Emissions",
    ),
    CDPQuestion(
        question_number="C4.2a",
        module=CDPModule.EMISSIONS,
        question_text="Please break down your total gross global Scope 3 emissions by category",
        question_text_cn="请按类别分解范围3排放总量",
        question_type=CDPQuestionType.TABLE,
        required=False,
        parent_question="C4.2",
        condition_value=True,
        mapping_field="scope3_inventory",
        calculation_method="从scope3_inventory.categories提取各类别排放数据",
        section="Scope 3 Breakdown",
    ),
    CDPQuestion(
        question_number="C4.3",
        module=CDPModule.EMISSIONS,
        question_text="Please account for your organization's Scope 3 emissions, disclosing and explaining any exclusions",
        question_text_cn="请核算贵组织的范围3排放，披露并解释任何排除项",
        question_type=CDPQuestionType.TABLE,
        required=False,
        mapping_field="scope3_inventory",
        calculation_method="从scope3_inventory获取各类别覆盖率、排除项说明",
        section="Scope 3 Accounting",
    ),
    CDPQuestion(
        question_number="C4.4",
        module=CDPModule.EMISSIONS,
        question_text="Are there any sources of Scope 1, Scope 2 or Scope 3 emissions that are within your inventory but not included in your disclosure?",
        question_text_cn="范围1、2或3排放中是否有任何来源在核算范围内但未包含在披露中？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Emissions Exclusions",
    ),
    CDPQuestion(
        question_number="C4.5",
        module=CDPModule.EMISSIONS,
        question_text="Please provide your emissions performance figures",
        question_text_cn="请提供排放绩效数据",
        question_type=CDPQuestionType.TABLE,
        required=True,
        mapping_field="get_emissions_breakdown",
        calculation_method="调用metrics.get_emissions_breakdown()获取完整排放分解",
        section="Emissions Performance",
    ),
    CDPQuestion(
        question_number="C4.6",
        module=CDPModule.EMISSIONS,
        question_text="Please describe your methodology for calculating emissions",
        question_text_cn="请描述排放计算方法",
        question_type=CDPQuestionType.TEXT,
        required=True,
        section="Methodology",
    ),
    
    # ========== Module 5: Targets 目标 ==========
    CDPQuestion(
        question_number="C5.1",
        module=CDPModule.TARGETS,
        question_text="Does your organization have any emissions reduction targets?",
        question_text_cn="贵组织是否有任何减排目标？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        mapping_field="sbti_target",
        calculation_method="检查sbti_target是否存在",
        section="Emissions Targets",
    ),
    CDPQuestion(
        question_number="C5.1a",
        module=CDPModule.TARGETS,
        question_text="Please provide details of your absolute emissions target",
        question_text_cn="请提供绝对排放目标的详细信息",
        question_type=CDPQuestionType.TABLE,
        required=True,
        parent_question="C5.1",
        condition_value="Yes",
        mapping_field="sbti_target",
        calculation_method="从sbti_target提取基准年、目标年、减排率、路径等信息",
        section="Absolute Target",
    ),
    CDPQuestion(
        question_number="C5.1b",
        module=CDPModule.TARGETS,
        question_text="Please provide details of your emissions intensity target",
        question_text_cn="请提供排放强度目标的详细信息",
        question_type=CDPQuestionType.TABLE,
        required=False,
        parent_question="C5.1",
        condition_value="Yes",
        mapping_field="carbon_intensity",
        calculation_method="结合carbon_intensity历史数据和目标计算",
        section="Intensity Target",
    ),
    CDPQuestion(
        question_number="C5.2",
        module=CDPModule.TARGETS,
        question_text="Does your organization have a target for reducing your Scope 3 emissions?",
        question_text_cn="贵组织是否有减少范围3排放的目标？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        mapping_field="sbti_target.scope_coverage",
        calculation_method="检查sbti_target.scope_coverage是否包含'1+2+3'",
        section="Scope 3 Target",
    ),
    CDPQuestion(
        question_number="C5.3",
        module=CDPModule.TARGETS,
        question_text="Have you had any emissions reduction initiatives active during the reporting year?",
        question_text_cn="贵组织在报告年度是否有任何减排举措？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Emissions Reduction Initiatives",
    ),
    
    # ========== Module 6: Value Chain 价值链 ==========
    CDPQuestion(
        question_number="C6.1",
        module=CDPModule.VALUE_CHAIN,
        question_text="Do you engage with your value chain on environmental issues?",
        question_text_cn="贵组织是否在环境问题上与价值链进行互动？",
        question_type=CDPQuestionType.YES_NO,
        required=True,
        section="Value Chain Engagement",
    ),
    CDPQuestion(
        question_number="C6.1a",
        module=CDPModule.VALUE_CHAIN,
        question_text="Please describe your engagement with your suppliers on environmental issues",
        question_text_cn="请描述与供应商在环境问题上的互动",
        question_type=CDPQuestionType.TABLE,
        required=False,
        parent_question="C6.1",
        condition_value="Yes",
        section="Supplier Engagement",
    ),
    CDPQuestion(
        question_number="C6.2",
        module=CDPModule.VALUE_CHAIN,
        question_text="Please state the percentage of your suppliers by spend that you have engaged on environmental issues",
        question_text_cn="请说明按支出计算的供应商中有多大比例在环境问题上与贵组织互动",
        question_type=CDPQuestionType.PERCENTAGE,
        required=False,
        mapping_field="scope3_inventory.categories[PURCHASED_GOODS_SERVICES].coverage_percentage",
        calculation_method="从范围3类别1数据覆盖率推断",
        section="Supplier Coverage",
    ),
]

# 创建题号索引
CDP_QUESTION_INDEX = {q.question_number: q for q in CDP_QUESTIONNAIRE}


@dataclass
class ClimateRisk:
    """气候风险定义（TCFD/CDP格式）
    
    Attributes:
        risk_id: 风险ID
        risk_type: 风险类型（acute/chronic）
        risk_category: 风险类别（如"Policy","Technology","Market"等）
        description: 风险描述
        time_horizon: 时间范围（short/medium/long）
        likelihood: 可能性（1-5）
        impact_magnitude: 影响程度（1-5）
        financial_impact: 财务影响估算（百万元）
        response_strategy: 应对策略
    """
    risk_id: str
    risk_type: str  # acute / chronic
    risk_category: str  # Policy, Technology, Market, Reputation, Physical
    description: str
    time_horizon: str  # short / medium / long
    likelihood: int  # 1-5
    impact_magnitude: int  # 1-5
    financial_impact: Optional[float] = None  # 百万元
    response_strategy: str = ""
    
    def get_risk_score(self) -> int:
        """计算风险评分（1-25）"""
        return self.likelihood * self.impact_magnitude
    
    def get_risk_level(self) -> str:
        """获取风险等级"""
        score = self.get_risk_score()
        if score >= 20:
            return "High"
        elif score >= 12:
            return "Medium"
        else:
            return "Low"


@dataclass
class ClimateOpportunity:
    """气候机遇定义
    
    Attributes:
        opportunity_id: 机遇ID
        opportunity_type: 机遇类型（Resource efficiency/Energy source/Products & services/Markets/Resilience）
        description: 机遇描述
        time_horizon: 时间范围
        likelihood: 可能性（1-5）
        impact_magnitude: 影响程度（1-5）
        financial_benefit: 财务收益估算（百万元）
        realization_strategy: 实现策略
    """
    opportunity_id: str
    opportunity_type: str
    description: str
    time_horizon: str
    likelihood: int
    impact_magnitude: int
    financial_benefit: Optional[float] = None
    realization_strategy: str = ""


class CDPAutoFiler:
    """CDP自动填报器
    
    自动从ESG数据模型提取答案，生成CDP填报文件。
    """
    
    def __init__(self, metrics: Any):
        """
        Args:
            metrics: ESGMetrics对象
        """
        self.metrics = metrics
        self.answers: Dict[str, CDPAnswer] = {}
        self.risks: List[ClimateRisk] = []
        self.opportunities: List[ClimateOpportunity] = []
        
    def auto_fill(self) -> Dict[str, CDPAnswer]:
        """自动填报所有问题
        
        Returns:
            题号到答案的映射
        """
        for question in CDP_QUESTIONNAIRE:
            answer = self._extract_answer(question)
            if answer:
                self.answers[question.question_number] = answer
        
        return self.answers
    
    def _extract_answer(self, question: CDPQuestion) -> Optional[CDPAnswer]:
        """从ESGMetrics提取单个问题的答案
        
        Args:
            question: CDP问题
            
        Returns:
            CDPAnswer或None
        """
        # 检查条件题
        if question.parent_question:
            parent_answer = self.answers.get(question.parent_question)
            if not parent_answer or parent_answer.answer_value != question.condition_value:
                return None
        
        # 根据映射字段提取答案
        if question.mapping_field == "scope1_emissions":
            value = getattr(self.metrics, 'scope1_emissions', None)
            if value is not None:
                return CDPAnswer(
                    question_number=question.question_number,
                    answer_value=value,
                    data_source="ESGMetrics.scope1_emissions",
                    confidence=0.95,
                )
        
        elif question.mapping_field == "scope2_emissions_location":
            value = getattr(self.metrics, 'scope2_emissions_location', None)
            if value is not None:
                return CDPAnswer(
                    question_number=question.question_number,
                    answer_value=value,
                    data_source="ESGMetrics.scope2_emissions_location",
                    confidence=0.95,
                )
        
        elif question.mapping_field == "scope2_emissions_market":
            value = getattr(self.metrics, 'scope2_emissions_market', None)
            if value is not None:
                return CDPAnswer(
                    question_number=question.question_number,
                    answer_value=value,
                    data_source="ESGMetrics.scope2_emissions_market",
                    confidence=0.95,
                )
        
        elif question.mapping_field == "scope3_emissions":
            # 优先使用scope3_inventory
            inventory = getattr(self.metrics, 'scope3_inventory', None)
            if inventory:
                value = inventory.get_total_emissions()
                if value is not None:
                    return CDPAnswer(
                        question_number=question.question_number,
                        answer_value=value,
                        data_source="ESGMetrics.scope3_inventory",
                        confidence=inventory.get_data_quality_score() / 100,
                    )
            # 回退到scope3_emissions字段
            value = getattr(self.metrics, 'scope3_emissions', None)
            if value is not None:
                return CDPAnswer(
                    question_number=question.question_number,
                    answer_value=value,
                    data_source="ESGMetrics.scope3_emissions",
                    confidence=0.7,
                )
        
        elif question.mapping_field == "scope3_inventory":
            inventory = getattr(self.metrics, 'scope3_inventory', None)
            if inventory:
                if question.question_number == "C4.2a":
                    # 范围3分类分解
                    breakdown = {}
                    for cat, cat_data in inventory.categories.items():
                        if cat_data.emissions is not None:
                            breakdown[cat.value] = {
                                "name": cat.name,
                                "emissions_tco2e": cat_data.emissions,
                                "data_quality": cat_data.data_quality.value,
                                "coverage": cat_data.coverage_percentage,
                            }
                    return CDPAnswer(
                        question_number=question.question_number,
                        answer_value=breakdown,
                        data_source="ESGMetrics.scope3_inventory.categories",
                        confidence=inventory.get_data_quality_score() / 100,
                    )
                elif question.question_number == "C4.3":
                    # 范围3核算说明
                    exclusions = []
                    for cat, cat_data in inventory.categories.items():
                        if cat_data.exclusions:
                            exclusions.extend(cat_data.exclusions)
                    return CDPAnswer(
                        question_number=question.question_number,
                        answer_value={
                            "methodology": "GHG Protocol Scope 3 Standard",
                            "coverage_percentage": inventory.get_coverage_percentage(),
                            "exclusions": exclusions,
                            "verification_status": inventory.verification_status,
                            "verification_provider": inventory.verification_provider,
                        },
                        data_source="ESGMetrics.scope3_inventory",
                        confidence=0.85,
                    )
        
        elif question.mapping_field == "sbti_target":
            sbti = getattr(self.metrics, 'sbti_target', None)
            if sbti:
                if question.question_number == "C5.1":
                    return CDPAnswer(
                        question_number=question.question_number,
                        answer_value="Yes",
                        data_source="ESGMetrics.sbti_target",
                        confidence=1.0,
                    )
                elif question.question_number == "C5.1a":
                    return CDPAnswer(
                        question_number=question.question_number,
                        answer_value={
                            "target_type": sbti.target_type or "Absolute",
                            "baseline_year": sbti.baseline_year,
                            "target_year": sbti.target_year,
                            "baseline_emissions": sbti.baseline_emissions,
                            "target_emissions": sbti.target_emissions,
                            "reduction_rate": sbti.reduction_rate,
                            "pathway": sbti.pathway,
                            "scope": sbti.scope_coverage,
                            "sbti_status": sbti.status,
                            "validation_date": sbti.validation_date,
                        },
                        data_source="ESGMetrics.sbti_target",
                        confidence=0.95,
                    )
            else:
                if question.question_number == "C5.1":
                    return CDPAnswer(
                        question_number=question.question_number,
                        answer_value="No",
                        data_source="ESGMetrics.sbti_target is None",
                        confidence=1.0,
                    )
        
        elif question.mapping_field == "get_emissions_breakdown":
            breakdown = self.metrics.get_emissions_breakdown()
            return CDPAnswer(
                question_number=question.question_number,
                answer_value=breakdown,
                data_source="ESGMetrics.get_emissions_breakdown()",
                confidence=0.9,
            )
        
        elif question.mapping_field == "esg_committee_independence":
            value = getattr(self.metrics, 'esg_committee_independence', None)
            if value is not None and value > 0:
                return CDPAnswer(
                    question_number=question.question_number,
                    answer_value="Yes",
                    data_source="ESGMetrics.esg_committee_independence",
                    confidence=0.9,
                )
        
        # 布尔/文本类问题返回默认值
        if question.question_type == CDPQuestionType.YES_NO:
            # 对于未映射的问题，返回默认"No"
            return CDPAnswer(
                question_number=question.question_number,
                answer_value="No",
                data_source="Default",
                confidence=0.5,
                notes="需要人工核实",
            )
        
        return None
    
    def add_climate_risk(self, risk: ClimateRisk) -> None:
        """添加气候风险"""
        self.risks.append(risk)
        # 同时更新答案
        self._update_risk_opportunity_answers()
    
    def add_climate_opportunity(self, opportunity: ClimateOpportunity) -> None:
        """添加气候机遇"""
        self.opportunities.append(opportunity)
        # 同时更新答案
        self._update_risk_opportunity_answers()
    
    def _update_risk_opportunity_answers(self) -> None:
        """更新风险和机遇相关答案"""
        # C2.1 - 是否识别风险和机遇
        if self.risks or self.opportunities:
            self.answers["C2.1"] = CDPAnswer(
                question_number="C2.1",
                answer_value="Yes",
                data_source="ClimateRisk/ClimateOpportunity objects",
                confidence=0.9,
            )
        
        # C2.2 - 风险和机遇详情
        if self.risks:
            risks_data = []
            for risk in self.risks:
                risks_data.append({
                    "risk_id": risk.risk_id,
                    "risk_type": risk.risk_type,
                    "category": risk.risk_category,
                    "description": risk.description,
                    "time_horizon": risk.time_horizon,
                    "likelihood": risk.likelihood,
                    "impact": risk.impact_magnitude,
                    "risk_score": risk.get_risk_score(),
                    "risk_level": risk.get_risk_level(),
                    "financial_impact_cny_millions": risk.financial_impact,
                    "response_strategy": risk.response_strategy,
                })
            self.answers["C2.2"] = CDPAnswer(
                question_number="C2.2",
                answer_value=risks_data,
                data_source="ClimateRisk objects",
                confidence=0.85,
            )
        
        # C2.3 - 是否识别机遇
        if self.opportunities:
            self.answers["C2.3"] = CDPAnswer(
                question_number="C2.3",
                answer_value="Yes",
                data_source="ClimateOpportunity objects",
                confidence=0.9,
            )
            
            # C2.4 - 机遇详情
            opportunities_data = []
            for opp in self.opportunities:
                opportunities_data.append({
                    "opportunity_id": opp.opportunity_id,
                    "opportunity_type": opp.opportunity_type,
                    "description": opp.description,
                    "time_horizon": opp.time_horizon,
                    "likelihood": opp.likelihood,
                    "impact": opp.impact_magnitude,
                    "opportunity_score": opp.likelihood * opp.impact_magnitude,
                    "financial_benefit_cny_millions": opp.financial_benefit,
                    "realization_strategy": opp.realization_strategy,
                })
            self.answers["C2.4"] = CDPAnswer(
                question_number="C2.4",
                answer_value=opportunities_data,
                data_source="ClimateOpportunity objects",
                confidence=0.85,
            )
        
        # C3.1 - 固有气候风险
        if self.risks:
            self.answers["C3.1"] = CDPAnswer(
                question_number="C3.1",
                answer_value="Yes",
                data_source="ClimateRisk objects",
                confidence=0.9,
            )
            
            # C3.1a - 风险详情（与C2.2类似但格式略有不同）
            risks_detail = []
            for risk in self.risks:
                risks_detail.append({
                    "risk_identifier": risk.risk_id,
                    "risk_type": "Transition" if risk.risk_category in ["Policy", "Technology", "Market", "Reputation"] else "Physical",
                    "primary_climate_related_risk_driver": risk.risk_category,
                    "risk_description": risk.description,
                    "time_horizon": risk.time_horizon,
                    "likelihood": risk.likelihood,
                    "magnitude_of_impact": risk.impact_magnitude,
                    "potential_financial_impact": risk.financial_impact,
                })
            self.answers["C3.1a"] = CDPAnswer(
                question_number="C3.1a",
                answer_value=risks_detail,
                data_source="ClimateRisk objects",
                confidence=0.85,
            )
    
    def generate_json_file(self, output_path: str) -> str:
        """生成CDP JSON填报文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            生成的文件路径
        """
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "company": self.metrics.company_name,
                "reporting_year": self.metrics.year,
                "questionnaire_version": "CDP Climate Change 2024",
            },
            "answers": {
                q_num: answer.to_dict()
                for q_num, answer in self.answers.items()
            },
            "risks": [
                {
                    "risk_id": r.risk_id,
                    "risk_type": r.risk_type,
                    "category": r.risk_category,
                    "description": r.description,
                    "time_horizon": r.time_horizon,
                    "likelihood": r.likelihood,
                    "impact": r.impact_magnitude,
                    "financial_impact_cny_millions": r.financial_impact,
                    "risk_score": r.get_risk_score(),
                    "risk_level": r.get_risk_level(),
                }
                for r in self.risks
            ],
            "opportunities": [
                {
                    "opportunity_id": o.opportunity_id,
                    "opportunity_type": o.opportunity_type,
                    "description": o.description,
                    "time_horizon": o.time_horizon,
                    "likelihood": o.likelihood,
                    "impact": o.impact_magnitude,
                    "financial_benefit_cny_millions": o.financial_benefit,
                }
                for o in self.opportunities
            ],
            "statistics": {
                "total_questions": len(CDP_QUESTIONNAIRE),
                "answered_questions": len(self.answers),
                "completion_rate": len(self.answers) / len(CDP_QUESTIONNAIRE) if CDP_QUESTIONNAIRE else 0,
                "average_confidence": sum(a.confidence for a in self.answers.values()) / len(self.answers) if self.answers else 0,
            },
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def generate_excel_file(self, output_path: str) -> str:
        """生成CDP Excel填报文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            生成的文件路径
        """
        # 准备数据
        rows = []
        for question in CDP_QUESTIONNAIRE:
            answer = self.answers.get(question.question_number)
            rows.append({
                "Question Number": question.question_number,
                "Module": question.module.value,
                "Section": question.section,
                "Question (EN)": question.question_text,
                "Question (CN)": question.question_text_cn,
                "Question Type": question.question_type.value,
                "Required": "Yes" if question.required else "No",
                "Answer": json.dumps(answer.answer_value, ensure_ascii=False) if answer else "",
                "Confidence": answer.confidence if answer else "",
                "Data Source": answer.data_source if answer else "",
                "Notes": answer.notes if answer else "",
                "Mapping Field": question.mapping_field,
            })
        
        df = pd.DataFrame(rows)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 主填报表
            df.to_excel(writer, sheet_name='CDP_Answers', index=False)
            
            # 风险清单
            if self.risks:
                risks_df = pd.DataFrame([
                    {
                        "Risk ID": r.risk_id,
                        "Type": r.risk_type,
                        "Category": r.risk_category,
                        "Description": r.description,
                        "Time Horizon": r.time_horizon,
                        "Likelihood (1-5)": r.likelihood,
                        "Impact (1-5)": r.impact_magnitude,
                        "Risk Score": r.get_risk_score(),
                        "Risk Level": r.get_risk_level(),
                        "Financial Impact (CNY Millions)": r.financial_impact,
                        "Response Strategy": r.response_strategy,
                    }
                    for r in self.risks
                ])
                risks_df.to_excel(writer, sheet_name='Climate_Risks', index=False)
            
            # 机遇清单
            if self.opportunities:
                opp_df = pd.DataFrame([
                    {
                        "Opportunity ID": o.opportunity_id,
                        "Type": o.opportunity_type,
                        "Description": o.description,
                        "Time Horizon": o.time_horizon,
                        "Likelihood (1-5)": o.likelihood,
                        "Impact (1-5)": o.impact_magnitude,
                        "Opportunity Score": o.likelihood * o.impact_magnitude,
                        "Financial Benefit (CNY Millions)": o.financial_benefit,
                        "Realization Strategy": o.realization_strategy,
                    }
                    for o in self.opportunities
                ])
                opp_df.to_excel(writer, sheet_name='Climate_Opportunities', index=False)
            
            # 汇总统计
            stats_df = pd.DataFrame([
                {"Metric": "Total Questions", "Value": len(CDP_QUESTIONNAIRE)},
                {"Metric": "Answered Questions", "Value": len(self.answers)},
                {"Metric": "Completion Rate", "Value": f"{len(self.answers) / len(CDP_QUESTIONNAIRE) * 100:.1f}%"},
                {"Metric": "Average Confidence", "Value": f"{sum(a.confidence for a in self.answers.values()) / len(self.answers) * 100:.1f}%" if self.answers else "N/A"},
                {"Metric": "Climate Risks Identified", "Value": len(self.risks)},
                {"Metric": "Climate Opportunities Identified", "Value": len(self.opportunities)},
            ])
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        return output_path
    
    def get_completion_report(self) -> Dict[str, Any]:
        """获取填报完成度报告
        
        Returns:
            完成度报告
        """
        module_stats = {module: {"total": 0, "answered": 0} for module in CDPModule}
        
        for question in CDP_QUESTIONNAIRE:
            module_stats[question.module]["total"] += 1
            if question.question_number in self.answers:
                module_stats[question.module]["answered"] += 1
        
        return {
            "overall": {
                "total_questions": len(CDP_QUESTIONNAIRE),
                "answered_questions": len(self.answers),
                "completion_rate": len(self.answers) / len(CDP_QUESTIONNAIRE) if CDP_QUESTIONNAIRE else 0,
                "average_confidence": sum(a.confidence for a in self.answers.values()) / len(self.answers) if self.answers else 0,
            },
            "by_module": {
                module.value: {
                    "total": stats["total"],
                    "answered": stats["answered"],
                    "completion_rate": stats["answered"] / stats["total"] if stats["total"] > 0 else 0,
                    "weight": CDP_SCORING_WEIGHTS[module],
                }
                for module, stats in module_stats.items()
            },
            "missing_required": [
                q.question_number
                for q in CDP_QUESTIONNAIRE
                if q.required and q.question_number not in self.answers
            ],
            "low_confidence_answers": [
                {
                    "question": q_num,
                    "confidence": answer.confidence,
                }
                for q_num, answer in self.answers.items()
                if answer.confidence < 0.7
            ],
        }
    
    def predict_cdp_score(self) -> Dict[str, Any]:
        """预测CDP评级
        
        基于填报完成度和数据质量预测CDP评级。
        
        Returns:
            预测评级详情
        """
        report = self.get_completion_report()
        
        # 计算各模块得分
        module_scores = {}
        for module, stats in report["by_module"].items():
            # 基础分：完成度 * 100
            base_score = stats["completion_rate"] * 100
            
            # 质量加成：该模块答案的平均置信度
            module_answers = [
                self.answers[q.question_number]
                for q in CDP_QUESTIONNAIRE
                if q.module.value == module and q.question_number in self.answers
            ]
            avg_confidence = sum(a.confidence for a in module_answers) / len(module_answers) if module_answers else 0
            
            # 最终得分
            module_scores[module] = base_score * (0.7 + 0.3 * avg_confidence)
        
        # 加权总分
        total_score = sum(
            module_scores[module.value] * CDP_SCORING_WEIGHTS[CDPModule(module.value)]
            for module in CDPModule
        )
        
        # 确定预测等级
        if total_score >= 80:
            predicted_level = "A/A-"
        elif total_score >= 65:
            predicted_level = "B/B-"
        elif total_score >= 50:
            predicted_level = "C/C-"
        else:
            predicted_level = "D/D-"
        
        return {
            "predicted_score": total_score,
            "predicted_level": predicted_level,
            "module_scores": module_scores,
            "recommendations": self._generate_score_recommendations(report, module_scores),
        }
    
    def _generate_score_recommendations(
        self, report: Dict[str, Any], module_scores: Dict[str, float]
    ) -> List[str]:
        """生成提升CDP评分的建议
        
        Args:
            report: 完成度报告
            module_scores: 模块得分
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 检查缺失的必填题
        if report["missing_required"]:
            recommendations.append(
                f"优先完成{len(report['missing_required'])}道必填题: {', '.join(report['missing_required'][:3])}..."
            )
        
        # 检查低分模块
        for module, score in module_scores.items():
            if score < 60:
                recommendations.append(
                    f"{module}模块得分较低({score:.1f})，建议完善该模块数据"
                )
        
        # 检查范围3数据
        if "C4.2" not in self.answers or not self.answers["C4.2"].answer_value:
            recommendations.append("补充范围3排放数据可显著提升评分（权重25%）")
        
        # 检查SBTi目标
        if "C5.1" not in self.answers or self.answers["C5.1"].answer_value != "Yes":
            recommendations.append("设定SBTi验证的减排目标可获得高分（权重15%）")
        
        # 检查气候风险
        if not self.risks:
            recommendations.append("识别并披露气候相关风险（建议至少3-5项）")
        
        return recommendations


def create_cdp_filer(metrics: Any) -> CDPAutoFiler:
    """创建CDP自动填报器
    
    Args:
        metrics: ESGMetrics对象
        
    Returns:
        CDPAutoFiler实例
    """
    return CDPAutoFiler(metrics)


# 便捷函数
def quick_generate_cdp_filing(
    metrics: Any,
    output_dir: str = "./",
    file_prefix: str = "CDP_Filing"
) -> Dict[str, str]:
    """快速生成CDP填报文件
    
    Args:
        metrics: ESGMetrics对象
        output_dir: 输出目录
        file_prefix: 文件名前缀
        
    Returns:
        生成的文件路径字典
    """
    filer = CDPAutoFiler(metrics)
    filer.auto_fill()
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, f"{file_prefix}_{metrics.year}.json")
    excel_path = os.path.join(output_dir, f"{file_prefix}_{metrics.year}.xlsx")
    
    return {
        "json": filer.generate_json_file(json_path),
        "excel": filer.generate_excel_file(excel_path),
        "report": filer.get_completion_report(),
        "predicted_score": filer.predict_cdp_score(),
    }
