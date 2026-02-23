"""
白盒规则匹配框架：纯代码实现，100%可解释
ESG合规核心工具：所有专业判断由白盒规则完成，AI仅做提取
P0阶段：外置配置化规则（从config/rule_templates/esg_topic_rules.json加载）
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from src.utils.config_utils import load_topic_rules, load_match_rules
from src.utils.exception_utils import RuleMatchException


class RuleMatcher:
    """白盒规则匹配器"""
    
    def __init__(self):
        # 从外置配置文件加载规则（完全移除硬编码）
        self._load_rules_from_config()
    
    def _load_rules_from_config(self):
        """从外置JSON配置文件加载规则"""
        try:
            self.topic_config = load_topic_rules()
            self.hardcoded_topics = self.topic_config.get("topics", [])
            self.supported_industries = self.topic_config.get("supported_industries", ["新能源"])
            self.match_rules = load_match_rules()
        except Exception as e:
            raise RuleMatchException(f"规则配置加载失败: {str(e)}", original_exception=e) from e
    
    def _match_single_topic(
        self,
        text: str,
        topic: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        匹配单个议题（内部方法）
        :param text: 待匹配的文本（通常是AI提取的内容或原文片段）
        :param topic: 单个议题的规则字典
        :return: (是否匹配, 匹配结果详情)
        """
        text_lower = text.lower()
        
        # 1. 关键词粗筛
        keyword_hit = False
        for keyword in topic["keywords"]:
            if keyword.lower() in text_lower:
                keyword_hit = True
                break
        if not keyword_hit:
            return False, None
        
        # 2. 正则细筛/数值提取
        extracted_values = []
        for pattern in topic["regex_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                # 扁平化匹配结果，过滤空值
                flat_matches = [m for sublist in matches for m in sublist if m]
                extracted_values.extend(flat_matches)
        
        # 3. 返回匹配结果
        return True, {
            "topic_id": topic["id"],
            "topic_name": topic["name"],
            "priority": topic.get("priority", 99),
            "has_quantitative_data": len(extracted_values) > 0,
            "extracted_values": extracted_values[:3]  # 最多返回3个提取值
        }
    
    def match_topic(
        self,
        text: str,
        company_industry: str = "新能源",
    ) -> List[Dict[str, Any]]:
        """
        白盒规则匹配实质性议题（P0核心方法）
        :param text: 待匹配的文本（通常是AI提取的内容或原文片段）
        :param company_industry: 所属行业（仅支持配置文件中定义的行业）
        :return: 匹配到的议题列表（按优先级+量化数据排序）
        """
        try:
            if company_industry not in self.supported_industries:
                return []  # 仅支持配置文件中定义的行业
            
            matched_topics = []
            for topic in self.hardcoded_topics:
                is_matched, match_detail = self._match_single_topic(text, topic)
                if is_matched and match_detail:
                    matched_topics.append(match_detail)
            
            # 按“优先级升序 + 有量化数据优先”排序
            matched_topics.sort(
                key=lambda x: (x["priority"], not x["has_quantitative_data"], -len(x["extracted_values"]))
            )
            
            return matched_topics
        
        except Exception as e:
            raise RuleMatchException(f"议题匹配失败: {str(e)}", original_exception=e) from e
    
    def match_esg_standard(
        self,
        extracted_content: str,
        standard_type: str = "ISSB",
    ) -> List[Dict[str, Any]]:
        """
        白盒规则匹配ESG披露标准（P0预留框架，暂不实现）
        :param extracted_content: AI提取的内容
        :param standard_type: 披露标准类型
        :return: 匹配到的标准条款列表
        """
        try:
            # TODO: P1阶段再实现标准匹配，P0先返回空列表
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