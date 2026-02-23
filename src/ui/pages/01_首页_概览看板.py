"""
首页：概览看板
功能：系统介绍、快速操作入口、核心数据展示
"""

import streamlit as st

from src.core_config import settings

# 页面配置（app.py全局配置）
st.header("🌱 ESG信息披露与沟通智能分析系统")
st.subheader("规则驱动、AI辅助的强合规分析工具")
st.divider()

# 系统介绍
st.markdown("### 系统定位")
st.info(
    "本系统针对新能源行业ESG披露的强合规、强监管场景设计，"
    "采用「人工定规则+AI做提取+白盒做校验+人工做决策」的混合架构。"
)
st.caption(f"版本：v{settings.VERSION} | 环境：{settings.ENVIRONMENT}")

st.divider()

# 核心数据看板（MVP阶段用静态数据演示，后期对接数据库）
st.markdown("### 📊 核心数据看板")
st.markdown("#### （MVP阶段用静态数据演示，后期对接数据库）")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="已接入语料库",
        value="120+",
        delta="TOP100新能源企业",
        help="已预加载新能源行业20份ESG报告",
    )
with col2:
    st.metric(
        label="覆盖披露标准",
        value="3套",
        delta="ISSB/SASB/HKEX",
        help="支持ISSB IFRS S1/S2、SASB可再生能源行业标准、港股HKEX披露要求",
    )
with col3:
    st.metric(
        label="核心实质性议题",
        value="15个",
        delta="新能源行业专属",
        help="基于新能源行业特性定制的15个核心实质性议题",
    )
with col4:
    st.metric(
        label="合规审计覆盖率",
        value="100%",
        delta="字符级双向溯源",
        help="所有操作全链路留痕，AI抽取内容支持字符级溯源到原文",
    )

st.divider()

# 快速操作入口
st.markdown("### 🚀 快速开始")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📄 导入ESG语料", use_container_width=True, type="primary"):
        st.switch_page("pages/02_ESG语料管理中心.py")
with col2:
    if st.button("🔍 分析实质性议题", use_container_width=True):
        st.switch_page("pages/03_实质性议题分析中心.py")
with col3:
    if st.button("📊 做企业对标分析", use_container_width=True):
        st.switch_page("pages/04_ESG对标分析中心.py")

st.divider()

# 合规声明（醒目标注）
st.markdown("### ⚠️ 合规声明")
st.error(
    "**重要提示**：\n\n"
    "1. 本系统的AI输出仅为辅助参考，不构成任何披露建议、投资建议或法律意见；\n"
    "2. 所有用于对外披露的内容，必须经企业ESG团队人工复核确认；\n"
    "3. 使用人自行承担所有法律责任与披露责任。"
)
