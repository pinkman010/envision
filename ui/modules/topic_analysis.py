"""模块一：行业实质性议题全景图

功能：LDA主题模型 + TF-IDF关键词提取 + 词云展示
"""

import os
from typing import Optional

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from analysis.topic_analyzer import TopicAnalyzer
from ui.styles import ESG_COLORS, ESG_DIMENSION_NAMES
from ui.state import AppState


def render():
    """渲染议题全景图模块"""
    st.markdown('<h1 class="module-title">📊 行业实质性议题全景图</h1>', unsafe_allow_html=True)
    st.markdown('<p class="tech-stack">技术栈: LDA主题模型 + TF-IDF关键词提取</p>', unsafe_allow_html=True)
    
    # 初始化分析器
    analyzer = TopicAnalyzer(year=AppState.get('analysis_year', '2025'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_wordcloud_section(analyzer)
        render_distribution_section(analyzer)
    
    with col2:
        render_trend_section(analyzer)


def render_wordcloud_section(analyzer: TopicAnalyzer):
    """渲染词云部分"""
    st.markdown("### 🔥 核心议题热度快照")
    
    wordcloud_data = analyzer.get_wordcloud_data(top_n=50)
    
    if not wordcloud_data:
        st.warning("暂无议题数据")
        return
    
    words_df = pd.DataFrame(wordcloud_data)
    words_df['color'] = words_df['category'].map(ESG_COLORS)
    
    if HAS_WORDCLOUD:
        render_matplotlib_wordcloud(words_df)
    else:
        render_plotly_wordcloud(words_df)


def render_matplotlib_wordcloud(words_df: pd.DataFrame):
    """使用matplotlib生成真实词云"""
    word_freq = {row['text']: row['value'] for _, row in words_df.iterrows()}
    category_map = {row['text']: row['category'] for _, row in words_df.iterrows()}
    
    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        cat = category_map.get(word, 'E')
        return ESG_COLORS.get(cat, '#666666')
    
    # 查找中文字体
    font_paths = [
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
        'C:/Windows/Fonts/msyh.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/System/Library/Fonts/PingFang.ttc',
    ]
    font_path = next((f for f in font_paths if os.path.exists(f)), None)
    
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
    
    fig, ax = plt.subplots(figsize=(10, 6.25))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    
    legend_elements = [
        Patch(facecolor=ESG_COLORS['E'], edgecolor='none', label='环境(E)'),
        Patch(facecolor=ESG_COLORS['S'], edgecolor='none', label='社会(S)'),
        Patch(facecolor=ESG_COLORS['G'], edgecolor='none', label='治理(G)')
    ]
    ax.legend(handles=legend_elements, loc='upper right',
             bbox_to_anchor=(1.02, 1), framealpha=0.9,
             title='ESG类别', title_fontsize=11)
    
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()
    
    # 详情表格
    st.markdown("**📊 议题详情**")
    hover_df = words_df[['text', 'category', 'value', 'growth']].head(10)
    hover_df.columns = ['议题', '类别', '权重', '增长率']
    hover_df['类别'] = hover_df['类别'].map(ESG_DIMENSION_NAMES)
    hover_df['增长率'] = hover_df['增长率'].apply(lambda x: f"{x:.1%}")
    st.dataframe(hover_df, use_container_width=True, hide_index=True)


def render_plotly_wordcloud(words_df: pd.DataFrame):
    """使用Plotly生成简化词云"""
    st.info("💡 安装 `wordcloud` 库可获得更密集的词云效果: `pip install wordcloud`")
    
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
            name=ESG_DIMENSION_NAMES[row['category']] if idx < 3 else None,
            showlegend=(idx < 3),
            hovertemplate=(
                f"<b>{row['text']}</b><br>" +
                f"类别: {ESG_DIMENSION_NAMES[row['category']]}<br>" +
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


def render_distribution_section(analyzer: TopicAnalyzer):
    """渲染ESG分布"""
    st.markdown("#### ESG维度议题分布")
    dist = analyzer.get_category_distribution()
    
    # 创建环形图，增加尺寸和交互性
    fig = go.Figure(data=[go.Pie(
        labels=['环境(E)', '社会(S)', '治理(G)'],
        values=[dist['E'], dist['S'], dist['G']],
        hole=0.5,
        marker_colors=[ESG_COLORS['E'], ESG_COLORS['S'], ESG_COLORS['G']],
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(size=14),
        hovertemplate='<b>%{label}</b><br>占比: %{percent}<extra></extra>',
        pull=[0.02, 0.02, 0.02],  # 轻微分离效果
        insidetextorientation='radial'
    )])
    
    fig.update_layout(
        height=400,
        showlegend=False,  # 隐藏图例，因为标签已显示完整信息
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)


def render_trend_section(analyzer: TopicAnalyzer):
    """渲染趋势部分"""
    st.markdown("### 📈 增长最快议题趋势追踪")
    
    trending = analyzer.get_trending_topics(top_n=10)
    
    if not trending:
        st.warning("暂无趋势数据")
        return
    
    # 议题选择器
    selected_topic = st.selectbox(
        "选择议题查看趋势",
        [t['text'] for t in trending],
        index=0
    )
    
    # 趋势图
    fig_trend = go.Figure()
    quarters = [f"Q{(i%4)+1}\n{2022+(i//4)}" for i in range(12)]
    
    for topic in trending:
        is_selected = topic['text'] == selected_topic
        opacity = 1.0 if is_selected else 0.3
        width = 3 if is_selected else 1
        
        fig_trend.add_trace(go.Scatter(
            x=list(range(12)),
            y=topic['trend'],
            name=topic['text'],
            line=dict(width=width),
            opacity=opacity,
            showlegend=is_selected
        ))
    
    fig_trend.update_layout(
        xaxis=dict(tickmode='array', tickvals=list(range(12)), ticktext=quarters, title="时间"),
        yaxis=dict(title="热度指数", range=[0, 100]),
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Top 10增长榜单
    st.markdown("#### Top 10 增长最快议题")
    trend_df = pd.DataFrame([
        {"排名": i+1, "议题": t['text'], "增长率": f"{t['growth']:.1%}",
         "类别": ESG_DIMENSION_NAMES[t['category']]}
        for i, t in enumerate(trending)
    ])
    st.dataframe(trend_df, use_container_width=True, hide_index=True)
