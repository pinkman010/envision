"""增强版ESG分析UI

提供4个模块的高级ESG分析界面：
1. 议题全景图 - 展示ESG议题热度和趋势
2. 权重配置 - AHP层次分析法配置维度权重
3. 差距诊断 - 对标行业标杆进行差距分析
4. AI策略建议 - 基于差距生成改进策略
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import streamlit as st

from src.esg.analysis.gap_analyzer import GapAnalyzer
from src.esg.analysis.strategy_generator import StrategyGenerator, StrategyPriority
from src.esg.analysis.timing_advisor import TimingAdvisor
from src.esg.analysis.topic_analyzer import TopicAnalyzer
from src.esg.completion.report_generator import ReportGenerator
from src.esg.config import (
    AHP_CONSISTENCY_THRESHOLD,
    ANALYSIS_YEARS,
    BENCHMARK_COMPANIES,
    ESG_COLORS,
    ESG_DIMENSION_NAMES,
)
from src.esg.core.models import AnalysisResult, ESGMetrics
from src.esg.extraction.metric_extractor import MetricExtractor
from src.esg.extraction.pdf_extractor import PDFContent, PDFExtractor
from src.esg.fusion.ahp import AHPFusionEngine
from src.esg.rag.engine import RAGEngine, RAGResponse
from src.esg.ui.components import (
    GapCardData,
    ScoreCardData,
    StrategyCardData,
    render_bidirectional_bar,
    render_business_unit_risk_matrix,
    render_dimension_comparison,
    render_empty_state,
    render_gap_card,
    render_gap_table,
    render_gauge_chart,
    render_header,
    render_info_box,
    render_metric_card,
    render_progress_step,
    render_radar_chart,
    render_score_card,
    render_section_title,
    render_strategy_card,
    render_topic_wordcloud,
)
from src.esg.ui.state import get_state_manager, init_session_state

# ============== 页面配置 ==============


def setup_page() -> None:
    """配置页面基础设置"""
    st.set_page_config(
        page_title="ESG智能分析系统 - 增强版",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()


# ============== 侧边栏 ==============


def render_sidebar() -> Dict[str, Any]:
    """渲染侧边栏

    Returns:
        配置参数字典
    """
    with st.sidebar:
        # 导航
        st.markdown("### 📍 功能导航")

        pages = {
            "home": "🏠 首页",
            "topics": "📊 议题全景图",
            "weights": "⚖️ 权重配置",
            "gap": "📉 差距诊断",
            "strategies": "💡 AI策略建议",
            "timing": "📅 沟通时机",
            "rag": "💬 RAG智能问答",
        }

        manager = get_state_manager()
        current_page = manager.get_current_page()

        for key, label in pages.items():
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if current_page == key else "secondary",
            ):
                manager.set_current_page(key)
                st.rerun()

        st.markdown("---")

        # 全局设置
        st.markdown("### ⚙️ 全局设置")

        industry = st.selectbox(
            "行业",
            ["新能源", "制造业", "科技", "金融", "消费品"],
            index=0,
        )

        year = st.selectbox(
            "年份",
            ANALYSIS_YEARS,
            index=0,
        )

        benchmark = st.selectbox(
            "对标企业",
            BENCHMARK_COMPANIES,
            index=len(BENCHMARK_COMPANIES) - 1,
        )

        st.markdown("---")

        # 快捷操作
        st.markdown("### 🚀 快捷操作")

        if st.button("🔄 重置所有数据", use_container_width=True):
            manager.reset()
            st.rerun()

        # 数据状态指示
        st.markdown("---")
        st.markdown("### 📋 数据状态")

        status_icon = "✅" if manager.has_metrics() else "❌"
        st.write(f"{status_icon} ESG指标数据")

        status_icon = "✅" if manager.has_analysis_result() else "❌"
        st.write(f"{status_icon} 分析结果")

        status_icon = "✅" if manager.has_gap_analysis() else "❌"
        st.write(f"{status_icon} 差距分析")

        return {
            "industry": industry,
            "year": year,
            "benchmark": benchmark,
        }


# ============== 模块1: 首页 ==============


def render_home_page(config: Dict[str, Any]) -> None:
    """渲染首页

    Args:
        config: 配置参数
    """
    render_header(title="ESG智能分析系统", subtitle="基于AI的ESG综合评估与改进建议平台")

    # 功能概览
    st.markdown("## 🎯 功能概览")

    cols = st.columns(4)

    features = [
        ("📊", "议题全景图", "了解行业ESG议题热度和趋势"),
        ("⚖️", "权重配置", "使用AHP方法定制维度权重"),
        ("📉", "差距诊断", "对标标杆企业进行差距分析"),
        ("💡", "AI策略建议", "获取AI生成的改进策略"),
    ]

    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(
                f"""
            <div style="
                background: white;
                border-radius: 10px;
                padding: 20px;
                border: 1px solid #e8e8e8;
                text-align: center;
                height: 100%;
            ">
                <div style="font-size: 2.5em; margin-bottom: 10px;">{icon}</div>
                <div style="font-weight: bold; margin-bottom: 8px;">{title}</div>
                <div style="font-size: 0.85em; color: #888;">{desc}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # 数据导入
    st.markdown("## 📥 数据导入")

    manager = get_state_manager()

    tab1, tab2, tab3 = st.tabs(["📄 上传PDF报告", "📝 手动输入", "🎲 示例数据"])

    with tab1:
        render_pdf_upload()

    with tab2:
        render_manual_input()

    with tab3:
        render_demo_data_selection()

    # 如果有数据，显示概览
    if manager.has_metrics():
        st.markdown("---")
        st.markdown("## 📊 当前数据概览")
        render_metrics_overview()


