"""议题动态更新器

模拟行业数据的动态更新机制，支持热度值的随机波动和变更记录。
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class TopicChangeLog:
    """议题变更日志"""
    topic_id: str
    topic_name: str
    old_value: float
    new_value: float
    change: float
    change_percent: float
    is_hot_rising: bool = False  # 是否为新晋热点
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        将议题变更日志转换为字典，便于序列化和前端展示。
        
        Returns:
            包含topic, old, new, change, change_percent, is_hot的字典
        """
        return {
            "topic": self.topic_name,
            "old": round(self.old_value, 1),
            "new": round(self.new_value, 1),
            "change": f"{self.change:+.1f}",
            "change_percent": f"{self.change_percent:+.1f}%",
            "is_hot": "新晋热点" if self.is_hot_rising else ""
        }


@dataclass
class UpdateRecord:
    """更新记录"""
    timestamp: str
    source: str
    version: str
    changed_topics: int
    summary: str
    change_logs: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后处理：设置默认值"""
        if self.change_logs is None:
            self.change_logs = []


class TopicUpdater:
    """议题动态更新器
    
    管理议题热度数据的动态更新和变更记录。
    
    Attributes:
        data_file: 数据文件路径
        current_version: 当前数据版本
        update_history: 更新历史记录
    """
    
    # 数据文件路径
    DATA_FILE = Path(__file__).parent.parent.parent / "data" / "mock_topic_updates.json"
    
    # 更新波动范围
    FLUCTUATION_RANGE = 0.05  # ±5%
    
    # 新晋热点阈值（增长率）
    HOT_RISING_THRESHOLD = 0.10  # 10%
    
    def __init__(self):
        """初始化更新器"""
        self.data_file = self.DATA_FILE
        self._data: Dict[str, Any] = {}
        self._current_version: str = "version_1"
        self._update_history: List[UpdateRecord] = []
        self._load_data()
    
    def _load_data(self) -> None:
        """加载数据文件"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = {"version_1": {"topics": {}}, "update_history": []}
        except json.JSONDecodeError:
            self._data = {"version_1": {"topics": {}}, "update_history": []}
    
    def get_current_data(self) -> Dict[str, Any]:
        """获取当前版本数据
        
        Returns:
            当前版本的议题数据
        """
        return self._data.get(self._current_version, {}).get("topics", {})
    
    def get_version_data(self, version: str) -> Dict[str, Any]:
        """获取指定版本数据
        
        Args:
            version: 版本标识（"version_1"或"version_2"）
            
        Returns:
            指定版本的议题数据
        """
        return self._data.get(version, {}).get("topics", {})
    
    def simulate_update(self, current_data: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[TopicChangeLog]]:
        """模拟数据更新
        
        在现有数据基础上随机波动±5%更新热度值，并记录变更日志。
        
        Args:
            current_data: 当前数据，None则使用当前版本数据
            
        Returns:
            (更新后的数据, 变更日志列表)
        """
        if current_data is None:
            current_data = self.get_current_data()
        
        updated_data = {}
        change_logs = []
        
        for topic_id, topic_info in current_data.items():
            # 复制原始数据
            updated_info = topic_info.copy()
            old_heat = topic_info.get("heat", 50)
            
            # 随机波动 ±5%
            fluctuation = random.uniform(-self.FLUCTUATION_RANGE, self.FLUCTUATION_RANGE)
            new_heat = old_heat * (1 + fluctuation)
            
            # 限制在合理范围
            new_heat = max(10, min(100, new_heat))
            
            # 更新数据
            updated_info["heat"] = round(new_heat, 1)
            
            # 计算变化
            change = new_heat - old_heat
            change_percent = (change / old_heat) * 100 if old_heat > 0 else 0
            
            # 判断是否为新晋热点
            is_hot_rising = change_percent >= self.HOT_RISING_THRESHOLD * 100
            
            # 更新趋势标识
            if change > 2:
                updated_info["trend"] = "up"
            elif change < -2:
                updated_info["trend"] = "down"
            else:
                updated_info["trend"] = "stable"
            
            updated_info["change"] = f"{change:+.1f}"
            
            updated_data[topic_id] = updated_info
            
            # 记录变更日志（只记录有变化的）
            if abs(change) > 0.5:
                change_logs.append(TopicChangeLog(
                    topic_id=topic_id,
                    topic_name=topic_info.get("name", topic_id),
                    old_value=old_heat,
                    new_value=new_heat,
                    change=change,
                    change_percent=change_percent,
                    is_hot_rising=is_hot_rising
                ))
        
        # 保存到session（实际应用中应保存到数据库）
        self._last_updated_data = updated_data
        self._last_change_logs = change_logs
        
        return updated_data, change_logs
    
    def create_update_record(
        self, 
        change_logs: List[TopicChangeLog],
        source: str = "模拟数据源：行业新闻聚合"
    ) -> UpdateRecord:
        """创建更新记录
        
        Args:
            change_logs: 变更日志列表
            source: 数据来源
            
        Returns:
            更新记录对象
        """
        now = datetime.now()
        version = f"v{now.strftime('%y%m%d_%H%M')}"
        
        record = UpdateRecord(
            timestamp=now.isoformat(),
            source=source,
            version=version,
            changed_topics=len(change_logs),
            summary=self._generate_summary(change_logs),
            change_logs=[log.to_dict() for log in change_logs[:10]]  # 只记录前10个变更
        )
        
        # 添加到历史
        self._update_history.insert(0, record)
        
        # 只保留最近10条记录
        self._update_history = self._update_history[:10]
        
        return record
    
    def _generate_summary(self, change_logs: List[TopicChangeLog]) -> str:
        """生成更新摘要
        
        Args:
            change_logs: 变更日志列表
            
        Returns:
            摘要描述
        """
        if not change_logs:
            return "无显著变化"
        
        rising_count = sum(1 for log in change_logs if log.change > 0)
        falling_count = sum(1 for log in change_logs if log.change < 0)
        hot_count = sum(1 for log in change_logs if log.is_hot_rising)
        
        parts = []
        if rising_count > 0:
            parts.append(f"{rising_count}个议题热度上升")
        if falling_count > 0:
            parts.append(f"{falling_count}个议题热度下降")
        if hot_count > 0:
            parts.append(f"{hot_count}个新晋热点")
        
        return "；".join(parts) if parts else "数据微调"
    
    def get_update_history(self, limit: int = 3) -> List[Dict[str, Any]]:
        """获取更新历史
        
        Args:
            limit: 返回最近几条记录
            
        Returns:
            更新记录列表
        """
        # 先从JSON文件读取历史
        json_history = self._data.get("update_history", [])
        
        # 合并内存中的记录
        all_history = []
        for record in self._update_history:
            all_history.append({
                "timestamp": record.timestamp,
                "source": record.source,
                "version": record.version,
                "changed_topics": record.changed_topics,
                "summary": record.summary
            })
        
        # 添加JSON中的历史（去重）
        existing_versions = {r["version"] for r in all_history}
        for item in json_history:
            if item.get("version") not in existing_versions:
                all_history.append(item)
        
        # 按时间倒序排列
        all_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return all_history[:limit]
    
    def get_hot_rising_topics(self, min_change_percent: float = 10.0) -> List[Dict[str, Any]]:
        """获取新晋热点议题
        
        Args:
            min_change_percent: 最小增长率阈值
            
        Returns:
            新晋热点议题列表
        """
        current = self.get_current_data()
        hot_topics = []
        
        for topic_id, info in current.items():
            change_str = info.get("change", "0")
            try:
                change = float(change_str)
                if change >= min_change_percent:
                    hot_topics.append({
                        "topic_id": topic_id,
                        "name": info.get("name", topic_id),
                        "heat": info.get("heat", 0),
                        "change": change,
                        "trend": info.get("trend", "stable")
                    })
            except ValueError:
                continue
        
        # 按变化幅度排序
        hot_topics.sort(key=lambda x: x["change"], reverse=True)
        return hot_topics
    
    def get_topic_rank_change(self, topic_id: str) -> Dict[str, Any]:
        """获取议题排名变化
        
        Args:
            topic_id: 议题ID
            
        Returns:
            排名变化信息
        """
        # 获取当前版本和上一版本数据
        current = self.get_current_data()
        previous = self.get_version_data("version_1")
        
        # 计算排名
        def get_rank(data: Dict[str, Any], tid: str) -> int:
            """计算议题在数据中的排名
            
            根据热度值对议题进行排序，返回指定议题的排名位置。
            
            Args:
                data: 议题数据字典
                tid: 要查询排名的议题ID
                
            Returns:
                排名位置（1开始计数），如果未找到则返回数据长度
            """
            # 边界条件检查：空数据
            if not data:
                return 0
            
            # 按热度排序
            sorted_topics = sorted(
                data.items(),
                key=lambda x: x[1].get("heat", 0),
                reverse=True
            )
            
            # 查找指定议题的排名
            for i, (t_id, _) in enumerate(sorted_topics, 1):
                if t_id == tid:
                    return i
            
            # 未找到时返回最后一名
            return len(sorted_topics)
        
        current_rank = get_rank(current, topic_id)
        previous_rank = get_rank(previous, topic_id)
        rank_change = previous_rank - current_rank  # 正值表示排名上升
        
        topic_info = current.get(topic_id, {})
        
        return {
            "topic_id": topic_id,
            "name": topic_info.get("name", topic_id),
            "current_rank": current_rank,
            "previous_rank": previous_rank,
            "rank_change": rank_change,
            "is_new_hot": rank_change >= 3  # 上升3位以上视为新晋热点
        }
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """格式化时间戳为友好显示
        
        Args:
            timestamp_str: ISO格式时间戳
            
        Returns:
            格式化后的时间字符串
        """
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return timestamp_str
