"""ESG分析系统 UI 模块

提供 Streamlit 界面组件。

Example:
    >>> from src.esg.ui import render_app
    >>> render_app()  # 启动增强版
"""

from src.esg.ui.app_enhanced import render_app
from src.esg.ui.pages import (
    render_competitor_page,
    render_gap_page,
    render_home_page,
    render_materiality_page,
    render_rag_page,
    render_strategies_page,
    render_timing_page,
    render_topics_page,
    render_weights_page,
)

__all__ = [
    "render_app",
    "render_home_page",
    "render_topics_page",
    "render_materiality_page",
    "render_competitor_page",
    "render_weights_page",
    "render_gap_page",
    "render_strategies_page",
    "render_timing_page",
    "render_rag_page",
]
