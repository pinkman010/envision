"""
议题识别与知识库检索页面
功能：调用议题检索接口、查看识别结果、进入差距分析
"""

import streamlit as st
import requests

from src.config import settings, get_logger

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("🔍 议题识别与知识库检索")
st.divider()

# 检查是否有语料处理结果
if "corpus_result" not in st.session_state or not st.session_state.corpus_result:
    st.warning("⚠️ 请先在「ESG语料管理中心」上传并处理语料")
    if st.button("📄 前往语料管理中心", use_container_width=True):
        st.switch_page("pages/02_corpus.py")
    st.stop()

# 主内容区
if "retrieval_result" not in st.session_state:
    st.session_state.retrieval_result = None

corpus_data = st.session_state.corpus_result

# 1. 调用议题检索接口
if not st.session_state.retrieval_result:
    with st.spinner("正在执行议题识别与知识库检索，请稍候..."):
        try:
            logger.info("用户开始议题检索")
            # 调用API层的议题检索接口
            request_data = {"corpus_result": corpus_data}
            response = requests.post(
                f"{settings.API_BASE_URL}{settings.API_PREFIX}/retrieval/run",
                json=request_data,
                timeout=300,
            )
            response.raise_for_status()
            result = response.json()
            
            if result["code"] == 200:
                st.session_state.retrieval_result = result["data"]
                st.success("✅ 议题识别成功！")
                logger.info("议题检索成功")
            else:
                st.error(f"❌ 议题识别失败: {result['message']}")
                logger.error(f"议题检索失败: {result['message']}")
        
        except Exception as e:
            st.error(f"❌ 系统错误: {str(e)}")
            logger.critical(f"系统错误: {str(e)}", exc_info=True)

# 2. 显示识别结果
if st.session_state.retrieval_result:
    retrieval_data = st.session_state.retrieval_result
    identified_topics = retrieval_data.get("identified_topics", [])
    retrieved_standards = retrieval_data.get("retrieved_standards", [])
    retrieved_peers = retrieval_data.get("retrieved_peers", [])
    coverage_summary = retrieval_data.get("coverage_summary", "")
    
    # 2.1 显示摘要统计
    st.subheader("📊 识别结果摘要")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("识别议题数", len(identified_topics))
    with col2:
        st.metric("检索标准条文", len(retrieved_standards))
    with col3:
        st.metric("参考同行案例", len(retrieved_peers))
    
    if coverage_summary:
        st.info(f"💡 {coverage_summary}")
    
    st.divider()
    
    # 2.2 显示识别出的ESG议题
    st.subheader("🏷️ 识别出的ESG议题")
    if identified_topics:
        # 按置信度分组显示
        high_conf = [t for t in identified_topics if t.get("confidence") == "high"]
        medium_conf = [t for t in identified_topics if t.get("confidence") == "medium"]
        low_conf = [t for t in identified_topics if t.get("confidence") == "low"]
        
        # 使用badge样式展示
        cols = st.columns(3)
        
        with cols[0]:
            if high_conf:
                st.markdown("**高置信度**")
                for topic in high_conf:
                    st.success(f"✓ {topic.get('topic_name', '未知')}")
        
        with cols[1]:
            if medium_conf:
                st.markdown("**中置信度**")
                for topic in medium_conf:
                    st.info(f"◐ {topic.get('topic_name', '未知')}")
        
        with cols[2]:
            if low_conf:
                st.markdown("**低置信度**")
                for topic in low_conf:
                    st.warning(f"○ {topic.get('topic_name', '未知')}")
        
        # 展开显示详情
        st.markdown("**议题详情**")
        for idx, topic in enumerate(identified_topics):
            topic_name = topic.get("topic_name", "未知议题")
            confidence = topic.get("confidence", "unknown")
            evidence = topic.get("evidence", "无证据")
            
            confidence_label = {"high": "高", "medium": "中", "low": "低"}.get(confidence, "未知")
            
            with st.expander(f"{topic_name}（置信度：{confidence_label}）"):
                st.markdown(f"**议题ID**: {topic.get('topic_id', 'N/A')}")
                st.markdown(f"**置信度**: {confidence_label}")
                st.markdown(f"**证据原文**:")
                st.text_area(f"evidence_{idx}", value=evidence, height=100, label_visibility="collapsed")
    else:
        st.warning("未识别到任何ESG议题")
    
    st.divider()
    
    # 2.3 显示检索到的相关标准
    st.subheader("📚 检索到的相关标准")
    if retrieved_standards:
        for idx, standard in enumerate(retrieved_standards):
            source = standard.get("source", "Unknown")
            clause_id = standard.get("clause_id", "")
            content = standard.get("content", "")[:300]
            score = standard.get("score", 0)
            
            with st.expander(f"{source} {clause_id}（相关度：{score:.1%}）"):
                st.markdown(f"**来源**: {source}")
                st.markdown(f"**条款**: {clause_id}")
                st.markdown(f"**内容**:")
                st.markdown(content + "..." if len(standard.get("content", "")) > 300 else content)
    else:
        st.info("知识库中暂无相关标准条文（standards集合为空）")
    
    st.divider()
    
    # 2.4 下一步操作
    st.subheader("➡️ 下一步操作")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 进入差距分析", use_container_width=True):
            st.switch_page("pages/04_analysis.py")
    with col2:
        if st.button("📄 重新上传语料", use_container_width=True):
            st.session_state.corpus_result = None
            st.session_state.retrieval_result = None
            st.switch_page("pages/02_corpus.py")
