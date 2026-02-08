"""简洁版ESG分析UI

提供简化的ESG分析流程：上传PDF → 提取指标 → 分析 → 下载报告
适合快速体验和基础使用场景。
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from src.esg.analysis.gap_analyzer import GapAnalyzer
from src.esg.analysis.strategy_generator import StrategyGenerator
from src.esg.completion.report_generator import ReportGenerator
from src.esg.config import ANALYSIS_YEARS, BENCHMARK_COMPANIES, ESG_DIMENSION_NAMES
from src.esg.core.models import AnalysisResult, ESGMetrics
from src.esg.extraction.metric_extractor import MetricExtractor
from src.esg.extraction.pdf_extractor import PDFContent, PDFExtractor
from src.esg.ui.components import (
    GapCardData,
    ScoreCardData,
    render_empty_state,
    render_gap_card,
    render_header,
    render_info_box,
    render_progress_step,
    render_radar_chart,
    render_score_card,
    render_section_title,
)
from src.esg.ui.state import get_state_manager, init_session_state

# ============== 页面配置 ==============


def setup_page() -> None:
    """配置页面基础设置"""
    st.set_page_config(
        page_title="ESG分析报告系统",
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
        st.markdown("## ⚙️ 分析设置")

        # 标杆企业选择
        benchmark = st.selectbox(
            "选择对标企业",
            options=BENCHMARK_COMPANIES,
            index=len(BENCHMARK_COMPANIES) - 1,
            help="选择要对比的行业标杆企业",
        )

        # 年份选择
        year = st.selectbox("报告年份", options=ANALYSIS_YEARS, index=0, help="选择ESG报告年份")

        st.markdown("---")

        # 权重配置（简化版）
        st.markdown("### 维度权重")
        col1, col2 = st.columns(2)
        with col1:
            e_weight = st.slider("环境(E)", 0.1, 0.7, 0.4, 0.05)
            s_weight = st.slider("社会(S)", 0.1, 0.7, 0.3, 0.05)
        with col2:
            g_weight = st.slider("治理(G)", 0.1, 0.7, 0.3, 0.05)

        # 归一化权重
        total = e_weight + s_weight + g_weight
        weights = {
            "E": round(e_weight / total, 2),
            "S": round(s_weight / total, 2),
            "G": round(g_weight / total, 2),
        }

        st.markdown("---")

        # 操作按钮
        st.markdown("### 操作")

        # 重置按钮
        if st.button("🔄 重新开始", use_container_width=True):
            manager = get_state_manager()
            manager.reset()
            st.rerun()

        return {
            "benchmark": benchmark,
            "year": year,
            "weights": weights,
        }


# ============== 主流程步骤 ==============


def render_upload_step() -> Optional[PDFContent]:
    """渲染文件上传步骤

    Returns:
        提取的PDF内容，如果未上传则返回None
    """
    render_section_title("步骤 1: 上传ESG报告", "📄")

    uploaded_file = st.file_uploader(
        "上传ESG报告PDF文件", type=["pdf"], help="支持PDF格式的ESG报告文件", key="pdf_uploader"
    )

    if uploaded_file is None:
        # 显示示例数据选项
        st.markdown("或 **使用示例数据** 体验功能：")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🌟 优秀案例", use_container_width=True):
                return load_demo_data("excellent")
        with col2:
            if st.button("📊 平均案例", use_container_width=True):
                return load_demo_data("average")
        with col3:
            if st.button("⚠️ 待改进案例", use_container_width=True):
                return load_demo_data("poor")

        return None

    # 处理上传的文件
    # 安全：使用try-finally确保临时文件总是被清理，即使在异常情况下
    tmp_path = None
    content = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        with st.spinner("📖 正在提取PDF文本..."):
            extractor = PDFExtractor()
            content = extractor.extract(tmp_path)

        # 保存状态
        manager = get_state_manager()
        manager.set(
            "uploaded_file",
            {
                "name": uploaded_file.name,
                "size": len(uploaded_file.getvalue()),
            },
        )

        st.success(f"✅ 成功提取PDF: {content.metadata.company} {content.metadata.year}")

        return content

    except Exception as e:
        st.error(f"❌ PDF提取失败: {str(e)}")
        return None

    finally:
        # 安全：确保即使在异常情况下临时文件也能被删除
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass  # 忽略清理时的错误


def render_extraction_step(content: PDFContent) -> Optional[ESGMetrics]:
    """渲染指标提取步骤

    Args:
        content: PDF内容

    Returns:
        提取的ESG指标，如果失败则返回None
    """
    render_section_title("步骤 2: 提取ESG指标", "🔍")

    manager = get_state_manager()

    # 检查是否已有提取结果
    existing_metrics = manager.get_metrics()
    if existing_metrics:
        st.success("✅ 指标已提取")
        display_metrics_summary(existing_metrics)
        return existing_metrics

    # 提取指标
    try:
        with st.spinner("🔍 正在提取ESG指标..."):
            extractor = MetricExtractor()
            result = extractor.extract(
                text=content.text,
                company=content.metadata.company,
                year=content.metadata.year or "2024",
            )

        # 转换为ESGMetrics
        metrics = create_metrics_from_extraction(result)
        manager.set_metrics(metrics)

        st.success(f"✅ 成功提取 {len(result.metrics)} 项指标")

        # 显示数据质量警告
        if result.warnings:
            with st.expander("⚠️ 数据质量警告"):
                for warning in result.warnings:
                    st.warning(warning)

        display_metrics_summary(metrics)

        return metrics

    except Exception as e:
        st.error(f"❌ 指标提取失败: {str(e)}")
        return None


def render_analysis_step(metrics: ESGMetrics, config: Dict[str, Any]) -> Optional[AnalysisResult]:
    """渲染分析步骤

    Args:
        metrics: ESG指标
        config: 配置参数

    Returns:
        分析结果，如果失败则返回None
    """
    render_section_title("步骤 3: ESG分析", "📊")

    manager = get_state_manager()

    # 检查是否已有分析结果
    existing_result = manager.get_analysis_result()
    if existing_result:
        st.success("✅ 分析已完成")
        display_analysis_result(existing_result, config)
        return existing_result

    # 执行分析
    try:
        with st.spinner("📊 正在进行差距分析..."):
            gap_analyzer = GapAnalyzer()
            dim_gaps = gap_analyzer.analyze_dimension_gap(
                metrics, benchmark_company=config["benchmark"]
            )

            # 转换为字典格式
            gap_analysis = {
                "dimensions": {
                    dim: {
                        "current": gap.current,
                        "target": gap.benchmark,
                        "gap": gap.gap,
                        "priority": gap.priority,
                    }
                    for dim, gap in dim_gaps.items()
                }
            }
            manager.set_gap_analysis(gap_analysis)

        with st.spinner("💡 正在生成改进策略..."):
            strategy_gen = StrategyGenerator(gap_analyzer)
            strategies = strategy_gen.generate_strategies(
                metrics,
                benchmark_company=config["benchmark"],
                max_strategies=5,
            )

            # 转换为字典列表
            strategy_list = [strategy_gen.to_dict(s) for s in strategies]
            manager.set_strategies(strategy_list)

        # 计算总体得分
        scores = metrics.get_all_dimension_scores()
        overall_score = sum(scores[d] * config["weights"][d] for d in ["E", "S", "G"])

        # 创建分析结果
        result = AnalysisResult(
            metrics=metrics,
            weights=config["weights"],
            gap_analysis=gap_analysis,
            strategies=strategy_list,
            overall_score=round(overall_score, 1),
            confidence_level=metrics.calculate_overall_confidence(),
        )

        manager.set_analysis_result(result)

        st.success("✅ 分析完成")
        display_analysis_result(result, config)

        return result

    except Exception as e:
        st.error(f"❌ 分析失败: {str(e)}")
        return None


def render_report_step(result: AnalysisResult) -> None:
    """渲染报告下载步骤

    Args:
        result: 分析结果
    """
    render_section_title("步骤 4: 生成报告", "📄")

    try:
        # 生成报告
        generator = ReportGenerator()
        report_md = generator.generate(result)

        col1, col2 = st.columns([3, 1])

        with col1:
            # 显示报告预览
            with st.expander("📄 报告预览", expanded=False):
                st.markdown(report_md)

        with col2:
            st.markdown("### 下载报告")

            # Markdown下载
            st.download_button(
                label="📥 下载Markdown报告",
                data=report_md,
                file_name=f"{result.metrics.company_name}_ESG报告.md",
                mime="text/markdown",
                use_container_width=True,
            )

            # JSON数据下载
            import json

            json_data = json.dumps(
                {
                    "company": result.metrics.company_name,
                    "year": result.metrics.year,
                    "overall_score": result.overall_score,
                    "weights": result.weights,
                    "scores": result.metrics.get_all_dimension_scores(),
                    "gap_analysis": result.gap_analysis,
                    "strategies": result.strategies,
                },
                ensure_ascii=False,
                indent=2,
            )

            st.download_button(
                label="📥 下载JSON数据",
                data=json_data,
                file_name=f"{result.metrics.company_name}_ESG数据.json",
                mime="application/json",
                use_container_width=True,
            )

    except Exception as e:
        st.error(f"❌ 报告生成失败: {str(e)}")


# ============== 辅助函数 ==============


def load_demo_data(case_type: str) -> PDFContent:
    """加载示例数据

    Args:
        case_type: 案例类型 (excellent/average/poor)

    Returns:
        PDF内容对象
    """
    demo_texts = {
        "excellent": """
        绿色能源集团 2024年度ESG报告
        
        碳排放量: 50000吨CO2
        可再生能源占比: 85%
        能源效率: 92%
        员工总数: 5000人
        女性员工比例: 45%
        独立董事比例: 60%
        人均培训时长: 50小时
        社区投资: 8000万元
        """,
        "average": """
        新能源科技有限公司 2024年度ESG报告
        
        碳排放量: 150000吨CO2
        可再生能源占比: 45%
        能源效率: 75%
        员工总数: 3000人
        女性员工比例: 35%
        独立董事比例: 40%
        人均培训时长: 30小时
        社区投资: 3000万元
        """,
        "poor": """
        传统能源企业 2024年度ESG报告
        
        碳排放量: 500000吨CO2
        可再生能源占比: 15%
        能源效率: 55%
        员工总数: 2000人
        女性员工比例: 25%
        独立董事比例: 25%
        人均培训时长: 15小时
        社区投资: 500万元
        """,
    }

    from src.esg.extraction.pdf_extractor import PDFMetadata

    text = demo_texts.get(case_type, demo_texts["average"])
    company_names = {
        "excellent": "绿色能源集团",
        "average": "新能源科技有限公司",
        "poor": "传统能源企业",
    }

    return PDFContent(
        text=text,
        metadata=PDFMetadata(
            filename=f"demo_{case_type}.pdf",
            company=company_names.get(case_type, "示例公司"),
            year="2024",
            total_pages=10,
        ),
        pages=[text],
    )


def create_metrics_from_extraction(result: Any) -> ESGMetrics:
    """从提取结果创建ESGMetrics对象

    Args:
        result: 提取结果

    Returns:
        ESGMetrics对象
    """
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
        # 环境指标
        carbon_emissions=get_value("carbon_emissions"),
        renewable_energy_ratio=get_value("renewable_energy_ratio"),
        energy_efficiency=get_value("energy_efficiency"),
        water_consumption=get_value("water_consumption"),
        waste_recycling_rate=get_value("waste_recycling_rate"),
        # 社会指标
        employee_count=int(get_value("employee_count", 0)) if get_value("employee_count") else None,
        female_ratio=get_value("female_ratio"),
        training_hours=get_value("training_hours"),
        safety_incidents=(
            int(get_value("safety_incidents", 0)) if get_value("safety_incidents") else None
        ),
        community_investment=get_value("community_investment"),
        # 治理指标
        board_independence_ratio=get_value("board_independence_ratio"),
        ethics_training_coverage=get_value("ethics_training_coverage"),
        esg_report_quality=get_value("esg_report_quality"),
        source="PDF提取",
        confidence={k: v.confidence for k, v in metrics_dict.items()},
    )


def display_metrics_summary(metrics: ESGMetrics) -> None:
    """显示指标摘要

    Args:
        metrics: ESG指标
    """
    with st.expander("📊 查看提取的指标", expanded=True):
        cols = st.columns(3)

        # 环境指标
        with cols[0]:
            st.markdown("**🌱 环境 (E)**")
            st.write(f"碳排放: {metrics.carbon_emissions or 'N/A'} 吨")
            st.write(f"可再生能源: {metrics.renewable_energy_ratio or 'N/A'} %")
            st.write(f"能源效率: {metrics.energy_efficiency or 'N/A'} %")

        # 社会指标
        with cols[1]:
            st.markdown("**👥 社会 (S)**")
            st.write(f"员工数: {metrics.employee_count or 'N/A'} 人")
            st.write(f"女性比例: {metrics.female_ratio or 'N/A'} %")
            st.write(f"培训时长: {metrics.training_hours or 'N/A'} 小时")

        # 治理指标
        with cols[2]:
            st.markdown("**⚖️ 治理 (G)**")
            st.write(f"独董比例: {metrics.board_independence_ratio or 'N/A'} %")
            st.write(f"伦理培训: {metrics.ethics_training_coverage or 'N/A'} %")


def display_analysis_result(result: AnalysisResult, config: Dict[str, Any]) -> None:
    """显示分析结果

    Args:
        result: 分析结果
        config: 配置参数
    """
    # 总体评分卡片
    col1, col2, col3 = st.columns(3)

    with col1:
        render_score_card(
            ScoreCardData(
                title="ESG综合得分",
                score=result.overall_score,
                description=f"数据置信度: {result.confidence_level}",
            )
        )

    with col2:
        scores = result.metrics.get_all_dimension_scores()
        best_dim = max(scores, key=scores.get)
        render_score_card(
            ScoreCardData(
                title=f"最佳维度: {ESG_DIMENSION_NAMES[best_dim]}",
                score=scores[best_dim],
                color="#52c41a",
            )
        )

    with col3:
        worst_dim = min(scores, key=scores.get)
        render_score_card(
            ScoreCardData(
                title=f"待改进: {ESG_DIMENSION_NAMES[worst_dim]}",
                score=scores[worst_dim],
                color="#faad14",
            )
        )

    # 雷达图
    st.plotly_chart(
        render_radar_chart(scores=scores, title="ESG维度评分雷达图"), use_container_width=True
    )

    # 差距分析
    with st.expander("📉 差距分析", expanded=True):
        gap_data = result.gap_analysis.get("dimensions", {})

        cols = st.columns(3)
        for i, dim in enumerate(["E", "S", "G"]):
            gap = gap_data.get(dim, {})
            with cols[i]:
                render_gap_card(
                    GapCardData(
                        dimension=dim,
                        current=gap.get("current", 0),
                        benchmark=gap.get("target", 0),
                        gap=gap.get("gap", 0),
                        priority=gap.get("priority", "中"),
                    )
                )

    # 改进策略
    with st.expander("💡 改进策略", expanded=False):
        for i, strategy in enumerate(result.strategies[:5], 1):
            priority = strategy.get("priority", "中")
            priority_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(priority, "⚪")

            st.markdown(f"**{i}. {priority_emoji} {strategy.get('title', '')}**")
            st.caption(f"置信度: {strategy.get('confidence', 0):.0%}")
            st.write(strategy.get("description", ""))

            actions = strategy.get("actions", [])
            if actions:
                with st.container():
                    for action in actions[:3]:  # 只显示前3个行动项
                        st.markdown(f"  • {action}")
            st.markdown("---")


# ============== 主入口 ==============


def render_simple_app() -> None:
    """渲染简洁版应用"""
    setup_page()

    # 头部
    render_header(title="ESG分析报告系统", subtitle="上传ESG报告，智能分析企业可持续发展表现")

    # 侧边栏配置
    config = render_sidebar()

    # 获取状态管理器
    manager = get_state_manager()

    # 确定当前步骤
    current_step = 0
    pdf_content = None
    metrics = None
    analysis_result = None

    # 步骤1: 上传
    pdf_content = render_upload_step()
    if pdf_content:
        current_step = 1

    st.markdown("---")

    # 步骤2: 提取
    if pdf_content:
        metrics = render_extraction_step(pdf_content)
        if metrics:
            current_step = 2

    st.markdown("---")

    # 步骤3: 分析
    if metrics:
        analysis_result = render_analysis_step(metrics, config)
        if analysis_result:
            current_step = 3

    st.markdown("---")

    # 步骤4: 报告
    if analysis_result:
        render_report_step(analysis_result)
        current_step = 4

    # 显示进度条
    progress = (current_step / 4) * 100
    st.sidebar.progress(int(progress), f"总进度: {int(progress)}%")


# 直接运行入口
if __name__ == "__main__":
    render_simple_app()
