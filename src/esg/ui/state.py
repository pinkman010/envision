"""会话状态管理模块

统一管理 Streamlit 的 session_state，提供类型安全的状态访问接口。
"""

from typing import Any, Dict, List, Optional, cast
from dataclasses import dataclass, field, asdict
from datetime import datetime
import streamlit as st

from src.esg.core.models import ESGMetrics, AnalysisResult


# 状态键名常量
STATE_KEYS = {
    "initialized": "_initialized",
    "current_page": "current_page",
    "metrics": "metrics",
    "analysis_result": "analysis_result",
    "weights": "weights",
    "selected_industry": "selected_industry",
    "selected_year": "selected_year",
    "uploaded_file": "uploaded_file",
    "extraction_progress": "extraction_progress",
    "analysis_progress": "analysis_progress",
    "gap_analysis": "gap_analysis",
    "strategies": "strategies",
    "benchmark_company": "benchmark_company",
    "ahp_matrix": "ahp_matrix",
    "ahp_result": "ahp_result",
    "topic_filter": "topic_filter",
    "selected_topics": "selected_topics",
}


@dataclass
class AppState:
    """应用状态数据类
    
    Attributes:
        initialized: 是否已初始化
        current_page: 当前页面标识
        metrics: 提取的ESG指标数据
        analysis_result: 分析结果
        weights: ESG维度权重配置
        selected_industry: 选择的行业
        selected_year: 选择的年份
        uploaded_file: 上传的文件信息
        extraction_progress: 数据提取进度 (0-100)
        analysis_progress: 分析进度 (0-100)
        gap_analysis: 差距分析结果
        strategies: 生成的策略列表
        benchmark_company: 选择的标杆企业
        ahp_matrix: AHP判断矩阵
        ahp_result: AHP计算结果
        topic_filter: 议题筛选条件
        selected_topics: 选中的议题列表
    """
    initialized: bool = False
    current_page: str = "home"
    metrics: Optional[ESGMetrics] = None
    analysis_result: Optional[AnalysisResult] = None
    weights: Dict[str, float] = field(default_factory=lambda: {"E": 0.4, "S": 0.3, "G": 0.3})
    selected_industry: str = "新能源"
    selected_year: str = "2025"
    uploaded_file: Optional[Dict[str, Any]] = None
    extraction_progress: int = 0
    analysis_progress: int = 0
    gap_analysis: Dict[str, Any] = field(default_factory=dict)
    strategies: List[Dict[str, Any]] = field(default_factory=list)
    benchmark_company: str = "行业平均"
    ahp_matrix: Optional[List[List[float]]] = None
    ahp_result: Optional[Dict[str, Any]] = None
    topic_filter: str = "all"
    selected_topics: List[str] = field(default_factory=list)


