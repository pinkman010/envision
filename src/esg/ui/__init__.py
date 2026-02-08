"""ESG分析系统 UI 模块

提供 Streamlit 界面组件，支持简洁版和增强版两种模式。

Example:
    >>> from src.ui import render_app, render_simple_app
    >>> render_simple_app()  # 启动简洁版
    >>> render_app()  # 启动增强版
"""

from src.esg.ui.app_simple import render_simple_app
from src.esg.ui.app_enhanced import render_app

__all__ = ["render_app", "render_simple_app"]
