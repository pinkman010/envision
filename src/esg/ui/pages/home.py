"""首页模块

提供数据导入与概览功能。
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from src.esg.config import ANALYSIS_YEARS, ESG_COLORS, ESG_DIMENSION_NAMES
from src.esg.extraction.metric_extractor import MetricExtractor
from src.esg.extraction.pdf_extractor import (
    PDFExtractionError,
    PDFExtractor,
    PDFLibraryNotFoundError,
    PDFNotFoundError,
)
from src.esg.ui.components import (
    ScoreCardData,
    render_gauge_chart,
    render_header,
    render_metric_card,
    render_score_card,
)
from src.esg.ui.state import get_state_manager
from src.esg.ui.utils.data_loader import load_demo_metrics
from src.esg.ui.utils.metrics import create_metrics_from_extraction


def render_home_page(config: Dict[str, Any]) -> None:
    """渲染首页

    Args:
        config: 配置参数
    """
    render_header(title="ESG智能分析系统", subtitle="基于AI的ESG综合评估与改进建议平台")

    # 功能概览
    st.markdown("## 🎯 功能概览")

    features = [
        ("📊", "议题全景图", "了解行业ESG议题热度和趋势"),
        ("📋", "实质性矩阵", "评估ESG实质性议题双重重要性"),
        ("🔍", "竞争对手分析", "行业最佳实践对标与竞争情报"),
        ("⚖️", "权重配置", "使用AHP方法定制维度权重"),
        ("📉", "差距诊断", "对标标杆企业进行差距分析"),
        ("💡", "AI策略建议", "获取AI生成的改进策略"),
        ("📅", "沟通时机", "推荐最佳ESG披露时机"),
        ("💬", "RAG智能问答", "基于知识库的AI问答助手"),
    ]

    # 第一行：4个功能
    cols = st.columns(4)
    for col, (icon, title, desc) in zip(cols, features[:4]):
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

    # 第二行：4个功能
    cols = st.columns(4)
    for col, (icon, title, desc) in zip(cols, features[4:]):
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
        _render_pdf_upload()

    with tab2:
        _render_manual_input()

    with tab3:
        _render_demo_data_selection()

    # 如果有数据，显示概览
    if manager.has_metrics():
        st.markdown("---")
        st.markdown("## 📊 当前数据概览")
        _render_metrics_overview()


def _render_pdf_upload() -> None:
    """渲染PDF上传区域"""
    uploaded_file = st.file_uploader(
        "上传ESG报告PDF",
        type=["pdf"],
        help="系统将从PDF中自动提取ESG相关指标",
    )

    if uploaded_file:
        # 1. 首先尝试PDF提取
        extraction_success = False
        extracted_metrics = None

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

                extracted_metrics = create_metrics_from_extraction(result)
                extraction_success = True

            Path(tmp_path).unlink(missing_ok=True)

        except PDFLibraryNotFoundError as e:
            # 情况1: PDF库未安装
            st.error(f"❌ PDF提取库未安装: {str(e)}")
            st.info("💡 请安装 PDF 提取库: `pip install pdfplumber` 或 `pip install PyPDF2`")
            _offer_fallback_options(uploaded_file)

        except PDFNotFoundError as e:
            # 情况2: 文件不存在或路径不安全
            st.error(f"❌ 文件读取失败: {str(e)}")
            _offer_fallback_options(uploaded_file)

        except PDFExtractionError as e:
            # 情况3: PDF提取失败（如文件损坏、加密等）
            st.error(f"❌ PDF解析失败: {str(e)}")
            st.warning("⚠️ PDF文件可能已损坏或为扫描版，请尝试:")
            st.info("  • 使用文本可复制的PDF文件")
            st.info("  • 手动提取文本后使用手动输入功能")
            _offer_fallback_options(uploaded_file)

        except (IOError, OSError) as e:
            # 情况4: 文件IO错误
            st.error(f"❌ 文件操作失败: {str(e)}")
            _offer_fallback_options(uploaded_file)

        except Exception as e:
            # 情况5: 其他未知错误
            st.error(f"❌ 提取过程中发生未知错误: {str(e)}")
            _offer_fallback_options(uploaded_file)

        # 2. 如果提取成功，保存指标
        if extraction_success and extracted_metrics:
            manager = get_state_manager()
            manager.set_metrics(extracted_metrics)
            manager.set(
                "uploaded_file",
                {
                    "name": uploaded_file.name,
                    "size": len(uploaded_file.getvalue()) / 1024,  # KB
                },
            )

            st.success(f"✅ 成功提取: {extracted_metrics.company_name} {extracted_metrics.year}")

            # 自动跳转到差距诊断
            if st.button("前往差距诊断 →"):
                manager.set_current_page("gap")
                st.rerun()


def _offer_fallback_options(uploaded_file) -> None:
    """提供备用选项给用户

    Args:
        uploaded_file: 用户上传的文件对象
    """
    st.markdown("---")
    st.markdown("**您可以尝试以下替代方案：**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 手动输入数据", use_container_width=True):
            # 切换到手动输入标签页
            st.session_state["active_tab"] = 1
            st.rerun()

    with col2:
        if st.button("🎲 使用示例数据", use_container_width=True):
            # 加载示例数据
            metrics = load_demo_metrics("average")
            manager = get_state_manager()
            manager.set_metrics(metrics)
            st.success(f"✅ 已加载示例数据: {metrics.company_name}")
            st.rerun()


def _render_manual_input() -> None:
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
            from src.esg.core.models import ESGMetrics

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


def _render_demo_data_selection() -> None:
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


def _render_metrics_overview() -> None:
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
