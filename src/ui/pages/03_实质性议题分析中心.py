"""
实质性议题分析中心页面
功能：调用信息抽取接口、查看抽取结果、相似度校验、进入合规提示
"""

import streamlit as st
import requests

from src.core_config import settings, get_logger
from src.ui.components import highlight_text

# 初始化logger
logger = get_logger(__name__)

# 页面配置
st.title("🔍 实质性议题分析中心")
st.divider()

# 检查是否有语料处理结果
if "corpus_result" not in st.session_state or not st.session_state.corpus_result:
    st.warning("⚠️ 请先在「ESG语料管理中心」上传并处理语料")
    if st.button("📄 前往语料管理中心", use_container_width=True):
        st.switch_page("pages/02_ESG语料管理中心.py")
    st.stop()

# 主内容区
if "extract_result" not in st.session_state:
    st.session_state.extract_result = None

corpus_data = st.session_state.corpus_result
fixed_text = corpus_data["fixed_text"]

# 1. 调用信息抽取接口
if not st.session_state.extract_result:
    with st.spinner("正在执行信息抽取，请稍候..."):
        try:
            logger.info("用户开始信息抽取")
            # 调用API层的信息抽取接口
            request_data = {"corpus_result": corpus_data}
            response = requests.post(
                f"{settings.API_BASE_URL}{settings.API_PREFIX}/extract/run",
                json=request_data,
                timeout=300,
            )
            response.raise_for_status()
            result = response.json()
            
            if result["code"] == 200:
                st.session_state.extract_result = result["data"]
                st.success("✅ 信息抽取成功！")
                logger.info("信息抽取成功")
            else:
                st.error(f"❌ 信息抽取失败: {result['message']}")
                logger.error(f"信息抽取失败: {result['message']}")
        
        except Exception as e:
            st.error(f"❌ 系统错误: {str(e)}")
            logger.critical(f"系统错误: {str(e)}", exc_info=True)

# 2. 显示信息抽取结果
if st.session_state.extract_result:
    extract_data = st.session_state.extract_result
    extraction_results = extract_data["extraction_results"]
    
    # 2.1 显示抽取统计
    st.subheader("📊 抽取结果统计")
    passed_count = len([r for r in extraction_results if r.get("validation_status") == "passed"])
    failed_count = len([r for r in extraction_results if r.get("validation_status") == "failed"])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总抽取字段数", len(extraction_results))
    with col2:
        st.metric("校验通过", passed_count, delta_color="normal")
    with col3:
        st.metric("校验失败", failed_count, delta_color="inverse")
    
    st.divider()
    
    # 2.2 显示详细抽取结果
    st.subheader("📝 详细抽取结果")
    for idx, result in enumerate(extraction_results):
        field_name = result["field_name"]
        extracted_content = result["extracted_content"]
        validation_status = result["validation_status"]
        similarity = result.get("similarity", 0.0)
        char_start = result["char_start"]
        char_end = result["char_end"]
        
        # 根据校验状态显示不同的颜色
        status_color = "#00A86B" if validation_status == "passed" else "#DC2626"
        status_text = "✅ 校验通过" if validation_status == "passed" else "❌ 校验失败"
        
        with st.expander(
            f"{status_text} | {field_name} | 相似度: {similarity:.2%}",
            expanded=validation_status == "failed",
        ):
            st.markdown(f"**字段名**: {field_name}")
            st.markdown(f"**抽取内容**: {extracted_content}")
            st.markdown(f"**字符位置**: {char_start} - {char_end}")
            st.markdown(f"**校验状态**: <span style='color:{status_color};font-weight:bold;'>{status_text}</span>", unsafe_allow_html=True)
            
            # 显示高亮原文片段
            st.markdown("**原文对应片段（高亮显示）**:")
            # 取前后各100字符作为上下文
            context_start = max(0, char_start - 100)
            context_end = min(len(fixed_text), char_end + 100)
            highlighted_snippet = highlight_text(
                fixed_text[context_start:context_end],
                char_start - context_start,
                char_end - context_start,
                color=status_color,
            )
            st.markdown(f"...{highlighted_snippet}...", unsafe_allow_html=True)
    
    st.divider()
    
    # 2.3 下一步操作
    st.subheader("➡️ 下一步操作")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚠️ 进入合规提示", use_container_width=True):
            st.switch_page("pages/05_披露优化与策略助手.py")
    with col2:
        if st.button("📄 重新上传语料", use_container_width=True):
            st.session_state.corpus_result = None
            st.session_state.extract_result = None
            st.switch_page("pages/02_ESG语料管理中心.py")
