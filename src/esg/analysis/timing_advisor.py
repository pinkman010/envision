"""披露时机建议器

基于策略主题和类型，推荐最佳披露时机。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.esg.config import COMMUNICATION_CALENDAR


class TimingSuggestion:
    """时机建议数据类"""

    def __init__(
        self,
        event_name: str,
        event_date: str,
        audience: str,
        opportunity: str,
        preparation_advice: str,
        match_reason: str,
        relevance_score: float,
    ):
        """初始化时机建议

        Args:
            event_name: 事件名称
            event_date: 事件日期
            audience: 目标受众
            opportunity: 披露机会描述
            preparation_advice: 准备建议
            match_reason: 匹配原因
            relevance_score: 相关度分数(0-1)
        """
        self.event_name = event_name
        self.event_date = event_date
        self.audience = audience
        self.opportunity = opportunity
        self.preparation_advice = preparation_advice
        self.match_reason = match_reason
        self.relevance_score = relevance_score

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_name": self.event_name,
            "event_date": self.event_date,
            "audience": self.audience,
            "opportunity": self.opportunity,
            "preparation_advice": self.preparation_advice,
            "match_reason": self.match_reason,
            "relevance_score": self.relevance_score,
        }


class TimingAdvisor:
    """ESG披露时机建议器

    基于策略主题和类型，从通信日历中匹配最佳披露时机。

    Attributes:
        calendar: 通信日历事件列表
    """

    # 主题关键词映射
    TOPIC_KEYWORDS = {
        "carbon": ["carbon", "climate", "emission", "温室气体", "碳排放", "气候"],
        "renewable": ["renewable", "energy", "green", "可再生能源", "绿电", "清洁能源"],
        "governance": ["governance", "board", "治理", "董事会", "管理"],
        "social": ["social", "employee", "diversity", "员工", "社会", "多元化"],
        "disclosure": ["disclosure", "report", "披露", "报告"],
        "ethics": ["ethics", "compliance", "道德", "合规", "反腐败"],
    }

    def __init__(self):
        """初始化时机建议器"""
        self.calendar = COMMUNICATION_CALENDAR

    def suggest_timing(
        self, strategy_topic: str, strategy_type: str, current_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """建议最佳披露时机

        基于规则匹配：
        - 如果strategy_type包含"carbon"/"climate"→匹配COP相关事件
        - 如果包含"governance"/"board"→匹配年报季

        Args:
            strategy_topic: 策略主题
            strategy_type: 策略类型
            current_date: 当前日期（可选，默认为今天）

        Returns:
            最近3个匹配事件及推荐理由的列表
        """
        if current_date is None:
            current_date = datetime.now()

        # 合并策略主题和类型用于匹配
        search_text = f"{strategy_topic} {strategy_type}".lower()

        # 确定匹配的主题类别
        matched_categories = self._identify_categories(search_text)

        # 匹配事件并计算相关度
        matched_events = []
        for event in self.calendar:
            relevance = self._calculate_relevance(event, matched_categories, search_text)
            if relevance > 0:
                matched_events.append(
                    {
                        "event": event,
                        "relevance": relevance,
                        "match_reason": self._generate_match_reason(event, matched_categories),
                    }
                )

        # 按相关度排序，取前3个
        matched_events.sort(key=lambda x: x["relevance"], reverse=True)
        top_events = matched_events[:3]

        # 构建建议列表
        suggestions = []
        for item in top_events:
            event = item["event"]
            suggestion = TimingSuggestion(
                event_name=event["event_name"],
                event_date=event["date"],
                audience=event["audience"],
                opportunity=event["opportunity"],
                preparation_advice=event["preparation_advice"],
                match_reason=item["match_reason"],
                relevance_score=item["relevance"],
            )
            suggestions.append(suggestion.to_dict())

        return suggestions

    def _identify_categories(self, search_text: str) -> List[str]:
        """识别策略所属的主题类别"""
        categories = []
        for category, keywords in self.TOPIC_KEYWORDS.items():
            if any(keyword in search_text for keyword in keywords):
                categories.append(category)
        return categories

    def _calculate_relevance(
        self, event: Dict[str, Any], matched_categories: List[str], search_text: str
    ) -> float:
        """计算事件与策略的相关度分数"""
        relevance = 0.0

        # 1. 基于主题类别的匹配
        suitable_topics = event.get("suitable_topics", [])
        for category in matched_categories:
            category_keywords = self.TOPIC_KEYWORDS.get(category, [])
            for topic in suitable_topics:
                if any(kw in topic.lower() for kw in category_keywords):
                    relevance += 0.3

        # 2. 直接文本匹配
        event_text = f"{event['event_name']} {event['opportunity']}".lower()
        if any(word in event_text for word in search_text.split()):
            relevance += 0.2

        # 3. 特殊规则匹配
        if "carbon" in matched_categories or "climate" in search_text:
            if "COP" in event["event_name"]:
                relevance += 0.4

        if "governance" in matched_categories or "board" in search_text:
            if "年报" in event["event_name"] or "财报" in event["event_name"]:
                relevance += 0.4

        return min(relevance, 1.0)

    def _generate_match_reason(self, event: Dict[str, Any], matched_categories: List[str]) -> str:
        """生成匹配原因说明"""
        reasons = []

        if "carbon" in matched_categories or "climate" in matched_categories:
            if "COP" in event["event_name"]:
                reasons.append("气候相关议题与COP大会高度契合")

        if "governance" in matched_categories:
            if "年报" in event["event_name"] or "财报" in event["event_name"]:
                reasons.append("治理议题适合在年报期披露")

        if not reasons:
            suitable_topics = event.get("suitable_topics", [])
            if suitable_topics:
                reasons.append(f"议题与{suitable_topics[0]}相关")

        return "；".join(reasons) if reasons else "议题与事件主题匹配"

    def get_all_events(self) -> List[Dict[str, Any]]:
        """获取所有通信日历事件"""
        return self.calendar

    def get_events_by_month(self, month: str) -> List[Dict[str, Any]]:
        """获取指定月份的所有事件

        Args:
            month: 月份格式 "YYYY-MM"

        Returns:
            该月份的事件列表
        """
        return [event for event in self.calendar if event["date"].startswith(month)]

    def detect_conflicts(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测披露时机冲突

        如果两个策略建议同一月份，显示资源冲突提醒。

        Args:
            suggestions: 时机建议列表（多个策略的建议）

        Returns:
            冲突列表，每个冲突包含月份和冲突事件数
        """
        # 统计每个月份的建议数量
        month_counts = {}
        for suggestion in suggestions:
            month = suggestion.get("event_date", "")[:7]  # 提取 YYYY-MM
            if month:
                month_counts[month] = month_counts.get(month, 0) + 1

        # 找出有冲突的月份（超过1个建议）
        conflicts = []
        for month, count in month_counts.items():
            if count > 1:
                conflicts.append(
                    {
                        "month": month,
                        "count": count,
                        "message": f"⚠️ 资源冲突提醒：{month}已有{count}项披露计划",
                    }
                )

        return conflicts

    def format_suggestion_display(self, suggestion: Dict[str, Any]) -> str:
        """格式化建议显示文本"""
        return (
            f"建议在【{suggestion['event_name']}】（{suggestion['event_date']}）期间披露，"
            f"受众：【{suggestion['audience']}】，"
            f"机会：【{suggestion['opportunity']}】"
        )


# 全局实例
timing_advisor = TimingAdvisor()
