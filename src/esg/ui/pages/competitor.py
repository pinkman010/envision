"""竞争对手分析模块

提供行业最佳实践对标与竞争情报分析功能。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.analysis.competitor_analyzer import CompetitorAnalyzer
from src.esg.config import ESG_DIMENSION_NAMES
from src.esg.ui.components import render_header


def render_competitor_page(config: Dict[str, Any]) -> None:
    """渲染竞争对手分析页面

    Args:
        config: 配置参数
    """
    render_header(title="竞争对手分析", subtitle="行业最佳实践对标与竞争情报分析")

    # 初始化竞争对手分析器
    try:
        analyzer = CompetitorAnalyzer()
    except Exception as e:
        st.error(f"竞争对手分析器初始化失败: {e}")
        return

    manager = get_state_manager()

    # 功能说明
    st.info("""
    🔍 **竞争对手分析** 基于行业最佳实践数据，
    生成深度对标分析和竞争情报，帮助企业了解与标杆的差距及改进方向。
    """)

    # 检查是否有指标数据
    has_metrics = manager.has_metrics()

    # 标杆企业选择
    st.markdown("### 🎯 选择对标企业")

    competitors = analyzer.get_competitor_list()
    if not competitors:
        competitors = ["维斯塔斯", "西门子歌美萨克", "通用电气"]

    benchmark_company = st.selectbox("选择标杆企业", competitors, index=0)

    # 如果有当前指标数据，显示差距分析
    if has_metrics:
        metrics = manager.get_metrics()

        # 构建gap_data
        scores = metrics.get_all_dimension_scores()
        gap_data = {}
        for dim in ["E", "S", "G"]:
            # 假设标杆分数为85
            gap_data[dim] = {"current": scores[dim], "target": 85, "gap": 85 - scores[dim]}

        # 生成分析报告
        with st.spinner("📊 正在生成对标分析..."):
            analysis = analyzer.generate_analysis(metrics, benchmark_company, gap_data)

        st.markdown("### 📈 对标分析报告")
        st.markdown(analysis)

        # 对比表格
        st.markdown("### 📊 维度对比")

        table_data = analyzer.generate_comparison_table(metrics, benchmark_company, gap_data)

        if table_data:
            st.dataframe(table_data, use_container_width=True, hide_index=True)

        # 整体对比
        st.markdown("### 🏆 整体排名")

        comparison = analyzer.get_overall_comparison(metrics)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "当前排名",
                f"{comparison['current_company']['rank']}/{comparison['current_company']['total_companies']}",
            )
        with col2:
            st.metric("ESG综合评分", f"{comparison['current_company']['overall_score']:.1f}")
        with col3:
            # 显示差距最大的维度
            max_gap_dim = max(gap_data.items(), key=lambda x: x[1].get("gap", 0))
            dim_name = ESG_DIMENSION_NAMES.get(max_gap_dim[0], max_gap_dim[0])
            st.metric("最大差距维度", dim_name)

    else:
        st.warning("⚠️ 请先在首页导入企业ESG数据以进行差距分析")

    # 标杆企业最佳实践
    st.markdown("---")
    st.markdown(f"### 🏅 {benchmark_company}最佳实践")

    for dim in ["E", "S", "G"]:
        strategy = analyzer.get_strategy_by_dimension(benchmark_company, dim)
        if strategy:
            with st.expander(f"{ESG_DIMENSION_NAMES[dim]} ({dim})"):
                st.markdown(f"**策略领域**: {strategy.strategy_area}")
                st.markdown(f"**最佳实践**: {strategy.best_practice_description}")
                st.markdown(f"**关键成果**: {strategy.key_results}")
                st.markdown(f"**实施周期**: {strategy.implementation_timeline}")
                st.markdown(f"**预计投资**: {strategy.investment}")
                st.markdown(f"**创新亮点**: {strategy.innovation_highlights}")

    # 创新亮点
    st.markdown("---")
    st.markdown("### 💡 行业创新亮点")

    highlights = analyzer.get_innovation_highlights(benchmark_company)

    if highlights:
        for highlight in highlights:
            st.markdown(f"- {highlight}")
    else:
        st.info("暂无创新亮点数据")


def get_state_manager():
    """获取状态管理器"""
    from src.esg.ui.state import get_state_manager

    return get_state_manager()
