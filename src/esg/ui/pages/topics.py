"""议题全景图模块

提供ESG议题热度分析与趋势洞察功能。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.analysis.topic_analyzer import TopicAnalyzer
from src.esg.config import ESG_COLORS, ESG_DIMENSION_NAMES
from src.esg.ui.components import render_header, render_topic_wordcloud


def render_topics_page(config: Dict[str, Any]) -> None:
    """渲染议题全景图页面

    Args:
        config: 配置参数
    """
    render_header(title="议题全景图", subtitle="行业ESG议题热度分析与趋势洞察")

    # 初始化议题分析器
    try:
        analyzer = TopicAnalyzer()
    except Exception as e:
        st.error(f"议题数据加载失败: {e}")
        return

    # 筛选条件
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        category_filter = st.selectbox(
            "筛选维度",
            ["all", "E", "S", "G"],
            format_func=lambda x: "全部" if x == "all" else f"{x} - {ESG_DIMENSION_NAMES[x]}",
        )

    with col2:
        min_weight = st.slider("最小权重", 0.0, 0.5, 0.0, 0.05)

    with col3:
        st.markdown("")
        st.caption("💡 词云大小代表议题热度，颜色代表维度")

    # 词云图
    wordcloud_data = analyzer.generate_wordcloud_data(
        category=category_filter if category_filter != "all" else None,
        min_weight=min_weight,
    )

    st.plotly_chart(
        render_topic_wordcloud(
            [{"name": w.text, "value": w.value, "category": w.category} for w in wordcloud_data],
            title="ESG议题热度云图",
        ),
        use_container_width=True,
        height=450,
    )

    # 议题分析
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔥 热门议题")
        trends = analyzer.analyze_trends(
            category=category_filter if category_filter != "all" else None
        )

        for topic in trends.get("hot_topics", [])[:5]:
            with st.container():
                cols = st.columns([3, 1, 1])
                cols[0].write(f"**{topic['name']}**")
                cols[1].write(f"热度: {topic['heat_score']}")
                cols[2].write(f"趋势: {topic['trend']}")

    with col2:
        st.markdown("### 📈 上升最快")

        for topic in trends.get("rising_topics", [])[:5]:
            with st.container():
                cols = st.columns([3, 1, 1])
                cols[0].write(f"**{topic['name']}**")
                cols[1].write(f"增长: +{topic['growth_rate']}%")
                cols[2].write(f"趋势: {topic['trend']}")

    # 维度汇总
    st.markdown("---")
    st.markdown("### 📊 维度汇总")

    summary = analyzer.get_category_summary()
    cols = st.columns(3)

    for i, dim in enumerate(["E", "S", "G"]):
        with cols[i]:
            if dim in summary:
                data = summary[dim]
                st.markdown(
                    f"""
                <div style="
                    background: {ESG_COLORS[dim]}10;
                    border-radius: 10px;
                    padding: 16px;
                    border-left: 4px solid {ESG_COLORS[dim]};
                ">
                    <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 8px;">
                        {data['name']} ({dim})
                    </div>
                    <div style="font-size: 0.9em; color: #666;">
                        议题数: {data['count']}<br>
                        平均热度: {data['avg_heat']}<br>
                        增长率: {data['avg_growth_rate']}%<br>
                        热门: {data['top_topic']}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