def render_pdf_upload() -> None:
    """渲染PDF上传区域"""
    uploaded_file = st.file_uploader(
        "上传ESG报告PDF",
        type=["pdf"],
        help="系统将从PDF中自动提取ESG相关指标",
    )

    if uploaded_file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            with st.spinner("📖 正在提取PDF内容..."):
                extractor = PDFExtractor()
                content = extractor.extract(tmp_path)

                # 提取指标
                metric_ext = MetricExtractor()
                result = metric_ext.extract(
                    content.text,
                    company=content.metadata.company,
                    year=content.metadata.year or "2024",
                )

                metrics = create_metrics_from_extraction(result)

                manager = get_state_manager()
                manager.set_metrics(metrics)
                manager.set(
                    "uploaded_file",
                    {
                        "name": uploaded_file.name,
                        "size": len(uploaded_file.getvalue()) / 1024,  # KB
                    },
                )

            Path(tmp_path).unlink(missing_ok=True)

            st.success(f"✅ 成功提取: {metrics.company_name} {metrics.year}")

            # 自动跳转到差距诊断
            if st.button("前往差距诊断 →"):
                manager.set_current_page("gap")
                st.rerun()

        except Exception as e:
            st.error(f"❌ 提取失败: {str(e)}")


def render_manual_input() -> None:
    """渲染手动输入表单"""
    with st.form("manual_input_form"):
        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("公司名称", "示例公司")
            year = st.selectbox("年份", ANALYSIS_YEARS, index=0)

        with col2:
            st.markdown("**数据说明**")
            st.caption("请输入已知的ESG指标，留空将使用默认值")

        st.markdown("#### 🌱 环境指标 (E)")
        cols = st.columns(3)
        with cols[0]:
            carbon = st.number_input("碳排放量(吨)", min_value=0, value=100000, step=1000)
            renewable = st.number_input(
                "可再生能源占比(%)", min_value=0.0, max_value=100.0, value=40.0
            )
        with cols[1]:
            efficiency = st.number_input("能源效率(%)", min_value=0.0, max_value=100.0, value=70.0)
            water = st.number_input("用水量(立方米)", min_value=0, value=50000)
        with cols[2]:
            waste = st.number_input("废物回收率(%)", min_value=0.0, max_value=100.0, value=60.0)

        st.markdown("#### 👥 社会指标 (S)")
        cols = st.columns(3)
        with cols[0]:
            employees = st.number_input("员工总数", min_value=0, value=3000)
            female = st.number_input("女性员工比例(%)", min_value=0.0, max_value=100.0, value=35.0)
        with cols[1]:
            training = st.number_input("人均培训时长(小时)", min_value=0.0, value=30.0)
            safety = st.number_input("安全事故数", min_value=0, value=5)
        with cols[2]:
            community = st.number_input("社区投资(万元)", min_value=0, value=500)

        st.markdown("#### ⚖️ 治理指标 (G)")
        cols = st.columns(3)
        with cols[0]:
            board = st.number_input("独立董事比例(%)", min_value=0.0, max_value=100.0, value=40.0)
        with cols[1]:
            ethics = st.number_input(
                "道德培训覆盖率(%)", min_value=0.0, max_value=100.0, value=70.0
            )
        with cols[2]:
            report_quality = st.number_input(
                "ESG报告质量评分", min_value=0.0, max_value=100.0, value=75.0
            )

        submitted = st.form_submit_button("✅ 保存数据", use_container_width=True)

        if submitted:
            metrics = ESGMetrics(
                company_name=company_name,
                year=year,
                carbon_emissions=float(carbon),
                renewable_energy_ratio=renewable / 100,
                energy_efficiency=efficiency,
                water_consumption=float(water),
                waste_recycling_rate=waste / 100,
                employee_count=int(employees),
                female_ratio=female / 100,
                training_hours=float(training),
                safety_incidents=int(safety),
                community_investment=float(community) * 10000,
                board_independence_ratio=board / 100,
                ethics_training_coverage=ethics / 100,
                esg_report_quality=report_quality,
                source="手动输入",
            )

            manager = get_state_manager()
            manager.set_metrics(metrics)
            st.success("✅ 数据已保存")


def render_demo_data_selection() -> None:
    """渲染示例数据选择"""
    st.markdown("选择一个示例数据集体验功能：")

    col1, col2, col3 = st.columns(3)

    demo_cases = {
        "excellent": ("🌟 优秀案例", "绿色能源集团", "ESG表现优异的企业"),
        "average": ("📊 平均案例", "新能源科技", "行业平均水平的企业"),
        "poor": ("⚠️ 待改进案例", "传统能源企业", "需要改进ESG表现的企业"),
    }

    for col, (case_type, (label, name, desc)) in zip([col1, col2, col3], demo_cases.items()):
        with col:
            st.markdown(f"**{label}**")
            st.caption(desc)
            if st.button(f"加载{name}", key=f"demo_{case_type}", use_container_width=True):
                metrics = load_demo_metrics(case_type)
                manager = get_state_manager()
                manager.set_metrics(metrics)
                st.success(f"✅ 已加载: {metrics.company_name}")
                st.rerun()


