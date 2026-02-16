"""应用配置模块

提供页面配置和初始化功能。
"""

import streamlit as st

from src.esg.ui.state import init_session_state


def setup_page() -> None:
    """配置页面基础设置"""
    st.set_page_config(
        page_title="ESG智能分析系统 - 增强版",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()
