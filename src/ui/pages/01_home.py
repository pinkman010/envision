"""
首页：P0 概览看板
功能：展示当前 P0 fixed-report 工作台状态和入口
"""

import streamlit as st

from src.config import settings

# 页面配置（app.py全局配置）
st.header("ESG 披露证据核验工作台")
st.subheader("单报告、条款级、证据可追溯的 P0 复核工具")
st.divider()

# 系统介绍
st.markdown("### 系统定位")
st.info(
    "当前 P0 基于远景能源 2024 中文 ESG 报告和 GRI 参照披露条款，"
    "展示 143 条 current disclosure assessment units、证据页码、requirement checks、"
    "AI-assisted Advisor coverage 和人工复核入口。"
)
st.caption(f"版本：v{settings.VERSION} | 环境：{settings.ENVIRONMENT}")

st.divider()

# 核心数据看板
st.markdown("### 核心状态")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="Assessment units",
        value="143",
        delta="current disclosure",
        help="114 条普通披露项 + 29 条 GRI 3-3 议题级实例。",
    )
with col2:
    st.metric(
        label="Advisor coverage",
        value="143",
        delta="AI-assisted",
        help="141 条建议 + 2 条 disclosed/no-action coverage，均等待人工复核。",
    )
with col3:
    st.metric(
        label="Review status",
        value="pending",
        delta="human review",
        help="当前数据可用于页面展示和人工复核录入，不能表述为最终人工验证通过。",
    )
with col4:
    st.metric(
        label="Evaluation status",
        value="pending",
        delta="F metrics",
        help="F 阶段指标和误差归因需在人工评测确认后再计算或展示。",
    )

st.divider()

# 快速操作入口
st.markdown("### 快速开始")
col1, col2 = st.columns(2)
with col1:
    if st.button("进入条款复核", use_container_width=True, type="primary"):
        st.switch_page("pages/09_p0_review_workbench.py")
with col2:
    if st.button("查看审计日志", use_container_width=True):
        st.switch_page("pages/07_audit.py")

st.divider()

# 合规声明（醒目标注）
st.markdown("### 合规声明")
st.error(
    "**重要提示**：\n\n"
    "1. 当前 AI 输出仅为披露证据核验辅助，不构成合规结论、投资建议或法律意见；\n"
    "2. Advisor 内容状态为 AI-assisted recommendation pending human review；\n"
    "3. 页面不得用于宣称最终准确率、人工验证通过或最终建议已确认。"
)