def render_metrics_overview() -> None:
    """渲染指标概览"""
    manager = get_state_manager()
    metrics = manager.get_metrics()

    if not metrics:
        return

    scores = metrics.get_all_dimension_scores()
    overall = sum(scores.values()) / 3

    # 总体评分
    cols = st.columns([2, 1, 1, 1])

    with cols[0]:
        st.plotly_chart(
            render_gauge_chart(overall, "ESG综合评分"),
            use_container_width=True,
            height=250,
        )

    for i, dim in enumerate(["E", "S", "G"]):
        with cols[i + 1]:
            render_score_card(
                ScoreCardData(
                    title=ESG_DIMENSION_NAMES[dim],
                    score=scores[dim],
                    color=ESG_COLORS[dim],
                )
            )

    # 详细指标
    with st.expander("查看详细指标"):
        cols = st.columns(3)

        with cols[0]:
            st.markdown("**🌱 环境指标**")
            st.write(
                f"碳排放: {metrics.carbon_emissions:,.0f} 吨"
                if metrics.carbon_emissions
                else "碳排放: N/A"
            )
            st.write(
                f"可再生能源: {metrics.renewable_energy_ratio:.1%}"
                if metrics.renewable_energy_ratio
                else "可再生能源: N/A"
            )
            st.write(
                f"能源效率: {metrics.energy_efficiency:.1f}%"
                if metrics.energy_efficiency
                else "能源效率: N/A"
            )

        with cols[1]:
            st.markdown("**👥 社会指标**")
            st.write(
                f"员工数: {metrics.employee_count:,} 人"
                if metrics.employee_count
                else "员工数: N/A"
            )
            st.write(
                f"女性比例: {metrics.female_ratio:.1%}" if metrics.female_ratio else "女性比例: N/A"
            )
            st.write(
                f"培训时长: {metrics.training_hours:.1f} 小时"
                if metrics.training_hours
                else "培训时长: N/A"
            )

        with cols[2]:
            st.markdown("**⚖️ 治理指标**")
            st.write(
                f"独董比例: {metrics.board_independence_ratio:.1%}"
                if metrics.board_independence_ratio
                else "独董比例: N/A"
            )
            st.write(
                f"伦理培训: {metrics.ethics_training_coverage:.1%}"
                if metrics.ethics_training_coverage
                else "伦理培训: N/A"
            )


# ============== 模块2: 议题全景图 ==============


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


# ============== 模块3: 权重配置 ==============


def render_weights_page(config: Dict[str, Any]) -> None:
    """渲染权重配置页面

    Args:
        config: 配置参数
    """
    render_header(title="权重配置", subtitle="使用AHP层次分析法科学配置ESG维度权重")

    manager = get_state_manager()

    # 权重输入方式选择
    method = st.radio(
        "配置方式",
        ["简单配置", "AHP层次分析法"],
        horizontal=True,
    )

    if method == "简单配置":
        render_simple_weights_config()
    else:
        render_ahp_weights_config()

    # 显示当前权重
    st.markdown("---")
    st.markdown("### 📊 当前权重配置")

    weights = manager.get_weights()

    cols = st.columns(3)
    for i, dim in enumerate(["E", "S", "G"]):
        with cols[i]:
            render_score_card(
                ScoreCardData(
                    title=f"{ESG_DIMENSION_NAMES[dim]} ({dim})",
                    score=weights[dim] * 100,
                    max_score=100,
                    description=f"权重: {weights[dim]:.0%}",
                    color=ESG_COLORS[dim],
                )
            )

    # 权重可视化
    st.plotly_chart(
        render_dimension_comparison(
            scores={"E": 100, "S": 100, "G": 100},
            weights=weights,
            title="权重配置可视化",
        ),
        use_container_width=True,
    )


def render_simple_weights_config() -> None:
    """渲染简单权重配置"""
    manager = get_state_manager()
    current_weights = manager.get_weights()

    st.markdown("### ⚙️ 调整维度权重")
    st.info("调整各维度权重，系统会自动归一化使总和为100%")

    col1, col2, col3 = st.columns(3)

    with col1:
        e_weight = st.slider(
            f"环境(E) 权重",
            0.1,
            0.8,
            current_weights["E"],
            0.05,
            key="simple_e",
        )

    with col2:
        s_weight = st.slider(
            f"社会(S) 权重",
            0.1,
            0.8,
            current_weights["S"],
            0.05,
            key="simple_s",
        )

    with col3:
        g_weight = st.slider(
            f"治理(G) 权重",
            0.1,
            0.8,
            current_weights["G"],
            0.05,
            key="simple_g",
        )

    # 归一化
    total = e_weight + s_weight + g_weight
    normalized = {
        "E": round(e_weight / total, 2),
        "S": round(s_weight / total, 2),
        "G": round(g_weight / total, 2),
    }

    st.write(
        f"**归一化后**: E={normalized['E']:.0%}, S={normalized['S']:.0%}, G={normalized['G']:.0%}"
    )

    if st.button("💾 保存权重", key="save_simple_weights"):
        manager.set_weights(normalized)
        st.success("✅ 权重已保存")


