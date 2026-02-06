"""通用UI组件模块

提供ESG分析系统中使用的各种可视化组件，包括图表、卡片、指标展示等。
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
import math

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.config import ESG_DIMENSION_NAMES, ESG_COLORS


# ============== 数据类定义 ==============

@dataclass
class ScoreCardData:
    """评分卡片数据"""
    title: str
    score: float
    max_score: float = 100.0
    description: str = ""
    color: Optional[str] = None


@dataclass
class GapCardData:
    """差距卡片数据"""
    dimension: str
    current: float
    benchmark: float
    gap: float
    priority: str


@dataclass
class StrategyCardData:
    """策略卡片数据"""
    id: str
    title: str
    description: str
    dimension: str
    priority: str
    confidence: float
    actions: List[str]
    timeframe: str = ""


# ============== 布局组件 ==============

def render_header(title: str, subtitle: Optional[str] = None) -> None:
    """渲染页面头部
    
    Args:
        title: 主标题
        subtitle: 副标题（可选）
    """
    st.title(f"📊 {title}")
    if subtitle:
        st.markdown(f"<p style='color: gray; font-size: 1.1em;'>{subtitle}</p>", 
                   unsafe_allow_html=True)
    st.markdown("---")


def render_section_title(title: str, icon: str = "📌") -> None:
    """渲染章节标题
    
    Args:
        title: 标题文本
        icon: 图标
    """
    st.markdown(f"### {icon} {title}")


def render_info_box(message: str, type_: str = "info") -> None:
    """渲染信息框
    
    Args:
        message: 消息内容
        type_: 类型 (info/success/warning/error)
    """
    if type_ == "info":
        st.info(message)
    elif type_ == "success":
        st.success(message)
    elif type_ == "warning":
        st.warning(message)
    elif type_ == "error":
        st.error(message)


def render_progress_step(
    steps: List[str], 
    current: int, 
    completed: Optional[List[bool]] = None
) -> None:
    """渲染进度步骤条
    
    Args:
        steps: 步骤名称列表
        current: 当前步骤索引
        completed: 各步骤完成状态
    """
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if completed and completed[i]:
                st.markdown(f"✅ **{step}**")
            elif i == current:
                st.markdown(f"🔵 **{step}**")
            else:
                st.markdown(f"⚪ {step}")


# ============== 卡片组件 ==============

def render_score_card(
    data: ScoreCardData, 
    show_progress: bool = True,
    key: Optional[str] = None
) -> None:
    """渲染评分卡片
    
    Args:
        data: 评分卡片数据
        show_progress: 是否显示进度条
        key: 组件key
    """
    color = data.color or get_score_color(data.score)
    percentage = data.score / data.max_score
    
    html = f"""
    <div style="
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid {color};
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.9em; color: #666; margin-bottom: 4px;">{data.title}</div>
                <div style="font-size: 2em; font-weight: bold; color: {color};">
                    {data.score:.1f}<span style="font-size: 0.5em; color: #999;">/{data.max_score}</span>
                </div>
            </div>
            <div style="font-size: 3em; opacity: 0.3;">{get_score_emoji(data.score)}</div>
        </div>
    """
    
    if show_progress:
        html += f"""
        <div style="margin-top: 12px;">
            <div style="
                background: #e0e0e0;
                border-radius: 10px;
                height: 8px;
                overflow: hidden;
            ">
                <div style="
                    background: {color};
                    width: {percentage * 100}%;
                    height: 100%;
                    border-radius: 10px;
                    transition: width 0.3s ease;
                "></div>
            </div>
        </div>
        """
    
    if data.description:
        html += f'<div style="margin-top: 8px; font-size: 0.85em; color: #888;">{data.description}</div>'
    
    html += "</div>"
    
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(
    title: str,
    value: Any,
    unit: str = "",
    delta: Optional[float] = None,
    delta_description: str = "",
    key: Optional[str] = None
) -> None:
    """渲染指标卡片
    
    Args:
        title: 指标名称
        value: 指标值
        unit: 单位
        delta: 变化值
        delta_description: 变化描述
        key: 组件key
    """
    delta_color = "green" if delta and delta > 0 else "red" if delta and delta < 0 else "gray"
    delta_icon = "↑" if delta and delta > 0 else "↓" if delta and delta < 0 else "→"
    
    html = f"""
    <div style="
        background: white;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="font-size: 0.85em; color: #888; margin-bottom: 4px;">{title}</div>
        <div style="font-size: 1.8em; font-weight: bold; color: #333;">
            {value}<span style="font-size: 0.6em; color: #999; margin-left: 4px;">{unit}</span>
        </div>
    """
    
    if delta is not None:
        html += f"""
        <div style="margin-top: 8px; font-size: 0.85em;">
            <span style="color: {delta_color};">{delta_icon} {abs(delta):.1f}</span>
            <span style="color: #999; margin-left: 4px;">{delta_description}</span>
        </div>
        """
    
    html += "</div>"
    
    st.markdown(html, unsafe_allow_html=True)


def render_gap_card(data: GapCardData, key: Optional[str] = None) -> None:
    """渲染差距分析卡片
    
    Args:
        data: 差距卡片数据
        key: 组件key
    """
    dim_name = ESG_DIMENSION_NAMES.get(data.dimension, data.dimension)
    dim_color = ESG_COLORS.get(data.dimension, "#999")
    
    priority_colors = {"高": "#ff4d4f", "中": "#faad14", "低": "#52c41a"}
    priority_color = priority_colors.get(data.priority, "#999")
    
    gap_status = "落后" if data.gap > 0 else "领先" if data.gap < 0 else "持平"
    
    html = f"""
    <div style="
        background: white;
        border-radius: 10px;
        padding: 16px;
        border: 2px solid {dim_color};
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="display: flex; align-items: center;">
                <div style="
                    width: 12px; height: 12px; border-radius: 50%;
                    background: {dim_color}; margin-right: 8px;
                "></div>
                <span style="font-weight: bold; color: #333;">{dim_name} ({data.dimension})</span>
            </div>
            <span style="
                background: {priority_color}20;
                color: {priority_color};
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.8em;
            ">优先级 {data.priority}</span>
        </div>
        
        <div style="display: flex; justify-content: space-between; text-align: center;">
            <div>
                <div style="font-size: 0.8em; color: #888;">当前</div>
                <div style="font-size: 1.5em; font-weight: bold; color: #333;">{data.current:.1f}</div>
            </div>
            <div style="color: #ccc; font-size: 1.5em;">→</div>
            <div>
                <div style="font-size: 0.8em; color: #888;">标杆</div>
                <div style="font-size: 1.5em; font-weight: bold; color: #52c41a;">{data.benchmark:.1f}</div>
            </div>
            <div style="color: #ccc; font-size: 1.5em;">=</div>
            <div>
                <div style="font-size: 0.8em; color: #888;">差距</div>
                <div style="font-size: 1.5em; font-weight: bold; color: {'#ff4d4f' if data.gap > 0 else '#52c41a'};">
                    {'+' if data.gap > 0 else ''}{data.gap:.1f}
                </div>
            </div>
        </div>
        
        <div style="margin-top: 8px; text-align: center; font-size: 0.85em; color: #666;">
            相比标杆{gap_status} {abs(data.gap):.1f} 分
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def render_strategy_card(
    data: StrategyCardData,
    expanded: bool = False,
    key: Optional[str] = None
) -> None:
    """渲染策略建议卡片
    
    Args:
        data: 策略卡片数据
        expanded: 默认展开
        key: 组件key
    """
    dim_name = ESG_DIMENSION_NAMES.get(data.dimension, data.dimension)
    dim_color = ESG_COLORS.get(data.dimension, "#999")
    
    priority_emojis = {"高": "🔴", "中": "🟡", "低": "🟢"}
    priority_emoji = priority_emojis.get(data.priority, "⚪")
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"**{priority_emoji} {data.title}**")
            st.caption(f"{dim_name} | AI置信度: {data.confidence:.0%}")
        
        with col2:
            confidence_color = get_confidence_color(data.confidence)
            st.markdown(
                f"<div style='text-align: right;'>"
                f"<span style='background: {confidence_color}20; color: {confidence_color}; "
                f"padding: 2px 8px; border-radius: 4px; font-size: 0.8em;'>"
                f"{data.confidence:.0%}</span></div>",
                unsafe_allow_html=True
            )
        
        with st.expander("查看详情", expanded=expanded):
            st.markdown(f"**描述**: {data.description}")
            
            if data.timeframe:
                st.markdown(f"**预计周期**: {data.timeframe}")
            
            st.markdown("**行动项**:")
            for action in data.actions:
                st.markdown(f"- {action}")


