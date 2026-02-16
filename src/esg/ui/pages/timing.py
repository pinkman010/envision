"""沟通时机模块

提供基于ESG策略主题的披露时机推荐功能。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.analysis.timing_advisor import TimingAdvisor
from src.esg.ui.components import render_header


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
    st.info("""
    💡 **沟通时机建议** 功能说明：
    - 基于您的ESG策略主题和类型，从通信日历中匹配最佳披露时机
    - 显示目标受众、披露机会和准备建议
    - 支持检测多策略间的时机冲突
    """)

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
                    st.markdown(f"""
                    **{event['event_name']}**
                    - 受众: {event['audience']}
                    - 机会: {event['opportunity'][:50]}...
                    """)

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
