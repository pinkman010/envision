"""ESG智能分析系统 - 入口

增强版功能模块：
- 📊 行业议题全景图
- ⚖️ AHP权重配置
- 🔍 披露差距诊断
- 💡 AI策略建议
- 💬 RAG智能问答
- 📅 沟通时机建议

用法:
    streamlit run src/main.py
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from src.esg.config import APP_ICON, APP_NAME, VERSION


def main():
    """主函数"""
    # 页面配置
    st.set_page_config(
        page_title=APP_NAME, page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded"
    )

    # 渲染应用界面
    from src.esg.ui.app_main import render_app

    render_app()


if __name__ == "__main__":
    main()
