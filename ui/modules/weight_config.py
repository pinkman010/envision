"""模块二：智能权重配置

功能：AHP层次分析法 + 一致性检验 + AI评估
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from fusion.ahp_fusion import AHPFusionEngine
from core.constants import (
    EVALUATION_PERSPECTIVES,
    AHP_SCALE_LABELS,
    AHP_CONSISTENCY_THRESHOLD
)
from ui.state import AppState


def render():
    """渲染权重配置模块"""
    st.markdown('<h1 class="module-title">⚖️ 智能权重配置</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: AHP层次分析法 + 一致性检验 + 舆情动态调整</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_matrix_config()
    
    with col2:
        render_consistency_check()
        render_weights_display()


def render_matrix_config():
    """渲染矩阵配置部分"""
    st.markdown("### 📝 判断矩阵配置")
    
    # AI虚拟专家评估
    st.markdown("#### 🤖 AI虚拟专家评估")
    st.write("本次评估更关注哪种视角？")
    
    perspective_options = [
        EVALUATION_PERSPECTIVES['financial']['name'],
        EVALUATION_PERSPECTIVES['compliance']['name'],
        EVALUATION_PERSPECTIVES['brand']['name'],
        "D. 自定义配置"
    ]
    
    perspective = st.radio(
        "选择评估视角",
        perspective_options,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # 映射选择到内部键
    perspective_map = {
        EVALUATION_PERSPECTIVES['financial']['name']: 'financial',
        EVALUATION_PERSPECTIVES['compliance']['name']: 'compliance',
        EVALUATION_PERSPECTIVES['brand']['name']: 'brand',
        "D. 自定义配置": 'custom'
    }
    
    selected_perspective = perspective_map[perspective]
    AppState.set('perspective', selected_perspective)
    
    # 使用AHP引擎生成建议
    ahp = AHPFusionEngine()
    suggestion = ahp.generate_suggestions(selected_perspective)
    
    if selected_perspective != 'custom':
        render_ai_suggestion(ahp, suggestion)
    else:
        render_custom_config(ahp)
    
    # 显示判断矩阵
    st.markdown("#### 判断矩阵")
    matrix_df = pd.DataFrame(
        ahp.matrix,
        index=['E', 'S', 'G'],
        columns=['E', 'S', 'G']
    )
    st.dataframe(matrix_df.style.format("{:.2f}"), use_container_width=True)


def render_ai_suggestion(ahp: AHPFusionEngine, suggestion: dict):
    """渲染AI建议"""
    st.info(f"🤖 AI建议: {suggestion.get('reasoning', '')}")
    
    weights = suggestion.get('weights', {})
    
    # 构建判断矩阵
    ahp.build_matrix(
        ['E', 'S', 'G'],
        {
            (0, 1): weights.get('E', 0.33) / weights.get('S', 0.33),
            (0, 2): weights.get('E', 0.33) / weights.get('G', 0.33),
            (1, 2): weights.get('S', 0.33) / weights.get('G', 0.33)
        }
    )
    
    weights_arr, ci, cr = ahp.calculate_weights()
    AppState.set('ahp_weights', ahp.get_weights_dict())
    AppState.set('ahp_cr', cr)


def render_custom_config(ahp: AHPFusionEngine):
    """渲染自定义配置"""
    st.markdown("#### 自定义权重配置")
    
    col_e, col_s, col_g = st.columns(3)
    
    with col_e:
        e_slider = st.slider("E vs S", 1/9, 9.0, 1.0, 0.1, format="%.1f")
    with col_s:
        s_slider = st.slider("E vs G", 1/9, 9.0, 1.0, 0.1, format="%.1f")
    with col_g:
        g_slider = st.slider("S vs G", 1/9, 9.0, 1.0, 0.1, format="%.1f")
    
    # 自然语言标签
    def get_label(value: float) -> str:
        if value > 7:
            return "绝对重要"
        elif value > 5:
            return "明显重要"
        elif value > 3:
            return "稍微重要"
        elif value > 1:
            return "略微重要"
        elif value == 1:
            return "同等重要"
        elif value > 1/3:
            return "略微不重要"
        elif value > 1/5:
            return "稍微不重要"
        elif value > 1/7:
            return "明显不重要"
        return "绝对不重要"
    
    st.caption(f"E相对于S: {get_label(e_slider)} | E相对于G: {get_label(s_slider)} | S相对于G: {get_label(g_slider)}")
    
    ahp.build_matrix(['E', 'S', 'G'], {(0, 1): e_slider, (0, 2): s_slider, (1, 2): g_slider})
    weights_arr, ci, cr = ahp.calculate_weights()
    AppState.set('ahp_weights', ahp.get_weights_dict())
    AppState.set('ahp_cr', cr)


def render_consistency_check():
    """渲染一致性检验"""
    st.markdown("### 🚦 一致性检验")
    
    cr = AppState.get('ahp_cr')
    
    if cr is None:
        st.info("请先配置判断矩阵")
        return
    
    threshold = AHP_CONSISTENCY_THRESHOLD
    
    if cr < threshold:
        st.markdown(f"""
        <div class="consistency-pass">
            <h4 style="margin: 0; color: #28a745;">✓ 逻辑自洽</h4>
            <p style="margin: 0.5rem 0 0 0; color: #666;">CR = {cr:.4f} < {threshold}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="consistency-fail">
            <h4 style="margin: 0; color: #dc3545;">✗ 一致性不足</h4>
            <p style="margin: 0.5rem 0 0 0; color: #666;">CR = {cr:.4f} ≥ {threshold}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🤖 AI自动修正", key="ai_fix"):
            ahp = AHPFusionEngine()
            weights = AppState.get('ahp_weights', {})
            if weights:
                ahp.build_matrix(['E', 'S', 'G'], {
                    (0, 1): weights.get('E', 0.33) / weights.get('S', 0.33),
                    (0, 2): weights.get('E', 0.33) / weights.get('G', 0.33),
                    (1, 2): weights.get('S', 0.33) / weights.get('G', 0.33)
                })
                ahp.auto_correct()
                weights_arr, ci, cr = ahp.calculate_weights()
                AppState.set('ahp_weights', ahp.get_weights_dict())
                AppState.set('ahp_cr', cr)
                st.rerun()


def render_weights_display():
    """渲染权重展示"""
    st.markdown("### 📊 权重分配")
    
    weights = AppState.get('ahp_weights')
    
    if not weights:
        st.info("暂无权重数据")
        return
    
    # 雷达图
    fig = go.Figure(data=go.Scatterpolar(
        r=[weights.get('E', 0), weights.get('S', 0), weights.get('G', 0), weights.get('E', 0)],
        theta=['环境(E)', '社会(S)', '治理(G)', '环境(E)'],
        fill='toself',
        marker_color='#1890ff'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 0.6])),
        showlegend=False,
        height=300,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 数值显示
    st.metric("环境(E)", f"{weights.get('E', 0):.1%}")
    st.metric("社会(S)", f"{weights.get('S', 0):.1%}")
    st.metric("治理(G)", f"{weights.get('G', 0):.1%}")
