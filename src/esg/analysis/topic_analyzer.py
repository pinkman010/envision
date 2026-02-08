"""行业议题分析器

分析ESG议题热度和趋势，生成词云数据。
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.esg.config import MOCK_DATA_DIR, ESG_DIMENSIONS, ESG_DIMENSION_NAMES


@dataclass
class TopicInfo:
    """议题信息"""
    id: str
    name: str
    base_weight: float
    growth: float
    category: str
    
    @property
    def heat_score(self) -> float:
        """计算热度分数 (0-100)"""
        # 热度 = 基础权重 * 50 + 增长率 * 100，归一化到0-100
        raw_score = self.base_weight * 50 + self.growth * 100
        return min(100.0, round(raw_score, 1))
    
    @property
    def trend_direction(self) -> str:
        """趋势方向"""
        if self.growth > 0.3:
            return "快速上升"
        elif self.growth > 0.15:
            return "上升"
        elif self.growth > 0.05:
            return "平稳"
        else:
            return "缓慢"


@dataclass
class WordCloudItem:
    """词云数据项"""
    text: str
    value: int
    category: str


class TopicAnalyzer:
    """ESG议题分析器
    
    分析行业ESG议题的热度和趋势，生成词云可视化数据。
    
    Attributes:
        data_source: Mock数据源路径
        topics: 加载的议题列表
        _cache: 分析结果缓存
    """
    
    DEFAULT_DATA_SOURCE = MOCK_DATA_DIR / "esg_topics.json"
    
    def __init__(self, data_source: Optional[Path] = None):
        """初始化分析器
        
        Args:
            data_source: 自定义数据源路径，默认使用MOCK_DATA_DIR/esg_topics.json
        """
        self.data_source = data_source or self.DEFAULT_DATA_SOURCE
        self.topics: List[TopicInfo] = []
        self._cache: Dict[str, Any] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """从JSON文件加载议题数据
        
        Raises:
            FileNotFoundError: 数据源文件不存在
            json.JSONDecodeError: JSON解析错误
        """
        try:
            with open(self.data_source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.topics = [
                TopicInfo(
                    id=t["id"],
                    name=t["name"],
                    base_weight=t["base_weight"],
                    growth=t["growth"],
                    category=t["category"]
                )
                for t in data.get("topics", [])
            ]
        except FileNotFoundError:
            raise FileNotFoundError(f"议题数据源文件不存在: {self.data_source}")
        except json.JSONDecodeError as e:
            raise ValueError(f"议题数据JSON解析错误: {e}")
    
    def analyze_trends(self, category: Optional[str] = None) -> Dict[str, Any]:
        """分析议题趋势
        
        Args:
            category: 筛选维度 (E/S/G)，None表示全部
            
        Returns:
            包含趋势分析结果的字典
        """
        cache_key = f"trends_{category or 'all'}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        filtered = self._filter_by_category(category)
        
        if not filtered:
            return {
                "category": category,
                "category_name": ESG_DIMENSION_NAMES.get(category, "全部"),
                "total_topics": 0,
                "hot_topics": [],
                "rising_topics": [],
                "avg_growth": 0.0
            }
        
        # 按热度排序
        sorted_by_heat = sorted(filtered, key=lambda t: t.heat_score, reverse=True)
        # 按增长率排序
        sorted_by_growth = sorted(filtered, key=lambda t: t.growth, reverse=True)
        
        result = {
            "category": category,
            "category_name": ESG_DIMENSION_NAMES.get(category, "全部"),
            "total_topics": len(filtered),
            "hot_topics": [
                {
                    "id": t.id,
                    "name": t.name,
                    "heat_score": t.heat_score,
                    "trend": t.trend_direction
                }
                for t in sorted_by_heat[:5]
            ],
            "rising_topics": [
                {
                    "id": t.id,
                    "name": t.name,
                    "growth_rate": round(t.growth * 100, 1),
                    "trend": t.trend_direction
                }
                for t in sorted_by_growth[:5]
            ],
            "avg_growth": round(
                sum(t.growth for t in filtered) / len(filtered) * 100, 1
            )
        }
        
        self._cache[cache_key] = result
        return result
    
    def generate_wordcloud_data(
        self, 
        category: Optional[str] = None,
        min_weight: float = 0.0
    ) -> List[WordCloudItem]:
        """生成词云数据
        
        Args:
            category: 筛选维度 (E/S/G)，None表示全部
            min_weight: 最小基础权重过滤
            
        Returns:
            词云数据项列表，按热度排序
        """
        filtered = self._filter_by_category(category)
        filtered = [t for t in filtered if t.base_weight >= min_weight]
        
        # 按热度分数排序并转换为词云格式
        sorted_topics = sorted(filtered, key=lambda t: t.heat_score, reverse=True)
        
        return [
            WordCloudItem(
                text=t.name,
                value=self._calculate_word_size(t.heat_score),
                category=t.category
            )
            for t in sorted_topics
        ]
    
    def get_category_summary(self) -> Dict[str, Any]:
        """获取各维度议题汇总
        
        Returns:
            各维度议题统计信息
        """
        if "category_summary" in self._cache:
            return self._cache["category_summary"]
        
        summary = {}
        for dim in ["E", "S", "G"]:
            topics = self._filter_by_category(dim)
            if topics:
                avg_heat = sum(t.heat_score for t in topics) / len(topics)
                avg_growth = sum(t.growth for t in topics) / len(topics)
                summary[dim] = {
                    "name": ESG_DIMENSION_NAMES[dim],
                    "count": len(topics),
                    "avg_heat": round(avg_heat, 1),
                    "avg_growth_rate": round(avg_growth * 100, 1),
                    "top_topic": max(topics, key=lambda t: t.heat_score).name
                }
        
        self._cache["category_summary"] = summary
        return summary
    
    def get_topic_detail(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """获取单个议题详情
        
        Args:
            topic_id: 议题ID
            
        Returns:
            议题详细信息，不存在则返回None
        """
        topic = next((t for t in self.topics if t.id == topic_id), None)
        if not topic:
            return None
        
        return {
            "id": topic.id,
            "name": topic.name,
            "category": topic.category,
            "category_name": ESG_DIMENSION_NAMES.get(topic.category, "未知"),
            "heat_score": topic.heat_score,
            "base_weight": topic.base_weight,
            "growth_rate": round(topic.growth * 100, 1),
            "trend_direction": topic.trend_direction
        }
    
    def _filter_by_category(self, category: Optional[str]) -> List[TopicInfo]:
        """按维度筛选议题"""
        if category is None:
            return self.topics
        return [t for t in self.topics if t.category == category]
    
    def _calculate_word_size(self, heat_score: float) -> int:
        """根据热度分数计算词云字体大小 (10-100)"""
        # 使用对数缩放使大小分布更合理
        normalized = heat_score / 100.0
        size = 10 + int(math.pow(normalized, 0.7) * 90)
        return min(100, max(10, size))
    
    def clear_cache(self) -> None:
        """清除分析缓存"""
        self._cache.clear()
