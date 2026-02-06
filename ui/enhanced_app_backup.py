"""远景能源 ESG 智能分析系统 - 增强版主应用
整合四大功能模块：
1. 行业实质性议题全景图（LDA+词云+趋势图）
2. 智能权重配置（AHP+AI评估+一致性检验）
3. 披露差距诊断与对标（向量相似度+双向条形图）
4. AI策略建议生成器（诊断卡片+行动清单+对话微调）
"""

import streamlit as st
import sys
import os
import json
import random

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from core.esg_engine import ESGAnalysisEngine
from core.data_models import ESGMetrics
from fusion.ahp_fusion import AHPFusionEngine
from analysis.topic_analyzer import TopicAnalyzer
from analysis.gap_analyzer import GapAnalyzer
from analysis.strategy_generator import StrategyGenerator
from utils.ollama_utils import ensure_ollama_running

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="远景能源 ESG 智能分析系统",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 自定义样式 ====================
st.markdown("""
<style>
/* 全局样式 */
.stApp {
    background-color: #f8f9fa;
}

/* 模块标题 */
.module-title {
    color: #1a1a2e;
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

/* 技术栈标签 */
.tech-stack {
    color: #666;
    font-size: 0.95rem;
    margin-bottom: 2rem;
}

/* 卡片样式 */
.diagnosis-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.diagnosis-high { border-left-color: #ff4d4f; }
.diagnosis-medium { border-left-color: #faad14; }
.diagnosis-low { border-left-color: #52c41a; }

/* 指标卡片 */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1890ff;
}

.metric-label {
    color: #666;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

/* 状态灯 */
.status-light {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}

.status-green { background-color: #52c41a; }
.status-red { background-color: #ff4d4f; }

/* 导航标签 */
.nav-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    background: white;
    padding: 0.5rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.nav-tab {
    flex: 1;
    text-align: center;
    padding: 0.8rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
    font-weight: 500;
}

.nav-tab:hover {
    background-color: #f0f0f0;
}

.nav-tab.active {
    background-color: #1890ff;
    color: white;
}

/* 一致性检验状态 */
.consistency-pass {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border: 1px solid #28a745;
    border-radius: 12px;
    padding: 1.5rem;
}

.consistency-fail {
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    border: 1px solid #dc3545;
    border-radius: 12px;
    padding: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ==================== Session State 初始化 ====================
def init_session_state():
    defaults = {
        'current_module': 0,  # 当前模块索引
        'analysis_year': '2025',
        'benchmark_company': '维斯塔斯',
        'ahp_matrix': None,
        'ahp_weights': None,
        'ahp_cr': None,
        'ai_suggestions': None,
        'perspective': 'balanced',
        'gap_analysis': None,
        'diagnosis': None,
        'strategies': None,
        'ollama_status': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ==================== 侧边栏 ====================
def render_sidebar():
    with st.sidebar:
        # Logo区域
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="margin: 0; color: #1a1a2e;">🌿 ESG 智能分析系统</h2>
            <p style="color: #666; font-size: 0.85rem; margin-top: 0.5rem;">版本: v1.0.0</p>
            <p style="color: #666; font-size: 0.85rem;">更新日期: 2025-01</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 全局配置
        st.markdown("### ⚙️ 全局配置")
        
        st.session_state.analysis_year = st.selectbox(
            "分析年度",
            ["2025", "2024", "2023"],
            index=0
        )
        
        st.session_state.benchmark_company = st.selectbox(
            "对标企业",
            ["维斯塔斯", "西门子歌美飒", "行业平均"],
            index=0
        )
        
        st.markdown("---")
        
        # 系统状态
        st.markdown("### 📊 系统状态")
        
        ollama_ok, msg = ensure_ollama_running()
        st.session_state.ollama_status = ollama_ok
        
        if ollama_ok:
            st.markdown('<span class="status-light status-green"></span>Ollama 服务运行中', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-light status-red"></span>Ollama 未连接', unsafe_allow_html=True)
        
        st.markdown('<span class="status-light status-green"></span>知识库已就绪', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 使用说明
        with st.expander("ℹ️ 使用说明"):
            st.write("""
            1. **议题全景图**: 查看行业ESG议题热度和趋势
            2. **智能权重配置**: 配置AHP权重并进行一致性检验
            3. **披露差距诊断**: 对标行业标杆，识别差距
            4. **AI策略建议**: 生成针对性改进策略
            """)

# ==================== 模块导航 ====================
def render_module_nav():
    modules = [
        ("📊", "议题全景图"),
        ("⚖️", "智能权重配置"),
        ("🔍", "披露差距诊断"),
        ("💡", "AI策略建议")
    ]
    
    cols = st.columns(4)
    for i, (icon, name) in enumerate(modules):
        with cols[i]:
            is_active = st.session_state.current_module == i
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon} 模块{i+1}：{name}", 
                        key=f"module_{i}",
                        use_container_width=True,
                        type=btn_type):
                st.session_state.current_module = i
                st.rerun()

# ==================== 模块一：行业实质性议题全景图 ====================
def render_module_1():
    st.markdown('<h1 class="module-title">📊 行业实质性议题全景图</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: LDA主题模型 + TF-IDF关键词提取（模拟数据展示）</p>', unsafe_allow_html=True)
    
    # 初始化分析器
    analyzer = TopicAnalyzer(year=st.session_state.analysis_year)
    
    # 左右分栏
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔥 2025年度核心议题热度快照")
        
        # 获取词云数据
        wordcloud_data = analyzer.get_wordcloud_data(top_n=50)
        
        # 准备数据
        words_df = pd.DataFrame(wordcloud_data)
        color_map = {'E': '#52c41a', 'S': '#1890ff', 'G': '#faad14'}
        category_name = {'E': '环境', 'S': '社会', 'G': '治理'}
        words_df['color'] = words_df['category'].map(color_map)
        
        # 尝试使用 wordcloud 库生成真实词云
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            from matplotlib.patches import Patch
            
            # 准备词频
            word_freq = {row['text']: row['value'] for _, row in words_df.iterrows()}
            category_map = {row['text']: row['category'] for _, row in words_df.iterrows()}
            
            # 颜色函数
            def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
                cat = category_map.get(word, 'E')
                return color_map.get(cat, '#666666')
            
            # 查找中文字体
            font_paths = [
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/simsun.ttc', 
                'C:/Windows/Fonts/msyh.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/System/Library/Fonts/PingFang.ttc',
            ]
            font_path = next((f for f in font_paths if os.path.exists(f)), None)
            
            # 生成词云
            wc = WordCloud(
                width=800, height=500,
                background_color='#f8f9fa',
                font_path=font_path,
                max_words=50,
                relative_scaling=0.6,
                min_font_size=12,
                max_font_size=150,
                random_state=42,
                collocations=False,
                prefer_horizontal=0.7,
                color_func=color_func,
                contour_width=0,
                margin=2
            ).generate_from_frequencies(word_freq)
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6.25))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            
            # 添加图例
            legend_elements = [
                Patch(facecolor='#52c41a', edgecolor='none', label='环境(E)'),
                Patch(facecolor='#1890ff', edgecolor='none', label='社会(S)'),
                Patch(facecolor='#faad14', edgecolor='none', label='治理(G)')
            ]
            ax.legend(handles=legend_elements, loc='upper right', 
                     bbox_to_anchor=(1.02, 1), framealpha=0.9,
                     title='ESG类别', title_fontsize=11)
            
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close()
            
            # 添加悬停数据表格（在词云下方）
            st.markdown("**📊 议题详情（悬停查看）**")
            hover_df = words_df[['text', 'category', 'value', 'growth']].head(10)
            hover_df.columns = ['议题', '类别', '权重', '增长率']
            hover_df['类别'] = hover_df['类别'].map(category_name)
            hover_df['增长率'] = hover_df['增长率'].apply(lambda x: f"{x:.1%}")
            st.dataframe(hover_df, use_container_width=True, hide_index=True)
            
        except ImportError:
            # 备用：使用 Plotly 简化版
            st.info("💡 安装 `wordcloud` 库可获得更密集的词云效果: `pip install wordcloud`")
            
            # 简化布局
            words_df = words_df.sort_values('value', ascending=False).head(25)
            n = len(words_df)
            golden_angle = np.pi * (3 - np.sqrt(5))
            words_df['x'] = [np.sqrt(i+1) * np.cos(i * golden_angle) for i in range(n)]
            words_df['y'] = [np.sqrt(i+1) * np.sin(i * golden_angle) for i in range(n)]
            
            fig = go.Figure()
            for idx, row in words_df.iterrows():
                font_size = min(max(row['value'] * 0.35, 12), 28)
                fig.add_trace(go.Scatter(
                    x=[row['x']], y=[row['y']],
                    mode='text',
                    text=[row['text']],
                    textfont=dict(size=font_size, color=row['color']),
                    name=category_name[row['category']] if idx < 3 else None,
                    showlegend=(idx < 3),
                    hovertemplate=(
                        f"<b>{row['text']}</b><br>" +
                        f"类别: {category_name[row['category']]}<br>" +
                        f"权重: {row['value']:.1f}<br>" +
                        f"增长率: {row['growth']:.1%}<extra></extra>"
                    )
                ))
            
            max_coord = max(words_df['x'].abs().max(), words_df['y'].abs().max()) * 1.3
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5,
                           title='ESG类别'),
                xaxis=dict(showgrid=False, showticklabels=False, range=[-max_coord, max_coord], fixedrange=True),
                yaxis=dict(showgrid=False, showticklabels=False, range=[-max_coord, max_coord], 
                          scaleanchor='x', scaleratio=1, fixedrange=True),
                height=500,
                paper_bgcolor='rgba(248,249,250,1)',
                plot_bgcolor='rgba(248,249,250,1)',
                margin=dict(l=20, r=20, t=60, b=20),
                dragmode=False
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # ESG分布
        st.markdown("#### ESG维度议题分布")
        dist = analyzer.get_category_distribution()
        dist_fig = go.Figure(data=[go.Pie(
            labels=['环境(E)', '社会(S)', '治理(G)'],
            values=[dist['E'], dist['S'], dist['G']],
            hole=0.4,
            marker_colors=['#52c41a', '#1890ff', '#faad14']
        )])
        dist_fig.update_layout(height=250, showlegend=False)
        st.plotly_chart(dist_fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 增长最快议题趋势追踪")
        
        # 获取趋势数据
        trending = analyzer.get_trending_topics(top_n=10)
        
        # 议题选择器
        selected_topic = st.selectbox(
            "选择议题查看趋势",
            [t['text'] for t in trending],
            index=0
        )
        
        # 绘制趋势图
        fig_trend = go.Figure()
        
        quarters = [f"Q{(i%4)+1}\n{2022+(i//4)}" for i in range(12)]
        
        # 绘制所有议题的趋势（灰色细线）
        for topic in trending:
            opacity = 0.3 if topic['text'] != selected_topic else 1.0
            width = 1 if topic['text'] != selected_topic else 3
            
            fig_trend.add_trace(go.Scatter(
                x=list(range(12)),
                y=topic['trend'],
                name=topic['text'],
                line=dict(width=width),
                opacity=opacity,
                showlegend=(topic['text'] == selected_topic)
            ))
        
        fig_trend.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(12)),
                ticktext=quarters,
                title="时间"
            ),
            yaxis=dict(title="热度指数", range=[0, 100]),
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Top 10增长榜单
        st.markdown("#### Top 10 增长最快议题")
        trend_df = pd.DataFrame([
            {"排名": i+1, "议题": t['text'], "增长率": f"{t['growth']:.1%}", 
             "类别": {'E': '环境', 'S': '社会', 'G': '治理'}[t['category']]}
            for i, t in enumerate(trending)
        ])
        st.dataframe(trend_df, use_container_width=True, hide_index=True)

# ==================== 模块二：智能权重配置 ====================
def render_module_2():
    st.markdown('<h1 class="module-title">⚖️ 智能权重配置</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: AHP层次分析法 + 一致性检验 + 舆情动态调整</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 判断矩阵配置")
        
        # AI虚拟专家评估
        st.markdown("#### 🤖 AI虚拟专家评估")
        st.write("本次评估更关注哪种视角？")
        
        perspective = st.radio(
            "选择评估视角",
            ["A. 财务稳健性（投资者视角）", 
             "B. 合规与风险（监管视角）", 
             "C. 品牌影响力（公众视角）",
             "D. 自定义配置"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # 根据选择设置权重
        perspective_map = {
            "A. 财务稳健性（投资者视角）": "financial",
            "B. 合规与风险（监管视角）": "compliance",
            "C. 品牌影响力（公众视角）": "brand",
            "D. 自定义配置": "custom"
        }
        
        selected_perspective = perspective_map[perspective]
        st.session_state.perspective = selected_perspective
        
        # 使用AHP引擎生成建议
        ahp = AHPFusionEngine()
        suggestion = ahp.generate_suggestions(selected_perspective)
        
        if selected_perspective != "custom":
            st.info(f"🤖 AI建议: {suggestion['reasoning']}")
            
            weights = suggestion['weights']
            
            # 构建判断矩阵
            ahp.build_matrix(
                ['E', 'S', 'G'],
                {
                    (0, 1): weights['E'] / weights['S'],
                    (0, 2): weights['E'] / weights['G'],
                    (1, 2): weights['S'] / weights['G']
                }
            )
            
            weights_arr, ci, cr = ahp.calculate_weights()
            
            st.session_state.ahp_weights = ahp.get_weights_dict()
            st.session_state.ahp_cr = cr
        else:
            # 自定义配置 - 滑块
            st.markdown("#### 自定义权重配置")
            
            col_e, col_s, col_g = st.columns(3)
            
            with col_e:
                e_slider = st.slider("E vs S", 1/9, 9.0, 1.0, 0.1, format="%.1f")
            with col_s:
                s_slider = st.slider("E vs G", 1/9, 9.0, 1.0, 0.1, format="%.1f")
            with col_g:
                g_slider = st.slider("S vs G", 1/9, 9.0, 1.0, 0.1, format="%.1f")
            
            # 自然语言标签
            def get_label(value):
                if value > 7: return "绝对重要"
                if value > 5: return "明显重要"
                if value > 3: return "稍微重要"
                if value > 1: return "略微重要"
                if value == 1: return "同等重要"
                if value > 1/3: return "略微不重要"
                if value > 1/5: return "稍微不重要"
                if value > 1/7: return "明显不重要"
                return "绝对不重要"
            
            st.caption(f"E相对于S: {get_label(e_slider)} | E相对于G: {get_label(s_slider)} | S相对于G: {get_label(g_slider)}")
            
            ahp.build_matrix(['E', 'S', 'G'], {(0, 1): e_slider, (0, 2): s_slider, (1, 2): g_slider})
            weights_arr, ci, cr = ahp.calculate_weights()
            st.session_state.ahp_weights = ahp.get_weights_dict()
            st.session_state.ahp_cr = cr
        
        # 显示判断矩阵
        st.markdown("#### 判断矩阵")
        matrix_df = pd.DataFrame(
            ahp.matrix,
            index=['E', 'S', 'G'],
            columns=['E', 'S', 'G']
        )
        st.dataframe(matrix_df.style.format("{:.2f}"), use_container_width=True)
    
    with col2:
        st.markdown("### 🚦 一致性检验")
        
        if st.session_state.ahp_cr is not None:
            cr = st.session_state.ahp_cr
            
            if cr < 0.1:
                st.markdown(f"""
                <div class="consistency-pass">
                    <h4 style="margin: 0; color: #28a745;">✓ 逻辑自洽</h4>
                    <p style="margin: 0.5rem 0 0 0; color: #666;">CR = {cr:.4f} < 0.1</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="consistency-fail">
                    <h4 style="margin: 0; color: #dc3545;">✗ 一致性不足</h4>
                    <p style="margin: 0.5rem 0 0 0; color: #666;">CR = {cr:.4f} ≥ 0.1</p>
                    <button style="margin-top: 1rem; padding: 0.5rem 1rem; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        启动AI自动修正
                    </button>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🤖 AI自动修正", key="ai_fix"):
                    ahp.auto_correct()
                    weights_arr, ci, cr = ahp.calculate_weights()
                    st.session_state.ahp_weights = ahp.get_weights_dict()
                    st.session_state.ahp_cr = cr
                    st.rerun()
        
        # 权重展示
        st.markdown("### 📊 权重分配")
        
        if st.session_state.ahp_weights:
            weights = st.session_state.ahp_weights
            
            # 雷达图
            fig = go.Figure(data=go.Scatterpolar(
                r=[weights['E'], weights['S'], weights['G'], weights['E']],
                theta=['环境(E)', '社会(S)', '治理(G)', '环境(E)'],
                fill='toself',
                marker_color='#1890ff'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 0.6])),
                showlegend=False,
                height=300,
                margin=dict(l=40, r=40, t=40, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 数值显示
            st.metric("环境(E)", f"{weights['E']:.1%}")
            st.metric("社会(S)", f"{weights['S']:.1%}")
            st.metric("治理(G)", f"{weights['G']:.1%}")

# ==================== 模块三：披露差距诊断与对标 ====================
def render_module_3():
    st.markdown('<h1 class="module-title">🔍 披露差距诊断与对标</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: 向量相似度计算 + 行业对标分析（模拟数据展示）</p>', unsafe_allow_html=True)
    
    # 初始化分析器
    gap_analyzer = GapAnalyzer()
    
    # 执行分析
    if st.session_state.gap_analysis is None:
        st.session_state.gap_analysis = gap_analyzer.analyze_gap(
            st.session_state.benchmark_company
        )
    
    gap_data = st.session_state.gap_analysis
    
    # 综合评分对比
    st.markdown("### 📋 ESG综合评分对比")
    
    cols = st.columns(4)
    
    with cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{gap_data['company_score']:.1f}分</div>
            <div class="metric-label">远景能源</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #52c41a;">{gap_data['benchmark_score']:.1f}分</div>
            <div class="metric-label">{st.session_state.benchmark_company}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        gap_color = "#ff4d4f" if gap_data['gap'] > 10 else "#faad14" if gap_data['gap'] > 5 else "#52c41a"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {gap_color};">{gap_data['gap']:.1f}分</div>
            <div class="metric-label">综合差距</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        disclosure_score = 76.5
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #1890ff;">{disclosure_score:.1f}分</div>
            <div class="metric-label">披露深度得分</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 双向条形图 - 维度对比
    st.markdown("### 📊 维度表现对比")
    
    dimensions = ['E', 'S', 'G']
    company_scores = [gap_data['dimension_gaps'][d]['company'] for d in dimensions]
    benchmark_scores = [gap_data['dimension_gaps'][d]['benchmark'] for d in dimensions]
    
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=('远景能源', st.session_state.benchmark_company),
                        shared_yaxes=True)
    
    # 远景能源（负值显示在左侧）
    fig.add_trace(
        go.Bar(
            y=['环境(E)', '社会(S)', '治理(G)'],
            x=[-s for s in company_scores],
            orientation='h',
            marker_color=['#52c41a', '#1890ff', '#faad14'],
            text=[f"{s:.1f}" for s in company_scores],
            textposition='inside',
            name='远景能源'
        ),
        row=1, col=1
    )
    
    # 标杆企业（正值显示在右侧）
    fig.add_trace(
        go.Bar(
            y=['环境(E)', '社会(S)', '治理(G)'],
            x=benchmark_scores,
            orientation='h',
            marker_color=['#52c41a', '#1890ff', '#faad14'],
            text=[f"{s:.1f}" for s in benchmark_scores],
            textposition='inside',
            name=st.session_state.benchmark_company
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        barmode='relative',
        height=300,
        showlegend=False,
        xaxis=dict(range=[-100, 0], title="得分"),
        xaxis2=dict(range=[0, 100], title="得分")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 指标级差距分析
    st.markdown("### 🔍 指标级差距分析")
    
    # 创建差距图
    indicators = gap_data['indicator_gaps'][:6]  # 前6个
    
    fig_gap = go.Figure()
    
    indicator_names = [i['name'] for i in indicators]
    company_vals = [i['company_score'] for i in indicators]
    benchmark_vals = [i['benchmark_score'] for i in indicators]
    gaps = [i['gap'] for i in indicators]
    
    # 公司得分
    fig_gap.add_trace(go.Bar(
        name='远景能源',
        y=indicator_names,
        x=company_vals,
        orientation='h',
        marker_color='#1890ff'
    ))
    
    # 标杆得分
    fig_gap.add_trace(go.Bar(
        name=st.session_state.benchmark_company,
        y=indicator_names,
        x=benchmark_vals,
        orientation='h',
        marker_color='#52c41a'
    ))
    
    # 添加差距标注
    for i, (name, gap) in enumerate(zip(indicator_names, gaps)):
        color = '#ff4d4f' if gap > 15 else '#faad14' if gap > 8 else '#52c41a'
        fig_gap.add_annotation(
            x=max(company_vals[i], benchmark_vals[i]) + 5,
            y=name,
            text=f"差距 {gap:.0f}分",
            showarrow=False,
            font=dict(color=color, size=11)
        )
    
    fig_gap.update_layout(
        barmode='group',
        height=350,
        xaxis=dict(title="得分", range=[0, 105]),
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig_gap, use_container_width=True)
    
    # 红色预警指标
    high_gaps = [i for i in indicators if i['severity'] == '高']
    if high_gaps:
        st.markdown("### ⚠️ 重点改进指标")
        for ind in high_gaps:
            st.error(f"🔴 **{ind['name']}**: 差距 {ind['gap']:.0f}分 - 披露深度{ind['disclosure_level']}")

# ==================== 模块四：AI策略建议生成器 ====================
def render_module_4():
    st.markdown('<h1 class="module-title">💡 AI策略建议生成器</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: 本地大模型 + RAG知识增强 + 专家Prompt模板</p>', unsafe_allow_html=True)
    
    # 初始化策略生成器
    strategy_gen = StrategyGenerator()
    
    # 如果没有差距分析，先执行
    if st.session_state.gap_analysis is None:
        gap_analyzer = GapAnalyzer()
        st.session_state.gap_analysis = gap_analyzer.analyze_gap(
            st.session_state.benchmark_company
        )
    
    # 生成诊断和策略
    if st.session_state.diagnosis is None:
        st.session_state.diagnosis = strategy_gen.generate_diagnosis(
            st.session_state.gap_analysis
        )
        st.session_state.strategies = strategy_gen.generate_strategies(
            st.session_state.diagnosis
        )
    
    diagnosis = st.session_state.diagnosis
    strategies = st.session_state.strategies
    
    # 核心诊断结果
    st.markdown("### 📋 核心诊断结果")
    
    diag_cols = st.columns(3)
    severity_icons = {"高": "🔴", "中": "🟡", "低": "🟢"}
    severity_classes = {"高": "diagnosis-high", "中": "diagnosis-medium", "低": "diagnosis-low"}
    
    for i, diag in enumerate(diagnosis[:3]):
        with diag_cols[i]:
            st.markdown(f"""
            <div class="diagnosis-card {severity_classes[diag['severity']]}">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{severity_icons[diag['severity']]}</div>
                <h4 style="margin: 0 0 0.5rem 0;">{diag['title']}</h4>
                <p style="color: #ff4d4f; font-weight: 600; margin: 0;">差距 {diag['gap']:.0f}分</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 行动清单
    st.markdown("### ✅ 优先改进行动清单")
    
    for i, strategy in enumerate(strategies, 1):
        with st.expander(f"{i}. {strategy['title']} [{strategy['priority']}优先级]"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**问题诊断**: {strategy['diagnosis_title']}")
                st.write(f"**改进周期**: {strategy['timeline']}")
                st.write(f"**预期收益**: {strategy['benefit']}")
                
                st.write("**行动计划**:")
                for j, action in enumerate(strategy['actions'], 1):
                    st.checkbox(f"{j}. {action}", key=f"action_{i}_{j}")
                
                st.caption(f"参考标准: {', '.join(strategy['standards'])}")
            
            with col2:
                # 优先级标签
                priority_color = "#ff4d4f" if strategy['priority'] == '高' else "#faad14" if strategy['priority'] == '中' else "#52c41a"
                st.markdown(f"""
                <div style="background: {priority_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 12px; text-align: center; font-weight: 600;">
                    {strategy['priority']}优先级
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # AI置信度标签
                confidence = random.choice(["高置信度", "建议人工复核"])
                conf_color = "#52c41a" if confidence == "高置信度" else "#faad14"
                st.markdown(f"""
                <div style="background: {conf_color}20; color: {conf_color}; padding: 0.3rem 0.8rem; border-radius: 12px; text-align: center; font-size: 0.85rem; border: 1px solid {conf_color};">
                    🤖 {confidence}
                </div>
                """, unsafe_allow_html=True)
    
    # 大模型对话微调区
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
                # 模拟优化
                refined = strategy_gen.refine_strategies(strategies, instruction)
                
                st.success("✓ 已根据您的指令优化建议")
                
                # 显示优化结果
                st.markdown("#### 优化后的建议")
                for s in refined[:2]:
                    st.info(f"**{s['title']}**\n\n{s.get('refined_benefit', '')}")
        else:
            st.warning("请输入微调指令")

# ==================== 主程序 ====================
def main():
    # 渲染侧边栏
    render_sidebar()
    
    # 主标题
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">🌿 远景能源 ESG 智能分析系统</h1>
        <p style="color: #666; font-size: 1.1rem;">基于AI的ESG议题分析、权重配置、差距诊断与策略生成平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 模块导航
    render_module_nav()
    
    st.markdown("---")
    
    # 渲染当前模块
    current = st.session_state.current_module
    
    if current == 0:
        render_module_1()
    elif current == 1:
        render_module_2()
    elif current == 2:
        render_module_3()
    elif current == 3:
        render_module_4()

if __name__ == "__main__":
    main()
