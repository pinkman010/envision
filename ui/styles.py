"""UI样式定义

集中管理所有CSS样式和样式常量。
"""

# Streamlit自定义CSS
CUSTOM_CSS = """
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
"""

# ESG维度颜色映射
ESG_COLORS = {
    'E': '#52c41a',
    'S': '#1890ff',
    'G': '#faad14'
}

# ESG维度名称映射
ESG_DIMENSION_NAMES = {
    'E': '环境',
    'S': '社会',
    'G': '治理'
}

# 严重程度样式映射
SEVERITY_STYLES = {
    '高': {'icon': '🔴', 'class': 'diagnosis-high', 'color': '#ff4d4f'},
    '中': {'icon': '🟡', 'class': 'diagnosis-medium', 'color': '#faad14'},
    '低': {'icon': '🟢', 'class': 'diagnosis-low', 'color': '#52c41a'}
}

# 优先级颜色映射
PRIORITY_COLORS = {
    '高': '#ff4d4f',
    '中': '#faad14',
    '低': '#52c41a'
}


def apply_styles():
    """应用自定义CSS样式"""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
