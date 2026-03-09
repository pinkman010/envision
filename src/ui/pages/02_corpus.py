"""
ESG语料管理中心页面
功能：上传ESG报告、查看语料处理结果、预览原文
"""

import streamlit as st
import requests
from pathlib import Path

from src.core_config import settings, get_logger

# 初始化logger
logger = get_logger(__name__)

# 页面配置（已在app.py全局配置，这里仅设置页面标题）
st.title("📄 ESG报告处理模块")
st.divider()

# 上传文件区域
st.subheader("📤 上传ESG报告")
uploaded_file = st.file_uploader(
    "选择PDF/Word/Excel文件",
    type=["pdf", "docx", "xlsx"],
    help="支持PDF、Word、Excel格式，最大50MB",
)
process_button = st.button("🚀 开始处理文件", use_container_width=True)
st.divider()


# 主内容区
if "corpus_result" not in st.session_state:
    st.session_state.corpus_result = None

# 1. 处理上传的文件
if process_button and uploaded_file:
    with st.spinner("正在处理，请稍候..."):
        try:
            logger.info(f"用户上传语料: {uploaded_file.name}")
            # 调用API层的语料处理接口
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(
                f"{settings.API_BASE_URL}{settings.API_PREFIX}/corpus/process",
                files=files,
                timeout=300,
            )
            response.raise_for_status()
            result = response.json()
            
            if result["code"] == 200:
                st.session_state.corpus_result = result["data"]
                st.success("✅ 处理成功！")
                logger.info(f"语料处理成功: {uploaded_file.name}")
            else:
                st.error(f"❌ 处理失败: {result['message']}")
                logger.error(f"语料处理失败: {result['message']}")
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ 网络请求失败: {str(e)}")
            logger.error(f"网络请求失败: {str(e)}", exc_info=True)
        except Exception as e:
            st.error(f"❌ 系统错误: {str(e)}")
            logger.critical(f"系统错误: {str(e)}", exc_info=True)

# 2. 显示语料处理结果
if st.session_state.corpus_result:
    corpus_data = st.session_state.corpus_result
    metadata = corpus_data["metadata"]
    
    # 2.1 显示元数据
    st.subheader("📊 语料元数据")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("文件名", metadata["file_name"])
    with col2:
        st.metric("文件大小", f"{metadata['file_size']/1024/1024:.2f}MB")
    with col3:
        st.metric("文本长度", f"{metadata['text_length']:,} 字符")
    with col4:
        st.metric("分块数", metadata["chunk_count"])
    
    st.divider()
    
    # 2.2 预览原文
    st.subheader("📖 原文预览")
    with st.expander("点击展开/收起原文", expanded=False):
        st.text_area(
            "修复后的文本",
            value=corpus_data["fixed_text"],
            height=400,
            disabled=True,
        )
    
    st.divider()
    
    # 2.3 下一步操作
    st.subheader("➡️ 下一步操作")
    if st.button("🔍 进入信息抽取", use_container_width=True):
        st.switch_page("pages/03_materiality.py")
