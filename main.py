"""ESG智能分析系统 - 入口

增强版功能模块：
- 📊 行业议题全景图
- ⚖️ AHP权重配置
- 🔍 披露差距诊断
- 💡 AI策略建议
- 💬 RAG智能问答
- 📅 沟通时机建议

用法:
    streamlit run main.py
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from src.esg.config import APP_NAME, APP_ICON, VERSION


def main():
    """主函数"""
    # 页面配置
    st.set_page_config(
        page_title=f"{APP_NAME} v{VERSION}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 渲染增强版界面
    from src.esg.ui.app_enhanced import render_app
    render_app()


if __name__ == "__main__":
    main()
