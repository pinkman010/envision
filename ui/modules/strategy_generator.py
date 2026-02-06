"""模块四：AI策略建议生成器

功能：大模型Prompt工程 + RAG知识增强
"""

import streamlit as st

from analysis.strategy_generator import StrategyGenerator
from ui.components.common import render_diagnosis_card, render_priority_badge, render_confidence_badge
from ui.state import AppState


def render():
    """渲染策略建议模块"""
    st.markdown('<h1 class="module-title">💡 AI策略建议生成器</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: 本地大模型 + RAG知识增强 + 专家Prompt模板</p>', unsafe_allow_html=True)
    
    strategy_gen = StrategyGenerator()
    
    # 如果没有差距分析，先执行
    if AppState.get('gap_analysis') is None:
        from analysis.gap_analyzer import GapAnalyzer
        gap_analyzer = GapAnalyzer()
        result = gap_analyzer.analyze_gap(AppState.get('benchmark_company', '维斯塔斯'))
        AppState.set('gap_analysis', result)
    
    # 生成诊断和策略
    if AppState.get('diagnosis') is None:
        gap_analysis = AppState.get('gap_analysis')
        AppState.set('diagnosis', strategy_gen.generate_diagnosis(gap_analysis))
        AppState.set('strategies', strategy_gen.generate_strategies(AppState.get('diagnosis')))
    
    diagnosis = AppState.get('diagnosis')
    strategies = AppState.get('strategies')
    
    render_diagnosis_section(diagnosis)
    render_action_list(strategies)
    render_refinement_section(strategy_gen, strategies)


def render_diagnosis_section(diagnosis: list):
    """渲染诊断结果"""
    st.markdown("### 📋 核心诊断结果")
    
    if not diagnosis:
        st.info("暂无诊断结果")
        return
    
    diag_cols = st.columns(min(3, len(diagnosis)))
    
    for i, diag in enumerate(diagnosis[:3]):
        with diag_cols[i]:
            render_diagnosis_card(
                title=diag.get('title', ''),
                severity=diag.get('severity', '中'),
                gap=diag.get('gap', 0)
            )
    
    st.markdown("---")


def render_action_list(strategies: list):
    """渲染行动清单"""
    st.markdown("### ✅ 优先改进行动清单")
    
    if not strategies:
        st.info("暂无策略建议")
        return
    
    for i, strategy in enumerate(strategies, 1):
        with st.expander(f"{i}. {strategy.get('title', '')} [{strategy.get('priority', '中')}优先级]"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**问题诊断**: {strategy.get('diagnosis_title', '')}")
                st.write(f"**改进周期**: {strategy.get('timeline', '')}")
                st.write(f"**预期收益**: {strategy.get('benefit', '')}")
                
                st.write("**行动计划**:")
                for j, action in enumerate(strategy.get('actions', []), 1):
                    st.checkbox(f"{j}. {action}", key=f"action_{i}_{j}")
                
                standards = strategy.get('standards', [])
                if standards:
                    st.caption(f"参考标准: {', '.join(standards)}")
            
            with col2:
                render_priority_badge(strategy.get('priority', '中'))
                st.markdown("<br>", unsafe_allow_html=True)
                
                confidence = strategy.get('confidence', {})
                render_confidence_badge(confidence)


def render_refinement_section(strategy_gen: StrategyGenerator, strategies: list):
    """渲染微调区"""
    st.markdown("---")
    st.markdown("### 🤖 大模型对话微调")
    
    st.write("对建议不满意？您可以输入指令进行微调：")
    
    instruction = st.text_input(
        "输入微调指令",
        placeholder="例如：'请把建议语气调整得更适合投资者阅读' 或 '重点关注环境维度的改进'",
        label_visibility="collapsed"
    )
    
    if st.button("✨ 生成优化建议", type="primary"):
        if instruction:
            with st.spinner("AI正在优化建议..."):
                refined = strategy_gen.refine_strategies(strategies, instruction)
                
                st.success("✓ 已根据您的指令优化建议")
                
                st.markdown("#### 优化后的建议")
                for s in refined[:2]:
                    st.info(f"**{s.get('title', '')}**\n\n{s.get('refined_benefit', '')}")
        else:
            st.warning("请输入微调指令")
