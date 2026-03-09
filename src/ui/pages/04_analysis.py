"""
差距分析与优化建议页面
功能：基于标准进行差距分析、与同行对比、生成优化建议
"""

import streamlit as st
import requests
import json
from datetime import datetime

from src.config import settings, get_logger

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("📊 差距分析与优化建议")
st.divider()

# 检查是否有议题检索结果
if "retrieval_result" not in st.session_state or not st.session_state.retrieval_result:
    st.warning("⚠️ 请先在「议题识别与知识库检索」完成议题识别")
    if st.button("🔍 前往议题识别", use_container_width=True):
        st.switch_page("pages/03_materiality.py")
    st.stop()

retrieval_result = st.session_state.retrieval_result

# 初始化session_state
if "analyst_result" not in st.session_state:
    st.session_state.analyst_result = None
if "advisor_result" not in st.session_state:
    st.session_state.advisor_result = None

# ==================== 第一部分：差距分析 ====================
st.markdown("### 📊 差距分析")

if st.button("🔍 获取差距分析", use_container_width=True, type="primary"):
    with st.spinner("正在生成差距分析，请稍候..."):
        try:
            logger.info("用户请求差距分析")
            request_data = {"retrieval_result": retrieval_result}
            response = requests.post(
                f"{settings.API_BASE_URL}{settings.API_PREFIX}/analyst/analyze",
                json=request_data,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            
            if result["code"] == 200:
                st.session_state.analyst_result = result["data"]
                st.success("✅ 差距分析生成成功！")
                logger.info("差距分析生成成功")
            else:
                st.error(f"❌ 差距分析生成失败: {result['message']}")
                logger.error(f"差距分析生成失败: {result['message']}")
        
        except Exception as e:
            st.error(f"❌ 系统错误: {str(e)}")
            logger.error(f"差距分析请求失败: {str(e)}", exc_info=True)

# 显示差距分析结果
if st.session_state.analyst_result:
    analyst_data = st.session_state.analyst_result
    gap_analysis = analyst_data.get("gap_analysis", [])
    peer_comparison = analyst_data.get("peer_comparison", [])
    overall_assessment = analyst_data.get("overall_assessment", "")
    
    # 显示整体评估
    if overall_assessment:
        st.info(f"📋 **整体评估**: {overall_assessment}")
    
    # 按gap_level分组显示差距
    if gap_analysis:
        st.subheader("🔍 差距详情")
        
        major_gaps = [g for g in gap_analysis if g.get("gap_level") == "major"]
        minor_gaps = [g for g in gap_analysis if g.get("gap_level") == "minor"]
        no_gaps = [g for g in gap_analysis if g.get("gap_level") == "none"]
        
        # 显示重大差距
        if major_gaps:
            st.error(f"**🔴 重大差距（{len(major_gaps)}项）**")
            for gap in major_gaps:
                topic = gap.get("topic_name", "未知议题")
                gap_desc = gap.get("gap", "未描述")
                standard_ref = gap.get("standard_ref", "N/A")
                
                with st.expander(f"{topic} - {gap_desc[:30]}... [{standard_ref}]"):
                    st.markdown(f"**议题**: {topic}")
                    st.markdown(f"**现有披露**: {gap.get('current_disclosure', 'N/A')}")
                    st.markdown(f"**标准要求**: {gap.get('standard_requirement', 'N/A')}")
                    st.markdown(f"**差距说明**: {gap_desc}")
                    st.markdown(f"**参考标准**: {standard_ref}")
                    # 查找同行对比
                    peer = next((p for p in peer_comparison if p.get("topic_name") == topic), None)
                    if peer:
                        st.markdown(f"**同行做法**: {peer.get('peer_practice', 'N/A')}")
                        st.markdown(f"**我方位置**: {peer.get('our_position', 'N/A')}")
        
        # 显示轻微差距
        if minor_gaps:
            st.warning(f"**🟡 轻微差距（{len(minor_gaps)}项）**")
            for gap in minor_gaps:
                topic = gap.get("topic_name", "未知议题")
                gap_desc = gap.get("gap", "未描述")
                standard_ref = gap.get("standard_ref", "N/A")
                
                with st.expander(f"{topic} - {gap_desc[:30]}... [{standard_ref}]"):
                    st.markdown(f"**议题**: {topic}")
                    st.markdown(f"**现有披露**: {gap.get('current_disclosure', 'N/A')}")
                    st.markdown(f"**标准要求**: {gap.get('standard_requirement', 'N/A')}")
                    st.markdown(f"**差距说明**: {gap_desc}")
                    st.markdown(f"**参考标准**: {standard_ref}")
        
        # 显示无差距（符合要求）
        if no_gaps:
            st.success(f"**🟢 符合要求（{len(no_gaps)}项）**")
            for gap in no_gaps:
                topic = gap.get("topic_name", "未知议题")
                with st.expander(f"{topic} - 披露符合要求"):
                    st.markdown(f"**议题**: {topic}")
                    st.markdown(f"**现有披露**: {gap.get('current_disclosure', 'N/A')}")
                    st.markdown(f"**符合的标准**: {gap.get('standard_ref', 'N/A')}")
    else:
        st.success("✅ 未发现明显差距")

st.divider()

# ==================== 第二部分：优化建议 ====================
st.markdown("### 💡 优化建议")

if st.button("🚀 生成优化建议", use_container_width=True, type="primary"):
    if not st.session_state.analyst_result:
        st.warning("⚠️ 请先生成差距分析结果")
    else:
        with st.spinner("正在生成优化建议，请稍候..."):
            try:
                logger.info("用户请求生成优化建议")
                request_data = {"analyst_result": st.session_state.analyst_result}
                response = requests.post(
                    f"{settings.API_BASE_URL}{settings.API_PREFIX}/advisor/recommend",
                    json=request_data,
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
                
                if result["code"] == 200:
                    st.session_state.advisor_result = result["data"]
                    st.success("✅ 优化建议生成成功！")
                    logger.info("优化建议生成成功")
                else:
                    st.error(f"❌ 优化建议生成失败: {result['message']}")
                    logger.error(f"优化建议生成失败: {result['message']}")
            
            except Exception as e:
                st.error(f"❌ 系统错误: {str(e)}")
                logger.error(f"优化建议请求失败: {str(e)}", exc_info=True)

# 显示优化建议结果
if st.session_state.advisor_result:
    advisor_data = st.session_state.advisor_result
    recommendations = advisor_data.get("recommendations", [])
    priority_actions = advisor_data.get("priority_actions", [])
    generated_content = advisor_data.get("generated_content", "")
    
    # 显示优先行动
    if priority_actions:
        st.subheader("🎯 优先行动（Top 3）")
        for i, action in enumerate(priority_actions[:3], 1):
            st.markdown(f"**{i}.** {action}")
    
    # 显示完整建议列表
    if recommendations:
        st.subheader("📋 完整建议列表")
        
        # 按优先级分组
        high_recs = [r for r in recommendations if r.get("priority") == "high"]
        medium_recs = [r for r in recommendations if r.get("priority") == "medium"]
        low_recs = [r for r in recommendations if r.get("priority") == "low"]
        
        for rec in high_recs + medium_recs + low_recs:
            topic = rec.get("topic_name", "未知议题")
            action = rec.get("action", "")
            priority = rec.get("priority", "")
            standard = rec.get("standard_basis", "")
            reference = rec.get("reference_case", "")
            
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            
            with st.expander(f"{priority_icon} {topic}"):
                st.markdown(f"**建议**: {action}")
                if standard:
                    st.markdown(f"**依据标准**: {standard}")
                if reference:
                    st.markdown(f"**参考案例**: {reference}")
    
    # 显示完整建议文本
    if generated_content:
        st.subheader("📄 完整建议文本（可编辑+下载）")
        edited_content = st.text_area(
            "建议文本（可编辑）",
            value=generated_content,
            height=400,
        )
        
        # 导出选项
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 下载建议文本",
                data=edited_content,
                file_name=f"ESG_优化建议_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            if st.button("✅ 确认并进入人工复核", use_container_width=True):
                # 保存到session_state供复核页面使用
                st.session_state.pending_review_content = {
                    "recommendations": recommendations,
                    "priority_actions": priority_actions,
                    "generated_content": edited_content,
                    "generated_at": datetime.now().isoformat(),
                }
                st.switch_page("pages/05_review.py")

st.divider()

# 下一步操作
st.subheader("➡️ 下一步操作")
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ 进入人工复核", use_container_width=True):
        st.switch_page("pages/05_review.py")
with col2:
    if st.button("🔍 返回议题识别", use_container_width=True):
        st.switch_page("pages/03_materiality.py")
