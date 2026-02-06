# -*- coding: utf-8 -*-
"""
模块一：行业实质性议题全景图
功能：词云图 + 趋势折线图
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from io import BytesIO
import base64
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_modules.topic_analyzer import TopicAnalyzer


def generate_wordcloud_image(topics_data):
    """生成词云图并返回base64编码"""
    try:
        # 调试信息
        print(f"词云生成 - 输入数据类型: {type(topics_data)}")
        print(f"词云生成 - 输入数据长度: {len(topics_data) if topics_data else 0}")
        
        # 检查是否有数据
        if not topics_data or len(topics_data) == 0:
            print("词云生成 - 无数据，返回占位图")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, '暂无数据\n请确保已提取ESG报告', 
                    ha='center', va='center', fontsize=20, color='gray')
            ax.axis('off')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            buf.seek(0)
            return buf
        
        # 构建词频字典
        # topics_data 格式: [(topic, weight, category), ...]
        word_freq = {}
        for item in topics_data:
            if len(item) >= 2:
                topic = item[0]
                weight = item[1]
                word_freq[topic] = weight * 100
        
        print(f"词云生成 - 词频字典: {len(word_freq)} 个词")
        
        # 如果没有有效数据，返回占位图
        if not word_freq or all(w <= 0 for w in word_freq.values()):
            print("词云生成 - 数据无效，返回占位图")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, '数据无效\n请检查ESG报告数据', 
                    ha='center', va='center', fontsize=20, color='gray')
            ax.axis('off')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close(fig)
            buf.seek(0)
            return buf
        
        # [FIXED] 改进字体路径处理，支持项目目录下的字体文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 按优先级查找字体：项目目录 > 系统目录
        possible_fonts = [
            os.path.join(current_dir, '..', 'assets', 'fonts', 'simhei.ttf'),
            os.path.join(current_dir, '..', 'simhei.ttf'),
            'simhei.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            'C:\\Windows\\Fonts\\simhei.ttf',
        ]
        
        font_path = None
        for font in possible_fonts:
            if os.path.exists(font):
                font_path = font
                print(f"词云生成 - 使用字体: {font_path}")
                break
        
    # 生成词云 - [FIXED] 使用与趋势图相同的高度
        try:
            wc = WordCloud(
                font_path=font_path,
                width=800,
                height=500,  # [FIXED] 与趋势图高度一致 (500px)
                background_color='white',
                max_words=50,
                colormap='viridis',
                prefer_horizontal=0.7,
                min_font_size=10,
                max_font_size=100,
                random_state=42
            )
            wc.generate_from_frequencies(word_freq)
            print("词云生成 - WordCloud 生成成功")
        except Exception as e:
            print(f"警告: 词云字体加载失败 ({e})，使用默认字体")
            wc = WordCloud(
                width=800,
                height=500,  # [FIXED] 与趋势图高度一致 (500px)
                background_color='white',
                max_words=50,
                colormap='viridis',
                random_state=42
            )
            wc.generate_from_frequencies(word_freq)
        
        # 转换为图片 - [FIXED] 与趋势图保持相同比例
        fig, ax = plt.subplots(figsize=(10, 6.25))  # [FIXED] 保持与500px高度相同的比例
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        ax.set_xlim(0, wc.width)
        ax.set_ylim(wc.height, 0)
        
        # 保存到内存
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        
        print(f"词云生成 - 图片生成成功，大小: {buf.getbuffer().nbytes} bytes")
        return buf
        
    except Exception as e:
        print(f"词云生成错误: {e}")
        import traceback
        traceback.print_exc()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'词云生成失败\n{str(e)[:100]}', 
                ha='center', va='center', fontsize=14, color='red')
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf


def create_trend_chart(trend_data, selected_topic=None):
    """创建趋势折线图"""
    # 检查是否有数据
    if not trend_data or len(trend_data) == 0:
        # 返回空图
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': '📈 Top 10 增长最快议题趋势',
                'font': {'size': 18}
            },
            xaxis_title='时间',
            yaxis_title='热度指数',
            height=500,
            template='plotly_white',
            annotations=[{
                'text': '暂无趋势数据<br>请确保已提取ESG报告',
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'font': {'size': 20, 'color': 'gray'}
            }]
        )
        return fig
    
    # 生成季度标签
    quarters = [f'Q{(i%4)+1}\n{2022 + i//4}' for i in range(12)]
    
    fig = go.Figure()
    
    # 定义颜色
    colors = px.colors.qualitative.Set2
    
    for i, item in enumerate(trend_data):
        topic = item['topic']
        trend = item['trend']
        
        # 判断是否高亮
        if selected_topic:
            is_selected = (topic == selected_topic)
            opacity = 1.0 if is_selected else 0.2
            width = 4 if is_selected else 1
        else:
            opacity = 0.8
            width = 2
        
        fig.add_trace(go.Scatter(
            x=quarters,
            y=trend,
            mode='lines+markers',
            name=topic,
            line=dict(
                color=colors[i % len(colors)],
                width=width
            ),
            opacity=opacity,
            hovertemplate=f'<b>{topic}</b><br>热度: %{{y:.1f}}<extra></extra>'
        ))
    
    # [FIXED] 移除标题（上方已有大标题），调整布局与词云图对齐
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.25,  # [FIXED] 调整图例位置
            xanchor='center',
            x=0.5,
            font=dict(size=10)  # [FIXED] 减小字体以适应空间
        ),
        height=500,  # [FIXED] 与词云图高度一致
        margin=dict(t=20, b=100, l=50, r=50),  # [FIXED] 减少顶部边距，增加底部边距
        template='plotly_white',
        xaxis=dict(title='时间'),
        yaxis=dict(title='热度指数')
    )
    
    return fig


def render_topic_panorama():
    """渲染模块一界面"""
    st.markdown("## 📊 行业实质性议题全景图")
    st.markdown("**技术栈**: LDA主题模型 + TF-IDF关键词提取（模拟数据展示）")
    st.markdown("---")
    
    # 初始化分析器
    use_real = st.session_state.get('use_real_data', False)
    analyzer = TopicAnalyzer(use_real_data=use_real)
    
    # 获取数据
    hot_topics = analyzer.get_current_hot_topics(top_n=30)
    growing_topics = analyzer.get_fastest_growing_topics(top_n=10)
    
    # === 左右分栏布局 ===
    col1, col2 = st.columns([1, 1])
    
    # === 左侧：词云图 ===
    with col1:
        st.markdown("### 🔥 2025年度核心议题热度快照")
        
        # 生成词云
        with st.spinner("生成词云中..."):
            wordcloud_buf = generate_wordcloud_image(hot_topics)
            st.image(wordcloud_buf, use_container_width=True)
        
        # 下拉选择器（用于联动）
        topic_options = [item['topic'] for item in growing_topics]
        selected_topic = st.selectbox(
            "🔍 选择议题查看趋势详情",
            options=["全部显示"] + topic_options,
            key="topic_selector"
        )
        
        # 显示统计信息
        st.markdown("#### 📋 议题分布统计")
        category_counts = {}
        for topic, weight, category in hot_topics:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        cols = st.columns(3)
        for i, (cat, count) in enumerate(category_counts.items()):
            with cols[i % 3]:
                color = {"E环境": "🟢", "S社会": "🔵", "G治理": "🟠"}.get(cat, "⚪")
                st.metric(f"{color} {cat}", f"{count} 个议题")
    
    # === 右侧：趋势图 ===
    with col2:
        st.markdown("### 📈 增长最快议题趋势追踪")
        
        # 处理选择
        highlight_topic = None if selected_topic == "全部显示" else selected_topic
        
        # 绘制趋势图
        trend_fig = create_trend_chart(growing_topics, highlight_topic)
        st.plotly_chart(trend_fig, use_container_width=True)
        
        # 增长率排行
        st.markdown("#### 🚀 增长率排行")
        growth_df = pd.DataFrame([
            {
                "议题": item['topic'],
                "当前热度": f"{item['current']:.1f}",
                "季度增长率": f"{item['growth_rate']:.2f}%",
                "趋势": "📈" if item['growth_rate'] > 0 else "📉"
            }
            for item in growing_topics[:5]
        ])
        st.dataframe(growth_df, hide_index=True, use_container_width=True)
    
    # === 详细分析面板 ===
    st.markdown("---")
    with st.expander("📊 查看完整议题数据", expanded=False):
        # 检查是否有数据
        if not hot_topics:
            st.info("暂无议题数据，请先提取ESG报告数据")
        else:
            # 转换为DataFrame
            full_df = pd.DataFrame([
                {
                    "议题": topic,
                    "权重": f"{weight:.3f}",
                    "分类": category,
                    "热度得分": f"{weight * 100:.1f}"
                }
                for topic, weight, category in hot_topics
            ])
            
            # 分类筛选
            if category_counts:
                cat_filter = st.multiselect(
                    "按分类筛选",
                    options=list(category_counts.keys()),
                    default=list(category_counts.keys())
                )
                filtered_df = full_df[full_df['分类'].isin(cat_filter)]
                st.dataframe(filtered_df, hide_index=True, use_container_width=True)
            else:
                st.dataframe(full_df, hide_index=True, use_container_width=True)
    
    # === 业务价值说明 ===
    st.markdown("---")
    st.info("""
    **📌 业务价值**
    - **词云图**: 一眼看到今年行业必须覆盖的重点议题
    - **趋势图**: 发现那些虽然现在权重较小，但增长极快的议题，提前布局建立先发优势
    - **数据来源**: 基于行业ESG报告、监管政策、新闻舆情的综合分析（当前为模拟数据）
    """)