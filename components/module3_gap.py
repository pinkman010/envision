# -*- coding: utf-8 -*-
"""
模块三：披露差距诊断与对标
功能：双向条形图 + 差距分析 + 预警标记
"""
import streamlit as st
import html  # [ADDED] 防止XSS攻击
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_modules.gap_analyzer import GapAnalyzer


def create_gap_bar_chart(gap_data):
    """创建双向条形图"""
    indicator_gaps = gap_data.get('indicator_gaps', {})
    
    # 检查是否有数据
    if not indicator_gaps:
        # 返回空图
        fig = go.Figure()
        fig.update_layout(
            title="暂无对标数据",
            height=400,
            annotations=[{
                'text': '暂无指标数据<br>请先提取ESG报告',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'font': {'size': 20, 'color': 'gray'}
            }]
        )
        return fig
    
    indicators = list(indicator_gaps.keys())
    yuanjing_scores = [indicator_gaps[ind]['yuanjing'] for ind in indicators]
    benchmark_scores = [indicator_gaps[ind]['benchmark'] for ind in indicators]
    gaps = [indicator_gaps[ind]['gap'] for ind in indicators]
    
    fig = go.Figure()
    
    # 远景能源（左侧，负值）
    fig.add_trace(go.Bar(
        y=indicators,
        x=[-s for s in yuanjing_scores],
        orientation='h',
        name='远景能源',
        marker_color='#1890ff',
        text=[f'{s}' for s in yuanjing_scores],
        textposition='inside',
        insidetextanchor='end'
    ))
    
    # 标杆企业（右侧，正值）
    fig.add_trace(go.Bar(
        y=indicators,
        x=benchmark_scores,
        orientation='h',
        name=gap_data['benchmark_company'],
        marker_color='#52c41a',
        text=[f'{s}' for s in benchmark_scores],
        textposition='inside',
        insidetextanchor='start'
    ))
    
    fig.update_layout(
        title=f"远景能源 vs {gap_data['benchmark_company']} 对标分析",
        barmode='overlay',
        xaxis=dict(
            title='得分',
            range=[-100, 100],
            tickvals=[-100, -75, -50, -25, 0, 25, 50, 75, 100],
            ticktext=['100', '75', '50', '25', '0', '25', '50', '75', '100']
        ),
        yaxis=dict(title=''),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        height=600,
        template='plotly_white'
    )
    
    return fig


def create_radar_comparison(radar_data, benchmark_name):
    """创建对比雷达图"""
    categories = radar_data.get('categories', [])
    
    # 检查是否有数据
    if not categories:
        fig = go.Figure()
        fig.update_layout(
            title="暂无雷达数据",
            height=400,
            annotations=[{
                'text': '暂无维度数据<br>请先提取ESG报告',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'font': {'size': 20, 'color': 'gray'}
            }]
        )
        return fig
    
    categories_closed = categories + [categories[0]]
    
    yuanjing_closed = radar_data['yuanjing'] + [radar_data['yuanjing'][0]]
    benchmark_closed = radar_data['benchmark'] + [radar_data['benchmark'][0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=yuanjing_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(24, 144, 255, 0.3)',
        line=dict(color='#1890ff', width=2),
        name='远景能源'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=benchmark_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(82, 196, 26, 0.3)',
        line=dict(color='#52c41a', width=2),
        name=benchmark_name
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="ESG维度对比",
        height=400,
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.1,
            xanchor='center',
            x=0.5
        )
    )
    
    return fig


