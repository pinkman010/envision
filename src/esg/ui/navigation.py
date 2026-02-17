"""导航模块（简化版）

提供侧边栏导航功能。
简化版：只保留首页和差距诊断两个页面。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.config import ANALYSIS_YEARS, BENCHMARK_COMPANIES
from src.esg.ui.state import get_state_manager


def render_sidebar() -> Dict[str, Any]:
    """渲染侧边栏（简化版）

    简化后导航：首页、差距诊断，共2个页面

    Returns:
        配置参数字典
    """
    with st.sidebar:
        # 导航 - 只保留2个页面
        st.markdown("### 📍 功能导航")

        pages = {
            "home": "🏠 首页",
            "gap": "📉 差距诊断",
        }

        manager = get_state_manager()
        current_page = manager.get_current_page()

        for key, label in pages.items():
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if current_page == key else "secondary",
            ):
                manager.set_current_page(key)
                st.rerun()

        st.markdown("---")

        # 全局设置
        st.markdown("### ⚙️ 全局设置")

        industry = st.selectbox(
            "行业",
            ["新能源", "制造业", "科技", "金融", "消费品"],
            index=0,
        )

        year = st.selectbox(
            "年份",
            ANALYSIS_YEARS,
            index=0,
        )

        benchmark = st.selectbox(
            "对标企业",
            BENCHMARK_COMPANIES,
            index=len(BENCHMARK_COMPANIES) - 1,
        )

        st.markdown("---")

        # 快捷操作
        st.markdown("### 🚀 快捷操作")

        if st.button("🔄 重置所有数据", use_container_width=True):
            manager.reset()
            st.rerun()

        return {
            "industry": industry,
            "year": year,
            "benchmark": benchmark,
        }