# ============== 图表组件 ==============

def render_radar_chart(
    scores: Dict[str, float],
    benchmark_scores: Optional[Dict[str, float]] = None,
    title: str = "ESG评分雷达图",
    height: int = 400
) -> go.Figure:
    """渲染雷达图
    
    Args:
        scores: 各维度得分 {"E": 80, "S": 70, "G": 90}
        benchmark_scores: 标杆得分（可选）
        title: 图表标题
        height: 图表高度
        
    Returns:
        plotly Figure 对象
    """
    categories = [ESG_DIMENSION_NAMES.get(d, d) for d in ["E", "S", "G"]]
    values = [scores.get(d, 0) for d in ["E", "S", "G"]]
    values.append(values[0])  # 闭合图形
    categories.append(categories[0])
    
    fig = go.Figure()
    
    # 添加当前企业数据
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='当前企业',
        line=dict(color='#1890ff', width=2),
        fillcolor='rgba(24, 144, 255, 0.2)'
    ))
    
    # 添加标杆数据
    if benchmark_scores:
        bench_values = [benchmark_scores.get(d, 0) for d in ["E", "S", "G"]]
        bench_values.append(bench_values[0])
        fig.add_trace(go.Scatterpolar(
            r=bench_values,
            theta=categories,
            fill='toself',
            name='行业标杆',
            line=dict(color='#52c41a', width=2, dash='dash'),
            fillcolor='rgba(82, 196, 26, 0.1)'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#333'),
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        title=dict(
            text=title,
            font=dict(size=16),
            x=0.5
        ),
        height=height,
        margin=dict(l=80, r=80, t=80, b=80),
    )
    
    return fig


def render_bidirectional_bar(
    data: Dict[str, Tuple[float, float]],
    title: str = "双向对比图",
    left_label: str = "当前",
    right_label: str = "标杆",
    height: int = 300
) -> go.Figure:
    """渲染双向条形图
    
    Args:
        data: 数据 {维度: (当前值, 标杆值)}
        title: 图表标题
        left_label: 左侧标签
        right_label: 右侧标签
        height: 图表高度
        
    Returns:
        plotly Figure 对象
    """
    dimensions = list(data.keys())
    dim_names = [ESG_DIMENSION_NAMES.get(d, d) for d in dimensions]
    current_values = [data[d][0] for d in dimensions]
    benchmark_values = [data[d][1] for d in dimensions]
    
    fig = go.Figure()
    
    # 左侧（当前值，负值显示在左边）
    fig.add_trace(go.Bar(
        y=dim_names,
        x=[-v for v in current_values],
        name=left_label,
        orientation='h',
        marker_color='#1890ff',
        text=[f"{v:.1f}" for v in current_values],
        textposition='inside',
        hovertemplate='%{y}: %{text}<extra></extra>'
    ))
    
    # 右侧（标杆值）
    fig.add_trace(go.Bar(
        y=dim_names,
        x=benchmark_values,
        name=right_label,
        orientation='h',
        marker_color='#52c41a',
        text=[f"{v:.1f}" for v in benchmark_values],
        textposition='inside',
        hovertemplate='%{y}: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        barmode='relative',
        height=height,
        xaxis=dict(
            title='得分',
            range=[-100, 100],
            tickvals=[-100, -50, 0, 50, 100],
            ticktext=['100', '50', '0', '50', '100'],
        ),
        yaxis=dict(title=''),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=100, r=40, t=60, b=40),
    )
    
    return fig


def render_dimension_comparison(
    scores: Dict[str, float],
    weights: Dict[str, float],
    title: str = "维度得分对比",
    height: int = 350
) -> go.Figure:
    """渲染维度对比柱状图
    
    Args:
        scores: 各维度得分
        weights: 各维度权重
        title: 图表标题
        height: 图表高度
        
    Returns:
        plotly Figure 对象
    """
    dimensions = ["E", "S", "G"]
    dim_names = [ESG_DIMENSION_NAMES.get(d, d) for d in dimensions]
    values = [scores.get(d, 0) for d in dimensions]
    weight_values = [weights.get(d, 0) for d in dimensions]
    colors = [ESG_COLORS.get(d, "#999") for d in dimensions]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 得分柱状图
    fig.add_trace(
        go.Bar(
            x=dim_names,
            y=values,
            name='得分',
            marker_color=colors,
            text=[f"{v:.1f}" for v in values],
            textposition='outside',
        ),
        secondary_y=False,
    )
    
    # 权重折线图
    fig.add_trace(
        go.Scatter(
            x=dim_names,
            y=[w * 100 for w in weight_values],
            name='权重 (%)',
            mode='lines+markers+text',
            line=dict(color='#fa8c16', width=2),
            marker=dict(size=10),
            text=[f"{w:.0%}" for w in weight_values],
            textposition='top center',
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=50, r=50, t=80, b=40),
        showlegend=True,
    )
    
    fig.update_yaxes(
        title_text="得分",
        range=[0, 100],
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="权重 (%)",
        range=[0, 100],
        secondary_y=True
    )
    
    return fig


def render_topic_wordcloud(
    topics: List[Dict[str, Any]],
    title: str = "议题热度云图",
    height: int = 400
) -> go.Figure:
    """渲染议题词云图（使用散点图模拟）
    
    Args:
        topics: 议题列表 [{"name": "碳排放", "value": 80, "category": "E"}]
        title: 图表标题
        height: 图表高度
        
    Returns:
        plotly Figure 对象
    """
    if not topics:
        fig = go.Figure()
        fig.update_layout(title="暂无数据", height=height)
        return fig
    
    # 按热度排序并限制数量
    topics = sorted(topics, key=lambda x: x.get("value", 0), reverse=True)[:30]
    
    # 生成位置（简单的螺旋布局）
    positions = []
    golden_angle = math.pi * (3 - math.sqrt(5))
    for i in range(len(topics)):
        r = 0.3 * math.sqrt(i)
        theta = i * golden_angle
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        positions.append((x, y))
    
    # 创建散点图
    fig = go.Figure()
    
    for i, topic in enumerate(topics):
        name = topic.get("name", "")
        value = topic.get("value", 0)
        category = topic.get("category", "E")
        color = ESG_COLORS.get(category, "#999")
        
        # 字体大小根据热度计算
        font_size = 12 + int(value / 100 * 20)
        
        fig.add_trace(go.Scatter(
            x=[positions[i][0]],
            y=[positions[i][1]],
            mode='text',
            text=[name],
            textfont=dict(size=font_size, color=color),
            hovertemplate=f"{name}<br>热度: {value}<extra></extra>",
            showlegend=False,
        ))
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        height=height,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=60, b=20),
    )
    
    return fig


