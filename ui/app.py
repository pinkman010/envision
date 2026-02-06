"""远景能源 ESG 智能分析系统 - 重构版

整合四大功能模块：
1. 行业实质性议题全景图（LDA+词云+趋势图）
2. 智能权重配置（AHP+AI评估+一致性检验）
3. 披露差距诊断与对标（向量相似度+双向条形图）
4. AI策略建议生成器（诊断卡片+行动清单+对话微调）
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import streamlit as st

# 导入样式和状态管理
from ui.styles import apply_styles
from ui.state import AppState

# 导入组件
from ui.components import sidebar

# 导入模块
from ui.modules import topic_analysis, weight_config, gap_analysis, strategy_generator

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="远景能源 ESG 智能分析系统",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 初始化 ====================
def init():
    """初始化应用"""
    AppState.init()
    apply_styles()


# ==================== 模块导航 ====================
def render_module_nav():
    """渲染模块导航"""
    modules = [
        ("📊", "议题全景图", 0),
        ("⚖️", "智能权重配置", 1),
        ("🔍", "披露差距诊断", 2),
        ("💡", "AI策略建议", 3)
    ]
    
    cols = st.columns(4)
    for i, (icon, name, idx) in enumerate(modules):
        with cols[i]:
            is_active = AppState.get_current_module() == idx
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon} 模块{idx+1}：{name}", 
                        key=f"module_{idx}",
                        use_container_width=True,
                        type=btn_type):
                AppState.switch_module(idx)
                st.rerun()


# ==================== 主程序 ====================
def main():
    """主入口"""
    init()
    
    # 渲染侧边栏
    sidebar.render()
    
    # 主标题
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">🌿 远景能源 ESG 智能分析系统</h1>
        <p style="color: #666; font-size: 1.1rem;">基于AI的ESG议题分析、权重配置、差距诊断与策略生成平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 模块导航
    render_module_nav()
    st.markdown("---")
    
    # 渲染当前模块
    current = AppState.get_current_module()
    
    module_renderers = {
        0: topic_analysis.render,
        1: weight_config.render,
        2: gap_analysis.render,
        3: strategy_generator.render
    }
    
    renderer = module_renderers.get(current)
    if renderer:
        renderer()
    else:
        st.error(f"未知模块索引: {current}")


if __name__ == "__main__":
    main()