def render_ahp_weights_config() -> None:
    """渲染AHP权重配置"""
    st.markdown("### ⚖️ AHP层次分析法")
    st.info("通过两两比较各维度的重要性，系统会自动计算权重并检验一致性")

    manager = get_state_manager()

    # 两两比较
    st.markdown("#### 维度重要性比较 (1-9标度)")
    st.caption("1=同等重要, 3=稍微重要, 5=明显重要, 7=强烈重要, 9=极端重要")

    comparisons = {}

    # E vs S
    e_vs_s = st.select_slider(
        "环境(E) 相对于 社会(S)",
        options=[1 / 9, 1 / 7, 1 / 5, 1 / 3, 1, 3, 5, 7, 9],
        value=1.0,
        format_func=lambda x: f"E {'>' if x > 1 else '<' if x < 1 else '='} S ({x:.2f})",
    )
    comparisons[(0, 1)] = e_vs_s  # E=index 0, S=index 1

    # E vs G
    e_vs_g = st.select_slider(
        "环境(E) 相对于 治理(G)",
        options=[1 / 9, 1 / 7, 1 / 5, 1 / 3, 1, 3, 5, 7, 9],
        value=1.0,
        format_func=lambda x: f"E {'>' if x > 1 else '<' if x < 1 else '='} G ({x:.2f})",
    )
    comparisons[(0, 2)] = e_vs_g  # E=index 0, G=index 2

    # S vs G
    s_vs_g = st.select_slider(
        "社会(S) 相对于 治理(G)",
        options=[1 / 9, 1 / 7, 1 / 5, 1 / 3, 1, 3, 5, 7, 9],
        value=1.0,
        format_func=lambda x: f"S {'>' if x > 1 else '<' if x < 1 else '='} G ({x:.2f})",
    )
    comparisons[(1, 2)] = s_vs_g  # S=index 1, G=index 2

    if st.button("🧮 计算权重", key="calc_ahp"):
        try:
            engine = AHPFusionEngine()
            engine.build_matrix(
                labels=["E", "S", "G"],
                comparisons=comparisons,
            )

            result = engine.calculate_weights()

            # 显示结果
            st.success("✅ 权重计算完成")

            cols = st.columns(2)

            with cols[0]:
                st.markdown("**权重结果**")
                for label, weight in result.weights_dict.items():
                    st.write(f"- {label} ({ESG_DIMENSION_NAMES[label]}): {weight:.2%}")

            with cols[1]:
                st.markdown("**一致性检验**")
                cr = result.consistency_ratio
                st.write(f"- 一致性比率 (CR): {cr:.4f}")
                st.write(f"- 阈值: {AHP_CONSISTENCY_THRESHOLD}")

                if result.is_consistent:
                    st.success("✅ 通过一致性检验")
                else:
                    st.warning("⚠️ 未通过一致性检验，建议调整比较值")

            # 保存结果
            manager.set_weights(result.weights_dict)
            manager.set_ahp_result(
                {
                    "weights": result.weights_dict,
                    "cr": cr,
                    "is_consistent": result.is_consistent,
                }
            )

        except Exception as e:
            st.error(f"计算失败: {e}")


# ============== 模块4: 差距诊断 ==============


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

    # 国际标准合规检查清单
    with st.expander("📋 国际标准合规检查清单"):
        try:
            from src.esg.core.compliance_checker import ComplianceChecker

            checker = ComplianceChecker()
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
                    st.metric(
                        "已合规条款", summary["compliant_count"], f"/ {summary['total_clauses']}"
                    )
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
                    st.markdown(
                        """
                    **优先改进项：**
                    1. 确保所有**强制**条款达到合规状态
                    2. 补充缺失的碳排放数据披露（范围1/2/3）
                    3. 完善董事会气候监督机制文档
                    4. 提升ESG报告质量和定量指标覆盖度

                    **参考标准：**
                    - ISSB S1/S2 国际可持续披露准则
                    - GRI Standards 全球报告倡议标准
                    """
                    )

        except Exception as e:
            st.error(f"合规检查加载失败: {e}")
            st.info("请确保合规检查配置正确")


# ============== 模块6: RAG智能问答 ==============


