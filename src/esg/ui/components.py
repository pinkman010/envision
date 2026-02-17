"""通用UI组件模块（简化版）

提供ESG分析系统中使用的基础可视化组件。
简化版：只保留评分卡片、差距卡片、雷达图、双向条形图。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go

from src.esg.config import ESG_COLORS, ESG_DIMENSION_NAMES

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


# ============== 布局组件 ==============


def render_header(title: str, subtitle: Optional[str] = None) -> None:
    """渲染页面头部"""
    import streamlit as st

    st.title(f"📊 {title}")
    if subtitle:
        st.markdown(
            f"<p style='color: gray; font-size: 1.1em;'>{subtitle}</p>", unsafe_allow_html=True
        )
    st.markdown("---")


def render_section_title(title: str, icon: str = "📌") -> None:
    """渲染章节标题"""
    import streamlit as st

    st.markdown(f"### {icon} {title}")


def render_info_box(message: str, type_: str = "info") -> None:
    """渲染信息框"""
    import streamlit as st

    if type_ == "info":
        st.info(message)
    elif type_ == "success":
        st.success(message)
    elif type_ == "warning":
        st.warning(message)
    elif type_ == "error":
        st.error(message)


# ============== 卡片组件 ==============


def render_score_card(
    data: ScoreCardData, show_progress: bool = True, key: Optional[str] = None
) -> None:
    """渲染评分卡片"""
    import streamlit as st

    color = data.color or get_score_color(data.score)
    percentage = data.score / data.max_score

    with st.container():
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

        if show_progress:
            st.progress(float(percentage), text="")

        if data.description:
            st.markdown(
                f'<div style="font-size: 0.85em; color: #888;">{data.description}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def render_gap_card(data: GapCardData, key: Optional[str] = None) -> None:
    """渲染差距分析卡片"""
    import streamlit as st

    dim_name = ESG_DIMENSION_NAMES.get(data.dimension, data.dimension)
    dim_color = ESG_COLORS.get(data.dimension, "#999")

    priority_colors = {"高": "#ff4d4f", "中": "#faad14", "低": "#52c41a"}
    priority_color = priority_colors.get(data.priority, "#999")

    gap_status = "落后" if data.gap > 0 else "领先" if data.gap < 0 else "持平"

    with st.container():
        # 标题行
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{dim_name} ({data.dimension})**")
        with col2:
            st.markdown(
                f"<span style='color: {priority_color}; font-size: 0.8em;'>优先级 {data.priority}</span>",
                unsafe_allow_html=True,
            )

        # 数据对比
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("当前", f"{data.current:.1f}")
        with col2:
            st.metric("标杆", f"{data.benchmark:.1f}")
        with col3:
            gap_color = "#ff4d4f" if data.gap > 0 else "#52c41a"
            gap_sign = "+" if data.gap > 0 else ""
            st.markdown("**差距**")
            st.markdown(
                f"<span style='color: {gap_color}; font-size: 1.2em; font-weight: bold;'>{gap_sign}{data.gap:.1f}</span>",
                unsafe_allow_html=True,
            )

        # 状态说明
        st.caption(f"相比标杆{gap_status} {abs(data.gap):.1f} 分")


# ============== 图表组件 ==============


def render_radar_chart(
    scores: Dict[str, float],
    benchmark_scores: Optional[Dict[str, float]] = None,
    title: str = "ESG评分雷达图",
    height: int = 400,
) -> go.Figure:
    """渲染雷达图"""
    categories = [ESG_DIMENSION_NAMES.get(d, d) for d in ["E", "S", "G"]]
    values = [scores.get(d, 0) for d in ["E", "S", "G"]]
    values.append(values[0])  # 闭合图形
    categories.append(categories[0])

    fig = go.Figure()

    # 添加当前企业数据
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="当前企业",
            line=dict(color="#1890ff", width=2),
            fillcolor="rgba(24, 144, 255, 0.2)",
        )
    )

    # 添加标杆数据
    if benchmark_scores:
        bench_values = [benchmark_scores.get(d, 0) for d in ["E", "S", "G"]]
        bench_values.append(bench_values[0])
        fig.add_trace(
            go.Scatterpolar(
                r=bench_values,
                theta=categories,
                fill="toself",
                name="行业标杆",
                line=dict(color="#52c41a", width=2, dash="dash"),
                fillcolor="rgba(82, 196, 26, 0.1)",
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#333"),
            ),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        title=dict(text=title, font=dict(size=16), x=0.5),
        height=height,
        margin=dict(l=80, r=80, t=80, b=80),
    )

    return fig


def render_bidirectional_bar(
    data: Dict[str, Tuple[float, float]],
    title: str = "双向对比图",
    left_label: str = "当前",
    right_label: str = "标杆",
    height: int = 300,
) -> go.Figure:
    """渲染双向条形图"""
    dimensions = list(data.keys())
    dim_names = [ESG_DIMENSION_NAMES.get(d, d) for d in dimensions]
    current_values = [data[d][0] for d in dimensions]
    benchmark_values = [data[d][1] for d in dimensions]

    fig = go.Figure()

    # 左侧（当前值，负值显示在左边）
    fig.add_trace(
        go.Bar(
            y=dim_names,
            x=[-v for v in current_values],
            name=left_label,
            orientation="h",
            marker_color="#1890ff",
            text=[f"{v:.1f}" for v in current_values],
            textposition="inside",
            hovertemplate="%{y}: %{text}<extra></extra>",
        )
    )

    # 右侧（标杆值）
    fig.add_trace(
        go.Bar(
            y=dim_names,
            x=benchmark_values,
            name=right_label,
            orientation="h",
            marker_color="#52c41a",
            text=[f"{v:.1f}" for v in benchmark_values],
            textposition="inside",
            hovertemplate="%{y}: %{text}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        barmode="relative",
        height=height,
        xaxis=dict(
            title="得分",
            range=[-100, 100],
            tickvals=[-100, -50, 0, 50, 100],
            ticktext=["100", "50", "0", "50", "100"],
        ),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=100, r=40, t=60, b=40),
    )

    return fig


def render_gauge_chart(
    value: float, title: str = "综合评分", max_value: float = 100.0, height: int = 300
) -> go.Figure:
    """渲染仪表盘图"""
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

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": f"/{max_value}", "font": {"size": 36}},
            title={"text": title, "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, max_value], "tickwidth": 1},
                "bar": {"color": color, "thickness": 0.6},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "#ccc",
                "steps": [
                    {"range": [0, max_value * 0.4], "color": "#fff1f0"},
                    {"range": [max_value * 0.4, max_value * 0.6], "color": "#fffbe6"},
                    {"range": [max_value * 0.6, max_value * 0.8], "color": "#e6f7ff"},
                    {"range": [max_value * 0.8, max_value], "color": "#f6ffed"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": value,
                },
            },
        )
    )

    fig.update_layout(
        height=height,
        margin=dict(l=30, r=30, t=50, b=30),
    )

    return fig


# ============== 辅助函数 ==============


def get_score_color(score: float) -> str:
    """根据分数获取颜色"""
    if score >= 80:
        return "#52c41a"
    elif score >= 60:
        return "#1890ff"
    elif score >= 40:
        return "#faad14"
    else:
        return "#ff4d4f"


def get_score_emoji(score: float) -> str:
    """根据分数获取表情符号"""
    if score >= 80:
        return "🌟"
    elif score >= 60:
        return "👍"
    elif score >= 40:
        return "📊"
    else:
        return "⚠️"


def render_empty_state(
    message: str = "暂无数据",
    sub_message: str = "请上传文件或选择示例数据开始分析",
    icon: str = "📂",
) -> None:
    """渲染空状态提示"""
    import streamlit as st

    st.markdown(
        f"""
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
    """,
        unsafe_allow_html=True,
    )
