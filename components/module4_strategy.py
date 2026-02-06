# -*- coding: utf-8 -*-
"""
模块四：AI策略建议生成器
功能：诊断卡片 + 行动清单 + 大模型对话
"""
import streamlit as st
import html  # [ADDED] 防止XSS攻击
import pandas as pd
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_modules.strategy_generator import StrategyGenerator
from new_modules.gap_analyzer import GapAnalyzer


def render_strategy_generator():
    """渲染模块四界面"""
    st.markdown("## 💡 AI策略建议生成器")
    st.markdown("**技术栈**: 本地大模型 + RAG知识增强 + 专家Prompt模板")
    st.markdown("---")
    
    # 初始化
    generator = StrategyGenerator()
    use_real = st.session_state.get('use_real_data', False)
    gap_analyzer = GapAnalyzer(use_real_data=use_real)
    
    # 获取差距分析结果
    benchmark_name = st.session_state.get('benchmark_company', '维斯塔斯')
    gap_data = gap_analyzer.calculate_gap(benchmark_name)
    
    # === 顶部：诊断卡片区 ===
    st.markdown("### 📋 核心诊断结果")
    
    # 检查是否有优先改进行动
    priority_actions = gap_data.get('priority_actions', [])
    if not priority_actions:
        st.info("暂无优先改进行动数据，请先提取ESG报告或检查差距分析")
        return
    
    card_cols = st.columns(len(priority_actions))
    
    for i, (col, action) in enumerate(zip(card_cols, priority_actions)):
        with col:
            card_color = "#fff2f0" if action['urgency'] == '高' else "#fffbe6"
            border_color = "#ff4d4f" if action['urgency'] == '高' else "#faad14"
            
            # [FIXED] 转义所有动态内容
            indicator_escaped = html.escape(str(action['indicator']))
            gap_str = html.escape(f"{action['gap']:.0f}")
            urgency_escaped = html.escape(str(action['urgency']))
            
            st.markdown(f"""
            <div style="background: {card_color}; border: 1px solid {border_color}; 
                        padding: 16px; border-radius: 8px; text-align: center;                <div style="font-size: 24px; margin-bottom: 8px;">{'🔴' if action['urgency'] == '高' else '🟡'}</div>
                <h4 style="margin: 0; color: #333;">{indicator_escaped}</h4>
                <p style="color: {border_color}; font-size: 18px; font-weight: bold; margin: 8px 0;">
                    差距 {gap_str}分
                </p>
                <span style="background: {border_color}; color: white; padding: 2px 12px; 
                            border-radius: 12px; font-size: 12px;">
                    {urgency_escaped}优先级
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === 生成策略 ===
    st.markdown("### 🎯 AI生成策略建议")
    
    # 策略数量选择
    strategy_count = st.slider("生成策略数量", min_value=3, max_value=8, value=5)
    
    # 目标读者选择
    target_audience = st.selectbox(
        "目标读者",
        ["投资者", "监管机构", "公众/媒体", "内部管理层"]
    )
    
    if st.button("🚀 生成策略建议", type="primary"):
        with st.spinner("AI正在分析并生成策略..."):
            strategies = generator.generate_strategies(gap_data, max_items=strategy_count)
            
            # 存储到session
            st.session_state.generated_strategies = strategies
            st.session_state.target_audience = target_audience
    
    # === 策略展示 ===
    if 'generated_strategies' in st.session_state:
        strategies = st.session_state.generated_strategies
        
        st.markdown(f"#### ✅ 已生成 {len(strategies)} 条策略建议")
        
        for i, strategy in enumerate(strategies):
            formatted = generator.format_strategy_for_display(strategy)
            
            # 优先级标签颜色
            priority_colors = {'高': '#ff4d4f', '中': '#faad14', '低': '#52c41a'}
            priority_color = priority_colors.get(formatted['priority'], '#999')
            
            # 时间线颜色
            timeline_colors = {'短期': '#1890ff', '中期': '#722ed1', '长期': '#13c2c2'}
            timeline_color = timeline_colors.get(formatted['timeline'], '#999')
            
            # [FIXED] 转义所有动态字符串内容
            title_escaped = html.escape(str(formatted['title']))
            priority_escaped = html.escape(str(formatted['priority']))
            timeline_escaped = html.escape(str(formatted['timeline']))
            responsible_escaped = html.escape(str(formatted['responsible']))
            description_escaped = html.escape(str(formatted['description']))
            outcome_escaped = html.escape(str(formatted['outcome']))
            
            with st.expander(f"**{i+1}. {title_escaped}** | 优先级: {priority_escaped} | {timeline_escaped}", expanded=(i==0)):
                
                # 标签行
                st.markdown(f"""
                <div style="margin-bottom: 12px;">
                    <span style="background: {priority_color}; color: white; padding: 2px 8px; 
                                border-radius: 4px; font-size: 12px; margin-right: 8px;">
                        {priority_escaped}优先级
                    </span>
                    <span style="background: {timeline_color}; color: white; padding: 2px 8px; 
                                border-radius: 4px; font-size: 12px; margin-right: 8px;">
                        {timeline_escaped}
                    </span>
                    <span style="background: #f0f0f0; color: #666; padding: 2px 8px; 
                                border-radius: 4px; font-size: 12px;">
                        📍 {responsible_escaped}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # 描述
                st.markdown(f"**描述**: {description_escaped}")
                
                # 行动步骤
                st.markdown("**📝 具体行动步骤:**")
                for j, step in enumerate(formatted['steps'], 1):
                    # [FIXED] 步骤内容也需要转义，防止策略生成器返回恶意内容
                    step_escaped = html.escape(str(step))
                    st.checkbox(f"{j}. {step_escaped}", key=f"step_{i}_{j}")
                
                # 参考标准
                st.markdown("**📚 参考标准:**")
                # [FIXED] 转义标准名称
                standards_escaped = " | ".join([f"`{html.escape(str(s))}`" for s in formatted['standards']])
                st.markdown(standards_escaped)
                
                # 预期效果
                st.success(f"**🎯 预期效果**: {outcome_escaped}")
        
        # === 实施路线图 ===
        st.markdown("---")
        st.markdown("### 🗺️ 实施路线图")
        
        roadmap = generator.get_implementation_roadmap(strategies)
        
        roadmap_cols = st.columns(3)
        
        for col, (period, items) in zip(roadmap_cols, roadmap.items()):
            with col:
                period_icons = {'短期(0-6个月)': '🏃', '中期(6-18个月)': '🚶', '长期(18个月+)': '🎯'}
                icon = period_icons.get(period, '📌')
                
                st.markdown(f"#### {icon} {html.escape(period)}")
                
                if items:
                    for item in items:
                        st.markdown(f"- {html.escape(str(item))}")
                else:
                    st.markdown("*暂无*")
        
        # === 任务检查表 ===
        st.markdown("---")
        with st.expander("📋 完整任务检查表", expanded=False):
            checklist = generator.generate_checklist(strategies)
            
            checklist_df = pd.DataFrame([
                {
                    "策略": html.escape(item['strategy_title'][:20] + "..."),
                    "步骤": html.escape(item['step_content']),
                    "优先级": item['priority'],
                    "完成": "☐"
                }
                for item in checklist
            ])
            
            st.dataframe(checklist_df, hide_index=True, use_container_width=True)
    
    # === 大模型对话微调区 ===
    st.markdown("---")
    st.markdown("### 💬 大模型对话微调")
    
    st.caption("对建议不满意？您可以输入指令进行微调")
    
    # 检查RAG系统是否可用
    rag_available = False
    try:
        from scripts.ollama_utils import check_ollama_running
        from scripts.config import VECTOR_DB_PATH
        
        ollama_ok = check_ollama_running()
        db_ok = os.path.exists(VECTOR_DB_PATH) and os.listdir(VECTOR_DB_PATH)
        rag_available = ollama_ok and db_ok
    except:
        pass
    
    if not rag_available:
        st.warning("⚠️ RAG系统未就绪。请确保：\n1. Ollama服务已启动 (`ollama serve`)\n2. 知识库已构建 (`python scripts/create_vector_db.py`)")
    
    # 用户输入
    user_input = st.text_area(
        "输入微调指令",
        placeholder="例如：请把建议语气调整得更适合投资者阅读...",
        height=100
    )
    
    example_prompts = [
        "请将策略简化为3条最核心的建议",
        "请添加更多关于Scope 3碳核算的具体步骤",
        "请用更专业的语气重写，适合给董事会汇报",
        "请为每条策略补充ROI预估"
    ]
    
    st.caption("💡 示例指令:")
    prompt_cols = st.columns(2)
    for i, prompt in enumerate(example_prompts):
        with prompt_cols[i % 2]:
            if st.button(prompt, key=f"example_{i}"):
                user_input = prompt
    
    if st.button("🔄 生成优化建议", disabled=not rag_available):
        if user_input:
            with st.spinner("正在调用大模型..."):
                try:
                    from scripts.rag_system import RAGSystem
                    
                    # 构建增强Prompt
                    context_prompt = generator.generate_llm_prompt(
                        gap_data, 
                        st.session_state.get('target_audience', '投资者')
                    )
                    
                    full_prompt = f"""
{context_prompt}

【用户微调指令】
{user_input}

请根据用户指令优化上述策略建议。
"""
                    
                    with RAGSystem() as rag:
                        response_text = ""
                        for msg_type, content in rag.ask_stream(full_prompt):
                            if msg_type == "answer":
                                response_text += content
                            elif msg_type == "done":
                                break
                        
                        st.markdown("#### 🤖 AI优化结果")
                        st.markdown(response_text)
                        
                except Exception as e:
                    st.error(f"调用失败: {e}")
                    st.info("提示：请确保Ollama服务正在运行且知识库已构建")
        else:
            st.warning("请输入微调指令")
    
    # === 业务价值说明 ===
    st.markdown("---")
    st.info("""
    **📌 业务价值**
    - **自动化策略生成**: 基于差距分析自动生成可执行策略
    - **标准对齐**: 策略与国际标准（ISO、GRI、SASB等）对齐
    - **可视化路线图**: 清晰的短中长期实施计划
    - **大模型微调**: 支持个性化调整，适应不同读者需求
    """)