def render_rag_page(config: Dict[str, Any]) -> None:
    """渲染RAG智能问答页面

    Args:
        config: 配置参数
    """
    render_header(title="RAG智能问答", subtitle="基于知识库的AI智能问答，展示COT深度思考过程")

    # 初始化RAG引擎
    try:
        rag_engine = RAGEngine()
    except Exception as e:
        st.error(f"RAG引擎初始化失败: {e}")
        st.info("请确保向量数据库已配置并且包含文档数据")
        return

    # 页面说明
    st.info(
        """
    💡 **RAG (Retrieval-Augmented Generation)** 功能说明：
    - 使用 DeepSeek-R1 本地大语言模型
    - 基于 ChromaDB 向量数据库进行知识检索
    - 展示 AI 的 COT (Chain of Thought) 深度思考过程
    - 答案基于知识库中的ESG相关文档
    """
    )

    # 两列布局
    col1, col2 = st.columns([2, 1])

    with col1:
        # 问题输入
        st.markdown("### ❓ 输入问题")
        question = st.text_area(
            "请输入您关于ESG的问题",
            placeholder="例如：什么是ESG评级？企业如何提高ESG评分？",
            height=100,
        )

        # 参数配置
        col_topk, col_button = st.columns([1, 1])
        with col_topk:
            top_k = st.slider("检索文档数", 1, 10, 5, help="从知识库中检索的相关文档数量")
        with col_button:
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.button("🚀 开始问答", use_container_width=True, type="primary")

    with col2:
        # 系统状态
        st.markdown("### 📊 系统状态")

        # 显示模型信息
        st.metric("使用模型", "DeepSeek-R1")

        # 初始化向量存储
        from src.esg.vector_store import ChromaDBStore, get_chromadb_error

        try:
            store = ChromaDBStore()
            if store.is_available():
                collection_count = store.count()
                st.metric("知识库文档数", collection_count)
            else:
                # 显示具体的错误信息
                error_msg = get_chromadb_error()
                if error_msg and "sqlite" in error_msg.lower():
                    st.metric("知识库文档数", "SQLite版本不兼容")
                    with st.expander("查看错误详情"):
                        st.error(f"ChromaDB初始化失败: {error_msg}")
                        st.info(
                            "💡 解决方案: Python 3.9 的 SQLite3 版本低于 ChromaDB 要求的 3.35.0"
                        )
                        st.info("   方案1: 升级 Python 到 3.10+")
                        st.info("   方案2: 使用 Conda 环境: conda install python=3.10")
                else:
                    st.metric("知识库文档数", "未初始化")
                store = None
        except Exception as e:
            st.metric("知识库文档数", f"错误: {str(e)[:20]}")
            store = None

        # 添加文档上传功能
        st.markdown("---")
        st.markdown("### 📄 添加文档")

        if store is None:
            st.warning("⚠️ 向量数据库未初始化，请检查配置")
        else:
            uploaded_file = st.file_uploader("上传PDF到知识库", type=["pdf"])
            if uploaded_file:
                with st.spinner("正在处理文档..."):
                    try:
                        from src.esg.vector_store.document_loader import DocumentLoader

                        loader = DocumentLoader()

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name

                        chunks = loader.load_pdf(tmp_path)
                        store.add_documents(chunks)

                        Path(tmp_path).unlink(missing_ok=True)
                        st.success(f"✅ 已添加 {len(chunks)} 个文档片段")
                    except Exception as e:
                        st.error(f"添加失败: {e}")

    # 执行问答
    if submit_button and question:
        with st.spinner("🔍 正在检索知识库并生成答案..."):
            try:
                response = rag_engine.query(question, top_k=top_k)

                # 保存到会话状态
                st.session_state.last_rag_response = response

            except Exception as e:
                st.error(f"问答失败: {e}")
                return

    # 显示结果
    if "last_rag_response" in st.session_state:
        response = st.session_state.last_rag_response

        st.markdown("---")
        st.markdown("### 📝 问答结果")

        # COT思考过程（可展开）
        with st.expander("🔍 查看AI思考过程 (COT)", expanded=True):
            st.markdown("**深度思考过程：**")
            st.markdown(f"```\n{response.reasoning}\n```")

        # 最终答案
        st.markdown("**💡 答案：**")
        st.markdown(response.answer)

        # 参考来源
        if response.sources:
            with st.expander("📚 参考来源"):
                for i, source in enumerate(response.sources, 1):
                    meta = source.get("metadata", {})
                    st.markdown(
                        f"**[{i}]** 来源: {meta.get('source', '未知')} | 相关度: {source.get('score', 0):.2f}"
                    )
                    st.caption(source.get("text", "")[:200] + "...")

        # 置信度
        confidence_color = (
            "green"
            if response.confidence > 0.7
            else "orange" if response.confidence > 0.4 else "red"
        )
        st.markdown(f"**置信度:** :{confidence_color}[{response.confidence:.0%}]")


# ============== 模块5: AI策略建议 ==============


