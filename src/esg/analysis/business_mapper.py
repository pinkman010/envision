"""业务映射分析器

用于建立ESG议题与企业业务单元之间的关联映射关系。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.esg.config import (
    BUSINESS_UNIT_DESCRIPTIONS,
    BUSINESS_UNITS,
    DEFAULT_MATERIALITY_SCORES,
    TOPIC_BUSINESS_MAP,
)


@dataclass
class BusinessUnit:
    """业务单元数据类"""

    name: str
    description: str
    related_topics: List[str]
    topic_impacts: Dict[str, str]  # topic_id -> impact level

    def get_high_impact_topics(self) -> List[str]:
        """获取高影响议题"""
        return [t for t, impact in self.topic_impacts.items() if impact == "高"]

    def get_medium_impact_topics(self) -> List[str]:
        """获取中影响议题"""
        return [t for t, impact in self.topic_impacts.items() if impact == "中"]

    def get_low_impact_topics(self) -> List[str]:
        """获取低影响议题"""
        return [t for t, impact in self.topic_impacts.items() if impact == "低"]


@dataclass
class TopicBusinessRelation:
    """议题-业务关联数据类"""

    topic_id: str
    topic_name: str
    business_unit: str
    impact_level: str
    dimension: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        将议题-业务关联对象转换为字典，便于序列化和传输。

        Returns:
            包含topic_id, topic_name, business_unit, impact_level, dimension的字典
        """
        return {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "business_unit": self.business_unit,
            "impact_level": self.impact_level,
            "dimension": self.dimension,
        }


