"""ESG智能分析系统 - 统一入口

支持两种运行模式:
- 简洁版(simple): 快速ESG分析流程
- 增强版(enhanced): 完整功能模块（议题分析、权重配置、差距诊断、策略建议）

用法:
    streamlit run main.py -- --mode simple
    streamlit run main.py -- --mode enhanced
    
    或不带参数，默认启动简洁版:
    streamlit run main.py
"""

import sys
import argparse
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from src.esg.config import APP_NAME, APP_ICON, VERSION


def parse_args():
    """解析命令行参数"""
    # 由于 Streamlit 会添加自己的参数，我们需要小心处理
    parser = argparse.ArgumentParser(description="ESG智能分析系统")
    parser.add_argument(
        "--mode",
        choices=["simple", "enhanced"],
        default="simple",
        help="运行模式: simple(简洁版) 或 enhanced(增强版)"
    )
    
    # 只解析我们知道的参数，其他的忽略（传给streamlit）
    try:
        args, _ = parser.parse_known_args()
        return args
    except Exception:
        return argparse.Namespace(mode="simple")


def get_mode_from_session() -> str:
    """从 session state 获取模式，或让用户选择"""
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "simple"
    return st.session_state.app_mode


def render_mode_selector():
    """渲染模式选择器"""
    st.sidebar.title(f"{APP_ICON} {APP_NAME}")
    st.sidebar.caption(f"版本: v{VERSION}")
    st.sidebar.markdown("---")
    
    mode = st.sidebar.radio(
        "选择运行模式",
        options=["simple", "enhanced"],
        format_func=lambda x: "简洁版" if x == "simple" else "增强版",
        index=0 if get_mode_from_session() == "simple" else 1
    )
    
    if mode != st.session_state.app_mode:
        st.session_state.app_mode = mode
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # 显示模式说明
    if mode == "simple":
        st.sidebar.info("""
        **简洁版功能:**
        - 📄 PDF报告上传
        - 🔍 ESG指标提取
        - 📊 智能分析评分
        - 📝 报告下载
        
        适合快速分析单份报告
        """)
    else:
        st.sidebar.info("""
        **增强版功能:**
        - 📊 行业议题全景图
        - ⚖️ AHP权重配置
        - 🔍 披露差距诊断
        - 💡 AI策略建议
        - 💬 RAG智能问答
        
        适合深度分析和对比
        """)
    
    return mode


def main():
    """主函数"""
    # 页面配置
    st.set_page_config(
        page_title=f"{APP_NAME} v{VERSION}",
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 解析参数或使用 session state
    args = parse_args()
    
    # 初始化 session state
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = args.mode
    
    # 渲染模式选择器
    mode = render_mode_selector()
    
    # 根据模式渲染不同界面
    if mode == "simple":
        render_simple_mode()
    else:
        render_enhanced_mode()


def render_simple_mode():
    """渲染简洁版"""
    from src.esg.ui.app_simple import render_simple_app
    render_simple_app()


def render_enhanced_mode():
    """渲染增强版"""
    from src.esg.ui.app_enhanced import render_app
    render_app()


if __name__ == "__main__":
    main()
