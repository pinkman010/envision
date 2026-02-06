# -*- coding: utf-8 -*-
"""
模块二：智能权重配置
功能：AHP层次分析法 + 一致性检验 + 舆情联动
"""
import streamlit as st
import html  # [ADDED] 用于防止XSS攻击
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_modules.ahp_calculator import AHPCalculator
from new_modules.news_crawler import NewsCrawler


def create_radar_chart(weights_dict, title="ESG权重分布"):
    """创建雷达图"""
    # 检查是否有数据
    if not weights_dict:
        fig = go.Figure()
        fig.update_layout(
            title="暂无权重数据",
            height=400,
            annotations=[{
                'text': '暂无权重数据',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'font': {'size': 20, 'color': 'gray'}
            }]
        )
        return fig
    
    categories = list(weights_dict.keys())
    values = list(weights_dict.values())
    
    # 闭合图形
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(99, 110, 250, 0.3)',
        line=dict(color='rgb(99, 110, 250)', width=2),
        name='当前权重'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.2]
            )
        ),
        title=title,
        showlegend=False,
        height=400
    )
    
    return fig


def create_pie_chart(weights_dict):
    """创建环形图"""
    # 检查是否有数据
    if not weights_dict:
        fig = go.Figure()
        fig.update_layout(
            title="暂无权重数据",
            height=400,
            annotations=[{
                'text': '暂无权重数据',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'font': {'size': 20, 'color': 'gray'}
            }]
        )
        return fig
    
    labels = list(weights_dict.keys())
    values = list(weights_dict.values())
    
    colors = {'E': '#52c41a', 'S': '#1890ff', 'G': '#faad14'}
    color_list = [colors.get(k, '#999') for k in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=color_list,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title="ESG维度权重占比",
        height=400,
        annotations=[dict(text='ESG', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    return fig


def render_weight_config():
    """渲染模块二界面"""
    st.markdown("## ⚖️ 智能权重配置")
    st.markdown("**技术栈**: AHP层次分析法 + 一致性检验 + 舆情动态调整")
    st.markdown("---")
    
    # 初始化
    if 'ahp_calculator' not in st.session_state:
        st.session_state.ahp_calculator = AHPCalculator()
    
    calculator = st.session_state.ahp_calculator
    
    # === 上方：交互配置区 ===
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 判断矩阵配置")
        
        # AI专家评估选择
        st.markdown("#### 🤖 AI虚拟专家评估")
        perspective = st.radio(
            "本次评估更关注哪种视角？",
            options=[
                "A. 财务稳健性（投资者视角）",
                "B. 合规与风险（监管视角）",
                "C. 品牌影响力（公众视角）",
                "D. 自定义配置"
            ],
            horizontal=True,
            key="perspective_radio"
        )
        
        # 映射视角
        perspective_map = {
            "A. 财务稳健性（投资者视角）": "financial",
            "B. 合规与风险（监管视角）": "compliance",
            "C. 品牌影响力（公众视角）": "brand",
            "D. 自定义配置": None
        }
        selected_perspective = perspective_map[perspective]
        
        # 语义标度说明
        st.markdown("""
        <div style="background: #f0f2f5; padding: 12px; border-radius: 8px; margin: 12px 0;">
        <b>语义标度说明</b>: 极端重要(9) | 明显重要(7) | 强烈重要(5) | 稍微重要(3) | 同等重要(1)
        </div>
        """, unsafe_allow_html=True)
        
        # 判断矩阵输入
        if selected_perspective:
            # AI自动填充
            ai_suggestion = calculator.generate_ai_suggestions(selected_perspective)
            st.success(f"✅ AI已根据【{html.escape(perspective)}】自动填充判断矩阵")
            
            with st.expander("🔍 查看AI推理依据", expanded=False):
                st.write(ai_suggestion['reasoning'])
                st.write(f"置信度: {ai_suggestion['confidence']*100:.0f}%")
            
            # 从AI建议中提取值
            suggestions = ai_suggestion['suggestions']
            e_vs_s = suggestions.get('EvsS', 1)
            e_vs_g = suggestions.get('EvsG', 1)
            s_vs_g = suggestions.get('SvsG', 1)
            
            # 显示矩阵（只读模式）
            matrix_data = {
                "": ["E 环境", "S 社会", "G 治理"],
                "E 环境": [1, e_vs_s, e_vs_g],
                "S 社会": [round(1/e_vs_s, 2), 1, s_vs_g],
                "G 治理": [round(1/e_vs_g, 2), round(1/s_vs_g, 2), 1]
            }
            st.dataframe(pd.DataFrame(matrix_data).set_index(""), use_container_width=True)
            
        else:
            # 手动配置模式
            st.markdown("##### 两两比较（拖动滑块）")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                e_vs_s = st.slider(
                    "E环境 vs S社会",
                    min_value=1/9, max_value=9.0, value=1.0,
                    format="%.2f",
                    help="大于1表示E比S重要，小于1表示S比E重要"
                )
                st.caption("当前: E " + ("更重要" if e_vs_s > 1 else "次要" if e_vs_s < 1 else "同等"))
            
            with col_b:
                e_vs_g = st.slider(
                    "E环境 vs G治理",
                    min_value=1/9, max_value=9.0, value=1.0,
                    format="%.2f"
                )
                st.caption("当前: E " + ("更重要" if e_vs_g > 1 else "次要" if e_vs_g < 1 else "同等"))
            
            with col_c:
                s_vs_g = st.slider(
                    "S社会 vs G治理",
                    min_value=1/9, max_value=9.0, value=1.0,
                    format="%.2f"
                )
                st.caption("当前: S " + ("更重要" if s_vs_g > 1 else "次要" if s_vs_g < 1 else "同等"))
        
        # 创建判断矩阵
        calculator.create_comparison_matrix(
            ['E', 'S', 'G'],
            {(0, 1): e_vs_s, (0, 2): e_vs_g, (1, 2): s_vs_g}
        )
        
        # 计算权重
        weights, ci, cr = calculator.calculate_weights()
    
    with col2:
        st.markdown("### 🚦 一致性检验")
        
        # 状态灯
        is_consistent = cr < 0.1
        
        # [FIXED] 使用 html.escape 转义所有动态数值输出
        cr_str = html.escape(f"{cr:.4f}")
        
        if is_consistent:
            st.markdown(f"""
            <div style="background: #f6ffed; border: 1px solid #b7eb8f; padding: 16px; border-radius: 8px;">
                <span class="status-green"></span>
                <b style="color: #52c41a;">逻辑自洽</b><br>
                <span style="color: #666;">CR = {cr_str} < 0.1</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #fff2f0; border: 1px solid #ffccc7; padding: 16px; border-radius: 8px;">
                <span class="status-red"></span>
                <b style="color: #ff4d4f;">逻辑不一致</b><br>
                <span style="color: #666;">CR = {cr_str} ≥ 0.1</span>
            </div>
            """, unsafe_allow_html=True)
            
            # AI自动修正按钮
            if st.button("🔧 AI自动修正", key="auto_correct"):
                with st.spinner("正在优化矩阵..."):
                    corrected = calculator.auto_correct()
                    new_weights, new_ci, new_cr = calculator.calculate_weights()
                    st.success(f"✅ 修正完成! 新CR = {new_cr:.4f}")
                    weights = new_weights
                    cr = new_cr
        
        st.markdown("---")
        
        # 舆情联动
        st.markdown("### 📡 舆情风险监控")
        
        crawler = NewsCrawler()
        sentiment = crawler.get_sentiment_by_category()
        
        risk_detected = False
        for dim, score in sentiment.items():
            short_dim = dim[0]  # 取E/S/G
            
            # [FIXED] 转义所有动态内容
            dim_escaped = html.escape(dim)
            score_str = html.escape(f"{score:.2f}")
            
            if score < -0.5:
                risk_detected = True
                st.markdown(f"""
                <div style="background: #fff2f0; border-left: 4px solid #ff4d4f; padding: 12px; margin: 8px 0;">
                    ⚠️ <b>{dim_escaped}</b> 负面舆情预警<br>
                    <span style="color: #ff4d4f;">情感得分: {score_str}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                color = "#52c41a" if score > 0 else "#faad14"
                st.markdown(f"**{dim_escaped}**: <span style='color:{color}'>{score_str}</span>", unsafe_allow_html=True)
        
        if risk_detected:
            st.warning("⚡ 检测到负面舆情，建议开启动态权重调整")
            if st.checkbox("启用舆情权重联动"):
                # 转换格式
                sentiment_for_adjust = {k[0]: v for k, v in sentiment.items()}
                adjusted = calculator.adjust_for_risk(sentiment_for_adjust)
                st.info(f"权重已动态调整: {html.escape(str(adjusted))}")
    
    # === 下方：结果展示区 ===
    st.markdown("---")
    st.markdown("### 📊 权重计算结果")
    
    weights_dict = calculator.get_weights_dict()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        radar_fig = create_radar_chart(weights_dict)
        st.plotly_chart(radar_fig, use_container_width=True)
    
    with col_chart2:
        pie_fig = create_pie_chart(weights_dict)
        st.plotly_chart(pie_fig, use_container_width=True)
    
    # 权重数值展示
    st.markdown("#### 📋 权重明细")
    weight_df = pd.DataFrame([
        {"维度": k, "权重": f"{v:.4f}", "占比": f"{v*100:.1f}%"}
        for k, v in weights_dict.items()
    ])
    st.dataframe(weight_df, hide_index=True, use_container_width=True)
    
    # === 业务价值说明 ===
    st.markdown("---")
    st.info("""
    **📌 业务价值**
    - **AHP层次分析法**: 将主观的专家判断转化为客观的数学权重
    - **一致性检验**: 确保决策逻辑自洽，CR < 0.1 为通过标准
    - **AI专家评估**: 引入客观第三方视角，避免内部局限性
    - **舆情联动**: 实时监控负面新闻，动态调整风险权重
    """)