class BusinessAlignmentMapper:
    """业务对齐映射器

    管理ESG议题与企业业务单元之间的映射关系。

    Attributes:
        business_units: 业务单元列表
        topic_business_map: 议题-业务映射关系
    """

    # 影响等级排序权重
    IMPACT_WEIGHTS = {"高": 3, "中": 2, "低": 1}

    # 影响等级颜色
    IMPACT_COLORS = {
        "高": "#ff4d4f",  # 红色
        "中": "#faad14",  # 黄色
        "低": "#52c41a",  # 绿色
    }

    def __init__(self):
        """初始化业务映射器"""
        self.business_units = BUSINESS_UNITS
        self.topic_business_map = TOPIC_BUSINESS_MAP
        self.unit_descriptions = BUSINESS_UNIT_DESCRIPTIONS
        self.topic_configs = DEFAULT_MATERIALITY_SCORES

    def get_related_units(self, topic_id: str) -> List[Dict[str, Any]]:
        """获取议题关联的业务单元

        Args:
            topic_id: 议题ID

        Returns:
            关联业务单元列表，每项包含名称、影响等级、描述
        """
        mapping = self.topic_business_map.get(topic_id, {})
        units = mapping.get("units", [])
        impacts = mapping.get("impact", {})

        result = []
        for unit in units:
            impact = impacts.get(unit, "低")
            result.append(
                {
                    "name": unit,
                    "impact": impact,
                    "impact_weight": self.IMPACT_WEIGHTS.get(impact, 1),
                    "color": self.IMPACT_COLORS.get(impact, "#999"),
                    "description": self.unit_descriptions.get(unit, ""),
                }
            )

        # 按影响等级排序（高->中->低）
        result.sort(key=lambda x: -x["impact_weight"])
        return result

    def get_unit_topics(self, unit_name: str) -> List[str]:
        """获取业务单元相关的所有议题

        Args:
            unit_name: 业务单元名称

        Returns:
            相关议题ID列表
        """
        topics = []
        for topic_id, mapping in self.topic_business_map.items():
            if unit_name in mapping.get("units", []):
                topics.append(topic_id)
        return topics

    def get_unit_topic_details(self, unit_name: str) -> List[TopicBusinessRelation]:
        """获取业务单元的详细议题信息

        Args:
            unit_name: 业务单元名称

        Returns:
            议题关联详情列表
        """
        relations = []
        for topic_id, mapping in self.topic_business_map.items():
            if unit_name in mapping.get("units", []):
                impact = mapping.get("impact", {}).get(unit_name, "低")
                topic_config = self.topic_configs.get(topic_id, {})
                relations.append(
                    TopicBusinessRelation(
                        topic_id=topic_id,
                        topic_name=topic_config.get("name", topic_id),
                        business_unit=unit_name,
                        impact_level=impact,
                        dimension=topic_config.get("dimension", "E"),
                    )
                )

        # 按影响等级排序
        relations.sort(key=lambda x: -self.IMPACT_WEIGHTS.get(x.impact_level, 1))
        return relations

    def get_top_risks_for_unit(self, unit_name: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """获取业务单元面临的主要ESG风险（TOP N）

        Args:
            unit_name: 业务单元名称
            top_n: 返回前N个风险

        Returns:
            TOP N风险议题列表
        """
        relations = self.get_unit_topic_details(unit_name)

        # 只考虑高和中影响等级的议题
        high_impact = [r for r in relations if r.impact_level == "高"]
        medium_impact = [r for r in relations if r.impact_level == "中"]

        # 合并并取前N个
        top_risks = (high_impact + medium_impact)[:top_n]

        result = []
        for risk in top_risks:
            result.append(
                {
                    "topic_id": risk.topic_id,
                    "topic_name": risk.topic_name,
                    "impact_level": risk.impact_level,
                    "dimension": risk.dimension,
                    "color": self.IMPACT_COLORS.get(risk.impact_level, "#999"),
                }
            )

        return result

    def get_all_business_units(self) -> List[Dict[str, Any]]:
        """获取所有业务单元信息"""
        units = []
        for name in self.business_units:
            units.append(
                {
                    "name": name,
                    "description": self.unit_descriptions.get(name, ""),
                    "topic_count": len(self.get_unit_topics(name)),
                }
            )
        return units

    def get_risk_matrix_data(self) -> List[Dict[str, Any]]:
        """获取风险矩阵数据（用于报表生成）

        Returns:
            业务单元x议题的风险矩阵数据
        """
        matrix = []

        for unit_name in self.business_units:
            row = {"business_unit": unit_name, "topics": {}}

            # 获取该业务单元的所有议题影响等级
            for topic_id, mapping in self.topic_business_map.items():
                if unit_name in mapping.get("units", []):
                    impact = mapping.get("impact", {}).get(unit_name, "低")
                    topic_config = self.topic_configs.get(topic_id, {})
                    row["topics"][topic_id] = {
                        "name": topic_config.get("name", topic_id),
                        "impact": impact,
                        "dimension": topic_config.get("dimension", "E"),
                    }

            matrix.append(row)

        return matrix

    def get_topic_summary_by_unit(self) -> Dict[str, Dict[str, int]]:
        """按业务单元统计议题影响分布

        Returns:
            每个业务单元的高/中/低影响议题数量
        """
        summary = {}

        for unit_name in self.business_units:
            high_count = 0
            medium_count = 0
            low_count = 0

            for topic_id, mapping in self.topic_business_map.items():
                if unit_name in mapping.get("units", []):
                    impact = mapping.get("impact", {}).get(unit_name, "低")
                    if impact == "高":
                        high_count += 1
                    elif impact == "中":
                        medium_count += 1
                    else:
                        low_count += 1

            summary[unit_name] = {
                "高": high_count,
                "中": medium_count,
                "低": low_count,
                "总计": high_count + medium_count + low_count,
            }

        return summary

    def get_business_unit_profile(self, unit_name: str) -> Optional[BusinessUnit]:
        """获取业务单元完整画像

        Args:
            unit_name: 业务单元名称

        Returns:
            业务单元对象
        """
        if unit_name not in self.business_units:
            return None

        topic_details = self.get_unit_topic_details(unit_name)

        return BusinessUnit(
            name=unit_name,
            description=self.unit_descriptions.get(unit_name, ""),
            related_topics=[t.topic_id for t in topic_details],
            topic_impacts={t.topic_id: t.impact_level for t in topic_details},
        )
