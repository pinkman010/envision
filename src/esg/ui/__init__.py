"""ESG分析系统 UI 模块

提供 Streamlit 界面组件。

Example:
    >>> from src.esg.ui import render_app
    >>> render_app()  # 启动增强版
"""

from src.esg.ui.app_enhanced import render_app

__all__ = ["render_app"]
