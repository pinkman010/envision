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
        st.switch_page("pages/02_upload.py")
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
        similarity = result.get("similarity")  # 可能是 float 或 None
        char_start = result.get("char_start")
        char_end = result.get("char_end")
        line_number = result.get("line_number")  # 获取行号

        # 根据校验状态显示不同的颜色
        if validation_status == "passed":
            status_color = "#00A86B"
            status_text = "✅ 校验通过"
        elif validation_status == "not_found":
            status_color = "#6B7280"
            status_text = "⬜ 原文未找到"
        else:  # failed
            status_color = "#DC2626"
            status_text = "❌ 校验失败"

        similarity_str = f"{similarity:.2%}" if similarity is not None else "N/A"
        with st.expander(
            f"{status_text} | {field_name} | 相似度: {similarity_str}",
            expanded=validation_status == "failed",
        ):
            st.markdown(f"**字段名**: {field_name}")
            st.markdown(f"**抽取内容**: {extracted_content}")
            # 显示行号
            line_display = f"第 {line_number} 行" if line_number is not None else "N/A"
            st.markdown(f"**行号**: {line_display}")
            # 显示字符位置
            char_display = f"{char_start} - {char_end}" if char_start is not None else "N/A"
            st.markdown(f"**字符位置**: {char_display}")
            st.markdown(f"**校验状态**: <span style='color:{status_color};font-weight:bold;'>{status_text}</span>", unsafe_allow_html=True)

            # 显示高亮原文片段（仅在找到原文时）
            if char_start is not None and char_end is not None:
                st.markdown("**原文对应片段（高亮显示）**:")
                
                # 按句子分割文本，获取前后各一句作为上下文
                def get_sentence_context(text: str, start: int, end: int) -> tuple:
                    """获取目标位置前后各一句的上下文"""
                    # 定义句子分隔符
                    separators = ['。', '！', '？', '！', '？', '；', ';\n', '. ', '! ', '? ', '\n']
                    
                    # 向前查找句子边界
                    context_start = 0
                    for sep in separators:
                        pos = text.rfind(sep, 0, start)
                        if pos >= 0 and pos + 1 > context_start:
                            context_start = pos + 1
                    
                    # 确保不超过目标位置的前一个句子
                    if context_start < start:
                        # 再向前找一个句子分隔符，取前一句
                        for sep in separators:
                            pos = text.rfind(sep, 0, context_start)
                            if pos >= 0 and pos + 1 > 0:
                                context_start = pos + 1
                                break
                    
                    # 向后查找句子边界
                    context_end = len(text)
                    for sep in separators:
                        pos = text.find(sep, end)
                        if pos >= 0 and pos + 1 < context_end:
                            context_end = pos + 1
                    
                    # 确保包含目标位置的后一个句子
                    if context_end > end:
                        # 再向后找一个句子分隔符，取后一句
                        for sep in separators:
                            pos = text.find(sep, context_end)
                            if pos >= 0 and pos + 1 < len(text):
                                context_end = pos + 1
                                break
                    
                    return context_start, context_end
                
                context_start, context_end = get_sentence_context(fixed_text, char_start, char_end)
                context_start = max(0, context_start)
                context_end = min(len(fixed_text), context_end)
                
                highlighted_snippet = highlight_text(
                    fixed_text[context_start:context_end],
                    char_start - context_start,
                    char_end - context_start,
                    color=status_color,
                )
                # 只有当上下文不是完整文本时才显示省略号
                prefix = "..." if context_start > 0 else ""
                suffix = "..." if context_end < len(fixed_text) else ""
                st.markdown(f"{prefix}{highlighted_snippet}{suffix}", unsafe_allow_html=True)
    
    st.divider()
    
    # 2.3 下一步操作
    st.subheader("➡️ 下一步操作")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚠️ 进入合规提示", use_container_width=True):
            st.switch_page("pages/04_disclosure.py")
    with col2:
        if st.button("📄 重新上传语料", use_container_width=True):
            st.session_state.corpus_result = None
            st.session_state.extract_result = None
            st.switch_page("pages/02_upload.py")