def render_gauge_chart(
    value: float,
    title: str = "综合评分",
    max_value: float = 100.0,
    height: int = 300
) -> go.Figure:
    """渲染仪表盘图
    
    Args:
        value: 当前值
        title: 图表标题
        max_value: 最大值
        height: 图表高度
        
    Returns:
        plotly Figure 对象
    """
    percentage = value / max_value
    
    # 根据百分比确定颜色
    if percentage >= 0.8:
        color = "#52c41a"
    elif percentage >= 0.6:
        color = "#1890ff"
    elif percentage >= 0.4:
        color = "#faad14"
    else:
        color = "#ff4d4f"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': f"/{max_value}", 'font': {'size': 36}},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.6},
            'bgcolor': 'white',
            'borderwidth': 2,
            'bordercolor': '#ccc',
            'steps': [
                {'range': [0, max_value * 0.4], 'color': '#fff1f0'},
                {'range': [max_value * 0.4, max_value * 0.6], 'color': '#fffbe6'},
                {'range': [max_value * 0.6, max_value * 0.8], 'color': '#e6f7ff'},
                {'range': [max_value * 0.8, max_value], 'color': '#f6ffed'},
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(l=30, r=30, t=50, b=30),
    )
    
    return fig


# ============== 辅助函数 ==============

