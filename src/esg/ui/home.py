"""首页模块（简化版）

提供数据导入与概览功能。
简化版：数据导入 → 提取指标 → 前往差距诊断
"""

import tempfile
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from src.esg.config import ESG_COLORS, ESG_DIMENSION_NAMES
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
    render_score_card,
)
from src.esg.ui.state import get_state_manager
from src.esg.ui.utils.data_loader import load_demo_metrics
from src.esg.ui.utils.metrics import create_metrics_from_extraction


def render_home_page(config: Dict[str, Any]) -> None:
    """渲染首页（简化版）

    简化后：数据导入 → 提取指标 → 前往差距诊断
    """
    render_header(title="ESG智能分析系统", subtitle="基于AI的ESG综合评估与改进建议平台")

    manager = get_state_manager()

    # 数据导入
    st.markdown("## 📥 数据导入")

    tab1, tab2 = st.tabs(["📄 上传PDF报告", "🎲 示例数据"])

    with tab1:
        _render_pdf_upload()

    with tab2:
        _render_demo_data_selection()

    # 如果有数据，显示概览和快速分析
    if manager.has_metrics():
        st.markdown("---")
        st.markdown("## 📊 指标概览")
        _render_metrics_overview()

        # 一键分析按钮（简化版）
        st.markdown("---")
        if st.button("🚀 一键分析 → 前往差距诊断", use_container_width=True, type="primary"):
            manager.set_current_page("gap")
            st.rerun()


def _render_pdf_upload() -> None:
    """渲染PDF上传区域"""
    uploaded_file = st.file_uploader(
        "上传ESG报告PDF",
        type=["pdf"],
        help="系统将从PDF中自动提取ESG相关指标",
    )

    if uploaded_file:
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
            st.error(f"❌ PDF提取库未安装: {str(e)}")
            st.info("💡 请安装 PDF 提取库: `pip install pdfplumber` 或 `pip install PyPDF2`")
            _offer_fallback_options()

        except PDFNotFoundError as e:
            st.error(f"❌ 文件读取失败: {str(e)}")
            _offer_fallback_options()

        except PDFExtractionError as e:
            st.error(f"❌ PDF解析失败: {str(e)}")
            st.warning("⚠️ PDF文件可能已损坏或为扫描版，请尝试:")
            st.info("  • 使用文本可复制的PDF文件")
            st.info("  • 手动提取文本后使用手动输入功能")
            _offer_fallback_options()

        except Exception as e:
            st.error(f"❌ 提取过程中发生未知错误: {str(e)}")
            _offer_fallback_options()

        # 如果提取成功，保存指标
        if extraction_success and extracted_metrics:
            manager = get_state_manager()
            manager.set_metrics(extracted_metrics)
            manager.set(
                "uploaded_file",
                {
                    "name": uploaded_file.name,
                    "size": len(uploaded_file.getvalue()) / 1024,
                },
            )

            st.success(f"✅ 成功提取: {extracted_metrics.company_name} {extracted_metrics.year}")


def _offer_fallback_options() -> None:
    """提供备用选项"""
    st.markdown("---")
    st.markdown("**您可以尝试以下替代方案：**")

    if st.button("🎲 使用示例数据", use_container_width=True):
        metrics = load_demo_metrics()
        manager = get_state_manager()
        manager.set_metrics(metrics)
        st.success(f"✅ 已加载示例数据: {metrics.company_name}")
        st.rerun()


def _render_demo_data_selection() -> None:
    """渲染示例数据选择"""
    st.markdown("加载示例数据集体验功能：")

    if st.button("加载绿色能源集团示例数据", key="demo_green_energy", use_container_width=True):
        metrics = load_demo_metrics()
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

        with cols[2]:
            st.markdown("**⚖️ 治理指标**")
            st.write(
                f"独董比例: {metrics.board_independence_ratio:.1%}"
                if metrics.board_independence_ratio
                else "独董比例: N/A"
            )
