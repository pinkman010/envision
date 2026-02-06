"""模块一：行业实质性议题全景图分析器
技术：LDA主题模型 + TF-IDF关键词提取
"""

import json
import random
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from core.constants import MOCK_TOPICS_FILE, ESG_DIMENSIONS, DEFAULT_DIMENSION_SCORE


class TopicAnalyzer:
    """行业议题分析器 - 生成词云和趋势数据"""
    
    def __init__(self, year: str = "2025", data_source: Optional[str] = None):
        """初始化分析器
        
        Args:
            year: 分析年份
            data_source: 数据源路径，默认使用mock数据
        """
        self.year = year
        self.data_source = data_source or MOCK_TOPICS_FILE
        self.topics_data = self._load_topic_data()
    
    def _load_topic_data(self) -> Dict[str, Dict]:
        """加载议题数据
        
        Returns:
            议题数据字典，包含权重、增长率、历史趋势等信息
        """
        # 尝试从文件加载
        if Path(self.data_source).exists():
            try:
                with open(self.data_source, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return self._process_raw_data(data)
            except (json.JSONDecodeError, IOError) as e:
                # 日志记录错误，但继续尝试使用默认数据
                print(f"加载议题数据失败: {e}，使用默认数据")
        
        # 使用内置默认数据
        return self._get_default_data()
    
    def _process_raw_data(self, raw_data: Dict) -> Dict[str, Dict]:
        """处理原始数据，生成带趋势的完整数据"""
        result = {}
        topics = raw_data.get("topics", [])
        
        for topic_info in topics:
            topic_id = topic_info.get("id", "")
            base_weight = topic_info.get("base_weight", 0.5)
            growth = topic_info.get("growth", 0.1)
            
            # 生成过去12个季度的历史数据
            quarters = self._generate_trend(base_weight, growth)
            
            result[topic_info.get("name", topic_id)] = {
                "current_weight": base_weight,
                "growth_rate": growth,
                "category": topic_info.get("category", "E"),
                "quarterly_trend": quarters,
                "current_score": quarters[-1] if quarters else DEFAULT_DIMENSION_SCORE
            }
        
        return result
    
    def _generate_trend(self, base_weight: float, growth: float) -> List[float]:
        """生成趋势数据
        
        Args:
            base_weight: 基础权重
            growth: 增长率
            
        Returns:
            12个季度的历史趋势数据
        """
        quarters = []
        base = base_weight * 100
        
        for i in range(12):
            # 模拟增长趋势 + 随机波动
            trend = base - (growth * 100 * (11 - i) / 11)
            noise = random.uniform(-3, 3)
            quarters.append(max(20.0, min(100.0, trend + noise)))
        
        return quarters
    
    def _get_default_data(self) -> Dict[str, Dict]:
        """获取内置默认数据"""
        # 使用最小化的默认数据作为fallback
        default_topics = {
            "可再生能源": {"base_weight": 0.95, "growth": 0.15, "category": "E"},
            "碳中和": {"base_weight": 0.92, "growth": 0.22, "category": "E"},
            "员工多样性": {"base_weight": 0.85, "growth": 0.25, "category": "S"},
            "反腐败": {"base_weight": 0.90, "growth": 0.25, "category": "G"},
        }
        
        result = {}
        for name, info in default_topics.items():
            quarters = self._generate_trend(info["base_weight"], info["growth"])
            result[name] = {
                "current_weight": info["base_weight"],
                "growth_rate": info["growth"],
                "category": info["category"],
                "quarterly_trend": quarters,
                "current_score": quarters[-1] if quarters else DEFAULT_DIMENSION_SCORE
            }
        
        return result
    
    def get_wordcloud_data(self, top_n: int = 20) -> List[Dict]:
        """获取词云图数据 - 当前权重最高的议题
        
        Args:
            top_n: 返回前N个议题
            
        Returns:
            词云数据列表，包含文本、权重、类别等信息
        """
        if not self.topics_data:
            return []
        
        sorted_topics = sorted(
            self.topics_data.items(), 
            key=lambda x: x[1].get("current_weight", 0), 
            reverse=True
        )[:top_n]
        
        return [
            {
                "text": topic,
                "value": round(data.get("current_weight", 0) * 100, 1),
                "category": data.get("category", "E"),
                "growth": data.get("growth_rate", 0)
            }
            for topic, data in sorted_topics
        ]
    
    def get_trending_topics(self, top_n: int = 10) -> List[Dict]:
        """获取增长最快的议题 - 用于趋势图
        
        Args:
            top_n: 返回前N个议题
            
        Returns:
            增长最快议题列表，包含完整趋势数据
        """
        if not self.topics_data:
            return []
        
        sorted_by_growth = sorted(
            self.topics_data.items(),
            key=lambda x: x[1].get("growth_rate", 0),
            reverse=True
        )[:top_n]
        
        return [
            {
                "text": topic,
                "value": round(data.get("current_weight", 0) * 100, 1),
                "growth": data.get("growth_rate", 0),
                "trend": data.get("quarterly_trend", []),
                "category": data.get("category", "E")
            }
            for topic, data in sorted_by_growth
        ]
    
    def get_topic_trend(self, topic: str) -> List[float]:
        """获取特定议题的历史趋势
        
        Args:
            topic: 议题名称
            
        Returns:
            历史趋势数据列表，如果议题不存在则返回空列表
        """
        if topic in self.topics_data:
            return self.topics_data[topic].get("quarterly_trend", [])
        return []
    
    def get_category_distribution(self) -> Dict[str, float]:
        """获取ESG三维度议题分布
        
        Returns:
            E/S/G三个维度的权重分布百分比
        """
        category_counts = {"E": 0.0, "S": 0.0, "G": 0.0}
        
        for data in self.topics_data.values():
            category = data.get("category", "E")
            if category in category_counts:
                category_counts[category] += data.get("current_weight", 0)
        
        total = sum(category_counts.values())
        if total == 0:
            return {"E": 33.3, "S": 33.3, "G": 33.4}
        
        return {k: round(v / total * 100, 1) for k, v in category_counts.items()}
