"""RAG智能问答模块

提供基于知识库的AI智能问答功能。
"""

from typing import Any, Dict

import streamlit as st

from src.esg.config import RAW_DATA_DIR
from src.esg.ui.components import render_header


def render_rag_page(config: Dict[str, Any]) -> None:
    """渲染RAG智能问答页面

    Args:
        config: 配置参数
    """
    render_header(title="RAG智能问答", subtitle="基于知识库的AI智能问答")

    # 初始化RAG引擎和向量存储
    try:
        from src.esg.vector_store import ChromaDBStore

        store = ChromaDBStore()

        # 自动加载数据（如果知识库为空）
        if store.is_available() and store.count() == 0:
            with st.spinner("🔄 正在自动加载知识库..."):
                loaded_count = store.auto_load_from_directory(str(RAW_DATA_DIR))
                if loaded_count > 0:
                    st.success(f"✅ 已自动加载 {loaded_count} 个文档到知识库")

        rag_engine = _get_rag_engine()
    except Exception as e:
        st.error(f"初始化失败: {e}")
        st.info("请确保向量数据库已正确配置")
        return

    # 页面说明
    st.info("""
    💡 **RAG (Retrieval-Augmented Generation)** 功能说明：
    - 使用 DeepSeek-R1 本地大语言模型
    - 基于 ChromaDB 向量数据库进行知识检索
    - 答案基于知识库中的ESG相关文档
    - 知识库会自动扫描 data/01_raw 目录下的PDF文件
    """)

    # 显示知识库状态
    st.markdown("### 📊 知识库状态")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("使用模型", "DeepSeek-R1")
    with col2:
        if store.is_available():
            doc_count = store.count()
            st.metric("知识库文档数", doc_count)
        else:
            st.metric("知识库文档数", "未初始化")
    with col3:
        st.metric("数据源目录", "data/01_raw")

    # 问题输入区域
    st.markdown("### ❓ 输入问题")
    question = st.text_area(
        "请输入您关于ESG的问题",
        placeholder="例如：什么是ESG评级？企业如何提高ESG评分？",
        height=100,
    )

    # 问答按钮
    if st.button("🚀 开始问答", use_container_width=True, type="primary"):
        if not question:
            st.warning("请输入问题")
        elif not store.is_available():
            st.error("向量数据库未初始化")
        elif store.count() == 0:
            st.warning("知识库为空，请确保 data/01_raw 目录下有PDF文件")
        else:
            _handle_question(question, rag_engine, store)


def _get_rag_engine():
    """获取RAG引擎实例"""
    from src.esg.rag.engine import RAGEngine

    return RAGEngine()


def _handle_question(question: str, rag_engine: Any, store: Any) -> None:
    """处理用户问答

    Args:
        question: 用户问题
        rag_engine: RAG引擎
        store: 向量存储
    """
    from src.esg.rag.engine import RAGEngine

    with st.spinner("🔍 正在检索知识库并生成答案..."):
        try:
            # 检索所有文档
            response = rag_engine.query(question, top_k=store.count())
            st.session_state.last_rag_response = response
        except Exception as e:
            st.error(f"问答失败: {e}")

    # 显示结果
    if "last_rag_response" in st.session_state:
        response = st.session_state.last_rag_response

        st.markdown("---")
        st.markdown("### 💡 答案")

        # 直接显示答案
        st.markdown(response.answer)

        # 参考来源
        if response.sources:
            with st.expander("📚 参考来源"):
                for i, source in enumerate(response.sources, 1):
                    meta = source.get("metadata", {})
                    st.markdown(
                        f"**[{i}]** 来源: {meta.get('source', '未知')} | 相关度: {source.get('score', 0):.2f}"
                    )
                    st.caption(source.get("text", "")[:200] + "...")

        # 置信度
        confidence_color = (
            "green"
            if response.confidence > 0.7
            else "orange" if response.confidence > 0.4 else "red"
        )
        st.markdown(f"**置信度:** :{confidence_color}[{response.confidence:.0%}]")
