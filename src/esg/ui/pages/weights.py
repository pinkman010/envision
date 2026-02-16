"""权重配置模块

提供AHP层次分析法配置维度权重功能。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.config import AHP_CONSISTENCY_THRESHOLD, ESG_COLORS, ESG_DIMENSION_NAMES
from src.esg.fusion.ahp import AHPFusionEngine
from src.esg.ui.components import (
    ScoreCardData,
    render_dimension_comparison,
    render_header,
    render_score_card,
)
from src.esg.ui.state import get_state_manager


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
        _render_simple_weights_config()
    else:
        _render_ahp_weights_config()

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


def _render_simple_weights_config() -> None:
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


def _render_ahp_weights_config() -> None:
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
