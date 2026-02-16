"""实质性矩阵模块

提供双重重要性评估功能。
"""

from typing import Any, Dict

import plotly.express as px
import streamlit as st

from src.esg.analysis.materiality_matrix import MaterialityMatrix
from src.esg.config import ESG_COLORS, ESG_DIMENSION_NAMES
from src.esg.ui.components import render_header


def render_materiality_page(config: Dict[str, Any]) -> None:
    """渲染实质性议题矩阵页面

    Args:
        config: 配置参数
    """
    render_header(title="实质性议题矩阵", subtitle="评估和管理ESG实质性议题的双重重要性")

    # 初始化实质性矩阵
    try:
        matrix = MaterialityMatrix()
    except Exception as e:
        st.error(f"实质性矩阵初始化失败: {e}")
        return

    manager = get_state_manager()

    # 功能说明
    st.info("""
    📊 **实质性议题矩阵** 基于双重重要性（财务重要性+影响重要性）原则，
    帮助企业识别和管理最关键的ESG议题。
    - 横轴: 财务重要性 (对企业财务的影响)
    - 纵轴: 影响重要性 (对企业利益相关方和环境的影响)
    """)

    # 议题评分配置
    st.markdown("### ⚙️ 议题评分配置")

    # 获取所有议题
    topics = matrix.get_all_topics()

    # 按维度分组显示
    for dim in ["E", "S", "G"]:
        dim_topics = [t for t in topics if t.dimension == dim]
        if dim_topics:
            with st.expander(f"{ESG_DIMENSION_NAMES[dim]}议题配置 ({dim})", expanded=True):
                cols = st.columns(3)
                for idx, topic in enumerate(dim_topics):
                    with cols[idx % 3]:
                        # 财务重要性
                        new_financial = st.slider(
                            f"{topic.name} - 财务重要性",
                            0,
                            10,
                            topic.financial_score,
                            key=f"financial_{topic.topic_id}",
                        )
                        # 影响重要性
                        new_impact = st.slider(
                            f"{topic.name} - 影响重要性",
                            0,
                            10,
                            topic.impact_score,
                            key=f"impact_{topic.topic_id}",
                        )
                        if (
                            new_financial != topic.financial_score
                            or new_impact != topic.impact_score
                        ):
                            matrix.update_topic_scores(topic.topic_id, new_financial, new_impact)

    # 矩阵可视化
    st.markdown("### 📊 实质性议题矩阵可视化")

    # 创建散点图数据
    matrix_data = matrix.get_matrix_data()

    if matrix_data:
        df = {
            "x": [d["x"] for d in matrix_data],
            "y": [d["y"] for d in matrix_data],
            "size": [d["size"] for d in matrix_data],
            "color": [d["color"] for d in matrix_data],
            "name": [d["name"] for d in matrix_data],
            "dimension": [d["dimension"] for d in matrix_data],
            "quadrant": [matrix.QUADRANT_LABELS.get(d["quadrant"], "") for d in matrix_data],
        }

        fig = px.scatter(
            df,
            x="x",
            y="y",
            size="size",
            color="dimension",
            hover_name="name",
            text="name",
            labels={"x": "财务重要性", "y": "影响重要性"},
            title="ESG实质性议题矩阵",
        )

        # 添加象限分隔线
        fig.add_hline(y=5, line_dash="dash", line_color="gray")
        fig.add_vline(x=5, line_dash="dash", line_color="gray")

        fig.update_traces(textposition="top center")
        fig.update_layout(height=500)

        st.plotly_chart(fig, use_container_width=True)

    # 象限统计
    st.markdown("### 📋 象限统计")

    quadrant_summary = matrix.get_quadrant_summary()
    cols = st.columns(4)

    for idx, (quadrant, count) in enumerate(quadrant_summary.items()):
        with cols[idx]:
            label = matrix.QUADRANT_LABELS.get(quadrant, quadrant)
            color = matrix.QUADRANT_COLORS.get(quadrant, "#999")
            st.markdown(
                f"""
                <div style="
                    background: {color}15;
                    border-radius: 8px;
                    padding: 12px;
                    border-left: 4px solid {color};
                ">
                    <div style="font-size: 0.85em; color: #666;">{label}</div>
                    <div style="font-size: 1.5em; font-weight: bold;">{count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 优先级列表
    st.markdown("### 🎯 优先级议题列表")

    priority_list = matrix.get_priority_list()

    priority_data = []
    for topic in priority_list[:10]:
        priority_data.append(
            {
                "议题": topic["name"],
                "维度": topic["dimension"],
                "财务重要性": topic["financial_score"],
                "影响重要性": topic["impact_score"],
                "象限": matrix.QUADRANT_LABELS.get(topic["quadrant"], ""),
                "优先级": topic["priority"],
            }
        )

    if priority_data:
        st.dataframe(priority_data, use_container_width=True, hide_index=True)

    # 披露建议
    st.markdown("### 📝 披露级别建议")

    for topic in priority_list[:5]:
        level = matrix.get_recommended_disclosure_level(topic["topic_id"])
        st.markdown(f"**{topic['name']}**: {level}")


def get_state_manager():
    """获取状态管理器"""
    from src.esg.ui.state import get_state_manager

    return get_state_manager()
