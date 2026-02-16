"""AI策略建议模块

提供基于差距分析的AI智能生成改进策略功能。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.analysis.gap_analyzer import GapAnalyzer
from src.esg.analysis.strategy_generator import StrategyGenerator, StrategyPriority
from src.esg.config import ESG_DIMENSION_NAMES
from src.esg.core.models import AnalysisResult
from src.esg.extraction.multilingual import Language
from src.esg.ui.components import (
    StrategyCardData,
    render_empty_state,
    render_header,
    render_metric_card,
    render_strategy_card,
)
from src.esg.ui.state import get_state_manager


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
            st.markdown("""
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
            """)

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
        _generate_report(
            report_languages, language_map, metrics, manager, strategies, strategy_list
        )


def _generate_report(
    report_languages: list,
    language_map: Dict[str, str],
    metrics: Any,
    manager: Any,
    strategies: list,
    strategy_list: list,
) -> None:
    """生成分析报告

    Args:
        report_languages: 报告语言列表
        language_map: 语言映射
        metrics: ESG指标
        manager: 状态管理器
        strategies: 策略列表
        strategy_list: 策略字典列表
    """
    try:
        from src.esg.completion.report_generator import ReportGenerator

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
