"""差距诊断模块

提供对标行业标杆进行差距分析功能。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.analysis.gap_analyzer import GapAnalyzer
from src.esg.config import BENCHMARK_COMPANIES, ESG_COLORS, ESG_DIMENSION_NAMES
from src.esg.ui.components import (
    GapCardData,
    render_bidirectional_bar,
    render_empty_state,
    render_gap_card,
    render_gap_table,
    render_header,
    render_radar_chart,
)
from src.esg.ui.state import get_state_manager


def render_gap_page(config: Dict[str, Any]) -> None:
    """渲染差距诊断页面

    Args:
        config: 配置参数
    """
    render_header(title="差距诊断", subtitle="对标行业标杆，全面诊断ESG表现差距")

    manager = get_state_manager()

    # 检查是否有指标数据
    if not manager.has_metrics():
        render_empty_state(message="暂无ESG指标数据", sub_message="请先前往首页导入数据", icon="📊")
        if st.button("前往首页导入数据"):
            manager.set_current_page("home")
            st.rerun()
        return

    metrics = manager.get_metrics()

    # 标杆选择
    benchmark = st.selectbox(
        "选择对标企业",
        BENCHMARK_COMPANIES,
        index=BENCHMARK_COMPANIES.index(config["benchmark"]),
    )

    # 执行差距分析
    try:
        gap_analyzer = GapAnalyzer()

        with st.spinner("📊 正在进行差距分析..."):
            # 维度差距
            dim_gaps = gap_analyzer.analyze_dimension_gap(metrics, benchmark)

            # 指标差距
            indicator_gaps = gap_analyzer.analyze_indicator_gap(metrics, benchmark)

            # 保存结果
            gap_analysis = {
                "dimensions": {
                    dim: {
                        "current": gap.current,
                        "target": gap.benchmark,
                        "gap": gap.gap,
                        "priority": gap.priority,
                    }
                    for dim, gap in dim_gaps.items()
                },
                "indicators": [
                    {
                        "name": gap.indicator_name,
                        "current": gap.current_score,
                        "target": gap.benchmark_score,
                        "gap": gap.gap,
                    }
                    for gap in indicator_gaps[:5]
                ],
            }
            manager.set_gap_analysis(gap_analysis)
            manager.set_benchmark_company(benchmark)

    except Exception as e:
        st.error(f"差距分析失败: {e}")
        return

    # 显示总体对比
    scores = metrics.get_all_dimension_scores()

    st.markdown("### 📊 总体对比")

    cols = st.columns([2, 3])

    with cols[0]:
        # 计算标杆分数
        benchmark_scores = {}
        for dim in ["E", "S", "G"]:
            gap_data = gap_analysis["dimensions"].get(dim, {})
            benchmark_scores[dim] = gap_data.get("target", 80)

        st.plotly_chart(
            render_radar_chart(
                scores=scores,
                benchmark_scores=benchmark_scores,
                title="与标杆对比",
            ),
            use_container_width=True,
        )

    with cols[1]:
        # 双向条形图
        bi_data = {}
        for dim in ["E", "S", "G"]:
            bi_data[dim] = (scores[dim], benchmark_scores[dim])

        st.plotly_chart(
            render_bidirectional_bar(
                data=bi_data,
                title="维度得分对比",
                left_label="当前企业",
                right_label=benchmark,
            ),
            use_container_width=True,
        )

    # 维度差距卡片
    st.markdown("---")
    st.markdown("### 📉 维度差距分析")

    gap_cols = st.columns(3)
    for i, dim in enumerate(["E", "S", "G"]):
        with gap_cols[i]:
            gap_data = gap_analysis["dimensions"].get(dim, {})
            render_gap_card(
                GapCardData(
                    dimension=dim,
                    current=gap_data.get("current", 0),
                    benchmark=gap_data.get("target", 0),
                    gap=gap_data.get("gap", 0),
                    priority=gap_data.get("priority", "中"),
                )
            )

    # 指标级差距
    with st.expander("🔍 指标级差距详情"):
        for gap in gap_analysis.get("indicators", []):
            cols = st.columns([2, 1, 1, 1, 1])
            cols[0].write(f"**{gap['name']}**")
            cols[1].write(f"当前: {gap['current']:.1f}")
            cols[2].write(f"标杆: {gap['target']:.1f}")
            cols[3].write(f"差距: {gap['gap']:+.1f}")

            priority = "高" if gap["gap"] > 15 else "中" if gap["gap"] > 8 else "低"
            priority_color = {"高": "red", "中": "orange", "低": "green"}[priority]
            cols[4].markdown(f":{priority_color}[优先级: {priority}]")

    # 前往策略建议
    st.markdown("---")
    if st.button("💡 获取AI改进策略 →", use_container_width=True, type="primary"):
        manager.set_current_page("strategies")
        st.rerun()

    # ============== 高级功能区域 ==============
    st.markdown("---")
    st.markdown("### 🔧 高级功能")

    # 业务单元风险映射详情
    with st.expander("🔍 查看业务单元风险映射详情"):
        _render_business_risk_mapping()

    # 国际标准合规检查清单
    with st.expander("📋 国际标准合规检查清单"):
        _render_compliance_checker()


def _render_business_risk_mapping() -> None:
    """渲染业务单元风险映射详情"""
    try:
        from src.esg.analysis.business_mapper import BusinessAlignmentMapper

        mapper = BusinessAlignmentMapper()

        # 业务单元风险统计
        st.markdown("#### 📊 业务单元风险分布")
        summary = mapper.get_topic_summary_by_unit()

        # 创建表格数据
        summary_data = []
        for unit_name, counts in summary.items():
            summary_data.append(
                {
                    "业务单元": unit_name,
                    "高风险议题": counts["高"],
                    "中风险议题": counts["中"],
                    "低风险议题": counts["低"],
                    "总计": counts["总计"],
                }
            )

        st.dataframe(summary_data, use_container_width=True, hide_index=True)

        # 各业务单元主要风险
        st.markdown("#### ⚠️ 各业务单元主要ESG风险（TOP 3）")

        for unit_name in mapper.business_units:
            top_risks = mapper.get_top_risks_for_unit(unit_name, top_n=3)
            if top_risks:
                with st.container():
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.markdown(f"**{unit_name}**")
                    with cols[1]:
                        risk_texts = []
                        for risk in top_risks:
                            color = risk["color"]
                            risk_texts.append(
                                f"<span style='color:{color};font-weight:bold;'>{risk['topic_name']}</span> ({risk['impact_level']})"
                            )
                        st.markdown(" | ".join(risk_texts), unsafe_allow_html=True)

        # 风险矩阵可视化
        st.markdown("#### 📈 风险矩阵")
        matrix_data = mapper.get_risk_matrix_data()

        # 获取所有议题名称
        all_topics = set()
        for row in matrix_data:
            all_topics.update(row["topics"].keys())

        # 创建矩阵表格
        matrix_df_data = []
        for row in matrix_data:
            row_data = {
                "业务单元": (
                    row["business_unit"][:8] + "..."
                    if len(row["business_unit"]) > 8
                    else row["business_unit"]
                )
            }
            for topic_id in sorted(all_topics)[:6]:  # 限制显示前6个议题
                if topic_id in row["topics"]:
                    topic = row["topics"][topic_id]
                    impact = topic["impact"]
                    row_data[topic["name"][:10]] = f"{impact}"
                else:
                    row_data[topic_id[:10]] = "-"
            matrix_df_data.append(row_data)

        st.dataframe(matrix_df_data, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"业务单元风险映射加载失败: {e}")
        st.info("请确保业务映射配置正确")


def _render_compliance_checker() -> None:
    """渲染合规检查清单"""
    try:
        from src.esg.core.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()
        manager = get_state_manager()
        metrics = manager.get_metrics()

        if not metrics:
            st.info("请先导入ESG指标数据")
        else:
            # 合规性汇总
            summary = checker.get_compliance_summary(metrics)

            st.markdown("#### 📊 合规性概览")

            # 汇总指标
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总体合规率", f"{summary['overall_rate']:.0%}")
            with col2:
                st.metric("已合规条款", summary["compliant_count"], f"/ {summary['total_clauses']}")
            with col3:
                st.metric("部分合规", summary["partial_count"])
            with col4:
                st.metric("未合规条款", summary["non_compliant_count"])

            # 按标准分组统计
            st.markdown("#### 📑 按标准分组统计")

            standards_data = []
            for std_key, std_summary in summary["standards_summary"].items():
                standards_data.append(
                    {
                        "标准": std_summary["name"],
                        "已合规": std_summary["compliant"],
                        "部分合规": std_summary["partial"],
                        "未合规": std_summary["non_compliant"],
                        "总计": std_summary["total"],
                    }
                )

            st.dataframe(standards_data, use_container_width=True, hide_index=True)

            # 未合规条款详情
            st.markdown("#### ⚠️ 需关注的未合规条款")

            non_compliant = checker.get_non_compliant_items(metrics)

            if not non_compliant:
                st.success("✅ 所有条款均已合规！")
            else:
                # 只显示前10个未合规条款
                for item in non_compliant[:10]:
                    with st.container():
                        cols = st.columns([2, 1, 2])
                        with cols[0]:
                            req_type_color = (
                                "red" if item["requirement_type"] == "强制" else "orange"
                            )
                            st.markdown(f"**{item['clause_name'][:20]}...**")
                            st.markdown(
                                f"<span style='color:{req_type_color};font-size:0.8em;'>[{item['requirement_type']}]</span>",
                                unsafe_allow_html=True,
                            )
                        with cols[1]:
                            status_color = {"未合规": "red", "部分合规": "orange"}.get(
                                item["status"], "gray"
                            )
                            st.markdown(
                                f"<span style='color:{status_color};font-weight:bold;'>{item['status']}</span>",
                                unsafe_allow_html=True,
                            )
                        with cols[2]:
                            if item["missing_items"]:
                                st.caption(f"缺失: {', '.join(item['missing_items'][:2])}")

                if len(non_compliant) > 10:
                    st.caption(f"... 还有 {len(non_compliant) - 10} 个未合规条款")

            # 合规建议
            with st.expander("💡 合规改进建议"):
                st.markdown("""
                **优先改进项：**
                1. 确保所有**强制**条款达到合规状态
                2. 补充缺失的碳排放数据披露（范围1/2/3）
                3. 完善董事会气候监督机制文档
                4. 提升ESG报告质量和定量指标覆盖度

                **参考标准：**
                - ISSB S1/S2 国际可持续披露准则
                - GRI Standards 全球报告倡议标准
                """)

    except Exception as e:
        st.error(f"合规检查加载失败: {e}")
        st.info("请确保合规检查配置正确")
