"""规则引擎"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Rule:
    """规则定义"""
    id: str
    name: str
    condition: str
    action: str
    priority: int = 1
    explanation: str = ""


class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        self.rules = self._load_default_rules()
    
    def _load_default_rules(self) -> List[Rule]:
        """加载默认规则库"""
        return [
            Rule(
                id="R001",
                name="碳排放预警",
                condition="carbon_emissions > 50000",
                action="ESG评级降一档 + 建议制定碳中和计划",
                priority=1,
                explanation="碳排放超过5万吨属于高排放企业，需重点关注"
            ),
            Rule(
                id="R002",
                name="可再生能源激励",
                condition="renewable_energy_ratio > 50",
                action="ESG评级加分 + 展示最佳实践",
                priority=2,
                explanation="可再生能源占比超过50%，表现优秀"
            ),
            Rule(
                id="R003",
                name="治理结构缺陷",
                condition="board_independence_ratio < 30",
                action="标记治理风险 + 建议提升独立董事比例",
                priority=1,
                explanation="独立董事比例低于30%，治理结构存在缺陷"
            ),
            Rule(
                id="R004",
                name="员工多元化不足",
                condition="female_ratio < 0.3",
                action="建议制定多元化招聘政策",
                priority=3,
                explanation="女性员工比例低于30%，多元化程度不足"
            ),
            Rule(
                id="R005",
                name="安全事故高发",
                condition="safety_incidents > 10",
                action="高风险标记 + 要求安全整改报告",
                priority=1,
                explanation="年度安全事故超过10起，安全管理存在严重问题"
            )
        ]
    
    def evaluate(self, metrics: Any) -> List[Dict]:
        """评估规则"""
        triggered = []
        
        for rule in sorted(self.rules, key=lambda r: r.priority):
            if self._check_condition(rule.condition, metrics):
                triggered.append({
                    'rule_id': rule.id,
                    'rule_name': rule.name,
                    'action': rule.action,
                    'priority': rule.priority,
                    'explanation': rule.explanation
                })
        
        return triggered
    
    def _check_condition(self, condition: str, metrics: Any) -> bool:
        """检查条件"""
        try:
            parts = condition.split()
            if len(parts) != 3:
                return False
            
            field, op, value = parts
            field_value = getattr(metrics, field, None)
            
            if field_value is None:
                return False
            
            value = float(value)
            
            if op == '>':
                return field_value > value
            elif op == '<':
                return field_value < value
            elif op == '>=':
                return field_value >= value
            elif op == '<=':
                return field_value <= value
            elif op == '==':
                return field_value == value
            
            return False
        except:
            return False