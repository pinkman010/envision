"""通用UI组件

可复用的UI组件，如图表、卡片等。
"""

from typing import Dict, List, Any, Optional
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.styles import ESG_COLORS, ESG_DIMENSION_NAMES, SEVERITY_STYLES, PRIORITY_COLORS


def render_metric_card(title: str, value: str, color: str = '#1890ff') -> None:
    """渲染指标卡片
    
    Args:
        title: 标题
        value: 值
        color: 颜色代码
    """
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {color};">{value}</div>
        <div class="metric-label">{title}</div>
    </div>
    """, unsafe_allow_html=True)


def render_diagnosis_card(title: str, severity: str, gap: float) -> None:
    """渲染诊断卡片
    
    Args:
        title: 诊断标题
        severity: 严重程度（高/中/低）
        gap: 差距分数
    """
    style = SEVERITY_STYLES.get(severity, SEVERITY_STYLES['中'])
    
    st.markdown(f"""
    <div class="diagnosis-card {style['class']}">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{style['icon']}</div>
        <h4 style="margin: 0 0 0.5rem 0;">{title}</h4>
        <p style="color: {style['color']}; font-weight: 600; margin: 0;">差距 {gap:.0f}分</p>
    </div>
    """, unsafe_allow_html=True)


def render_radar_chart(
    values: List[float],
    labels: Optional[List[str]] = None,
    title: str = "ESG评分"
) -> go.Figure:
    """渲染雷达图
    
    Args:
        values: 三个维度的值
        labels: 标签列表，默认使用ESG维度
        title: 图表标题
        
    Returns:
        Plotly图表对象
    """
    if labels is None:
        labels = [ESG_DIMENSION_NAMES['E'], ESG_DIMENSION_NAMES['S'], ESG_DIMENSION_NAMES['G']]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill='toself',
        marker_color='#1890ff'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=300,
        margin=dict(l=40, r=40, t=40, b=40),
        title=title
    )
    
    return fig


def render_bidirectional_bar(
    categories: List[str],
    left_values: List[float],
    right_values: List[float],
    left_label: str,
    right_label: str
) -> go.Figure:
    """渲染双向条形图
    
    Args:
        categories: 类别列表
        left_values: 左侧值（应为负数）
        right_values: 右侧值
        left_label: 左侧标签
        right_label: 右侧标签
        
    Returns:
        Plotly图表对象
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(left_label, right_label),
        shared_yaxes=True
    )
    
    colors = [ESG_COLORS['E'], ESG_COLORS['S'], ESG_COLORS['G']]
    
    # 左侧（负值）
    fig.add_trace(
        go.Bar(
            y=categories,
            x=left_values,
            orientation='h',
            marker_color=colors[:len(categories)],
            text=[f"{abs(v):.1f}" for v in left_values],
            textposition='inside',
            name=left_label
        ),
        row=1, col=1
    )
    
    # 右侧（正值）
    fig.add_trace(
        go.Bar(
            y=categories,
            x=right_values,
            orientation='h',
            marker_color=colors[:len(categories)],
            text=[f"{v:.1f}" for v in right_values],
            textposition='inside',
            name=right_label
        ),
        row=1, col=2
    )
    
    max_val = max(abs(min(left_values)), max(right_values)) * 1.2
    
    fig.update_layout(
        barmode='relative',
        height=300,
        showlegend=False,
        xaxis=dict(range=[-max_val, 0]),
        xaxis2=dict(range=[0, max_val])
    )
    
    return fig


def render_priority_badge(priority: str) -> None:
    """渲染优先级标签
    
    Args:
        priority: 优先级（高/中/低）
    """
    color = PRIORITY_COLORS.get(priority, '#666')
    st.markdown(f"""
    <div style="background: {color}; color: white; padding: 0.3rem 0.8rem; 
                border-radius: 12px; text-align: center; font-weight: 600;">
        {priority}优先级
    </div>
    """, unsafe_allow_html=True)


def render_confidence_badge(confidence: Dict[str, Any]) -> None:
    """渲染置信度标签
    
    Args:
        confidence: 置信度信息字典
    """
    level = confidence.get('level', '建议人工复核')
    needs_review = confidence.get('needs_review', True)
    
    color = '#52c41a' if not needs_review else '#faad14'
    
    st.markdown(f"""
    <div style="background: {color}20; color: {color}; padding: 0.3rem 0.8rem; 
                border-radius: 12px; text-align: center; font-size: 0.85rem; 
                border: 1px solid {color};">
        🤖 {level}
    </div>
    """, unsafe_allow_html=True)
