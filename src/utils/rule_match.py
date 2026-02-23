"""
白盒规则匹配框架：纯代码实现，100%可解释
ESG合规核心工具：所有专业判断由白盒规则完成，AI仅做提取
注：MVP阶段先写框架，具体规则逻辑等你的行业研究成果定了再填
"""

from typing import Dict, Any, List, Optional

from src.utils.config_utils import load_topic_rules, load_match_rules
from src.utils.exception_utils import RuleMatchException


class RuleMatcher:
    """白盒规则匹配器"""
    
    def __init__(self):
        self.topic_rules = load_topic_rules()
        self.match_rules = load_match_rules()
    
    def match_topic(
        self,
        extracted_fields: List[Dict[str, Any]],
        company_industry: str = "新能源",
    ) -> Optional[str]:
        """
        白盒规则匹配实质性议题
        :param extracted_fields: AI提取的事实字段列表
        :param company_industry: 所属行业
        :return: 匹配到的实质性议题ID，未匹配到返回None
        """
        try:
            # TODO: 等你的行业研究成果定了，在这里填具体的白盒匹配逻辑
            # 示例逻辑（仅演示，需替换为真实规则）：
            # for topic in self.topic_rules["topics"]:
            #     if self._check_topic_conditions(extracted_fields, topic["conditions"]):
            #         return topic["id"]
            return None
        
        except Exception as e:
            raise RuleMatchException(f"议题匹配失败: {str(e)}", original_exception=e) from e
    
    def match_esg_standard(
        self,
        extracted_content: str,
        standard_type: str = "ISSB",
    ) -> List[Dict[str, Any]]:
        """
        白盒规则匹配ESG披露标准
        :param extracted_content: AI提取的内容
        :param standard_type: 披露标准类型
        :return: 匹配到的标准条款列表
        """
        try:
            # TODO: 等你的行业研究成果定了，在这里填具体的白盒匹配逻辑
            return []
        
        except Exception as e:
            raise RuleMatchException(f"ESG标准匹配失败: {str(e)}", original_exception=e) from e


# 全局单例
_rule_matcher: Optional[RuleMatcher] = None


def get_rule_matcher() -> RuleMatcher:
    """获取规则匹配器单例"""
    global _rule_matcher
    if not _rule_matcher:
        _rule_matcher = RuleMatcher()
    return _rule_matcher
