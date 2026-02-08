"""实质性议题矩阵分析器

用于评估和管理ESG实质性议题的双重重要性（财务重要性+影响重要性）。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.esg.config import DEFAULT_MATERIALITY_SCORES, ESG_COLORS


@dataclass
class MaterialityTopic:
    """实质性议题数据类"""

    topic_id: str
    name: str
    dimension: str  # E/S/G
    description: str
    financial_score: int  # 0-10 财务重要性
    impact_score: int  # 0-10 影响重要性
    heat_score: float = 0.0  # 议题热度

    def get_quadrant(self) -> str:
        """根据坐标确定象限"""
        if self.financial_score >= 5 and self.impact_score >= 5:
            return "high_materiality"
        elif self.financial_score < 5 and self.impact_score >= 5:
            return "impact_driven"
        elif self.financial_score >= 5 and self.impact_score < 5:
            return "financial_driven"
        else:
            return "low_priority"

    def get_priority(self) -> str:
        """根据双重要性计算优先级"""
        high_count = sum([self.financial_score >= 7, self.impact_score >= 7])
        if high_count == 2:
            return "高"
        elif high_count == 1:
            return "中"
        else:
            return "低"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "dimension": self.dimension,
            "description": self.description,
            "financial_score": self.financial_score,
            "impact_score": self.impact_score,
            "heat_score": self.heat_score,
            "quadrant": self.get_quadrant(),
            "priority": self.get_priority(),
        }


class MaterialityMatrix:
    """实质性议题矩阵

    管理ESG实质性议题的双重重要性评估。

    Attributes:
        topics: 议题列表
        default_scores: 默认评分配置
    """

    # 象限标签映射
    QUADRANT_LABELS = {
        "high_materiality": "高度实质性-必须披露",
        "impact_driven": "影响驱动-合规披露",
        "financial_driven": "财务驱动-风险披露",
        "low_priority": "低优先级-自愿披露",
    }

    # 象限颜色
    QUADRANT_COLORS = {
        "high_materiality": "#ff4d4f",  # 红色 - 高度重要
        "impact_driven": "#1890ff",  # 蓝色 - 影响驱动
        "financial_driven": "#faad14",  # 黄色 - 财务驱动
        "low_priority": "#52c41a",  # 绿色 - 低优先级
    }

    def __init__(self, custom_scores: Optional[Dict] = None):
        """初始化实质性议题矩阵

        Args:
            custom_scores: 自定义评分配置，默认使用 DEFAULT_MATERIALITY_SCORES
        """
        self.default_scores = custom_scores or DEFAULT_MATERIALITY_SCORES
        self.topics: Dict[str, MaterialityTopic] = {}
        self._initialize_topics()

    def _initialize_topics(self) -> None:
        """初始化议题列表"""
        for topic_id, config in self.default_scores.items():
            self.topics[topic_id] = MaterialityTopic(
                topic_id=topic_id,
                name=config.get("name", topic_id),
                dimension=config.get("dimension", "E"),
                description=config.get("description", ""),
                financial_score=config.get("financial", 5),
                impact_score=config.get("impact", 5),
                heat_score=config.get("heat_score", 50.0),
            )

    def get_topic_position(self, topic_id: str) -> Tuple[int, int]:
        """获取议题在矩阵中的坐标位置

        Args:
            topic_id: 议题ID

        Returns:
            (财务重要性, 影响重要性) 元组
        """
        topic = self.topics.get(topic_id)
        if topic:
            return (topic.financial_score, topic.impact_score)
        return (5, 5)  # 默认居中

    def update_topic_scores(
        self, topic_id: str, financial: Optional[int] = None, impact: Optional[int] = None
    ) -> None:
        """更新议题评分

        Args:
            topic_id: 议题ID
            financial: 财务重要性评分 (0-10)
            impact: 影响重要性评分 (0-10)
        """
        if topic_id in self.topics:
            if financial is not None:
                self.topics[topic_id].financial_score = max(0, min(10, financial))
            if impact is not None:
                self.topics[topic_id].impact_score = max(0, min(10, impact))

    def get_all_topics(self) -> List[MaterialityTopic]:
        """获取所有议题"""
        return list(self.topics.values())

    def get_topics_by_dimension(self, dimension: str) -> List[MaterialityTopic]:
        """按维度获取议题"""
        return [t for t in self.topics.values() if t.dimension == dimension]

    def get_topics_by_quadrant(self, quadrant: str) -> List[MaterialityTopic]:
        """按象限获取议题"""
        return [t for t in self.topics.values() if t.get_quadrant() == quadrant]

    def get_priority_list(self) -> List[Dict[str, Any]]:
        """获取按优先级排序的议题列表

        Returns:
            按优先级（高->中->低）排序的议题字典列表
        """
        priority_order = {"高": 0, "中": 1, "低": 2}
        topics = [t.to_dict() for t in self.topics.values()]
        topics.sort(
            key=lambda x: (
                priority_order.get(x["priority"], 3),
                -x["financial_score"],
                -x["impact_score"],
            )
        )
        return topics

    def get_matrix_data(self) -> List[Dict[str, Any]]:
        """获取矩阵可视化数据

        Returns:
            包含所有议题坐标、颜色、大小等信息的列表
        """
        data = []
        for topic in self.topics.values():
            data.append(
                {
                    "topic_id": topic.topic_id,
                    "name": topic.name,
                    "x": topic.financial_score,
                    "y": topic.impact_score,
                    "dimension": topic.dimension,
                    "color": ESG_COLORS.get(topic.dimension, "#999"),
                    "size": max(20, topic.heat_score * 2),  # 热度决定点的大小
                    "quadrant": topic.get_quadrant(),
                    "priority": topic.get_priority(),
                }
            )
        return data

    def get_quadrant_summary(self) -> Dict[str, int]:
        """获取各象限议题数量统计"""
        summary = {
            "high_materiality": 0,
            "impact_driven": 0,
            "financial_driven": 0,
            "low_priority": 0,
        }
        for topic in self.topics.values():
            summary[topic.get_quadrant()] = summary.get(topic.get_quadrant(), 0) + 1
        return summary

    def get_recommended_disclosure_level(self, topic_id: str) -> str:
        """获取推荐披露级别

        Args:
            topic_id: 议题ID

        Returns:
            推荐披露级别描述
        """
        topic = self.topics.get(topic_id)
        if not topic:
            return "未知"

        quadrant = topic.get_quadrant()
        levels = {
            "high_materiality": "必须披露 - 详细数据+定量指标+第三方鉴证",
            "impact_driven": "合规披露 - 定性描述+关键数据",
            "financial_driven": "风险披露 - 财务影响+风险管理",
            "low_priority": "自愿披露 - 简要提及即可",
        }
        return levels.get(quadrant, "未知")

    def reset_to_defaults(self) -> None:
        """重置为默认评分"""
        self._initialize_topics()

    def export_scores(self) -> Dict[str, Dict[str, int]]:
        """导出当前评分为字典"""
        return {
            topic_id: {
                "financial": topic.financial_score,
                "impact": topic.impact_score,
            }
            for topic_id, topic in self.topics.items()
        }