def render_strategies_page(config: Dict[str, Any]) -> None:
    """渲染AI策略建议页面

    Args:
        config: 配置参数
    """
    render_header(title="AI策略建议", subtitle="基于差距分析，AI智能生成改进策略")

    manager = get_state_manager()

    # 检查前提条件
    if not manager.has_metrics():
        render_empty_state(message="暂无ESG指标数据", sub_message="请先前往首页导入数据", icon="📊")
        return

    if not manager.has_gap_analysis():
        render_empty_state(
            message="暂无差距分析数据", sub_message="请先前往差距诊断页面进行分析", icon="📉"
        )
        if st.button("前往差距诊断 →"):
            manager.set_current_page("gap")
            st.rerun()
        return

    metrics = manager.get_metrics()
    benchmark = manager.get_benchmark_company()

    # 策略生成配置
    col1, col2 = st.columns([1, 3])

    with col1:
        max_strategies = st.slider("策略数量", 3, 10, 5)
        show_confidence = st.checkbox("显示AI置信度", value=True)

    with col2:
        st.info("💡 AI基于差距大小、数据质量和行业标杆自动生成策略，置信度越高表示策略针对性越强")

    # 生成策略
    try:
        gap_analyzer = GapAnalyzer()
        strategy_gen = StrategyGenerator(gap_analyzer)

        with st.spinner("🤖 AI正在生成改进策略..."):
            strategies = strategy_gen.generate_strategies(
                metrics,
                benchmark_company=benchmark,
                max_strategies=max_strategies,
            )

            # 保存策略
            strategy_list = [strategy_gen.to_dict(s) for s in strategies]
            manager.set_strategies(strategy_list)

    except Exception as e:
        st.error(f"策略生成失败: {e}")
        return

    # 策略统计
    st.markdown("### 📊 策略概览")

    priority_counts = {"高": 0, "中": 0, "低": 0}
    dim_counts = {"E": 0, "S": 0, "G": 0}
    total_confidence = 0

    for s in strategies:
        priority_counts[s.priority.value] += 1
        dim_counts[s.dimension] += 1
        total_confidence += s.confidence

    avg_confidence = total_confidence / len(strategies) if strategies else 0

    cols = st.columns(5)

    with cols[0]:
        render_metric_card("策略总数", len(strategies), "个")
    with cols[1]:
        render_metric_card(
            "高优先级", priority_counts["高"], "个", delta=1, delta_description="需重点关注"
        )
    with cols[2]:
        render_metric_card("平均置信度", f"{avg_confidence:.0%}", "")
    with cols[3]:
        top_dim = max(dim_counts, key=dim_counts.get)
        render_metric_card("主要维度", ESG_DIMENSION_NAMES[top_dim], f"{dim_counts[top_dim]}项")
    with cols[4]:
        est_impact = (
            sum(s.expected_impact for s in strategies) / len(strategies) if strategies else 0
        )
        render_metric_card("预期改进", f"{est_impact:.1f}", "分")

    # 策略列表
    st.markdown("---")
    st.markdown("### 💡 改进策略详情")

    # 按优先级排序
    priority_order = {StrategyPriority.HIGH: 0, StrategyPriority.MEDIUM: 1, StrategyPriority.LOW: 2}
    sorted_strategies = sorted(strategies, key=lambda s: priority_order.get(s.priority, 1))

    for i, strategy in enumerate(sorted_strategies, 1):
        with st.container():
            render_strategy_card(
                StrategyCardData(
                    id=strategy.id,
                    title=f"{i}. {strategy.title}",
                    description=strategy.description,
                    dimension=strategy.dimension,
                    priority=strategy.priority.value,
                    confidence=strategy.confidence,
                    actions=strategy.actions,
                    timeframe=strategy.timeframe,
                ),
                expanded=(i <= 2),
            )

    # 置信度解释
    if show_confidence:
        with st.expander("📖 AI置信度说明"):
            st.markdown(
                """
            **AI置信度**表示策略建议的可靠程度，基于以下因素计算：
            
            1. **差距大小 (40%)**: 差距越大，策略针对性越强
            2. **数据完整度 (30%)**: 数据越完整，置信度越高
            3. **模板匹配度 (20%)**: 预设策略模板的成熟度
            4. **行业可比性 (10%)**: 与行业标杆的可比性
            
            **置信度等级**:
            - 🟢 **高 (≥85%)**: 差距明显，策略匹配度高，实施路径清晰
            - 🔵 **较高 (70-84%)**: 差距适中，有成熟的行业实践可参考
            - 🟡 **中等 (55-69%)**: 差距较小或策略需要一定定制化
            - 🔴 **待提升 (<55%)**: 差距较小或数据不足，建议进一步分析
            """
            )

    # 报告生成
    st.markdown("---")
    st.markdown("### 📄 生成分析报告")

    # 语言选择
    col_lang1, col_lang2 = st.columns([1, 2])
    with col_lang1:
        report_languages = st.multiselect(
            "选择报告语言",
            options=["中文", "英文", "繁体中文"],
            default=["中文"],
            help="选择要生成的报告语言",
        )

    # 语言到枚举的映射
    language_map = {"中文": "zh_CN", "英文": "en", "繁体中文": "zh_TW"}

    if st.button("📝 生成完整报告", use_container_width=True, type="primary"):
        try:
            # 创建分析结果
            weights = manager.get_weights()
            gap_analysis = manager.get_gap_analysis()

            scores = metrics.get_all_dimension_scores()
            overall_score = sum(scores[d] * weights[d] for d in ["E", "S", "G"])

            result = AnalysisResult(
                metrics=metrics,
                weights=weights,
                gap_analysis=gap_analysis,
                strategies=strategy_list,
                overall_score=round(overall_score, 1),
                confidence_level=metrics.calculate_overall_confidence(),
            )

            generator = ReportGenerator()

            # 判断生成单语言还是多语言报告
            if len(report_languages) == 1:
                # 单语言报告
                lang_code = language_map[report_languages[0]]
                if lang_code == "zh_CN":
                    report_md = generator.generate(result)
                    file_name = f"{metrics.company_name}_ESG分析报告.md"
                else:
                    # 使用多语言功能生成
                    from src.esg.extraction.multilingual import Language

                    lang_enum = (
                        Language.ZH_CN
                        if lang_code == "zh_CN"
                        else (Language.EN if lang_code == "en" else Language.ZH_TW)
                    )
                    reports = generator.generate_multilingual(result, [lang_enum])
                    report_md = reports[lang_enum]
                    file_name = f"{metrics.company_name}_ESG分析报告_{lang_code}.md"
            else:
                # 多语言报告
                from src.esg.extraction.multilingual import Language

                lang_enums = []
                for lang in report_languages:
                    lang_code = language_map[lang]
                    if lang_code == "zh_CN":
                        lang_enums.append(Language.ZH_CN)
                    elif lang_code == "en":
                        lang_enums.append(Language.EN)
                    else:
                        lang_enums.append(Language.ZH_TW)

                reports = generator.generate_multilingual(result, lang_enums)

                # 为每个语言生成下载按钮
                for lang, content in reports.items():
                    lang_label = (
                        "中文"
                        if lang == Language.ZH_CN
                        else ("英文" if lang == Language.EN else "繁体中文")
                    )
                    st.download_button(
                        label=f"📥 下载{lang_label}报告",
                        data=content,
                        file_name=f"{metrics.company_name}_ESG分析报告_{language_map[lang_label]}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                st.success(f"已生成 {len(reports)} 份多语言报告")
                return

            # 下载按钮
            st.download_button(
                label="📥 下载Markdown报告",
                data=report_md,
                file_name=file_name,
                mime="text/markdown",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"报告生成失败: {e}")


# ============== 模块7: 沟通时机 ==============


def render_timing_page(config: Dict[str, Any]) -> None:
    """渲染沟通时机页面

    Args:
        config: 配置参数
    """
    render_header(title="沟通时机", subtitle="基于ESG策略主题，推荐最佳披露时机")

    # 初始化时机建议器
    try:
        advisor = TimingAdvisor()
    except Exception as e:
        st.error(f"时机建议器初始化失败: {e}")
        return

    # 功能说明
    st.info(
        """
    💡 **沟通时机建议** 功能说明：
    - 基于您的ESG策略主题和类型，从通信日历中匹配最佳披露时机
    - 显示目标受众、披露机会和准备建议
    - 支持检测多策略间的时机冲突
    """
    )

    # 页面布局：两列
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📝 输入策略信息")

        # 策略主题输入
        strategy_topic = st.text_input(
            "策略主题",
            placeholder="例如：碳排放管理、董事会多元化、员工培训",
            help="输入您想要披露的ESG策略主题",
        )

        # 策略类型选择
        strategy_type = st.selectbox(
            "策略类型",
            [
                "碳管理与气候",
                "可再生能源",
                "公司治理",
                "董事会多元化",
                "员工关怀",
                "社区投资",
                "生物多样性",
                "ESG披露",
                "商业道德",
            ],
        )

        # 生成建议按钮
        if st.button("🎯 获取时机建议", use_container_width=True, type="primary"):
            if strategy_topic:
                with st.spinner("🔍 正在分析最佳披露时机..."):
                    try:
                        suggestions = advisor.suggest_timing(
                            strategy_topic=strategy_topic,
                            strategy_type=strategy_type,
                        )
                        # 保存到会话状态
                        st.session_state.timing_suggestions = suggestions
                        st.session_state.current_topic = strategy_topic
                    except Exception as e:
                        st.error(f"获取建议失败: {e}")
            else:
                st.warning("请输入策略主题")

    with col2:
        st.markdown("### 📅 通信日历")

        # 显示日历事件
        all_events = advisor.get_all_events()

        # 按月份分组
        events_by_month = {}
        for event in all_events:
            month = event["date"][:7]  # YYYY-MM
            if month not in events_by_month:
                events_by_month[month] = []
            events_by_month[month].append(event)

        # 按月份排序显示
        for month in sorted(events_by_month.keys()):
            with st.expander(f"📆 {month}", expanded=False):
                for event in events_by_month[month]:
                    st.markdown(
                        f"""
                    **{event['event_name']}**
                    - 受众: {event['audience']}
                    - 机会: {event['opportunity'][:50]}...
                    """
                    )

    # 显示建议结果
    if "timing_suggestions" in st.session_state:
        suggestions = st.session_state.timing_suggestions

        st.markdown("---")
        st.markdown("### 💡 推荐时机")

        if not suggestions:
            st.warning("未找到匹配的时机建议，请尝试调整策略主题")
        else:
            # 显示建议卡片
            for i, suggestion in enumerate(suggestions, 1):
                with st.container():
                    # 相关度指示器
                    relevance_color = (
                        "green"
                        if suggestion["relevance_score"] >= 0.7
                        else "orange" if suggestion["relevance_score"] >= 0.4 else "gray"
                    )

                    st.markdown(
                        f"""
                    <div style="
                        background: white;
                        border-radius: 10px;
                        padding: 16px;
                        margin-bottom: 12px;
                        border: 1px solid #e8e8e8;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <h4 style="margin: 0;">{i}. {suggestion['event_name']}</h4>
                            <span style="
                                background: {relevance_color};
                                color: white;
                                padding: 4px 12px;
                                border-radius: 12px;
                                font-size: 0.85em;
                            ">
                                相关度: {suggestion['relevance_score']:.0%}
                            </span>
                        </div>
                        <div style="font-size: 0.9em; color: #666;">
                            <p><strong>📅 日期:</strong> {suggestion['event_date']}</p>
                            <p><strong>👥 受众:</strong> {suggestion['audience']}</p>
                            <p><strong>💡 机会:</strong> {suggestion['opportunity']}</p>
                            <p><strong>🔧 准备建议:</strong> {suggestion['preparation_advice']}</p>
                            <p><strong>📊 匹配原因:</strong> {suggestion['match_reason']}</p>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # 冲突检测
            if len(suggestions) > 1:
                conflicts = advisor.detect_conflicts(suggestions)
                if conflicts:
                    st.markdown("---")
                    st.markdown("### ⚠️ 时机冲突提醒")

                    for conflict in conflicts:
                        st.warning(conflict["message"])

        # 重置按钮
        if st.button("🔄 重新输入", use_container_width=True):
            if "timing_suggestions" in st.session_state:
                del st.session_state.timing_suggestions
            if "current_topic" in st.session_state:
                del st.session_state.current_topic
            st.rerun()


# ============== 辅助函数 ==============


def load_demo_metrics(case_type: str) -> ESGMetrics:
    """加载示例指标数据

    Args:
        case_type: 案例类型 (excellent/average/poor)

    Returns:
        ESGMetrics对象
    """
    demo_data = {
        "excellent": {
            "name": "绿色能源集团",
            "carbon": 50000,
            "renewable": 0.85,
            "efficiency": 92,
            "employees": 5000,
            "female": 0.45,
            "training": 50,
            "board": 0.60,
            "ethics": 0.90,
            "report": 90,
        },
        "average": {
            "name": "新能源科技有限公司",
            "carbon": 150000,
            "renewable": 0.45,
            "efficiency": 75,
            "employees": 3000,
            "female": 0.35,
            "training": 30,
            "board": 0.40,
            "ethics": 0.70,
            "report": 75,
        },
        "poor": {
            "name": "传统能源企业",
            "carbon": 500000,
            "renewable": 0.15,
            "efficiency": 55,
            "employees": 2000,
            "female": 0.25,
            "training": 15,
            "board": 0.25,
            "ethics": 0.50,
            "report": 60,
        },
    }

    data = demo_data.get(case_type, demo_data["average"])

    return ESGMetrics(
        company_name=data["name"],
        year="2024",
        carbon_emissions=data["carbon"],
        renewable_energy_ratio=data["renewable"],
        energy_efficiency=data["efficiency"],
        waste_recycling_rate=0.7,
        employee_count=data["employees"],
        female_ratio=data["female"],
        training_hours=data["training"],
        safety_incidents=2,
        community_investment=5000000,
        board_independence_ratio=data["board"],
        ethics_training_coverage=data["ethics"],
        esg_report_quality=data["report"],
        source="示例数据",
    )


def create_metrics_from_extraction(result: Any) -> ESGMetrics:
    """从提取结果创建ESGMetrics对象"""
    metrics_dict = result.metrics

    def get_value(name: str, default=None):
        """从指标字典中获取值

        安全地从提取结果字典中获取指定指标的值，
        如果指标不存在则返回默认值。

        Args:
            name: 指标名称
            default: 默认值，当指标不存在时返回

        Returns:
            指标值或默认值
        """
        # 边界条件检查：参数有效性
        if not isinstance(name, str) or not name.strip():
            return default

        metric = metrics_dict.get(name)

        # 边界条件检查：确保metric有value属性
        if metric is None:
            return default

        # 返回指标值
        return metric.value if hasattr(metric, "value") else default

    return ESGMetrics(
        company_name=result.company_name,
        year=result.year,
        carbon_emissions=get_value("carbon_emissions"),
        renewable_energy_ratio=get_value("renewable_energy_ratio"),
        energy_efficiency=get_value("energy_efficiency"),
        water_consumption=get_value("water_consumption"),
        waste_recycling_rate=get_value("waste_recycling_rate"),
        employee_count=int(get_value("employee_count", 0)) if get_value("employee_count") else None,
        female_ratio=get_value("female_ratio"),
        training_hours=get_value("training_hours"),
        safety_incidents=(
            int(get_value("safety_incidents", 0)) if get_value("safety_incidents") else None
        ),
        community_investment=get_value("community_investment"),
        board_independence_ratio=get_value("board_independence_ratio"),
        ethics_training_coverage=get_value("ethics_training_coverage"),
        esg_report_quality=get_value("esg_report_quality"),
        source="PDF提取",
        confidence={k: v.confidence for k, v in metrics_dict.items()},
    )


# ============== 主入口 ==============


def render_app() -> None:
    """渲染增强版应用"""
    setup_page()

    # 获取配置
    config = render_sidebar()

    # 获取当前页面
    manager = get_state_manager()
    current_page = manager.get_current_page()

    # 路由到对应页面
    if current_page == "home":
        render_home_page(config)
    elif current_page == "topics":
        render_topics_page(config)
    elif current_page == "weights":
        render_weights_page(config)
    elif current_page == "gap":
        render_gap_page(config)
    elif current_page == "strategies":
        render_strategies_page(config)
    elif current_page == "timing":
        render_timing_page(config)
    elif current_page == "rag":
        render_rag_page(config)
    else:
        render_home_page(config)


# 直接运行入口
if __name__ == "__main__":
    render_app()
