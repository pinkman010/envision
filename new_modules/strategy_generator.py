# -*- coding: utf-8 -*-
"""
模块四：AI策略建议生成器
技术：调用本地大模型 + RAG增强
"""
import json
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class StrategyItem:
    """策略建议项"""
    id: str
    title: str
    description: str
    action_steps: List[str]
    reference_standards: List[str]
    priority: str  # '高', '中', '低'
    timeline: str  # '短期', '中期', '长期'
    responsible_dept: str
    expected_outcome: str


class StrategyGenerator:
    """ESG策略生成器"""
    
    def __init__(self):
        # 预设策略模板库
        self.strategy_templates = {
            'Scope 3数据': [
                StrategyItem(
                    id='S3-001',
                    title='建立供应商碳盘查机制',
                    description='建立覆盖核心供应商的碳排放数据收集体系，实现Scope 3排放的可测量、可报告、可验证。',
                    action_steps=[
                        '识别核心供应商名单（采购额占比前80%）',
                        '制定供应商碳盘查问卷和技术规范',
                        '建立供应商碳数据管理系统',
                        '开展供应商培训和能力建设',
                        '年度审核和数据质量验证'
                    ],
                    reference_standards=['GHG Protocol', 'ISO 14064-1', 'SBTi'],
                    priority='高',
                    timeline='中期',
                    responsible_dept='供应链管理部 + ESG部',
                    expected_outcome='核心供应商碳数据覆盖率80%，数据质量达到CDP披露要求'
                ),
                StrategyItem(
                    id='S3-002',
                    title='推动供应链绿色转型',
                    description='通过绿色采购政策和激励机制，推动供应商制定减排目标和行动计划。',
                    action_steps=[
                        '修订采购政策，纳入ESG评价权重',
                        '建立供应商ESG评级体系',
                        '与头部供应商签署绿色供应链协议',
                        '提供技术支持和最佳实践分享',
                        '设立供应商绿色创新奖励基金'
                    ],
                    reference_standards=['供应商道德准则', '绿色供应链标准'],
                    priority='高',
                    timeline='长期',
                    responsible_dept='采购部',
                    expected_outcome='50%核心供应商设定科学碳目标'
                )
            ],
            '供应链审核': [
                StrategyItem(
                    id='SC-001',
                    title='建立全供应链社会责任审核体系',
                    description='构建覆盖Tier 1和Tier 2供应商的社会责任审核机制，确保劳工权益和人权保护。',
                    action_steps=[
                        '绘制完整供应链图谱（至少到二级供应商）',
                        '制定供应商行为准则（Code of Conduct）',
                        '建立第三方审核机制（如RBA、Sedex）',
                        '高风险供应商重点审核和整改跟踪',
                        '建立申诉和举报机制'
                    ],
                    reference_standards=['RBA标准', 'SA8000', 'UN Guiding Principles'],
                    priority='高',
                    timeline='中期',
                    responsible_dept='供应链管理部',
                    expected_outcome='高风险供应商审核覆盖率100%，重大违规事件0起'
                )
            ],
            '利益相关方沟通': [
                StrategyItem(
                    id='ST-001',
                    title='构建利益相关方参与机制',
                    description='建立系统化的利益相关方识别、沟通和反馈机制，提升ESG决策的包容性和透明度。',
                    action_steps=[
                        '开展利益相关方重要性评估（Materiality Assessment）',
                        '建立多方利益相关方咨询委员会',
                        '季度投资者沟通会（ESG专题）',
                        '年度社区开放日活动',
                        '建立线上反馈平台'
                    ],
                    reference_standards=['GRI标准', 'AA1000SES', 'ISO 26000'],
                    priority='中',
                    timeline='短期',
                    responsible_dept='ESG部 + 投资者关系部',
                    expected_outcome='利益相关方满意度提升20%，ESG评级沟通效率提升'
                )
            ],
            'ESG报告质量': [
                StrategyItem(
                    id='RP-001',
                    title='提升ESG报告披露深度和可比性',
                    description='对标国际最佳实践，提升ESG报告的数据质量、披露深度和第三方鉴证水平。',
                    action_steps=[
                        '对标SASB、TCFD标准完善披露框架',
                        '引入ESG数据管理系统，提升数据自动化程度',
                        '开展温室气体排放第三方核证',
                        '增加ESG报告的定量指标和同比数据',
                        '聘请专业机构进行报告质量审阅'
                    ],
                    reference_standards=['GRI Standards', 'SASB', 'TCFD', 'ISSB'],
                    priority='中',
                    timeline='短期',
                    responsible_dept='ESG部 + 财务部',
                    expected_outcome='ESG报告评级从B级提升至A级'
                )
            ]
        }
        
        # 通用改进策略
        self.general_strategies = [
            StrategyItem(
                id='GEN-001',
                title='建立ESG数据治理体系',
                description='构建统一的ESG数据收集、验证和报告流程，确保数据质量和一致性。',
                action_steps=[
                    '制定ESG数据管理政策和流程',
                    '部署ESG数据管理系统',
                    '建立跨部门数据协调机制',
                    '开展数据质量培训和审核'
                ],
                reference_standards=['ISO 14001', 'ISO 45001'],
                priority='高',
                timeline='中期',
                responsible_dept='ESG部 + IT部',
                expected_outcome='ESG数据收集效率提升50%，错误率降低80%'
            ),
            StrategyItem(
                id='GEN-002',
                title='开展ESG内部能力建设',
                description='通过培训和意识提升，将ESG理念融入业务各环节。',
                action_steps=[
                    '制定ESG培训年度计划',
                    '高层管理者ESG战略培训',
                    '业务部门ESG融入工作坊',
                    'ESG最佳实践内部分享'
                ],
                reference_standards=['UNGC', 'UN SDGs'],
                priority='中',
                timeline='短期',
                responsible_dept='人力资源部 + ESG部',
                expected_outcome='员工ESG意识调研得分提升30%'
            )
        ]
    
    def generate_strategies(self, gap_analysis: Dict, max_items: int = 5) -> List[StrategyItem]:
        """
        基于差距分析生成策略建议
        
        Args:
            gap_analysis: 模块三的差距分析结果
            max_items: 最多返回几条策略
        
        Returns:
            策略建议列表
        """
        strategies = []
        
        # 优先处理短板指标
        for action in gap_analysis.get('priority_actions', []):
            indicator = action['indicator']
            if indicator in self.strategy_templates:
                strategies.extend(self.strategy_templates[indicator])
        
        # 补充通用策略
        if len(strategies) < max_items:
            strategies.extend(self.general_strategies[:max_items - len(strategies)])
        
        # 去重并按优先级排序
        seen_ids = set()
        unique_strategies = []
        for s in strategies:
            if s.id not in seen_ids:
                seen_ids.add(s.id)
                unique_strategies.append(s)
        
        priority_order = {'高': 0, '中': 1, '低': 2}
        unique_strategies.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return unique_strategies[:max_items]
    
    def generate_llm_prompt(self, gap_analysis: Dict, perspective: str = '投资者') -> str:
        """
        生成给大模型的Prompt
        
        Args:
            gap_analysis: 差距分析结果
            perspective: 目标读者视角
        
        Returns:
            Prompt文本
        """
        weaknesses = gap_analysis.get('weaknesses', [])
        weakness_text = '\n'.join([f"- {ind} (差距{gap}分)" for ind, gap in weaknesses[:3]])
        
        prompt = f"""作为ESG咨询专家，请为远景能源制定ESG改进策略。

【公司背景】
- 行业：新能源装备制造（风电、储能）
- 当前ESG得分：{gap_analysis.get('yuanjing_score')}分
- 行业平均：{gap_analysis.get('benchmark_score')}分

【主要短板】
{weakness_text}

【目标读者】{perspective}

请生成3-5条具体、可执行的建议，每条建议包括：
1. 标题
2. 具体行动步骤
3. 参考标准
4. 预期效果
5. 负责部门

请用中文回答，语气专业且适合{perspective}阅读。"""
        
        return prompt
    
    def format_strategy_for_display(self, strategy: StrategyItem) -> Dict:
        """格式化策略用于前端展示"""
        return {
            'id': strategy.id,
            'title': strategy.title,
            'description': strategy.description,
            'priority': strategy.priority,
            'timeline': strategy.timeline,
            'responsible': strategy.responsible_dept,
            'steps': strategy.action_steps,
            'standards': strategy.reference_standards,
            'outcome': strategy.expected_outcome,
            'expanded': False  # UI状态
        }
    
    def get_implementation_roadmap(self, strategies: List[StrategyItem]) -> Dict:
        """
        生成实施路线图
        """
        roadmap = {
            '短期(0-6个月)': [],
            '中期(6-18个月)': [],
            '长期(18个月+)': []
        }
        
        for s in strategies:
            if s.timeline in roadmap:
                roadmap[s.timeline].append(s.title)
        
        return roadmap
    
    def generate_checklist(self, strategies: List[StrategyItem]) -> List[Dict]:
        """
        生成任务检查表
        """
        checklist = []
        
        for s in strategies:
            for i, step in enumerate(s.action_steps, 1):
                checklist.append({
                    'strategy_id': s.id,
                    'strategy_title': s.title,
                    'step_number': i,
                    'step_content': step,
                    'completed': False,
                    'priority': s.priority
                })
        
        # 按优先级排序
        priority_order = {'高': 0, '中': 1, '低': 2}
        checklist.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return checklist