def get_score_color(score: float) -> str:
    """根据分数获取颜色
    
    Args:
        score: 分数 (0-100)
        
    Returns:
        颜色代码
    """
    if score >= 80:
        return "#52c41a"
    elif score >= 60:
        return "#1890ff"
    elif score >= 40:
        return "#faad14"
    else:
        return "#ff4d4f"


def get_score_emoji(score: float) -> str:
    """根据分数获取表情符号
    
    Args:
        score: 分数 (0-100)
        
    Returns:
        表情符号
    """
    if score >= 80:
        return "🌟"
    elif score >= 60:
        return "👍"
    elif score >= 40:
        return "📊"
    else:
        return "⚠️"


def get_confidence_color(confidence: float) -> str:
    """根据置信度获取颜色
    
    Args:
        confidence: 置信度 (0-1)
        
    Returns:
        颜色代码
    """
    if confidence >= 0.85:
        return "#52c41a"
    elif confidence >= 0.70:
        return "#1890ff"
    elif confidence >= 0.55:
        return "#faad14"
    else:
        return "#ff4d4f"


def render_empty_state(
    message: str = "暂无数据",
    sub_message: str = "请上传文件或选择示例数据开始分析",
    icon: str = "📂"
) -> None:
    """渲染空状态提示
    
    Args:
        message: 主消息
        sub_message: 副消息
        icon: 图标
    """
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 60px 20px;
        background: #f5f5f5;
        border-radius: 12px;
        border: 2px dashed #d9d9d9;
    ">
        <div style="font-size: 4em; margin-bottom: 16px;">{icon}</div>
        <div style="font-size: 1.2em; color: #333; margin-bottom: 8px;">{message}</div>
        <div style="font-size: 0.9em; color: #888;">{sub_message}</div>
    </div>
    """, unsafe_allow_html=True)
