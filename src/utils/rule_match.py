"""
白盒规则匹配框架：纯代码实现，100%可解释
ESG合规核心工具：所有专业判断由白盒规则完成，AI仅做提取
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from src.utils.config_utils import load_topic_rules, load_match_rules
from src.utils.exception_utils import RuleMatchException


class RuleMatcher:
    """白盒规则匹配器"""
    
    def __init__(self):
        self._load_rules_from_config()
    
    def _load_rules_from_config(self):
        """从外置JSON配置文件加载规则"""
        try:
            self.topic_config = load_topic_rules()
            self.hardcoded_topics = self.topic_config.get("topics", [])
            self.supported_industries = self.topic_config.get("supported_industries", ["新能源"])
            self.match_rules = load_match_rules()
        except Exception as e:
            raise RuleMatchException(f"规则配置加载失败: {str(e)}") from e
    
    def _match_single_topic(
        self,
        text: str,
        topic: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        匹配单个议题
        :param text: 待匹配的文本
        :param topic: 议题规则字典
        :return: (是否匹配, 匹配结果详情)
        """
        text_lower = text.lower()
        
        keyword_hit = False
        for keyword in topic["keywords"]:
            if keyword.lower() in text_lower:
                keyword_hit = True
                break
        if not keyword_hit:
            return False, None
        
        extracted_values = []
        for pattern in topic["regex_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                # 处理单个或多个捕获组的情况
                for match in matches:
                    if isinstance(match, tuple):
                        # 多个捕获组，展平并过滤空值
                        extracted_values.extend([m for m in match if m])
                    else:
                        # 单个捕获组，直接使用
                        extracted_values.append(match)
        
        return True, {
            "topic_id": topic["id"],
            "topic_name": topic["name"],
            "priority": topic.get("priority", 99),
            "has_quantitative_data": len(extracted_values) > 0,
            "extracted_values": extracted_values[:3]
        }
    
    def match_topic(
        self,
        text: str,
        company_industry: str = "新能源",
    ) -> List[Dict[str, Any]]:
        """
        白盒规则匹配实质性议题
        :param text: 待匹配的文本
        :param company_industry: 所属行业
        :return: 匹配到的议题列表
        """
        try:
            if company_industry not in self.supported_industries:
                return []
            
            matched_topics = []
            for topic in self.hardcoded_topics:
                is_matched, match_detail = self._match_single_topic(text, topic)
                if is_matched and match_detail:
                    matched_topics.append(match_detail)
            
            matched_topics.sort(
                key=lambda x: (x["priority"], not x["has_quantitative_data"], -len(x["extracted_values"]))
            )
            
            return matched_topics
        
        except Exception as e:
            raise RuleMatchException(f"议题匹配失败: {str(e)}") from e
    
    def match_esg_standard(
        self,
        extracted_content: str,
        standard_type: str = "ISSB",
    ) -> List[Dict[str, Any]]:
        """
        白盒规则匹配ESG披露标准（预留接口，待后续实现）
        
        TODO[P1]: 实现ESG标准条款匹配逻辑
        - 支持标准：ISSB、GRI、SASB、TCFD 等主流披露框架
        - 匹配逻辑：基于规则的白盒匹配（非AI黑盒）
        - 输入：AI提取的结构化ESG内容
        - 输出：匹配到的标准条款列表（条款编号、要求描述、符合度评分）
        
        Issue: 当前为预留空实现，返回空列表
        预计实现时间：v1.5 版本
        
        :param extracted_content: AI提取的内容
        :param standard_type: 披露标准类型
        :return: 匹配到的标准条款列表（当前为空列表）
        """
        # TODO[P1]: 待实现ESG标准条款匹配逻辑
        return []


_rule_matcher: Optional[RuleMatcher] = None


def get_rule_matcher() -> RuleMatcher:
    """获取规则匹配器单例"""
    global _rule_matcher
    if not _rule_matcher:
        _rule_matcher = RuleMatcher()
    return _rule_matcher
