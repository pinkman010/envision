"""差距诊断模块（简化版）

提供对标行业标杆进行差距分析功能。
简化版：差距总览 + 维度差距 + 合规状态 + 导出报告
"""

from typing import Any, Dict

import streamlit as st

from src.esg.analysis.gap_analyzer import GapAnalyzer, GapLevel
from src.esg.config import BENCHMARK_COMPANIES, ESG_COLORS, ESG_DIMENSION_NAMES
from src.esg.core.compliance_checker import ComplianceChecker
from src.esg.ui.components import (
    GapCardData,
    render_bidirectional_bar,
    render_empty_state,
    render_gap_card,
    render_header,
    render_radar_chart,
)
from src.esg.ui.state import get_state_manager


def render_gap_page(config: Dict[str, Any]) -> None:
    """渲染差距诊断页面（简化版）

    简化后：差距总览 + 维度差距 + 合规状态 + 导出报告
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
                        "level": gap.level.value,
                    }
                    for dim, gap in dim_gaps.items()
                },
                "indicators": [
                    {
                        "name": gap.indicator_name,
                        "current": gap.current_score,
                        "target": gap.benchmark_score,
                        "gap": gap.gap,
                        "level": gap.level.value,
                    }
                    for gap in indicator_gaps[:5]
                ],
            }
            manager.set_gap_analysis(gap_analysis)
            manager.set_benchmark_company(benchmark)

    except Exception as e:
        st.error(f"差距分析失败: {e}")
        return

    # ============== 差距总览 ==============
    st.markdown("### 📊 总体对比")

    scores = metrics.get_all_dimension_scores()

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

    # ============== 维度差距分析 ==============
    st.markdown("---")
    st.markdown("### 📉 维度差距分析")

    gap_cols = st.columns(3)
    for i, dim in enumerate(["E", "S", "G"]):
        with gap_cols[i]:
            gap_data = gap_analysis["dimensions"].get(dim, {})
            level = gap_data.get("level", "中")
            render_gap_card(
                GapCardData(
                    dimension=dim,
                    current=gap_data.get("current", 0),
                    benchmark=gap_data.get("target", 0),
                    gap=gap_data.get("gap", 0),
                    priority=level,
                )
            )

    # ============== 简化版合规状态 ==============
    st.markdown("---")
    st.markdown("### ✅ 合规状态")

    try:
        checker = ComplianceChecker()
        compliance_summary = checker.get_compliance_summary(metrics)

        # 简化的合规状态显示
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("合规率", f"{compliance_summary['compliance_rate']:.0f}%")
        with col2:
            st.metric("已合规", compliance_summary["compliant_count"])
        with col3:
            st.metric("部分合规", compliance_summary["partial_count"])
        with col4:
            st.metric("不合规", compliance_summary["non_compliant_count"])

        # 按标准分组
        st.markdown("#### 按标准统计")
        for std_key, std_summary in compliance_summary["standards_summary"].items():
            with st.expander(f"{std_summary['name']}"):
                cols = st.columns(4)
                cols[0].write(f"**{std_summary['name']}**")
                cols[1].write(f"合规: {std_summary['compliant']}")
                cols[2].write(f"部分: {std_summary['partial']}")
                cols[3].write(f"不合规: {std_summary['non_compliant']}")

    except Exception as e:
        st.warning(f"合规检查加载失败: {e}")

    # ============== 导出报告按钮 ==============
    st.markdown("---")
    st.markdown("### 📥 导出差距分析报告")

    if st.button("📥 导出差距分析报告", use_container_width=True):
        # 生成简单的文本报告
        report = _generate_gap_report(metrics, gap_analysis, benchmark)

        # 提供下载
        st.download_button(
            label="📥 下载报告",
            data=report,
            file_name=f"gap_analysis_{metrics.company_name}_{benchmark}.txt",
            mime="text/plain",
        )


def _generate_gap_report(metrics, gap_analysis: Dict[str, Any], benchmark: str) -> str:
    """生成差距分析报告"""
    scores = metrics.get_all_dimension_scores()

    report_lines = [
        f"ESG差距分析报告",
        f"=" * 50,
        f"",
        f"公司: {metrics.company_name}",
        f"年份: {metrics.year}",
        f"对标企业: {benchmark}",
        f"",
        f"一、维度得分对比",
        f"-" * 30,
    ]

    for dim in ["E", "S", "G"]:
        gap_data = gap_analysis["dimensions"].get(dim, {})
        report_lines.append(
            f"{ESG_DIMENSION_NAMES.get(dim, dim)}: "
            f"当前 {gap_data.get('current', 0):.1f} | "
            f"标杆 {gap_data.get('target', 0):.1f} | "
            f"差距 {gap_data.get('gap', 0):+.1f}"
        )

    report_lines.extend(
        [
            f"",
            f"二、差距等级",
            f"-" * 30,
        ]
    )

    for dim in ["E", "S", "G"]:
        gap_data = gap_analysis["dimensions"].get(dim, {})
        level = gap_data.get("level", "中")
        report_lines.append(f"{ESG_DIMENSION_NAMES.get(dim, dim)}: {level}优先级")

    report_lines.extend(
        [
            f"",
            f"三、指标级差距",
            f"-" * 30,
        ]
    )

    for indicator in gap_analysis.get("indicators", []):
        report_lines.append(
            f"{indicator['name']}: "
            f"当前 {indicator['current']:.1f} | "
            f"标杆 {indicator['target']:.1f} | "
            f"差距 {indicator['gap']:+.1f} ({indicator['level']})"
        )

    return "\n".join(report_lines)
