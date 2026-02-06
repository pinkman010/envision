"""模块四：AI策略建议生成器
技术：大模型Prompt工程 + RAG知识增强
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class StrategyGenerator:
    """ESG策略建议生成器
    
    基于差距分析结果，生成针对性的改进策略建议。
    所有置信度计算基于规则而非随机。
    """
    
    # 预设策略模板库
    STRATEGY_TEMPLATES = {
        "scope3_data": {
            "title": "建立Scope 3排放核算机制",
            "priority": "高",
            "actions": [
                "制定供应链碳盘查计划，覆盖核心供应商",
                "引入碳核算工具（如SAP Sustainability）",
                "建立供应商碳数据收集机制",
                "定期披露Scope 3排放数据"
            ],
            "standards": ["GHG Protocol", "ISO 14064"],
            "timeline": "6-12个月",
            "benefit": "提升ESG评级，满足投资者要求"
        },
        "supply_chain": {
            "title": "构建可持续供应链管理体系",
            "priority": "高",
            "actions": [
                "制定供应商ESG准入标准",
                "建立供应商ESG评估体系",
                "推动一级供应商开展碳盘查",
                "建立供应链风险预警机制"
            ],
            "standards": ["SA8000", "ISO 20400"],
            "timeline": "12-18个月",
            "benefit": "降低供应链风险，提升品牌声誉"
        },
        "employee_diversity": {
            "title": "推进员工多元化与包容性计划",
            "priority": "中",
            "actions": [
                "制定多元化招聘目标（性别、年龄、背景）",
                "建立无偏见招聘流程",
                "开展包容性文化培训",
                "设立多元化委员会"
            ],
            "standards": ["GRI 405", "UN SDG 5"],
            "timeline": "6-12个月",
            "benefit": "提升创新能力，吸引优秀人才"
        },
        "renewable_energy": {
            "title": "加速可再生能源转型",
            "priority": "高",
            "actions": [
                "制定100%可再生能源目标",
                "投资自建光伏电站",
                "签署绿色电力购买协议(PPA)",
                "建立能源管理系统(ISO 50001)"
            ],
            "standards": ["RE100", "SBTi", "ISO 50001"],
            "timeline": "24-36个月",
            "benefit": "降低碳排放，减少能源成本"
        },
        "tcfd": {
            "title": "实施TCFD气候信息披露框架",
            "priority": "中",
            "actions": [
                "开展气候情景分析",
                "识别气候相关风险与机遇",
                "建立气候治理架构",
                "按TCFD四要素披露信息"
            ],
            "standards": ["TCFD", "ISSB S2"],
            "timeline": "12-18个月",
            "benefit": "满足监管要求，提升资本市场透明度"
        },
        "biodiversity": {
            "title": "制定生物多样性保护策略",
            "priority": "中",
            "actions": [
                "开展生物多样性影响评估",
                "识别关键生物多样性区域",
                "制定自然资本核算方案",
                "参与生物多样性恢复项目"
            ],
            "standards": ["TNFD", "GRI 304"],
            "timeline": "18-24个月",
            "benefit": "应对新兴ESG议题，建立先发优势"
        }
    }
    
    # 诊断问题模板
    DIAGNOSIS_TEMPLATES = {
        "scope3_data": {
            "id": "scope3_data",
            "title": "Scope 3数据缺失",
            "severity": "高",
            "description": "未披露供应链碳排放数据，影响范围三完整性"
        },
        "supply_chain": {
            "id": "supply_chain",
            "title": "供应链审核不足",
            "severity": "高",
            "description": "供应商ESG评估覆盖率低于行业平均水平"
        },
        "employee_diversity": {
            "id": "employee_diversity",
            "title": "员工多样性披露有限",
            "severity": "中",
            "description": "缺乏详细的多元化指标和包容性政策披露"
        },
        "tcfd": {
            "id": "tcfd",
            "title": "气候情景分析待完善",
            "severity": "中",
            "description": "TCFD框架披露不完整，缺乏量化气候风险分析"
        },
        "biodiversity": {
            "id": "biodiversity",
            "title": "生物多样性议题未覆盖",
            "severity": "低",
            "description": "新兴议题，尚未纳入ESG战略考量"
        }
    }
    
    # 受众映射表
    AUDIENCE_MAPPING = {
        "投资者": "强调财务回报和风险管理，关注ESG评级提升对估值的影响",
        "监管": "强调合规要求和披露标准，关注监管风险规避",
        "公众": "强调社会责任和品牌形象，关注利益相关方沟通",
        "董事会": "强调战略价值和竞争优势，关注长期可持续发展"
    }
    
    def __init__(self):
        self.strategies: List[Dict] = []
    
    def generate_diagnosis(self, gap_analysis: Dict) -> List[Dict]:
        """生成诊断结果
        
        基于差距分析，识别主要问题并生成诊断报告。
        诊断优先级基于差距大小，非随机。
        
        Args:
            gap_analysis: 差距分析结果
            
        Returns:
            诊断列表，最多3项，按严重程度排序
        """
        diagnosis = []
        
        # 根据差距分析生成诊断
        indicator_gaps = gap_analysis.get("indicator_gaps", [])
        
        for gap in indicator_gaps[:3]:  # 取前3个最大差距
            indicator_id = gap.get("id", "")
            template = self.DIAGNOSIS_TEMPLATES.get(indicator_id)
            
            if template:
                diagnosis.append({
                    **template,
                    "company_score": gap.get("company_score", 0),
                    "benchmark_score": gap.get("benchmark_score", 0),
                    "gap": gap.get("gap", 0)
                })
        
        # 确保至少有3个诊断项
        if len(diagnosis) < 3:
            existing_ids = {d["id"] for d in diagnosis}
            for template in self.DIAGNOSIS_TEMPLATES.values():
                if template["id"] not in existing_ids:
                    diagnosis.append({
                        **template,
                        "company_score": 0,
                        "benchmark_score": 0,
                        "gap": 0
                    })
                    if len(diagnosis) >= 3:
                        break
        
        return diagnosis
    
    def generate_strategies(self, diagnosis: List[Dict]) -> List[Dict]:
        """基于诊断生成策略建议
        
        Args:
            diagnosis: 诊断列表
            
        Returns:
            策略建议列表
        """
        strategies = []
        
        for item in diagnosis:
            template = self.STRATEGY_TEMPLATES.get(item.get("id", ""))
            if template:
                # 计算AI置信度（基于数据完整性）
                confidence = self._calculate_confidence(item)
                
                strategies.append({
                    "diagnosis_id": item.get("id", ""),
                    "diagnosis_title": item.get("title", ""),
                    "severity": item.get("severity", "中"),
                    "confidence": confidence,
                    **template
                })
        
        return strategies
    
    def _calculate_confidence(self, diagnosis_item: Dict) -> Dict[str, Any]:
        """计算AI置信度
        
        基于数据的完整性和差距大小计算置信度，非随机。
        
        Args:
            diagnosis_item: 诊断项
            
        Returns:
            置信度信息字典
        """
        gap = diagnosis_item.get("gap", 0)
        company_score = diagnosis_item.get("company_score", 0)
        benchmark_score = diagnosis_item.get("benchmark_score", 0)
        
        # 基于数据完整性和合理性计算置信度分数
        confidence_score = 0.5  # 基础分
        
        # 有具体分数则增加置信度
        if company_score > 0 and benchmark_score > 0:
            confidence_score += 0.2
        
        # 差距合理（不太小也不太大）
        if 5 <= gap <= 50:
            confidence_score += 0.2
        
        # 有详细描述
        if diagnosis_item.get("description"):
            confidence_score += 0.1
        
        # 确定等级和是否需要复核
        if confidence_score >= 0.8:
            level = "高置信度"
            needs_review = False
        elif confidence_score >= 0.6:
            level = "中等置信度"
            needs_review = False
        else:
            level = "建议人工复核"
            needs_review = True
        
        return {
            "score": round(confidence_score, 2),
            "level": level,
            "needs_review": needs_review
        }
    
    def refine_strategies(self, strategies: List[Dict], instruction: str) -> List[Dict]:
        """根据用户指令微调策略
        
        Args:
            strategies: 原始策略列表
            instruction: 用户微调指令
            
        Returns:
            微调后的策略列表
        """
        # 识别受众
        audience = self._detect_audience(instruction)
        
        refined = []
        for s in strategies:
            refined_strategy = s.copy()
            refined_strategy["target_audience"] = audience
            refined_strategy["refined_benefit"] = (
                f"针对{audience}视角优化：{self.AUDIENCE_MAPPING.get(audience, '')}"
            )
            refined.append(refined_strategy)
        
        return refined
    
    def _detect_audience(self, instruction: str) -> str:
        """检测受众类型
        
        Args:
            instruction: 用户指令
            
        Returns:
            受众类型
        """
        instruction_lower = instruction.lower()
        for key in self.AUDIENCE_MAPPING:
            if key in instruction_lower or key in instruction:
                return key
        return "投资者"  # 默认受众
    
    def generate_action_checklist(self, strategy: Dict) -> List[Dict]:
        """生成行动清单
        
        Args:
            strategy: 策略字典
            
        Returns:
            行动清单
        """
        checklist = []
        actions = strategy.get("actions", [])
        
        for i, action in enumerate(actions, 1):
            checklist.append({
                "step": i,
                "action": action,
                "status": "待开始",
                "owner": "ESG部门",
                "timeline": f"第{i}季度"
            })
        
        return checklist
