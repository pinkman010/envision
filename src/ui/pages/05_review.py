"""
人工复核中心页面
功能：复核AI生成的优化建议，确认/修改后导出最终版本
"""

import streamlit as st
import json
from datetime import datetime

from src.core_config import settings, get_logger

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("✅ 人工复核中心")
st.divider()

# 检查是否有待复核内容
if "pending_review_content" not in st.session_state or not st.session_state.pending_review_content:
    st.warning("⚠️ 暂无待复核的优化建议")
    st.info("请先在「差距分析与优化建议」页面生成建议后进入复核")
    if st.button("📊 前往差距分析", use_container_width=True):
        st.switch_page("pages/04_analysis.py")
    st.stop()

review_content = st.session_state.pending_review_content

# 复核声明
st.error(
    "⚠️ **复核声明**：\n\n"
    "1. 以下内容仅为AI辅助生成的优化建议，不构成任何合规决策；\n"
    "2. 最终决策权100%在企业ESG团队手里；\n"
    "3. 所有用于对外披露的内容，必须经人工复核确认。"
)

# 显示优先行动
priority_actions = review_content.get("priority_actions", [])
if priority_actions:
    st.subheader("🎯 优先行动（Top 3）")
    for i, action in enumerate(priority_actions[:3], 1):
        st.markdown(f"**{i}.** {action}")

st.divider()

# 显示建议复核列表
st.subheader("📝 建议复核列表")

recommendations = review_content.get("recommendations", [])
if recommendations:
    # 初始化复核状态（如果还没有）
    if "review_status" not in st.session_state:
        st.session_state.review_status = {}
    
    for idx, rec in enumerate(recommendations):
        topic = rec.get("topic_name", "未知议题")
        action = rec.get("action", "")
        priority = rec.get("priority", "")
        standard = rec.get("standard_basis", "")
        
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
        priority_label = {"high": "高", "medium": "中", "low": "低"}.get(priority, "未知")
        
        with st.expander(f"{priority_icon} {topic}（优先级：{priority_label}）"):
            st.markdown(f"**议题**: {topic}")
            
            # 可编辑的建议内容
            edited_action = st.text_area(
                f"建议内容_{idx}",
                value=action,
                height=100,
                label_visibility="collapsed",
            )
            
            if standard:
                st.markdown(f"**依据标准**: {standard}")
            
            # 复核状态选择
            status_key = f"review_status_{idx}"
            if status_key not in st.session_state.review_status:
                st.session_state.review_status[status_key] = "pending"
            
            status = st.radio(
                f"复核状态_{idx}",
                options=["pending", "approved", "rejected", "modified"],
                format_func=lambda x: {
                    "pending": "⏳ 待复核",
                    "approved": "✅ 通过",
                    "rejected": "❌ 不采纳",
                    "modified": "✏️ 已修改",
                }.get(x, x),
                key=status_key,
                horizontal=True,
            )
            
            # 备注
            note_key = f"review_note_{idx}"
            if note_key not in st.session_state:
                st.session_state[note_key] = ""
            st.text_input(
                f"复核备注_{idx}",
                placeholder="添加复核备注...",
                key=note_key,
            )
    
    # 统计复核状态
    approved_count = sum(1 for i in range(len(recommendations)) if st.session_state.get(f"review_status_{i}") == "approved")
    rejected_count = sum(1 for i in range(len(recommendations)) if st.session_state.get(f"review_status_{i}") == "rejected")
    modified_count = sum(1 for i in range(len(recommendations)) if st.session_state.get(f"review_status_{i}") == "modified")
    pending_count = len(recommendations) - approved_count - rejected_count - modified_count
    
    st.divider()
    st.subheader("📊 复核统计")
    cols = st.columns(4)
    with cols[0]:
        st.metric("已通过", approved_count)
    with cols[1]:
        st.metric("已修改", modified_count)
    with cols[2]:
        st.metric("不采纳", rejected_count)
    with cols[3]:
        st.metric("待复核", pending_count)
    
    # 复核进度
    progress = (approved_count + modified_count + rejected_count) / len(recommendations)
    st.progress(progress, text=f"复核进度: {progress:.0%}")

else:
    st.warning("没有可复核的建议列表")

st.divider()

# 完整建议文本
st.subheader("📄 完整建议文本（最终版）")
generated_content = review_content.get("generated_content", "")
if generated_content:
    final_content = st.text_area(
        "最终建议文本（可编辑）",
        value=generated_content,
        height=400,
    )
else:
    final_content = ""

# 导出选项
st.subheader("📥 导出最终版本")
col1, col2 = st.columns(2)

with col1:
    # 导出文本
    if final_content:
        st.download_button(
            label="📄 下载建议文本",
            data=final_content,
            file_name=f"ESG_优化建议_已复核_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

with col2:
    # 导出JSON（包含复核状态）
    if recommendations:
        export_data = {
            "recommendations": [
                {
                    **rec,
                    "review_status": st.session_state.get(f"review_status_{i}", "pending"),
                    "review_note": st.session_state.get(f"review_note_{i}", ""),
                }
                for i, rec in enumerate(recommendations)
            ],
            "priority_actions": priority_actions,
            "final_content": final_content,
            "exported_at": datetime.now().isoformat(),
        }
        st.download_button(
            label="📋 下载完整报告(JSON)",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name=f"ESG_优化报告_已复核_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

st.divider()

# 下一步操作
st.subheader("➡️ 下一步操作")
col1, col2 = st.columns(2)
with col1:
    if st.button("📊 返回差距分析", use_container_width=True):
        st.switch_page("pages/04_analysis.py")
with col2:
    if st.button("🏠 返回首页", use_container_width=True):
        # 清空复核状态，避免污染下次使用
        st.session_state.pending_review_content = None
        st.session_state.review_status = {}
        st.switch_page("pages/01_home.py")
