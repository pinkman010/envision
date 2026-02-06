"""模块三：披露差距诊断与对标

功能：向量相似度计算 + 行业对标分析
"""

import streamlit as st
import plotly.graph_objects as go

from analysis.gap_analyzer import GapAnalyzer
from core.constants import ESG_DIMENSION_NAMES, GAP_THRESHOLD_HIGH, GAP_THRESHOLD_MEDIUM
from ui.components.common import render_metric_card, render_bidirectional_bar
from ui.state import AppState


def render():
    """渲染差距诊断模块"""
    st.markdown('<h1 class="module-title">🔍 披露差距诊断与对标</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: 向量相似度计算 + 行业对标分析</p>', unsafe_allow_html=True)
    
    # 执行分析
    if AppState.get('gap_analysis') is None:
        gap_analyzer = GapAnalyzer()
        result = gap_analyzer.analyze_gap(AppState.get('benchmark_company', '维斯塔斯'))
        AppState.set('gap_analysis', result)
    
    gap_data = AppState.get('gap_analysis')
    
    render_score_comparison(gap_data)
    render_dimension_comparison(gap_data)
    render_indicator_gaps(gap_data)


def render_score_comparison(gap_data: dict):
    """渲染综合评分对比"""
    st.markdown("### 📋 ESG综合评分对比")
    
    cols = st.columns(4)
    
    with cols[0]:
        render_metric_card("远景能源", f"{gap_data.get('company_score', 0):.1f}分")
    
    with cols[1]:
        benchmark_name = AppState.get('benchmark_company', '维斯塔斯')
        render_metric_card(benchmark_name, f"{gap_data.get('benchmark_score', 0):.1f}分", '#52c41a')
    
    with cols[2]:
        gap = gap_data.get('gap', 0)
        gap_color = "#ff4d4f" if gap > 10 else "#faad14" if gap > 5 else "#52c41a"
        render_metric_card("综合差距", f"{gap:.1f}分", gap_color)
    
    with cols[3]:
        # 计算披露深度得分（基于指标覆盖度）
        indicators = gap_data.get('indicator_gaps', [])
        if indicators:
            # 基于指标披露等级计算得分
            disclosure_levels = {'详细': 100, '中等': 60, '基础': 30, '未知': 0}
            disclosure_score = sum(
                disclosure_levels.get(i.get('disclosure_level', '未知'), 0) 
                for i in indicators
            ) / len(indicators)
        else:
            disclosure_score = 0.0
        render_metric_card("披露深度得分", f"{disclosure_score:.1f}分", '#1890ff')
    
    st.markdown("<br>", unsafe_allow_html=True)


def render_dimension_comparison(gap_data: dict):
    """渲染维度对比"""
    st.markdown("### 📊 维度表现对比")
    
    dimensions = ['E', 'S', 'G']
    dimension_gaps = gap_data.get('dimension_gaps', {})
    
    company_scores = [dimension_gaps.get(d, {}).get('company', 0) for d in dimensions]
    benchmark_scores = [dimension_gaps.get(d, {}).get('benchmark', 0) for d in dimensions]
    
    categories = [f"{ESG_DIMENSION_NAMES[d]}({d})" for d in dimensions]
    
    fig = render_bidirectional_bar(
        categories=categories,
        left_values=[-s for s in company_scores],
        right_values=benchmark_scores,
        left_label='远景能源',
        right_label=AppState.get('benchmark_company', '维斯塔斯')
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_indicator_gaps(gap_data: dict):
    """渲染指标级差距分析"""
    st.markdown("### 🔍 指标级差距分析")
    
    indicators = gap_data.get('indicator_gaps', [])[:6]
    
    if not indicators:
        st.info("暂无指标差距数据")
        return
    
    indicator_names = [i.get('name', i.get('id', '')) for i in indicators]
    company_vals = [i.get('company_score', 0) for i in indicators]
    benchmark_vals = [i.get('benchmark_score', 0) for i in indicators]
    gaps = [i.get('gap', 0) for i in indicators]
    
    fig = go.Figure()
    
    # 公司得分
    fig.add_trace(go.Bar(
        name='远景能源',
        y=indicator_names,
        x=company_vals,
        orientation='h',
        marker_color='#1890ff'
    ))
    
    # 标杆得分
    benchmark_name = AppState.get('benchmark_company', '维斯塔斯')
    fig.add_trace(go.Bar(
        name=benchmark_name,
        y=indicator_names,
        x=benchmark_vals,
        orientation='h',
        marker_color='#52c41a'
    ))
    
    # 差距标注
    for i, (name, gap) in enumerate(zip(indicator_names, gaps)):
        color = '#ff4d4f' if gap > GAP_THRESHOLD_HIGH else '#faad14' if gap > GAP_THRESHOLD_MEDIUM else '#52c41a'
        fig.add_annotation(
            x=max(company_vals[i], benchmark_vals[i]) + 5,
            y=name,
            text=f"差距 {gap:.0f}分",
            showarrow=False,
            font=dict(color=color, size=11)
        )
    
    fig.update_layout(
        barmode='group',
        height=350,
        xaxis=dict(title="得分", range=[0, 105]),
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 红色预警
    high_gaps = [i for i in indicators if i.get('severity') == '高']
    if high_gaps:
        st.markdown("### ⚠️ 重点改进指标")
        for ind in high_gaps:
            st.error(f"🔴 **{ind.get('name', '')}**: 差距 {ind.get('gap', 0):.0f}分 - 披露深度{ind.get('disclosure_level', '未知')}")