class StateManager:
    """会话状态管理器
    
    提供对 Streamlit session_state 的类型安全封装。
    所有状态访问都应通过此类进行。
    
    Example:
        >>> manager = StateManager()
        >>> manager.init_state()  # 初始化状态
        >>> manager.set_metrics(metrics)
        >>> metrics = manager.get_metrics()
    """
    
    def __init__(self) -> None:
        """初始化状态管理器"""
        self._state = st.session_state
    
    def init_state(self) -> None:
        """初始化默认状态
        
        如果状态未初始化，则设置所有默认值。
        应在应用启动时调用一次。
        """
        if STATE_KEYS["initialized"] not in self._state:
            default_state = AppState()
            for key, value in asdict(default_state).items():
                self._state[key] = value
            self._state[STATE_KEYS["initialized"]] = True
    
    def reset(self) -> None:
        """重置所有状态到默认值"""
        default_state = AppState()
        for key, value in asdict(default_state).items():
            self._state[key] = value
    
    # === 基本状态访问 ===
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取任意状态值
        
        Args:
            key: 状态键名
            default: 默认值
            
        Returns:
            状态值或默认值
        """
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置任意状态值
        
        Args:
            key: 状态键名
            value: 要设置的值
        """
        self._state[key] = value
    
    # === 特定状态访问 ===
    
    def get_metrics(self) -> Optional[ESGMetrics]:
        """获取ESG指标数据"""
        return cast(Optional[ESGMetrics], self._state.get("metrics"))
    
    def set_metrics(self, metrics: ESGMetrics) -> None:
        """设置ESG指标数据"""
        self._state["metrics"] = metrics
    
    def get_analysis_result(self) -> Optional[AnalysisResult]:
        """获取分析结果"""
        return cast(Optional[AnalysisResult], self._state.get("analysis_result"))
    
    def set_analysis_result(self, result: AnalysisResult) -> None:
        """设置分析结果"""
        self._state["analysis_result"] = result
    
    def get_weights(self) -> Dict[str, float]:
        """获取权重配置"""
        return cast(Dict[str, float], self._state.get("weights", {"E": 0.4, "S": 0.3, "G": 0.3}))
    
    def set_weights(self, weights: Dict[str, float]) -> None:
        """设置权重配置"""
        self._state["weights"] = weights
    
    def get_current_page(self) -> str:
        """获取当前页面"""
        return cast(str, self._state.get("current_page", "home"))
    
    def set_current_page(self, page: str) -> None:
        """设置当前页面"""
        self._state["current_page"] = page
    
    def get_benchmark_company(self) -> str:
        """获取标杆企业"""
        return cast(str, self._state.get("benchmark_company", "行业平均"))
    
    def set_benchmark_company(self, company: str) -> None:
        """设置标杆企业"""
        self._state["benchmark_company"] = company
    
    def get_gap_analysis(self) -> Dict[str, Any]:
        """获取差距分析结果"""
        return cast(Dict[str, Any], self._state.get("gap_analysis", {}))
    
    def set_gap_analysis(self, gap: Dict[str, Any]) -> None:
        """设置差距分析结果"""
        self._state["gap_analysis"] = gap
    
    def get_strategies(self) -> List[Dict[str, Any]]:
        """获取策略列表"""
        return cast(List[Dict[str, Any]], self._state.get("strategies", []))
    
    def set_strategies(self, strategies: List[Dict[str, Any]]) -> None:
        """设置策略列表"""
        self._state["strategies"] = strategies
    
    def get_ahp_result(self) -> Optional[Dict[str, Any]]:
        """获取AHP计算结果"""
        return cast(Optional[Dict[str, Any]], self._state.get("ahp_result"))
    
    def set_ahp_result(self, result: Dict[str, Any]) -> None:
        """设置AHP计算结果"""
        self._state["ahp_result"] = result
    
    # === 进度相关 ===
    
    def get_extraction_progress(self) -> int:
        """获取数据提取进度"""
        return cast(int, self._state.get("extraction_progress", 0))
    
    def set_extraction_progress(self, progress: int) -> None:
        """设置数据提取进度"""
        self._state["extraction_progress"] = max(0, min(100, progress))
    
    def get_analysis_progress(self) -> int:
        """获取分析进度"""
        return cast(int, self._state.get("analysis_progress", 0))
    
    def set_analysis_progress(self, progress: int) -> None:
        """设置分析进度"""
        self._state["analysis_progress"] = max(0, min(100, progress))
    
    # === 标志位方法 ===
    
    def has_metrics(self) -> bool:
        """检查是否已有指标数据"""
        return self._state.get("metrics") is not None
    
    def has_analysis_result(self) -> bool:
        """检查是否已有分析结果"""
        return self._state.get("analysis_result") is not None
    
    def has_gap_analysis(self) -> bool:
        """检查是否已有差距分析"""
        return bool(self._state.get("gap_analysis"))
    
    def has_strategies(self) -> bool:
        """检查是否已有策略"""
        return bool(self._state.get("strategies"))


# 全局状态管理器实例
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """获取全局状态管理器实例
    
    Returns:
        StateManager: 状态管理器单例
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def init_session_state() -> None:
    """初始化会话状态（便捷函数）"""
    manager = get_state_manager()
    manager.init_state()
