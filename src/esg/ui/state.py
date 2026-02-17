"""会话状态管理模块（简化版）

统一管理 Streamlit 的 session_state，提供类型安全的状态访问接口。
简化版：只保留核心状态。
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, cast

import streamlit as st

from src.esg.core.models import AnalysisResult, ESGMetrics

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
}


@dataclass
class AppState:
    """应用状态数据类（简化版）

    简化后状态：metrics, analysis_result, current_page, weights
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


class StateManager:
    """会话状态管理器（简化版）

    提供对 Streamlit session_state 的类型安全封装。
    简化版：只保留核心状态访问方法。
    """

    def __init__(self) -> None:
        """初始化状态管理器"""
        self._state = st.session_state

    def init_state(self) -> None:
        """初始化默认状态"""
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
        """获取任意状态值"""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置任意状态值"""
        self._state[key] = value

    # === 核心状态访问 ===

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

    def get_gap_analysis(self) -> Dict[str, Any]:
        """获取差距分析结果"""
        return cast(Dict[str, Any], self._state.get("gap_analysis", {}))

    def set_gap_analysis(self, gap: Dict[str, Any]) -> None:
        """设置差距分析结果"""
        self._state["gap_analysis"] = gap

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


# 全局状态管理器实例
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """获取全局状态管理器实例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def init_session_state() -> None:
    """初始化会话状态（便捷函数）"""
    manager = get_state_manager()
    manager.init_state()