def render_gap_analysis():
    """渲染模块三界面"""
    st.markdown("## 🔍 披露差距诊断与对标")
    st.markdown("**技术栈**: 向量相似度计算 + 行业对标分析（模拟数据展示）")
    st.markdown("---")
    
    # 初始化分析器
    use_real = st.session_state.get('use_real_data', False)
    analyzer = GapAnalyzer(use_real_data=use_real)
    
    # 获取对标企业
    benchmark_name = st.session_state.get('benchmark_company', '维斯塔斯')
    
    # 进行差距分析
    gap_data = analyzer.calculate_gap(benchmark_name)
    
    # === 顶部评分卡 ===
    st.markdown("### 📋 ESG综合评分对比")
    
    score_col1, score_col2, score_col3, score_col4 = st.columns(4)
    
    with score_col1:
        st.metric(
            "远景能源",
            f"{gap_data['yuanjing_score']}分",
            delta=None
        )
    
    with score_col2:
        st.metric(
            benchmark_name,
            f"{gap_data['benchmark_score']}分",
            delta=None
        )
    
    with score_col3:
        gap_value = gap_data['overall_gap']
        delta_color = "inverse" if gap_value > 0 else "normal"
        st.metric(
            "综合差距",
            f"{abs(gap_value):.1f}分",
            delta=f"{'落后' if gap_value > 0 else '领先'}{abs(gap_value):.1f}分",
            delta_color=delta_color
        )
    
    with score_col4:
        # 披露深度
        depth = analyzer.get_disclosure_depth_score()
        st.metric("披露深度得分", f"{depth['总体披露']}分")
    
    st.markdown("---")
    
    # === 主内容区 ===
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📊 指标对标分析")
        
        # 双向条形图
        gap_chart = create_gap_bar_chart(gap_data)
        st.plotly_chart(gap_chart, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 维度雷达对比")
        
        radar_data = analyzer.generate_radar_data(benchmark_name)
        radar_chart = create_radar_comparison(radar_data, benchmark_name)
        st.plotly_chart(radar_chart, use_container_width=True)
        
        # 披露深度分解
        st.markdown("#### 📈 披露深度分解")
        depth_df = pd.DataFrame([
            {"维度": k, "得分": v, "状态": "✅" if v >= 80 else "⚠️" if v >= 60 else "❌"}
            for k, v in depth.items() if k != '总体披露'
        ])
        st.dataframe(depth_df, hide_index=True, use_container_width=True)
    
    # === 短板与优势分析 ===
    st.markdown("---")
    st.markdown("### ⚠️ 差距诊断结果")
    
    diag_col1, diag_col2 = st.columns(2)
    
    with diag_col1:
        st.markdown("#### 🔴 主要短板（需重点关注）")
        
        weaknesses = gap_data.get('weaknesses', [])
        if not weaknesses:
            st.info("暂无短板数据")
        
        for ind, gap in weaknesses:
            severity = "🔴 高风险" if gap > 20 else "🟡 中风险"
            # [FIXED] 转义指标名称和数值，防止HTML注入
            ind_escaped = html.escape(str(ind))
            gap_str = html.escape(f"{gap:.0f}")
            
            st.markdown(f"""
            <div style="background: #fff2f0; border-left: 4px solid #ff4d4f; padding: 12px; margin: 8px 0; border-radius: 4px;">
                <b>{ind_escaped}</b> <span style="color: #ff4d4f;">差距 {gap_str}分</span> {severity}
                <br><span style="color: #666; font-size: 12px;">披露深度不足，建议加强相关信息披露</span>
            </div>
            """, unsafe_allow_html=True)
    
    with diag_col2:
        st.markdown("#### 🟢 相对优势")
        
        if gap_data['strengths']:
            for ind, lead in gap_data['strengths']:
                # [FIXED] 转义指标名称和数值
                ind_escaped = html.escape(str(ind))
                lead_str = html.escape(f"{lead:.0f}")
                
                st.markdown(f"""
                <div style="background: #f6ffed; border-left: 4px solid #52c41a; padding: 12px; margin: 8px 0; border-radius: 4px;">
                    <b>{ind_escaped}</b> <span style="color: #52c41a;">领先 {lead_str}分</span>
                    <br><span style="color: #666; font-size: 12px;">表现优于行业标杆，继续保持</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无明显领先指标")
    
    # === 优先行动建议 ===
    st.markdown("---")
    st.markdown("### 🎯 优先改进行动")
    
    priority_actions = gap_data.get('priority_actions', [])
    if not priority_actions:
        st.info("暂无优先行动建议")
    
    for i, action in enumerate(priority_actions, 1):
        urgency_color = "#ff4d4f" if action['urgency'] == '高' else "#faad14"
        # [FIXED] 转义所有动态内容
        indicator_escaped = html.escape(str(action['indicator']))
        gap_str = html.escape(f"{action['gap']:.0f}")
        urgency_escaped = html.escape(str(action['urgency']))
        
        st.markdown(f"""
        <div style="background: white; padding: 16px; margin: 8px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <span style="background: {urgency_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                {urgency_escaped}优先级
            </span>
            <h4 style="margin: 8px 0;">{i}. {indicator_escaped}</h4>
            <p style="color: #666;">当前差距: <b style="color: #ff4d4f;">{gap_str}分</b>،建议在下一报告周期重点提升</p>
        </div>
        """, unsafe_allow_html=True)
    
    # === 详细数据表 ===
    with st.expander("📋 查看完整对标数据", expanded=False):
        detail_data = []
        for ind, data in gap_data['indicator_gaps'].items():
            detail_data.append({
                "指标": ind,
                "远景能源": data['yuanjing'],
                benchmark_name: data['benchmark'],
                "差距": data['gap'],
                "差距比例": f"{data['gap_pct']:.1f}%",
                "状态": "⚠️ 需改进" if data['gap'] > 10 else "✅ 正常"
            })
        
        detail_df = pd.DataFrame(detail_data)
        st.dataframe(detail_df, hide_index=True, use_container_width=True)
    
    # === 业务价值说明 ===
    st.markdown("---")
    st.info("""
    **📌 业务价值**
    - **精准定位短板**: 快速识别与行业标杆的差距，聚焦改进重点
    - **数据驱动决策**: 基于定量分析而非主观判断
    - **行业对标**: 了解竞争格局，把握ESG披露趋势
    - **优先级排序**: 资源有限情况下，优先改进影响最大的指标
    """)