"""侧边栏组件

全局侧边栏，包含配置和系统状态。
"""

import streamlit as st

from utils.ollama_utils import ensure_ollama_running
from core.constants import ANALYSIS_YEARS, BENCHMARK_COMPANIES
from ui.state import AppState


def render():
    """渲染侧边栏"""
    with st.sidebar:
        # Logo区域
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="margin: 0; color: #1a1a2e;">🌿 ESG 智能分析系统</h2>
            <p style="color: #666; font-size: 0.85rem; margin-top: 0.5rem;">版本: v1.1.0</p>
            <p style="color: #666; font-size: 0.85rem;">更新日期: 2025-01</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 全局配置
        st.markdown("### ⚙️ 全局配置")
        
        year = st.selectbox("分析年度", ANALYSIS_YEARS, index=0)
        if year != AppState.get('analysis_year'):
            AppState.set('analysis_year', year)
            AppState.reset_analysis()
        
        benchmark = st.selectbox("对标企业", BENCHMARK_COMPANIES, index=0)
        if benchmark != AppState.get('benchmark_company'):
            AppState.set('benchmark_company', benchmark)
            AppState.reset_analysis()
        
        st.markdown("---")
        
        # 系统状态
        st.markdown("### 📊 系统状态")
        render_system_status()
        
        st.markdown("---")
        
        # 使用说明
        with st.expander("ℹ️ 使用说明"):
            st.write("""
            1. **议题全景图**: 查看行业ESG议题热度和趋势
            2. **智能权重配置**: 配置AHP权重并进行一致性检验
            3. **披露差距诊断**: 对标行业标杆，识别差距
            4. **AI策略建议**: 生成针对性改进策略
            """)


def render_system_status():
    """渲染系统状态"""
    ollama_ok, msg = ensure_ollama_running()
    AppState.set('ollama_status', ollama_ok)
    
    if ollama_ok:
        st.markdown('<span class="status-light status-green"></span>Ollama 服务运行中', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-light status-red"></span>Ollama 未连接', unsafe_allow_html=True)
    
    st.markdown('<span class="status-light status-green"></span>知识库已就绪', unsafe_allow_html=True)
