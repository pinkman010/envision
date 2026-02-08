"""自动数据更新器（模拟版）

模拟从外部数据源自动获取ESG议题热度更新。
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.esg.config import DATA_DIR


class AutoUpdater:
    """自动数据更新器
    
    模拟从外部数据源（财新ESG、Wind、Bloomberg）
    自动获取ESG议题热度更新。
    
    Attributes:
        updates_dir: 模拟更新文件目录
        available_sources: 可用的数据源列表
    """
    
    AVAILABLE_SOURCES = ["财新ESG", "Wind", "Bloomberg"]
    
    def __init__(self):
        """初始化自动更新器"""
        self.updates_dir = DATA_DIR / "mock_auto_updates"
        self._update_files = None
        self._last_update_time = None
        self._current_data = None
    
    def _get_update_files(self) -> List[Path]:
        """获取所有可用的更新文件"""
        if self._update_files is None:
            if self.updates_dir.exists():
                self._update_files = sorted(
                    [f for f in self.updates_dir.glob("update_*.json")]
                )
            else:
                self._update_files = []
        return self._update_files
    
    def simulate_scheduled_update(
        self,
        preferred_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """模拟执行定时更新
        
        随机选择一个update文件加载，模拟从外部数据源获取更新。
        
        Args:
            preferred_sources: 偏好的数据源列表
            
        Returns:
            更新结果字典，包含：
            - update_time: 更新时间
            - source: 数据来源
            - changes_count: 变更数量
            - updated_topics: 更新的议题列表
            - summary: 更新摘要
        """
        update_files = self._get_update_files()
        
        if not update_files:
            # 如果没有文件，生成模拟数据
            return self._generate_mock_update(preferred_sources)
        
        # 随机选择一个更新文件
        selected_file = random.choice(update_files)
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                update_data = json.load(f)
        except Exception as e:
            return {
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": "模拟数据源",
                "changes_count": 0,
                "updated_topics": [],
                "summary": f"更新失败: {str(e)}",
                "error": True
            }
        
        # 记录更新时间
        self._last_update_time = datetime.now()
        self._current_data = update_data
        
        # 构建返回结果
        return {
            "update_time": update_data.get("update_time", datetime.now().strftime("%Y-%m-%d")),
            "source": update_data.get("source", "模拟数据源"),
            "changes_count": update_data.get("changes_count", 0),
            "updated_topics": update_data.get("updated_topics", []),
            "summary": update_data.get("summary", "数据已更新"),
            "data_sources": update_data.get("data_sources", self.AVAILABLE_SOURCES[:2])
        }
    
    def _generate_mock_update(
        self,
        preferred_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """生成模拟更新数据（当没有文件时）"""
        sources = preferred_sources or self.AVAILABLE_SOURCES[:2]
        source_str = "+".join(sources)
        
        # 模拟议题热度变化
        topics = [
            "碳排放管理", "可再生能源使用", "供应链碳管理",
            "员工职业健康与安全", "员工培训与发展", "社区投资",
            "董事会多元化", "ESG信息披露", "商业道德与合规",
            "循环经济实践"
        ]
        
        updated_topics = []
        changes_count = random.randint(8, 15)
        
        for topic in random.sample(topics, min(changes_count, len(topics))):
            trend = random.choice(["up", "down", "stable"])
            heat_change = round(random.uniform(-3, 8), 1) if trend == "up" else (
                round(random.uniform(-5, 2), 1) if trend == "down" else round(random.uniform(-1, 1), 1)
            )
            
            updated_topics.append({
                "topic": topic,
                "trend": trend,
                "heat_change": heat_change,
                "new_heat": round(random.uniform(50, 90), 1)
            })
        
        return {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": f"模拟数据源：{source_str}",
            "changes_count": len(updated_topics),
            "updated_topics": updated_topics,
            "summary": f"已更新{len(updated_topics)}个议题热度数据",
            "data_sources": sources
        }
    
    def get_data_freshness(self) -> Dict[str, Any]:
        """获取数据新鲜度信息
        
        Returns:
            包含更新时间、时间差等信息的字典
        """
        if self._last_update_time is None:
            # 模拟上次更新时间为2小时前
            return {
                "last_update": "2024-02-15 10:30",
                "time_ago": "2小时前",
                "freshness_level": "fresh",  # fresh, stale, outdated
                "freshness_text": "数据较新"
            }
        
        now = datetime.now()
        time_diff = now - self._last_update_time
        hours_ago = int(time_diff.total_seconds() / 3600)
        
        if hours_ago < 1:
            time_ago = "刚刚"
            freshness_level = "fresh"
            freshness_text = "数据最新"
        elif hours_ago < 24:
            time_ago = f"{hours_ago}小时前"
            freshness_level = "fresh"
            freshness_text = "数据较新"
        elif hours_ago < 72:
            time_ago = f"{hours_ago // 24}天前"
            freshness_level = "stale"
            freshness_text = "数据需要更新"
        else:
            time_ago = f"{hours_ago // 24}天前"
            freshness_level = "outdated"
            freshness_text = "数据已过期"
        
        return {
            "last_update": self._last_update_time.strftime("%Y-%m-%d %H:%M"),
            "time_ago": time_ago,
            "freshness_level": freshness_level,
            "freshness_text": freshness_text
        }
    
    def get_available_sources(self) -> List[str]:
        """获取所有可用的数据源"""
        return self.AVAILABLE_SOURCES.copy()
    
    def format_update_display(self, update_result: Dict[str, Any]) -> str:
        """格式化更新结果显示"""
        if update_result.get("error"):
            return f"❌ 更新失败: {update_result.get('summary', '未知错误')}"
        
        source = update_result.get("source", "未知来源")
        count = update_result.get("changes_count", 0)
        
        return f"✅ 已从【{source}】获取【{count}】条更新，议题热度已调整"
    
    def get_topic_heatmap_data(self, update_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从更新结果获取词云图数据
        
        Args:
            update_result: 更新结果字典
            
        Returns:
            词云图数据列表
        """
        updated_topics = update_result.get("updated_topics", [])
        
        wordcloud_data = []
        for topic in updated_topics:
            wordcloud_data.append({
                "name": topic.get("topic", ""),
                "value": topic.get("new_heat", 50),
                "trend": topic.get("trend", "stable"),
                "change": topic.get("heat_change", 0)
            })
        
        return wordcloud_data


# 全局实例
auto_updater = AutoUpdater()
