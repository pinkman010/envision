"""通用UI组件模块

提供ESG分析系统中使用的各种可视化组件，包括图表、卡片、指标展示等。
"""

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

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
    target_audiences: List[str] = None
    communication_style: str = "正式"
    recommended_channels: List[Dict[str, str]] = None

    def __post_init__(self):
        """初始化默认值"""
        if self.target_audiences is None:
            self.target_audiences = []
        if self.recommended_channels is None:
            self.recommended_channels = []


# ============== 布局组件 ==============


def render_header(title: str, subtitle: Optional[str] = None) -> None:
    """渲染页面头部

    Args:
        title: 主标题
        subtitle: 副标题（可选）
    """
    st.title(f"📊 {title}")
    if subtitle:
        st.markdown(
            f"<p style='color: gray; font-size: 1.1em;'>{subtitle}</p>", unsafe_allow_html=True
        )
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
    steps: List[str], current: int, completed: Optional[List[bool]] = None
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
    data: ScoreCardData, show_progress: bool = True, key: Optional[str] = None
) -> None:
    """渲染评分卡片

    Args:
        data: 评分卡片数据
        show_progress: 是否显示进度条
        key: 组件key
    """
    color = data.color or get_score_color(data.score)
    percentage = data.score / data.max_score

    # 使用st.container和原生组件替代HTML
    with st.container():
        # 卡片背景
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
            # 使用原生Streamlit progress bar
            st.progress(float(percentage), text="")

        if data.description:
            st.markdown(
                f'<div style="font-size: 0.85em; color: #888;">{data.description}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def render_metric_card(
    title: str,
    value: Any,
    unit: str = "",
    delta: Optional[float] = None,
    delta_description: str = "",
    key: Optional[str] = None,
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
    with st.container():
        st.caption(title)
        st.markdown(f"**{value}** {unit}")

        if delta is not None:
            delta_color = "green" if delta > 0 else "red" if delta < 0 else "gray"
            delta_icon = "↑" if delta > 0 else "↓" if delta < 0 else "→"
            st.markdown(f":{delta_color}[{delta_icon} {abs(delta):.1f}] {delta_description}")


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


def render_strategy_card(
    data: StrategyCardData,
    expanded: bool = False,
    key: Optional[str] = None,
    disabled: bool = False,
) -> None:
    """渲染策略建议卡片

    Args:
        data: 策略卡片数据
        expanded: 默认展开
        key: 组件key
        disabled: 是否置灰显示
    """
    dim_name = ESG_DIMENSION_NAMES.get(data.dimension, data.dimension)
    dim_color = ESG_COLORS.get(data.dimension, "#999")

    priority_emojis = {"高": "🔴", "中": "🟡", "低": "🟢"}
    priority_emoji = priority_emojis.get(data.priority, "⚪")

    # 受众标签颜色映射
    audience_colors = {
        "投资者": ("#1890ff", "🔵"),  # 蓝色
        "监管机构": ("#ff4d4f", "🔴"),  # 红色
        "员工": ("#52c41a", "🟢"),  # 绿色
        "社区/公众": ("#faad14", "🟠"),  # 橙色
        "供应链伙伴": ("#722ed1", "🟣"),  # 紫色
        "评级机构": ("#13c2c2", "⚪"),  # 青色
    }

    # 透明度处理（置灰时）
    opacity = "0.5" if disabled else "1.0"

    with st.container():
        # 受众标签行
        if data.target_audiences:
            audience_tags_html = ""
            for audience in data.target_audiences:
                color, emoji = audience_colors.get(audience, ("#999", "⚪"))
                audience_tags_html += (
                    f'<span style="'
                    f"background: {color}20; "
                    f"color: {color}; "
                    f"padding: 2px 8px; "
                    f"border-radius: 10px; "
                    f"font-size: 0.75em; "
                    f"margin-right: 6px; "
                    f"border: 1px solid {color}40; "
                    f"opacity: {opacity};"
                    f'">{emoji} {audience}</span>'
                )
            st.markdown(
                f"<div style='margin-bottom: 8px; opacity: {opacity};'>{audience_tags_html}</div>",
                unsafe_allow_html=True,
            )

        col1, col2 = st.columns([4, 1])

        with col1:
            title_style = f"opacity: {opacity};" if disabled else ""
            st.markdown(
                f"<div style='{title_style}'>**{priority_emoji} {data.title}**</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"{dim_name} | AI置信度: {data.confidence:.0%}")

        with col2:
            confidence_color = get_confidence_color(data.confidence)
            st.markdown(
                f"<div style='text-align: right; opacity: {opacity};'>"
                f"<span style='background: {confidence_color}20; color: {confidence_color}; "
                f"padding: 2px 8px; border-radius: 4px; font-size: 0.8em;'>"
                f"{data.confidence:.0%}</span></div>",
                unsafe_allow_html=True,
            )

        # 沟通风格标签
        if data.communication_style:
            style_colors = {
                "正式": "#595959",
                "亲和": "#52c41a",
                "技术": "#1890ff",
                "营销": "#fa8c16",
            }
            style_color = style_colors.get(data.communication_style, "#999")
            st.markdown(
                f"<div style='margin-top: 4px; opacity: {opacity};'>"
                f"<span style='font-size: 0.75em; color: {style_color};'>"
                f"💬 {data.communication_style}风格</span></div>",
                unsafe_allow_html=True,
            )

        with st.expander("查看详情", expanded=expanded):
            content_style = f"opacity: {opacity};" if disabled else ""
            st.markdown(
                f"<div style='{content_style}'>**描述**: {data.description}</div>",
                unsafe_allow_html=True,
            )

            if data.timeframe:
                st.markdown(
                    f"<div style='{content_style}'>**预计周期**: {data.timeframe}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("**行动项**:")
            for action in data.actions:
                st.markdown(
                    f"<div style='{content_style}'>- {action}</div>", unsafe_allow_html=True
                )

            # 建议沟通渠道
            if data.recommended_channels:
                st.markdown("---")
                st.markdown("**💬 建议沟通渠道**")

                # 分离主渠道和辅助渠道
                primary_channels = [
                    c for c in data.recommended_channels if c.get("priority") == "主渠道"
                ]
                supporting_channels = [
                    c for c in data.recommended_channels if c.get("priority") == "辅助渠道"
                ]

                # 渠道图标映射
                channel_icons = {
                    "年度ESG报告": "📊",
                    "官网ESG专栏": "🌐",
                    "社交媒体": "📱",
                    "投资者路演": "🎯",
                    "员工培训": "🎓",
                    "股东大会": "🏛️",
                    "ESG评级回复": "📋",
                    "新闻发布会": "📰",
                    "供应商大会": "🤝",
                    "社区活动": "🎉",
                    "员工大会": "👥",
                    "内部通讯": "📧",
                    "员工内网": "💻",
                    "招聘网站": "🔍",
                    "内部举报热线": "📞",
                    "官网合规专栏": "⚖️",
                    "公司治理公告": "📢",
                    "投资者说明会": "💼",
                    "供应商培训": "📚",
                    "官网供应商门户": "🏭",
                }

                # 显示主渠道（2-3个）
                if primary_channels:
                    st.markdown(
                        "<div style='font-size: 0.85em; color: #666; margin-bottom: 4px;'>主渠道</div>",
                        unsafe_allow_html=True,
                    )
                    cols = st.columns(min(len(primary_channels), 3))
                    for idx, channel in enumerate(primary_channels[:3]):
                        with cols[idx]:
                            channel_name = channel.get("channel_name", "")
                            icon = channel_icons.get(channel_name, "📢")
                            reason = channel.get("reason", "")
                            st.markdown(
                                f"<div style='{content_style} text-align: center;'>"
                                f"<div style='font-size: 1.5em; margin-bottom: 2px;'>{icon}</div>"
                                f"<div style='font-weight: bold; font-size: 0.85em;'>{channel_name}</div>"
                                f"<span style='background: #ff4d4f; color: white; padding: 1px 6px; "
                                f"border-radius: 4px; font-size: 0.7em;'>主渠道</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                            if reason:
                                st.caption(reason)

                # 显示辅助渠道（折叠）
                if supporting_channels:
                    with st.expander("查看辅助渠道"):
                        for channel in supporting_channels:
                            channel_name = channel.get("channel_name", "")
                            icon = channel_icons.get(channel_name, "📢")
                            reason = channel.get("reason", "")
                            st.markdown(
                                f"<div style='{content_style} margin-bottom: 8px;'>"
                                f"{icon} **{channel_name}** "
                                f"<span style='background: #999; color: white; padding: 1px 6px; "
                                f"border-radius: 4px; font-size: 0.75em;'>辅助渠道</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                            if reason:
                                st.caption(reason)


# ============== 图表组件 ==============


def render_radar_chart(
    scores: Dict[str, float],
    benchmark_scores: Optional[Dict[str, float]] = None,
    title: str = "ESG评分雷达图",
    height: int = 400,
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


def render_dimension_comparison(
    scores: Dict[str, float],
    weights: Dict[str, float],
    title: str = "维度得分对比",
    height: int = 350,
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
            name="得分",
            marker_color=colors,
            text=[f"{v:.1f}" for v in values],
            textposition="outside",
        ),
        secondary_y=False,
    )

    # 权重折线图
    fig.add_trace(
        go.Scatter(
            x=dim_names,
            y=[w * 100 for w in weight_values],
            name="权重 (%)",
            mode="lines+markers+text",
            line=dict(color="#fa8c16", width=2),
            marker=dict(size=10),
            text=[f"{w:.0%}" for w in weight_values],
            textposition="top center",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=80, b=40),
        showlegend=True,
    )

    fig.update_yaxes(title_text="得分", range=[0, 100], secondary_y=False)
    fig.update_yaxes(title_text="权重 (%)", range=[0, 100], secondary_y=True)

    return fig


def render_topic_wordcloud(
    topics: List[Dict[str, Any]], title: str = "议题热度云图", height: int = 400
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

        fig.add_trace(
            go.Scatter(
                x=[positions[i][0]],
                y=[positions[i][1]],
                mode="text",
                text=[name],
                textfont=dict(size=font_size, color=color),
                hovertemplate=f"{name}<br>热度: {value}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        height=height,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def render_gauge_chart(
    value: float, title: str = "综合评分", max_value: float = 100.0, height: int = 300
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


# ============== 表格组件 ==============


def render_gap_table(gap_data: Dict[str, Any]) -> None:
    """渲染差距分析表格

    Args:
        gap_data: 差距数据 {"dimensions": {"E": {"current": 27.6, "target": 70.0, ...}}}
    """
    import pandas as pd

    dimensions = gap_data.get("dimensions", {})

    # 创建表格数据
    table_data = []
    for dim, data in dimensions.items():
        dim_name = ESG_DIMENSION_NAMES.get(dim, dim)
        current = data.get("current", 0)
        target = data.get("target", 0)
        gap = data.get("gap", 0)
        priority = data.get("priority", "中")

        # 状态颜色
        status_color = "🔴" if gap > 30 else "🟠" if gap > 15 else "🟡" if gap > 5 else "🟢"
        status_text = "严重" if gap > 30 else "较大" if gap > 15 else "中等" if gap > 5 else "良好"

        table_data.append(
            {
                "维度": f"{dim} ({dim_name})",
                "当前得分": f"{current:.1f}",
                "目标得分": f"{target:.1f}",
                "差距": f"{gap:.1f}",
                "状态": f"{status_color} {status_text}",
                "优先级": priority,
            }
        )

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_business_unit_risk_matrix(matrix_data: List[Dict[str, Any]]) -> None:
    """渲染业务单元风险矩阵

    Args:
        matrix_data: 矩阵数据列表
    """
    import pandas as pd

    if not matrix_data:
        st.info("暂无业务单元风险数据")
        return

    # 创建DataFrame
    df_data = []
    for row in matrix_data:
        unit_name = row.get("business_unit", "")
        topics = row.get("topics", {})

        row_data = {"业务单元": unit_name}

        # 添加每个议题的影响等级
        for topic_id, topic_info in topics.items():
            topic_name = topic_info.get("name", topic_id)
            impact = topic_info.get("impact", "低")

            # 使用颜色和符号
            impact_symbol = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(impact, "⚪")
            row_data[topic_name] = f"{impact_symbol} {impact}"

        df_data.append(row_data)

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


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
    icon: str = "📂",
) -> None:
    """渲染空状态提示

    Args:
        message: 主消息
        sub_message: 副消息
        icon: 图标
    """
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
